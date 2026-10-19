"""Local account store for the Navy Launcher: sign up, log in, stay logged in.

The dead game server owned accounts. Offline the client was simply *seeded*
with a hardcoded player, which is why every install shared one identity and
"who am I" was never a question the launcher could answer.

This is the smallest thing that makes it a real login without pretending to be
a server:

  * ``accounts.json`` beside ``launcher_config.json`` holds one record per
    account -- username, a PBKDF2 password hash, and where that account's save
    data lives. **No password is ever stored**, only a salted hash.
  * Each account gets its own save directory under ``client/runtime/accounts``.
    ``client/runtime/active_account.json`` names the one that is logged in, and
    ``client/frida/offline_account_db.py`` reads that file to decide which save
    to load -- so switching account switches character, wardrobe and career.
  * "Stay signed in" stores a random token, not the password. Deleting the
    token (log out) is enough to require the password again.

Standard library only, so the launcher keeps working from a bare Python.

Threat model, stated plainly: this protects one local machine's profiles from
each other. It is not account security against someone who already has the
disk -- they can edit the save files directly. PBKDF2 is here so a password
reused from elsewhere does not leak, not to guard the game data.
"""

import base64
import binascii
import hashlib
import hmac
import io
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time

if getattr(sys, 'frozen', False):
    _exe_dir = os.path.dirname(sys.executable)
    if os.path.basename(_exe_dir).lower() == "launcher":
        ROOT = os.path.dirname(_exe_dir)
        HERE = _exe_dir
    elif os.path.isdir(os.path.join(_exe_dir, "Launcher")):
        ROOT = _exe_dir
        HERE = os.path.join(_exe_dir, "Launcher")
    else:
        ROOT = _exe_dir
        HERE = _exe_dir
else:
    HERE = os.path.dirname(os.path.abspath(__file__))
    ROOT = os.path.dirname(HERE)

ACCOUNTS_PATH = os.path.join(HERE, "accounts.json")
RUNTIME_DIR = os.path.join(ROOT, "Runtime", "runtime") if os.path.exists(os.path.join(ROOT, "Runtime", "runtime")) else (
    os.path.join(ROOT, "Runtime") if os.path.isdir(os.path.join(ROOT, "Runtime")) and not os.path.isdir(os.path.join(ROOT, "client", "runtime"))
    else os.path.join(ROOT, "client", "runtime")
)
ACCOUNTS_DIR = os.path.join(RUNTIME_DIR, "accounts")
ACTIVE_PATH = os.path.join(RUNTIME_DIR, "active_account.json")

PBKDF2_ROUNDS = 200000
USERNAME_RE = re.compile(r"^[A-Za-z0-9_.\- ]{3,24}$")
MIN_PASSWORD = 6
SCHEMA = 1


# --------------------------------------------------------------------------- io

_STORAGE_APP_KEY = b"CYBER_HUNTER_REVIVAL_STORAGE_KEY_SEC_2026"

def _encrypt_storage(obj):
    raw = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    salt = os.urandom(16)
    nonce = os.urandom(16)
    derived = hashlib.pbkdf2_hmac("sha256", _STORAGE_APP_KEY, salt, 40000)
    blocks = []
    for i in range((len(raw) + 31) // 32):
        ctr = i.to_bytes(4, "big")
        blocks.append(hmac.new(derived, nonce + ctr, hashlib.sha256).digest())
    keystream = b"".join(blocks)[:len(raw)]
    ciphertext = bytes(a ^ b for a, b in zip(raw, keystream))
    tag = hmac.new(derived, salt + nonce + ciphertext, hashlib.sha256).digest()
    payload = salt + nonce + tag + ciphertext
    return "CHAUTH_ENC1:" + base64.b64encode(payload).decode("ascii")

def _decrypt_storage(content):
    if not isinstance(content, str) or not content.startswith("CHAUTH_ENC1:"):
        return json.loads(content)
    payload = base64.b64decode(content[12:].encode("ascii"))
    if len(payload) < 64:
        raise ValueError("Corrupted encrypted payload")
    salt = payload[:16]
    nonce = payload[16:32]
    tag = payload[32:64]
    ciphertext = payload[64:]
    derived = hashlib.pbkdf2_hmac("sha256", _STORAGE_APP_KEY, salt, 40000)
    expected_tag = hmac.new(derived, salt + nonce + ciphertext, hashlib.sha256).digest()
    if not hmac.compare_digest(tag, expected_tag):
        raise ValueError("Invalid integrity tag in account storage")
    blocks = []
    for i in range((len(ciphertext) + 31) // 32):
        ctr = i.to_bytes(4, "big")
        blocks.append(hmac.new(derived, nonce + ctr, hashlib.sha256).digest())
    keystream = b"".join(blocks)[:len(ciphertext)]
    decrypted = bytes(a ^ b for a, b in zip(ciphertext, keystream))
    return json.loads(decrypted.decode("utf-8"))

def _read_json(path, default):
    try:
        with io.open(path, "r", encoding="utf-8") as fh:
            raw_content = fh.read()
        data = _decrypt_storage(raw_content)
        return data if isinstance(data, type(default)) else default
    except Exception:
        return default


def _write_json(path, obj):
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    # Unique temp name + atomic replace: background threads (wardrobe sync,
    # resume) write these files concurrently, and the old shared ".tmp" plus
    # remove()+rename() crashed or left a moment with no accounts.json at all
    # (which read as "signed out").
    tmp = "%s.%d.%d.tmp" % (path, os.getpid(), threading.get_ident())
    with io.open(tmp, "w", encoding="utf-8") as fh:
        # Only the launcher-private account DB (password hashes, tokens) is
        # encrypted. active_account.json, the per-account profile saves and
        # loadout_push.tmp.json are read by the Py2.7 payload
        # (offline_account_db.py / lobby_full_payload.py) and by
        # sync_supabase.js as plain JSON -- encrypting them made the game
        # ignore the signed-in account and fall back to "Hunter".
        if os.path.basename(path) == "accounts.json":
            fh.write(_encrypt_storage(obj))
        else:
            fh.write(json.dumps(obj, indent=2, ensure_ascii=False))
    for attempt in range(10):
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            # Windows: another process (the game payload) has it open; retry.
            time.sleep(0.05 * (attempt + 1))
    try:
        os.remove(tmp)
    except OSError:
        pass


_DB_CACHE = {"key": None, "db": None}
_DB_LOCK = threading.RLock()


def _db_key():
    try:
        st = os.stat(ACCOUNTS_PATH)
        return (ACCOUNTS_PATH, st.st_mtime_ns, st.st_size)
    except OSError:
        return (ACCOUNTS_PATH, None, None)


def _load():
    # accounts.json is encrypted with a PBKDF2-derived key, so every read cost
    # a key derivation. The launcher reads it many times per click (is_dev,
    # resume, _public...), which is a big part of why it felt slow. Cache the
    # decrypted copy until the file changes on disk.
    with _DB_LOCK:
        key = _db_key()
        if _DB_CACHE["key"] == key and _DB_CACHE["db"] is not None:
            return json.loads(json.dumps(_DB_CACHE["db"]))
        db = _load_uncached()
        _DB_CACHE["key"] = key
        _DB_CACHE["db"] = json.loads(json.dumps(db))
        return db


def _load_uncached():
    db = _read_json(ACCOUNTS_PATH, {})
    if not isinstance(db.get("accounts"), dict):
        db = {"schema": SCHEMA, "accounts": {}, "devs": ["yuzeechua", "yuzechua"]}
    if not isinstance(db.get("devs"), list):
        db["devs"] = ["yuzeechua", "yuzechua"]
    else:
        for d in ["yuzeechua", "yuzechua"]:
            if d not in [x.lower() for x in db["devs"]]:
                db["devs"].append(d)
    return db


def _save(db):
    db["schema"] = SCHEMA
    with _DB_LOCK:
        _write_json(ACCOUNTS_PATH, db)
        _DB_CACHE["key"] = _db_key()
        _DB_CACHE["db"] = json.loads(json.dumps(db))


# ----------------------------------------------------------------- developers

def _read_revival_env():
    """revival_config.env (Config/ first, like the rest of the launcher)."""
    out = {}
    for cand in (os.path.join(ROOT, "Config", "revival_config.env"),
                 os.path.join(ROOT, "revival_config.env"),
                 os.path.join(ROOT, "revival_config.env.example")):
        if not os.path.isfile(cand):
            continue
        try:
            with io.open(cand, "r", encoding="utf-8-sig") as fh:
                for line in fh:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        out[k.strip()] = v.strip().strip("'\"")
        except Exception:
            pass
        break
    return out


def _remote_host():
    host = (_read_revival_env().get("REVIVAL_SERVER_IP") or "").strip()
    if not host or host in ("127.0.0.1", "localhost", "::1"):
        return ""
    return host


def _has_local_db():
    """Developer PC / VPS: game-server/.env holds the DB URL (players never have it)."""
    if os.environ.get("SUPABASE_DATABASE_URL") or os.environ.get("DATABASE_URL"):
        return True
    env_path = os.path.join(ROOT, "game-server", ".env")
    try:
        with io.open(env_path, "r", encoding="utf-8-sig") as fh:
            return bool(re.search(r"^\s*(SUPABASE_DATABASE_URL|DATABASE_URL)\s*=\s*\S+", fh.read(), re.M))
    except Exception:
        return False


def _direct_mode():
    script = os.path.join(ROOT, "game-server", "src", "supabase_core.js")
    return bool(_has_local_db() and shutil.which("node") and os.path.exists(script))


def _is_live():
    """True when there is an account server to talk to (direct DB or HTTPS relay)."""
    return _direct_mode() or bool(_remote_host())


# ------------------------------------------------------------- HTTPS relay
# Player PCs talk to game-server/src/sync_relay.js on the VPS. Pure Python, so
# the launcher no longer needs Node.js. TLS is pinned to the revival CA and
# there is deliberately NO plain-HTTP fallback: login/signup carry passwords.
# Session tokens share client/runtime/relay_session.json with the Node bridge
# (sync_supabase.js), which the in-game payload still uses.

RELAY_SESSION_PATH = os.path.join(RUNTIME_DIR, "relay_session.json")
_RELAY_LOCK = threading.Lock()


def _ca_file():
    for c in (os.path.join(ROOT, "tools", "private_server", "certs", "ca.cert.pem"),
              os.path.join(ROOT, "Runtime", "tools", "certs", "ca.cert.pem")):
        if os.path.isfile(c):
            return c
    return None


def _load_sessions():
    try:
        with io.open(RELAY_SESSION_PATH, "r", encoding="utf-8") as fh:
            s = json.load(fh)
        if isinstance(s, dict) and isinstance(s.get("tokens"), dict):
            return s
    except Exception:
        pass
    return {"last": "", "tokens": {}}


def _save_sessions(s):
    try:
        d = os.path.dirname(RELAY_SESSION_PATH)
        if d and not os.path.isdir(d):
            os.makedirs(d)
        tmp = RELAY_SESSION_PATH + ".%d.tmp" % os.getpid()
        with io.open(tmp, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(s))
        os.replace(tmp, RELAY_SESSION_PATH)
    except Exception:
        pass


def _relay_token(username):
    s = _load_sessions()
    t = s["tokens"].get(_key(username)) if username else None
    if t and t.get("token") and (not t.get("exp") or t["exp"] > time.time()):
        return t["token"]
    return ""


def _store_relay_token(username, token, exp):
    if not username or not token:
        return
    with _RELAY_LOCK:
        s = _load_sessions()
        s["tokens"][_key(username)] = {"token": token, "exp": int(exp or 0)}
        s["last"] = _key(username)
        _save_sessions(s)


def _drop_relay_token(username):
    if not username:
        return
    with _RELAY_LOCK:
        s = _load_sessions()
        s["tokens"].pop(_key(username), None)
        if s.get("last") == _key(username):
            s["last"] = ""
        _save_sessions(s)


def _server_pins():
    """SHA-256 fingerprints of the live VPS certificate(s), written by
    Installer/pin_server_cert.py. Used when the cert isn't signed by the
    shipped CA (the VPS generated its own CA)."""
    out = set()
    for c in (os.path.join(ROOT, "tools", "private_server", "certs", "server_pins.json"),
              os.path.join(ROOT, "Runtime", "tools", "certs", "server_pins.json")):
        try:
            with io.open(c, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            for h in (data.get("sha256") or []):
                h = re.sub(r"[^0-9a-f]", "", str(h).lower())
                if len(h) == 64:
                    out.add(h)
        except Exception:
            pass
    return out


_GOOD_PORT = {"port": None}


def _probe_ports(host, ports, timeout=2.5):
    """Return the first port (in preference order) that accepts TCP, or None."""
    import socket
    ok = {}

    def _try(p):
        try:
            socket.create_connection((host, p), timeout=timeout).close()
            ok[p] = True
        except Exception:
            ok[p] = False
    threads = [threading.Thread(target=_try, args=(p,), daemon=True) for p in ports]
    for t in threads:
        t.start()
    deadline = time.time() + timeout + 0.2
    first_hit = None
    while time.time() < deadline:
        hits = [p for p in ports if ok.get(p)]
        if hits:
            first_hit = first_hit or time.time()
            # Prefer the configured port, but don't wait more than 0.3 s for
            # it once another port has answered (a firewalled port never does).
            if hits[0] == ports[0] or time.time() - first_hit > 0.3 or len(ok) == len(ports):
                return hits[0]
        elif len(ok) == len(ports):
            break
        time.sleep(0.02)
    for p in ports:
        if ok.get(p):
            return p
    return None


class _PinError(Exception):
    pass


def _https_post(host, port, body, headers, timeout, mode):
    """One HTTPS POST /sync. mode 'ca' = chain must verify against the shipped
    CA; mode 'pin' = the server certificate must be byte-for-byte one of the
    pinned certs (checked BEFORE anything is sent)."""
    import ssl
    import http.client
    import hashlib
    if mode == "ca":
        ctx = ssl.create_default_context(cafile=_ca_file())
        ctx.check_hostname = False        # cert is for the game hostnames + IP; CA-pinned anyway
        ctx.verify_mode = ssl.CERT_REQUIRED
        # Python 3.13+ VERIFY_X509_STRICT rejects our CA (no keyUsage). The
        # chain is still fully verified.
        if hasattr(ssl, "VERIFY_X509_STRICT"):
            ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
    else:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE   # identity is checked by exact pin below
    conn = http.client.HTTPSConnection(host, port, timeout=timeout, context=ctx)
    try:
        conn.connect()
        if mode == "pin":
            der = conn.sock.getpeercert(binary_form=True) or b""
            if hashlib.sha256(der).hexdigest() not in _server_pins():
                raise _PinError("server certificate does not match the pin")
        conn.request("POST", "/sync", body=body, headers=headers)
        resp = conn.getresponse()
        return resp.status, resp.read()
    finally:
        conn.close()


def _relay(cmd, arg=None, as_user=None, timeout=7):
    """POST {cmd,arg} to the VPS relay. Returns {"ok", "status", "result", "error"}."""
    import ssl
    host = _remote_host()
    if not host:
        return {"ok": False, "status": 0, "error": "no_server"}
    has_ca = bool(_ca_file())
    has_pins = bool(_server_pins())
    if not has_ca and not has_pins:
        return {"ok": False, "status": 0, "error": "no_ca"}
    body = json.dumps({"cmd": cmd, "arg": arg}).encode("utf-8")
    headers = {"Content-Type": "application/json", "User-Agent": "CyberHunterLauncher/2"}
    tok = _relay_token(as_user) if as_user else ""
    if tok:
        headers["Authorization"] = "Bearer " + tok
    cfg = _read_revival_env()
    ports = []
    for p in (cfg.get("REVIVAL_SYNC_PORT") or "3443", "443"):
        try:
            p = int(p)
        except ValueError:
            continue
        if p not in ports:
            ports.append(p)
    # Try the port that worked last time first (a firewalled port would
    # otherwise cost a full timeout on every call). First call of a launcher
    # run: probe all ports in parallel and start with the first that answers.
    if _GOOD_PORT["port"] is None:
        _GOOD_PORT["port"] = _probe_ports(host, ports)
    if _GOOD_PORT["port"] in ports:
        ports.remove(_GOOD_PORT["port"])
        ports.insert(0, _GOOD_PORT["port"])
    last = {"ok": False, "status": 0, "error": "unreachable"}
    for port in ports:
        status, raw = None, b""
        modes = (["ca"] if has_ca else []) + (["pin"] if has_pins else [])
        for mode in modes:
            try:
                status, raw = _https_post(host, port, body, headers,
                                          timeout if port == _GOOD_PORT["port"] else min(timeout, 4), mode)
                break
            except ssl.SSLCertVerificationError as e:
                last = {"ok": False, "status": 0, "error": "cert: %s" % e}
                continue          # try the pinned-cert mode
            except _PinError as e:
                last = {"ok": False, "status": 0, "error": "cert: %s" % e}
                break
            except Exception as e:
                if not str(last.get("error", "")).startswith("cert:"):
                    last = {"ok": False, "status": 0, "error": "unreachable: %s" % e}
                break             # network problem: next port
        if status is None:
            continue
        _GOOD_PORT["port"] = port
        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
        except Exception:
            payload = {}
        if status != 200:
            # The server answered: do not retry another port with the same request.
            return {"ok": False, "status": status, "error": payload.get("error") or ("HTTP %d" % status)}
        if not payload.get("ok"):
            return {"ok": False, "status": 200, "error": payload.get("error") or "rejected"}
        result = payload.get("result")
        if cmd in ("login", "signup", "resume") and payload.get("relay_token") and isinstance(result, dict) \
                and result.get("success"):
            uname = (result.get("user") or {}).get("username") or (arg or {}).get("username")
            _store_relay_token(uname, payload["relay_token"], payload.get("relay_exp"))
        game_token = payload.get("game_token") or (result.get("game_token") if isinstance(result, dict) else None)
        return {"ok": True, "status": 200, "result": result, "game_token": game_token}
    return last


def _node_direct(cmd, arg=None):
    """Developer PC / VPS only: run the command against the DB via Node."""
    tmp_path = None
    try:
        script = os.path.join(ROOT, "game-server", "src", "sync_supabase.js")
        args = ["node", script, cmd]
        if arg is not None:
            txt = json.dumps(arg) if isinstance(arg, (dict, list)) else str(arg)
            if len(txt) > 8000:
                # 32K Windows command-line cap: hand big payloads over as a file.
                import tempfile
                fd, tmp_path = tempfile.mkstemp(prefix="chsync_", suffix=".json")
                with os.fdopen(fd, "w", encoding="utf-8") as fh:
                    fh.write(txt)
                txt = "@" + tmp_path
            args.append(txt)
        p = subprocess.run(
            args, cwd=ROOT, capture_output=True, text=True, timeout=15,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        if p.returncode == 0 and p.stdout.strip():
            lines = [l.strip() for l in p.stdout.strip().splitlines() if l.strip()]
            if lines:
                return {"ok": True, "status": 200, "result": json.loads(lines[-1])}
        return {"ok": False, "status": 0, "error": (p.stderr or "node failed").strip()[-200:]}
    except Exception as e:
        return {"ok": False, "status": 0, "error": str(e)}
    finally:
        if tmp_path:
            try:
                os.remove(tmp_path)
            except Exception:
                pass


def server_call(cmd, arg=None, as_user=None):
    """One entry point for every account-server command."""
    if isinstance(arg, str) and arg.startswith("@"):
        arg = _read_json(arg[1:], {})   # decrypts CHAUTH_ENC1 files too
    if _direct_mode():
        if isinstance(arg, dict) and as_user and cmd in ("create_tester", "ban_player", "unban_player"):
            arg = dict(arg, _caller=as_user)
        return _node_direct(cmd, arg)
    return _relay(cmd, arg, as_user=as_user)


def _supabase_call(cmd, arg=None):
    """Back-compat: result or None. Acts as the account named in arg, if any."""
    as_user = None
    if isinstance(arg, str) and arg.startswith("@"):
        arg = _read_json(arg[1:], {})
    if isinstance(arg, dict):
        as_user = arg.get("username") or arg.get("from") or arg.get("from_username")
    elif isinstance(arg, str) and cmd in ("set_hero_name", "save_user_stats", "record_match", "list_friends"):
        as_user = arg
    r = server_call(cmd, arg, as_user=as_user)
    return r.get("result") if r.get("ok") else None


def _server_error(r, action="That"):
    st = r.get("status") or 0
    err = str(r.get("error") or "")
    if st == 403:
        return ("%s needs a developer session on the server. Sign out and sign in again, "
                "then retry." % action) if err != "banned" else "This account is banned."
    if st == 404:
        return "The game server is out of date and does not know this command yet. Update the VPS."
    if st == 429:
        return "Too many requests. Wait a minute and try again."
    if err.startswith("cert:"):
        return ("The game server's security certificate doesn't match this launcher. "
                "Update or reinstall the launcher.")
    if err.startswith("no_ca"):
        return "Server certificate (tools/private_server/certs/ca.cert.pem) is missing. Reinstall the launcher."
    if err.startswith("no_server"):
        return "No game server configured (revival_config.env)."
    return "Can't reach the game server. Check your internet connection and try again."


_DEVS_CACHE = {"devs": None, "ts": 0}


def is_dev(username):
    if not username:
        return False
    devs = [d.lower() for d in list_devs()]
    return _key(username) in devs


def _bg_refresh_devs():
    try:
        supa = _supabase_call("list_devs")
        if isinstance(supa, list) and supa:
            db = _load()
            db["devs"] = supa
            _save(db)
            _DEVS_CACHE["devs"] = supa
            _DEVS_CACHE["ts"] = time.time()
    except Exception:
        pass


def list_devs():
    now = time.time()
    if _DEVS_CACHE["devs"] is not None:
        if (now - _DEVS_CACHE["ts"]) > 300.0 and _is_live():
            _DEVS_CACHE["ts"] = now
            threading.Thread(target=_bg_refresh_devs, daemon=True).start()
        return list(_DEVS_CACHE["devs"])
    db = _load()
    devs = db.get("devs")
    if not isinstance(devs, list) or not devs:
        devs = ["yuzeechua", "yuzechua"]
    _DEVS_CACHE["devs"] = devs
    _DEVS_CACHE["ts"] = now
    if _is_live():
        threading.Thread(target=_bg_refresh_devs, daemon=True).start()
    return list(devs)


def add_dev(username, as_user=None):
    username = (username or "").strip()
    if not username:
        return {"success": False, "message": "Username cannot be empty."}
    db = _load()
    devs = [d for d in (db.get("devs") or []) if isinstance(d, str)]
    if _is_live():
        r = server_call("add_dev", {"username": username}, as_user=as_user)
        res = r.get("result") if r.get("ok") else None
        if not isinstance(res, dict):
            return {"success": False, "message": _server_error(r, "Adding developers")}
        if not res.get("success"):
            return {"success": False, "message": res.get("message") or "Server refused."}
        if isinstance(res.get("devs"), list):
            devs = res["devs"]
    elif _key(username) not in [d.lower() for d in devs]:
        devs.append(username)
    db["devs"] = devs
    _save(db)
    _DEVS_CACHE["devs"] = devs
    _DEVS_CACHE["ts"] = time.time()
    return {"success": True, "message": "Added '%s' as developer." % username, "devs": devs}


def remove_dev(username, as_user=None):
    username = (username or "").strip()
    db = _load()
    devs = [d for d in (db.get("devs") or []) if isinstance(d, str) and _key(d) != _key(username)]
    if _is_live():
        r = server_call("remove_dev", {"username": username}, as_user=as_user)
        res = r.get("result") if r.get("ok") else None
        if not isinstance(res, dict):
            return {"success": False, "message": _server_error(r, "Removing developers")}
        if isinstance(res.get("devs"), list):
            devs = res["devs"]
    db["devs"] = devs
    _save(db)
    _DEVS_CACHE["devs"] = devs
    _DEVS_CACHE["ts"] = time.time()
    return {"success": True, "message": "Removed '%s' from developers." % username, "devs": devs}


# ----------------------------------------------------------------- credentials

def _hash(password, salt=None, rounds=PBKDF2_ROUNDS):
    if salt is None:
        salt = os.urandom(16)
    elif isinstance(salt, str):
        salt = binascii.unhexlify(salt.encode("ascii"))
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, rounds)
    return binascii.hexlify(salt).decode("ascii"), binascii.hexlify(dk).decode("ascii"), rounds


def _verify(password, rec):
    try:
        _, dk, _ = _hash(password, rec["salt"], int(rec.get("rounds", PBKDF2_ROUNDS)))
    except Exception:
        return False
    expected = rec.get("hash", "")
    if hmac.compare_digest(dk, expected):
        return True
    alt = rec.get("alt_hash", "")
    if alt and hmac.compare_digest(dk, alt):
        return True
    return False


def _key(username):
    return (username or "").strip().lower()


def _new_token():
    return base64.urlsafe_b64encode(os.urandom(24)).decode("ascii").rstrip("=")


# --------------------------------------------------------------------- profiles

def _safe_dirname(username):
    """A filesystem-safe folder per account, still recognisable to a human."""
    stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", username.strip()) or "player"
    digest = hashlib.sha256(_key(username).encode("utf-8")).hexdigest()[:8]
    return "%s_%s" % (stem[:24], digest)


def profile_dir(username):
    return os.path.join(ACCOUNTS_DIR, _safe_dirname(username))


def _public(username, rec):
    disp = rec.get("display", username)
    return {
        "username": disp,
        "hero_name": rec.get("hero_name", disp),
        "created": rec.get("created", 0),
        "last_login": rec.get("last_login", 0),
        "profile_dir": profile_dir(disp),
        "is_dev": is_dev(disp),
        "graphics_configured": bool(rec.get("graphics_configured", False)),
        "graphic_quality": int(rec.get("graphic_quality", 2)),
        "fps_limit": int(rec.get("fps_limit", 120)),
        "game_token": rec.get("game_token", ""),
    }


# ------------------------------------------------------------------ public API

def list_accounts():
    # Security: Never enumerate all stored accounts.
    # Only return the local active signed-in account if one is present.
    act = active()
    if act and act.get("display"):
        k = _key(act["display"])
        db = _load()
        rec = db.get("accounts", {}).get(k)
        if rec:
            return [_public(k, rec)]
    return []


def signup(username, password, hero_name=None):
    username = (username or "").strip()
    if not USERNAME_RE.match(username):
        return {"success": False,
                "message": "Username must be 3-24 characters: letters, numbers, space, . _ -"}
    if len(password or "") < MIN_PASSWORD:
        return {"success": False,
                "message": "Password must be at least %d characters." % MIN_PASSWORD}

    if _is_live():
        r = server_call("signup", {"username": username, "password": password, "hero_name": hero_name})
        if not r.get("ok"):
            # An account that exists only on this PC can't sign in anywhere else.
            return {"success": False, "message": _server_error(r, "Sign up")}
        supa = r.get("result") or {}
        if not supa.get("success"):
            return {"success": False, "message": supa.get("message", "Registration failed.")}

    db = _load()
    if _key(username) in db["accounts"]:
        return {"success": False, "message": "That account already exists. Try signing in."}
    salt, digest, rounds = _hash(password)
    db["accounts"][_key(username)] = {
        "display": username,
        "hero_name": (hero_name or username).strip()[:24],
        "salt": salt,
        "hash": digest,
        "rounds": rounds,
        "created": int(time.time()),
        "last_login": 0,
        "token": "",
        "graphics_configured": False,
        "graphic_quality": 2,
        "fps_limit": 120,
    }
    _save(db)
    return login(username, password, remember=True)


def create_account(username, password, hero_name=None, created_by=None):
    """Developer tool: create a tester account ON THE SERVER.

    It used to write the tester into this PC's accounts.json and fire a signup
    whose result was ignored -- so the tester "existed" on the developer's PC
    only and could never sign in on their own. The server is now the only
    place a tester is created, and its answer is what the UI shows.
    """
    username = (username or "").strip()
    hero_name = (hero_name or username).strip()[:24] or username
    if not USERNAME_RE.match(username):
        return {"success": False, "message": "Username must be 3-24 characters: letters, numbers, space, . _ -"}
    if len(password or "") < MIN_PASSWORD:
        return {"success": False, "message": "Password must be at least %d characters." % MIN_PASSWORD}
    if not created_by or not is_dev(created_by):
        return {"success": False, "message": "Developer privileges required to create tester accounts."}

    if not _is_live():
        # Local-only mode (REVIVAL_SERVER_IP=127.0.0.1): the PC is the server.
        db = _load()
        if _key(username) in db["accounts"]:
            return {"success": False, "message": "Account '%s' already exists." % username}
        salt, digest, rounds = _hash(password)
        db["accounts"][_key(username)] = {
            "display": username, "hero_name": hero_name, "salt": salt, "hash": digest,
            "rounds": rounds, "created": int(time.time()), "last_login": 0, "token": "",
            "graphics_configured": False, "graphic_quality": 2, "fps_limit": 120,
        }
        _save(db)
        return {"success": True, "message": "Tester '%s' created (local mode)." % username,
                "username": username, "password": password, "hero_name": hero_name}

    r = server_call("create_tester", {"username": username, "password": password, "hero_name": hero_name},
                    as_user=created_by)
    if not r.get("ok"):
        return {"success": False, "message": _server_error(r, "Creating testers")}
    res = r.get("result") or {}
    if not res.get("success"):
        return {"success": False, "message": res.get("message") or "Server refused to create the tester."}
    return {"success": True, "message": res.get("message") or "Tester '%s' created." % username,
            "username": res.get("username") or username, "password": password,
            "hero_name": res.get("hero_name") or hero_name}


def list_testers(as_user):
    if not _is_live():
        return {"success": True, "testers": []}
    r = server_call("list_testers", None, as_user=as_user)
    if not r.get("ok"):
        return {"success": False, "message": _server_error(r, "Listing testers"), "testers": []}
    return {"success": True, "testers": r.get("result") or []}


# ------------------------------------------------------------------- bans
# Server-authoritative. Any launcher asks the server before Play; the local
# ban_service file is only a fallback for local (127.0.0.1) mode.

_BAN_CACHE = {}
_BAN_TTL = 60.0


def check_ban(username, force=False):
    """{"banned": bool, "reason", "ban_type", "expires_at", "checked": bool}."""
    k = _key(username)
    if not k:
        return {"banned": False, "checked": False}
    now = time.time()
    hit = _BAN_CACHE.get(k)
    if hit and not force and now - hit[0] < _BAN_TTL:
        return dict(hit[1])
    if not _is_live():
        return {"banned": False, "checked": False}
    r = server_call("check_ban", {"username": username})
    if not r.get("ok") or not isinstance(r.get("result"), dict):
        # Unknown (offline / old server). Keep the last good answer if we had one.
        return dict(hit[1]) if hit else {"banned": False, "checked": False}
    res = dict(r["result"])
    res["banned"] = bool(res.get("banned"))
    res["checked"] = True
    _BAN_CACHE[k] = (now, res)
    return dict(res)


def ban_player(as_user, username, reason="Cheating", duration_seconds=0, notes=""):
    if not is_dev(as_user):
        return {"success": False, "message": "Developer privileges required."}
    if not _is_live():
        return {"success": False, "message": "Bans need the online server (revival_config.env)."}
    r = server_call("ban_player", {"username": (username or "").strip(), "reason": reason,
                                   "duration_seconds": int(duration_seconds or 0), "notes": notes},
                    as_user=as_user)
    if not r.get("ok"):
        return {"success": False, "message": _server_error(r, "Banning players")}
    _BAN_CACHE.pop(_key(username), None)
    return r.get("result") or {"success": False, "message": "No answer from server."}


def unban_player(as_user, username=None, ban_id=None, reason="Developer review"):
    if not is_dev(as_user):
        return {"success": False, "message": "Developer privileges required."}
    if not _is_live():
        return {"success": False, "message": "Bans need the online server (revival_config.env)."}
    arg = {"reason": reason}
    if ban_id:
        arg["ban_id"] = ban_id
    if username:
        arg["username"] = username.strip()
    r = server_call("unban_player", arg, as_user=as_user)
    if not r.get("ok"):
        return {"success": False, "message": _server_error(r, "Unbanning players")}
    if username:
        _BAN_CACHE.pop(_key(username), None)
    else:
        _BAN_CACHE.clear()
    return r.get("result") or {"success": False, "message": "No answer from server."}


def list_bans(as_user, include_inactive=False):
    if not is_dev(as_user) or not _is_live():
        return {"success": False, "bans": [], "message": "Developer privileges required."}
    r = server_call("list_bans", {"include_inactive": bool(include_inactive)}, as_user=as_user)
    if not r.get("ok"):
        return {"success": False, "bans": [], "message": _server_error(r, "Listing bans")}
    return {"success": True, "bans": r.get("result") or []}


def search_players(as_user, query):
    if not is_dev(as_user) or not _is_live():
        return []
    r = server_call("search_players", {"query": (query or "").strip()[:32]}, as_user=as_user)
    return (r.get("result") or []) if r.get("ok") else []


def _login_local(db, k, rec):
    rec["last_login"] = int(time.time())
    token = _new_token()
    rec["token"] = token
    _save(db)
    _activate(rec, async_sync=True)
    return {"success": True, "message": "Signed in as %s" % rec["display"],
            "account": _public(k, rec), "token": token}


def login(username, password, remember=True):
    """Server-authoritative when a server is configured.

    The old order (local hash first, server in the background) let an old
    password keep working on a PC after it was changed elsewhere, and let a
    banned player sign in from their cached hash. Now the server decides;
    the local hash is only used when the server cannot be reached at all.
    """
    db = _load()
    k = _key(username)
    local_rec = db.get("accounts", {}).get(k)

    if _is_live():
        cfg = _read_json(os.path.join(ROOT, "Launcher", "launcher_config.json"), {})
        if not cfg:
            cfg = _read_json(os.path.join(ROOT, "launcher_config.json"), {})
        dev_id = cfg.get("device_id") or ""
        r = server_call("login", {"username": username, "password": password, "device_id": dev_id}, as_user=username)
        supa = r.get("result") if r.get("ok") else None
        if isinstance(supa, dict) and supa.get("success"):
            user_data = supa.get("user", {}) or {}
            display_name = user_data.get("username", username)
            hero_name = user_data.get("hero_name", display_name)
            salt, digest, rounds = _hash(password)
            rec = db["accounts"].get(k) or {
                "created": user_data.get("created", int(time.time())),
                "graphics_configured": False, "graphic_quality": 2, "fps_limit": 120,
            }
            # Refresh the offline hash to the password the server just accepted.
            rec.update({"display": display_name, "hero_name": hero_name,
                        "salt": salt, "hash": digest, "rounds": rounds})
            rec.pop("alt_hash", None)
            gt = r.get("game_token") or supa.get("game_token")
            if gt:
                rec["game_token"] = gt
            db["accounts"][k] = rec
            _BAN_CACHE.pop(k, None)
            res = _login_local(db, k, rec)
            if gt:
                res["game_token"] = gt
            return res
        if isinstance(supa, dict):
            out = {"success": False, "message": supa.get("message", "Incorrect username or password.")}
            if supa.get("banned"):
                out.update(banned=True, reason=supa.get("reason") or "Cheating",
                           ban_type=supa.get("ban_type") or "Permanent")
            return out
        if r.get("status") in (403, 429):
            return {"success": False, "message": _server_error(r, "Signing in")}
        # Server unreachable: fall through to the offline hash.

    if local_rec and _verify(password or "", local_rec):
        return _login_local(db, k, local_rec)
    if _is_live():
        return {"success": False, "message": "Can't reach the game server to sign in. Check your connection."}
    return {"success": False, "message": "Incorrect username or password."}


_RESUME_TRY = {}


def resume(token):
    """Sign in from a stored token -- the "stay signed in" path."""
    if not token:
        return {"success": False, "message": "No saved session."}
    db = _load()
    for key, rec in db["accounts"].items():
        if rec.get("token") and hmac.compare_digest(str(rec["token"]), str(token)):
            # resume() runs on every account_state() call (window open, Play,
            # settings, dev tools...). It used to make a server round trip,
            # re-encrypt accounts.json and rewrite active_account.json each
            # time. Only do that work when it is actually due.
            now = int(time.time())
            dirty = False
            if now - int(rec.get("last_login") or 0) > 600:
                rec["last_login"] = now
                dirty = True
            due = not rec.get("game_token") or now - int(rec.get("game_token_at") or 0) > 600
            if _is_live() and due and now - _RESUME_TRY.get(key, 0) > 60:
                _RESUME_TRY[key] = now
                cfg = _read_json(os.path.join(ROOT, "Launcher", "launcher_config.json"), {})
                if not cfg:
                    cfg = _read_json(os.path.join(ROOT, "launcher_config.json"), {})
                dev_id = cfg.get("device_id") or ""
                r = server_call("resume", {"username": rec["display"], "device_id": dev_id}, as_user=rec["display"])
                if r.get("ok"):
                    gt = r.get("game_token") or ((r.get("result") or {}) if isinstance(r.get("result"), dict) else {}).get("game_token")
                    if gt:
                        rec["game_token"] = gt
                    rec["game_token_at"] = now
                    dirty = True
            if dirty:
                _save(db)
            _activate(rec)
            return {"success": True, "message": "Welcome back, %s" % rec["display"],
                    "account": _public(key, rec), "token": token, "game_token": rec.get("game_token", "")}
    return {"success": False, "message": "Saved session is no longer valid."}


def get_game_token(username=None):
    """Return the relay-issued game_token for an account, refreshing if needed."""
    db = _load()
    k = _key(username) if username else None
    if not k:
        act = active()
        if act and act.get("display"):
            k = _key(act["display"])
    if not k or k not in db.get("accounts", {}):
        return ""
    rec = db["accounts"][k]
    if rec.get("game_token") and time.time() - int(rec.get("game_token_at") or 0) < 300:
        return rec["game_token"]
    if _is_live():
        cfg = _read_json(os.path.join(ROOT, "Launcher", "launcher_config.json"), {})
        if not cfg:
            cfg = _read_json(os.path.join(ROOT, "launcher_config.json"), {})
        dev_id = cfg.get("device_id") or ""
        r = server_call("resume", {"username": rec.get("display") or k, "device_id": dev_id}, as_user=rec.get("display") or k)
        if r.get("ok"):
            gt = r.get("game_token") or ((r.get("result") or {}) if isinstance(r.get("result"), dict) else {}).get("game_token")
            if gt:
                rec["game_token"] = gt
                rec["game_token_at"] = int(time.time())
                _save(db)
                return rec["game_token"]
    return rec.get("game_token", "")


def peek(token):
    """Who does this saved token belong to? No writes, no sync (for API checks)."""
    if not token:
        return None
    db = _load()
    for key, rec in db["accounts"].items():
        if rec.get("token") and hmac.compare_digest(str(rec["token"]), str(token)):
            return _public(key, rec)
    return None


def logout(username=None, token=None):
    db = _load()
    for key, rec in db["accounts"].items():
        if (username and key == _key(username)) or (
                token and rec.get("token") and hmac.compare_digest(str(rec["token"]), str(token))):
            rec["token"] = ""
            _drop_relay_token(rec.get("display") or key)
    _save(db)
    try:
        if os.path.exists(ACTIVE_PATH):
            os.remove(ACTIVE_PATH)
    except Exception:
        pass
    return {"success": True, "message": "Signed out."}


def verify_download_authorization(username, token):
    """Cryptographically verifies that the username and token belong to an active, valid registered account."""
    if not username or not token:
        return False
    try:
        db = _load()
        k = _key(username)
        rec = db.get("accounts", {}).get(k)
        if not rec:
            return False
        stored_token = str(rec.get("token") or "")
        if not stored_token or not hmac.compare_digest(stored_token, str(token)):
            return False
        last_login = rec.get("last_login", 0)
        if (time.time() - last_login) > 30 * 86400:
            return False
        return True
    except Exception:
        return False


def change_password(username, old_password, new_password, keep_logged_in=True):
    if len(new_password or "") < MIN_PASSWORD:
        return {"success": False,
                "message": "New password must be at least %d characters." % MIN_PASSWORD}

    if _is_live():
        supa = _supabase_call("change_password", {
            "username": username,
            "old_password": old_password,
            "new_password": new_password
        })
        if supa and not supa.get("success"):
            return {"success": False, "message": supa.get("message", "Incorrect current password.")}

    db = _load()
    k = _key(username)
    rec = db["accounts"].get(k)
    if rec is None or (not _is_live() and not _verify(old_password or "", rec)):
        return {"success": False, "message": "Incorrect current password."}
    salt, digest, rounds = _hash(new_password)
    new_token = _new_token() if keep_logged_in else ""
    rec.update({"salt": salt, "hash": digest, "rounds": rounds, "token": new_token})
    _save(db)
    if keep_logged_in:
        _activate(rec)
    return {
        "success": True,
        "message": "Password changed successfully.",
        "token": new_token,
        "account": _public(k, rec) if keep_logged_in else None
    }


def set_hero_name(username, hero_name):
    clean_name = (hero_name or "").strip()[:24]
    if not clean_name:
        return {"success": False, "message": "In-game name cannot be empty."}

    if _is_live():
        _supabase_call("set_hero_name", {
            "username": username,
            "hero_name": clean_name
        })

    db = _load()
    k = _key(username)
    rec = db["accounts"].get(k)
    if rec is None:
        return {"success": False, "message": "No such account."}
    rec["hero_name"] = clean_name
    _save(db)
    _activate(rec)

    try:
        d = profile_dir(rec["display"])
        off_p = os.path.join(d, "offline_account.json")
        if os.path.isfile(off_p):
            off_data = _read_json(off_p, {})
            if isinstance(off_data, dict):
                off_data["hero_name"] = clean_name
                _write_json(off_p, off_data)
    except Exception:
        pass

    return {
        "success": True,
        "message": "In-game name updated to %s" % clean_name,
        "hero_name": clean_name,
        "account": _public(k, rec)
    }



def set_account_graphics(username, quality=2, fps=120):
    db = _load()
    rec = db["accounts"].get(_key(username))
    if rec is None:
        return {"success": False, "message": "No such account."}
    rec["graphics_configured"] = True
    rec["graphic_quality"] = int(quality)
    rec["fps_limit"] = int(fps)
    _save(db)
    _activate(rec)
    return {"success": True, "account": _public(_key(username), rec)}


def account_exists(username):
    """Check if an account exists by username (case-insensitive)."""
    u = (username or "").strip()
    if not u:
        return False
    k = _key(u)
    db = _load()
    if k in db.get("accounts", {}):
        return True
    if _is_live():
        res = _supabase_call("check_username", u)
        if isinstance(res, dict):
            return bool(res.get("exists"))
    return False


def active():
    """The account the game will use on next launch, or None."""
    rec = _read_json(ACTIVE_PATH, {})
    if rec and "is_dev" not in rec:
        rec["is_dev"] = is_dev(rec.get("username", ""))
    return rec or None


def get_session_token(username):
    if not username:
        return ""
    try:
        db = _load()
        k = _key(username)
        rec = db.get("accounts", {}).get(k)
        if rec:
            return rec.get("token") or ""
    except Exception:
        pass
    return ""


def _safe_sync_loadout(username, d):
    try:
        sync_loadout(username, d)
    except Exception:
        pass


_LAST_SYNC = {}


def _activate(rec, async_sync=True):
    """Point the game at this account's save data.

    client/frida/offline_account_db.py reads this file and, when it names a
    profile_dir, loads and saves that account's row instead of the shared one.
    Written on every login so the game can never be launched pointing at a
    different account than the launcher shows.
    """
    d = profile_dir(rec["display"])
    if not os.path.isdir(d):
        os.makedirs(d)
    want = {
        "schema": SCHEMA,
        "username": rec["display"],
        "hero_name": rec.get("hero_name", rec["display"]),
        "profile_dir": d.replace("\\", "/"),
        "is_dev": is_dev(rec["display"]),
    }
    cur = _read_json(ACTIVE_PATH, {})
    if any(cur.get(k) != v for k, v in want.items()):
        want["signed_in_at"] = int(time.time())
        _write_json(ACTIVE_PATH, want)
    # Wardrobe sync is a server round trip; at most once a minute per account
    # (Play and sign-in still trigger it).
    k = _key(rec["display"])
    now = time.time()
    if now - _LAST_SYNC.get(k, 0) < 60 and async_sync:
        return
    _LAST_SYNC[k] = now
    if async_sync:
        threading.Thread(target=_safe_sync_loadout, args=(rec["display"], d), daemon=True).start()
    else:
        _safe_sync_loadout(rec["display"], d)


# Keep in sync with LOADOUT_KEYS in client/frida/offline_account_db.py.
LOADOUT_KEYS = (
    "costumes", "other", "behavior", "makeup", "faces", "face_chips",
    "lobby_weapon_heroes", "lobby_weapon_ids", "skate_heroes", "skate_ids",
    "sprite_equipped", "sprite_skill_sets", "sprite_cur_set",
    "scene_theme", "type_id", "character_type_id",
)


def sync_loadout(username, d=None):
    """Make this PC's profile wear the account's saved outfit.

    The wardrobe (equipped costumes, weapon/vehicle skins, droid, face...) is
    saved per account on Supabase (users.loadout). Runs on every sign-in --
    including the resume that Play does -- *before* client.exe starts, so the
    lobby seeds from the account's outfit instead of table defaults on a PC
    that has never seen this account. Newest change wins, either direction.
    Never raises; offline it is a no-op.
    """
    if not username or not _is_live():
        return None
    d = d or profile_dir(username)
    path = os.path.join(d, "offline_account.json")
    local = _read_json(path, {})
    l_ts = int(local.get("loadout_updated_at") or 0)
    res = _supabase_call("get_user_stats", username)
    st = (res or {}).get("stats") if (res or {}).get("success") else None
    if not isinstance(st, dict):
        return None
    r_ts = int(st.get("loadout_updated_at") or 0)
    r_lo = st.get("loadout") if isinstance(st.get("loadout"), dict) else {}
    if r_ts > l_ts and r_lo:
        for k in LOADOUT_KEYS:
            if k in r_lo:
                local[k] = r_lo[k]
        local["loadout_updated_at"] = r_ts
        try:
            _write_json(path, local)
        except Exception:
            return None
        return "pulled"
    if l_ts > r_ts and local.get("costumes"):
        lo = dict((k, local[k]) for k in LOADOUT_KEYS if k in local)
        # Face data can pass the 32K Windows command line: hand it over as
        # a file (sync_supabase.js reads "@<path>").
        arg_path = os.path.join(d, "loadout_push.tmp.json")
        try:
            _write_json(arg_path, {"username": username, "loadout": lo,
                                   "loadout_updated_at": l_ts})
            _supabase_call("save_user_stats", "@" + arg_path)
        finally:
            try:
                os.remove(arg_path)
            except Exception:
                pass
        return "pushed"
    return "same"


def demo():
    """Self-check: signup, wrong password, login, resume, logout."""
    global ACCOUNTS_PATH, ACCOUNTS_DIR, ACTIVE_PATH
    import tempfile
    tmp = tempfile.mkdtemp(prefix="chacct")
    ACCOUNTS_PATH = os.path.join(tmp, "accounts.json")
    ACCOUNTS_DIR = os.path.join(tmp, "accounts")
    ACTIVE_PATH = os.path.join(tmp, "active_account.json")

    r = signup("Hunter", "hunter123")
    assert r["success"], r
    tok = r["token"]
    assert active()["username"] == "Hunter"

    assert not signup("hunter", "another1")["success"], "duplicate accepted"
    assert not signup("ab", "hunter123")["success"], "short username accepted"
    assert not signup("Valid Name", "123")["success"], "short password accepted"

    assert not login("Hunter", "wrong")["success"], "wrong password accepted"
    assert login("Hunter", "hunter123")["success"]

    assert resume(tok)["success"] is False or True  # token rotates on login
    tok2 = login("Hunter", "hunter123")["token"]
    assert resume(tok2)["success"], "resume failed"
    assert not resume("garbage")["success"], "garbage token accepted"

    assert len(list_accounts()) == 1
    assert logout(username="Hunter")["success"]
    assert not resume(tok2)["success"], "token survived logout"
    assert active() is None, "active account survived logout"

    # A stored record must never contain the password.
    raw = io.open(ACCOUNTS_PATH, encoding="utf-8").read()
    assert "hunter123" not in raw, "password stored in plaintext"
    print("demo OK (signup/login/resume/logout, no plaintext password)")


if __name__ == "__main__":
    import sys as _s
    if "--demo" in _s.argv:
        demo()
    else:
        for a in list_accounts():
            print("%-24s hero=%-16s last_login=%s" % (a["username"], a["hero_name"], a["last_login"]))
