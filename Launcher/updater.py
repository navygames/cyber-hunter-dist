"""
Cyber Hunter Reawakening - player auto-updater (manifest based).

Why not git any more
  The old updater ran ``git fetch`` of the ``reawakening-final`` branch. Even
  though it only *checked out* allow-listed files afterwards, git had already
  downloaded every object on that branch into the player's ``.git`` folder --
  server code, configs and anything else committed there were readable with
  ``git show``. It also needed git installed, read access to the repo, and an
  install that was a git clone (the Setup.exe install never is), so most
  players never got updates at all.

How it works now
  1. GET ``<update url>/update_manifest.json`` over HTTPS. The manifest lists
     player files only: ``{"path", "sha256", "size"}``. It is produced on the
     developer PC by ``Installer/make_update_manifest.py`` from the Release
     folder.
  2. Every path is checked against a strict ALLOW list (and a DENY list that
     wins over it). Anything else in the manifest is ignored, so even a
     mistaken manifest can't make a player download server files, keys,
     accounts or configs.
  3. Only files whose SHA-256 differs from the local copy are downloaded, one
     by one, verified against the manifest hash, then swapped in atomically.
  4. ``launcher.exe`` / ``CyberHunterLauncher.exe`` are staged as ``*.new``
     and swapped by ``restart_launcher`` after this process exits.

The update URL comes from ``REVIVAL_UPDATE_URL`` in revival_config.env
(https only). Default: the raw files of the ``reawakening-final`` branch.
"""

import hashlib
import json
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_UPDATE_URL = "https://raw.githubusercontent.com/navygames/cyber-hunter-dist/main/"
MANIFEST_NAME = "update_manifest.json"
USER_AGENT = "CyberHunterLauncher/2.0 (updater)"
MAX_FILE_BYTES = 200 * 1024 * 1024

# Player-side files the updater may write. Everything else is ignored.
ALLOW = (
    "CyberHunter.bat",
    "README.txt",
    "requirements.txt",
    "revival_config.env.example",
    "launcher.exe",
    "CyberHunterLauncher.exe",
    "Launcher/*.py",
    "Launcher/app_icon.ico",
    "Launcher/ui/**",
    "client/client_manifest.json",
    # The offline brain ships compiled only (docs/NATIVE_SCRIPTS.md):
    # tools/neox_script/build_native.py output, loaded by client.exe itself.
    "client/native/build/script/**.nxs",
    "client/native/build/script/manifest.json",
    "client/launchers/*.ps1",
    "tools/verify_game_files.py",
    "tools/client_manifest.py",
    "tools/npk.py",
    "tools/private_server/*.py",
    "tools/private_server/*.ps1",
    "tools/private_server/responses/*",
    "tools/private_server/certs/ca.cert.pem",
    "game-server/src/sync_supabase.js",
)

# Never written, even if a manifest lists them and they match ALLOW.
# ("*" stays inside one folder, "**" crosses folders.)
DENY = (
    "**.env", "**/.env*", ".env*", "**.env.local", "**.env.prod*",
    "**.key", "**.key.pem", "**server.key**", "**ca.key**",
    "**accounts.json", "**launcher_config.json", "**player_account.json",
    "**relay_session.json", "**session_token.json", "**moderation_db.json",
    "client/runtime/**", "Runtime/**", "Config/**",
    "game/**", "Game/**", "Cyber Hunter/**", "Cyber Steam/**", "**.npk", "**.npk.**",
    "**.git/**", "**node_modules/**", "**__pycache__/**", "**.pyc",
    "ControlPanel/**",
    "game-server/src/supabase_core.js", "game-server/src/sync_relay.js", "**.relay_secret",
    "**referee**", "**anti_cheat**", "**social_service**",
    # Moderation / admin tooling and dev-only probes never ship to players.
    "**ban_service**", "**token_service**",
    # Readable mod source + the Frida hook no longer ship (native boot).
    "client/frida/**", "client/native/*.py", "client/native/game_overlay/**",
    # frida_see_probe.py is NOT dev-only: run_offline_python.ps1 calls it on
    # every Play (leaving it out made Play kill the client).
    "**check_payload.py**", "**spawn_mapper.py**",
    "**make_update_manifest.py**", "**build_installer.py**", "**build_all.py**",
    "**protect_release.py**", "**py2parse.py**",
    # server_pins.json gets a fresh pinned_at timestamp on every connect
    # (TOFU), so its hash is a moving target -- never auto-update it.
    "**server_pins.json",
    "tools/private_server/certs/server.**", "tools/private_server/certs/*.key*",
    "tools/private_server/generate_certs.py",
)

EXE_NAMES = ("launcher.exe", "cyberhunterlauncher.exe")

# Shipped by earlier builds, replaced by client/native/build/script/*.nxs.
# Deleted from player installs once the native pack is in place, so the
# readable source does not linger on disk after the update.
RETIRED = (
    "client/frida/lobby_full_payload.py", "client/frida/lobby_offline_server.py",
    "client/frida/offline_account_db.py", "client/frida/br_world4k_spawns.py",
    "client/frida/br_world4k_anchors.py", "client/frida/offline_weapon_damage.json",
    "client/frida/map_catalog.py", "client/frida/spawn_mapper.py",
    "client/frida/check_payload.py", "client/frida/lobby_full.js",
    "client/frida/run_frida_attach.py", "client/frida/frida_see_probe.py",
)
NATIVE_PACK = "client/native/build/script/reawakening/pack.nxs"


def retire_old_files(root_dir):
    """Remove RETIRED files from a player install that has the native pack.

    Never on a developer checkout (AGENTS.md present): there client/frida is
    the source the pack is built from."""
    if os.path.isfile(os.path.join(root_dir, "AGENTS.md")):
        return []
    if not os.path.isfile(os.path.join(root_dir, *NATIVE_PACK.split("/"))):
        return []
    gone = []
    for rel in RETIRED:
        p = os.path.join(root_dir, *rel.split("/"))
        if os.path.isfile(p):
            try:
                os.remove(p)
                gone.append(rel)
            except OSError:
                pass
    pyc = os.path.join(root_dir, "client", "frida", "__pycache__")
    if os.path.isdir(pyc):
        try:
            import shutil
            shutil.rmtree(pyc, ignore_errors=True)
        except Exception:
            pass
    return gone
_SAFE_PATH = re.compile(r"^[A-Za-z0-9 _.\-/]+$")


def clean_path(rel):
    """Normalise a manifest path; '' if it is unsafe (absolute, .., drive, odd chars)."""
    if not isinstance(rel, str):
        return ""
    rel = rel.replace("\\", "/").strip()
    if not rel or rel.startswith("/") or ":" in rel or not _SAFE_PATH.match(rel):
        return ""
    parts = rel.split("/")
    if any(p in ("", ".", "..") for p in parts):
        return ""
    return "/".join(parts)


def _glob_re(pat):
    out = ""
    i = 0
    while i < len(pat):
        if pat.startswith("**", i):
            out += ".*"
            i += 2
        elif pat[i] == "*":
            out += "[^/]*"
            i += 1
        else:
            out += re.escape(pat[i])
            i += 1
    return re.compile("^" + out + "$", re.I)


_ALLOW_RE = [_glob_re(p) for p in ALLOW]
_DENY_RE = [_glob_re(p) for p in DENY]


def is_allowed(rel):
    rel = clean_path(rel)
    if not rel:
        return False
    if any(r.match(rel) for r in _DENY_RE):
        return False
    return any(r.match(rel) for r in _ALLOW_RE)


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_env(root_dir):
    out = {}
    for cand in (os.path.join(root_dir, "Config", "revival_config.env"),
                 os.path.join(root_dir, "revival_config.env"),
                 os.path.join(root_dir, "revival_config.env.example")):
        if os.path.isfile(cand):
            try:
                with open(cand, "r", encoding="utf-8-sig") as fh:
                    for line in fh:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            out[k.strip()] = v.strip().strip("'\"")
            except Exception:
                pass
            break
    return out


def update_base_url(root_dir):
    url = (_read_env(root_dir).get("REVIVAL_UPDATE_URL") or DEFAULT_UPDATE_URL).strip()
    if not url.lower().startswith("https://"):
        raise RuntimeError("REVIVAL_UPDATE_URL must be an https:// URL.")
    return url if url.endswith("/") else url + "/"


def _get(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Cache-Control": "no-cache"})
    resp = urllib.request.urlopen(req, timeout=timeout)
    if not (resp.geturl() or "").lower().startswith("https://"):
        resp.close()
        raise RuntimeError("Update server redirected to an insecure URL.")
    return resp


class Updater:
    def __init__(self, root_dir):
        self.root = root_dir
        self.frozen = bool(getattr(sys, "frozen", False))
        self.lock = threading.Lock()
        self.state = {
            "status": "idle",   # idle | available | up_to_date | updating | done | error | unavailable
            "phase": "", "percent": 0.0, "received_bytes": 0, "total_bytes": 0,
            "speed_bps": 0.0, "local_sha": "", "remote_sha": "", "message": "",
            "launcher_changed": False, "checked_at": 0.0, "pending": [],
        }
        self._manifest = None
        self._hash_cache = {}

    # ---------------------------------------------------------------- state
    def set(self, **kw):
        with self.lock:
            self.state.update(kw)

    def get(self):
        with self.lock:
            st = dict(self.state)
        st.pop("pending", None)
        return st

    def _state_file(self):
        return os.path.join(self.root, "client", "runtime", "update_state.json")

    def _local_version(self):
        try:
            with open(self._state_file(), "r", encoding="utf-8") as fh:
                return str(json.load(fh).get("version") or "")
        except Exception:
            return ""

    def _save_version(self, version):
        try:
            p = self._state_file()
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w", encoding="utf-8") as fh:
                json.dump({"version": version, "applied_at": int(time.time())}, fh)
        except Exception:
            pass

    # ------------------------------------------------------------ manifest
    def fetch_manifest(self):
        base = update_base_url(self.root)
        with _get(base + MANIFEST_NAME) as resp:
            raw = resp.read(4 * 1024 * 1024 + 1)
        if len(raw) > 4 * 1024 * 1024:
            raise RuntimeError("Update manifest is too large.")
        man = json.loads(raw.decode("utf-8"))
        if not isinstance(man, dict) or not isinstance(man.get("files"), list):
            raise RuntimeError("Update manifest is malformed.")
        files = []
        for f in man["files"]:
            if not isinstance(f, dict):
                continue
            rel = clean_path(f.get("path"))
            sha = str(f.get("sha256") or "").lower()
            size = f.get("size")
            if not rel or not is_allowed(rel) or not re.match(r"^[0-9a-f]{64}$", sha):
                continue
            if not isinstance(size, int) or size < 0 or size > MAX_FILE_BYTES:
                continue
            files.append({"path": rel, "sha256": sha, "size": size})
        man["files"] = files
        man["_base"] = base
        return man

    def _local_hash(self, rel):
        full = os.path.join(self.root, *rel.split("/"))
        staged = full + ".new"
        try:
            st = os.stat(full)
        except OSError:
            st = None
        # A staged exe waiting for the restart counts as applied.
        if rel.lower() in EXE_NAMES and os.path.isfile(staged):
            full, st = staged, os.stat(staged)
        if st is None:
            return ""
        key = (full, st.st_size, st.st_mtime)
        h = self._hash_cache.get(key)
        if h is None:
            h = _sha256(full)
            self._hash_cache[key] = h
        return h

    def _wanted(self, man):
        out = []
        for f in man["files"]:
            rel = f["path"]
            # The .exe only matters to the .exe build; script installs skip it
            # (and vice versa the frozen build can't run updated Launcher/*.py,
            # but those still update so a later script launch is current).
            if rel.lower() in EXE_NAMES:
                if not self.frozen:
                    continue
                if os.path.basename(sys.executable).lower() != rel.lower() and \
                        not os.path.isfile(os.path.join(self.root, rel)):
                    continue
            if self._local_hash(rel) != f["sha256"]:
                out.append(f)
        return out

    # --------------------------------------------------------------- check
    def check(self):
        if self.get()["status"] == "updating":
            return self.get()
        try:
            man = self.fetch_manifest()
        except urllib.error.HTTPError as e:
            msg = ("No update manifest published yet." if e.code == 404
                   else "Update server answered HTTP %d." % e.code)
            self.set(status="unavailable", message=msg, checked_at=time.time())
            return self.get()
        except Exception as e:
            self.set(status="error", message="Could not reach update server: %s" % str(e)[:160],
                     checked_at=time.time())
            return self.get()
        pending = self._wanted(man)
        self._manifest = man
        try:
            retire_old_files(self.root)
        except Exception:
            pass
        version = str(man.get("version") or "")
        self.set(status="available" if pending else "up_to_date",
                 local_sha=self._local_version(), remote_sha=version,
                 total_bytes=sum(f["size"] for f in pending), pending=pending,
                 message=("%d file(s) to update" % len(pending)) if pending else "Up to date",
                 checked_at=time.time())
        return self.get()

    # --------------------------------------------------------------- apply
    def start(self):
        with self.lock:
            if self.state["status"] == "updating":
                return {"success": True, "message": "Update already running."}
            self.state.update(status="updating", phase="Connecting...", percent=0.0,
                              received_bytes=0, total_bytes=0, speed_bps=0.0,
                              message="", launcher_changed=False)
        threading.Thread(target=self._run, daemon=True).start()
        return {"success": True, "message": "Update started."}

    def _download(self, base, f, received_before, total):
        rel = f["path"]
        dest = os.path.join(self.root, *rel.split("/"))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        tmp = dest + ".part"
        url = base + urllib.parse.quote(rel)
        h = hashlib.sha256()
        got = 0
        t0, since, speed = time.time(), 0, 0.0
        with _get(url, timeout=30) as resp, open(tmp, "wb") as out:
            while True:
                chunk = resp.read(256 * 1024)
                if not chunk:
                    break
                got += len(chunk)
                if got > f["size"]:
                    raise RuntimeError("%s is larger than the manifest says." % rel)
                h.update(chunk)
                out.write(chunk)
                since += len(chunk)
                now = time.time()
                if now - t0 >= 0.5:
                    speed, t0, since = since / (now - t0), now, 0
                done = received_before + got
                self.set(received_bytes=done, speed_bps=speed,
                         percent=min(98.0, done * 98.0 / total) if total else 50.0)
        if h.hexdigest() != f["sha256"]:
            os.remove(tmp)
            raise RuntimeError("%s failed its integrity check; update aborted." % rel)
        if rel.lower() in EXE_NAMES:
            # Can't overwrite the running exe: stage it for restart_launcher.
            os.replace(tmp, dest + ".new")
        else:
            os.replace(tmp, dest)
        return got

    def _run(self):
        try:
            man = self.fetch_manifest()
            pending = self._wanted(man)
            total = sum(f["size"] for f in pending)
            self.set(total_bytes=total, phase="Downloading")
            received = 0
            for i, f in enumerate(pending, 1):
                self.set(phase="Downloading %d/%d: %s" % (i, len(pending), f["path"].split("/")[-1]))
                received += self._download(man["_base"], f, received, total)
            self._save_version(str(man.get("version") or ""))
            try:
                retire_old_files(self.root)
            except Exception:
                pass
            launcher_changed = any(
                (f["path"].lower() in EXE_NAMES) if self.frozen else f["path"].startswith("Launcher/")
                for f in pending)
            self.set(status="done", phase="Update complete", percent=100.0, speed_bps=0.0,
                     local_sha=str(man.get("version") or ""), remote_sha=str(man.get("version") or ""),
                     launcher_changed=launcher_changed, pending=[],
                     message="Updated %d file(s)" % len(pending))
        except Exception as e:
            self.set(status="error", phase="Update failed", message=str(e)[:400], speed_bps=0.0)

    # ------------------------------------------------------------ restart
    def staged_exes(self):
        out = []
        for name in ("launcher.exe", "CyberHunterLauncher.exe"):
            p = os.path.join(self.root, name + ".new")
            if os.path.isfile(p):
                out.append(name)
        return out
