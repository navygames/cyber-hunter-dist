"""
Cyber Hunter Reawakening - game client downloader & installer.

Downloads the multi-part game archive, extracts it, and puts the game in
``game\\`` next to the launcher (``<launcher folder>\\game\\bin\\client.exe``),
whatever top-level folder name the archives use. The launcher then points its
Game Path at that client.exe automatically.

Pause / resume survives launcher restarts (state in .installer_tmp\\).

Security
  * No credentials ship with the launcher. The previous build carried a GitHub
    OAuth token (XOR-"encrypted" with a key stored next to it), i.e. every
    player had full access to that GitHub account. Archives are now fetched
    from a PUBLIC URL: GitHub release assets of a public repo by default, or
    any HTTPS mirror set with REVIVAL_GAME_DOWNLOAD_URL in revival_config.env.
  * Archive members that would land outside the game folder (absolute paths,
    "..", drive letters) are refused.
"""

import json
import os
import shutil
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile

# Public manifest. No secrets here on purpose.
_MANIFEST = {
    "repo": "navygames/cyber-hunter-dist",  # PUBLIC distribution repo (game assets only, no source)
    "tag": "game-client-v1",
    "parts": [
        {"name": "game-part1.zip", "size": 1564143619},
        {"name": "game-part2.zip", "size": 1705633438},
        {"name": "game-part3.zip", "size": 1764076156},
        {"name": "game-part4.zip", "size": 1442823548},
        {"name": "game-part5.zip", "size": 1802815908},
        {"name": "game-part6.zip", "size": 1506131282},
    ],
}

_STATE_FILE_NAME = "download_state.json"
_TMP_DIR_NAME = ".installer_tmp"
_EXTRACT_DIR_NAME = "extract"
GAME_DIR_NAME = "game"
_USER_AGENT = "CyberHunterLauncher/2.0"
_CHUNK = 1024 * 1024
# Folders of the launcher package an archive may never write into.
_PROTECTED_TOP = {"launcher", "client", "tools", "game-server", "controlpanel", "config",
                  "runtime", _TMP_DIR_NAME, ".git"}


def _read_revival_env(root_dir):
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


def _load_manifest(username=None, auth_token=None):
    try:
        import accounts
    except ImportError:
        from Launcher import accounts
    if not accounts.verify_download_authorization(username, auth_token):
        return None
    return json.loads(json.dumps(_MANIFEST))


def _part_url(root_dir, manifest, part):
    base = (_read_revival_env(root_dir).get("REVIVAL_GAME_DOWNLOAD_URL") or "").strip()
    name = urllib.parse.quote(part["name"])
    if base:
        if not base.lower().startswith("https://"):
            raise RuntimeError("REVIVAL_GAME_DOWNLOAD_URL must be an https:// URL.")
        return base.rstrip("/") + "/" + name
    return "https://github.com/%s/releases/download/%s/%s" % (
        manifest["repo"], urllib.parse.quote(manifest["tag"]), name)


def _tmp_dir(root_dir):
    return os.path.join(root_dir, _TMP_DIR_NAME)


def _get_state_file(root_dir):
    return os.path.join(_tmp_dir(root_dir), _STATE_FILE_NAME)


def _load_disk_state(root_dir):
    try:
        path = _get_state_file(root_dir)
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _save_disk_state(root_dir, data):
    try:
        d = _tmp_dir(root_dir)
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, _STATE_FILE_NAME)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_path, path)
    except Exception:
        pass


def _find_client_exe(base, max_depth=4):
    """Return the game folder (the parent of bin\\client.exe) under base, or None."""
    if not os.path.isdir(base):
        return None
    base_depth = base.rstrip("\\/").count(os.sep)
    for cur, dirs, files in os.walk(base):
        depth = cur.count(os.sep) - base_depth
        if os.path.basename(cur).lower() == "bin" and any(f.lower() == "client.exe" for f in files):
            return os.path.dirname(cur)
        if depth >= max_depth:
            dirs[:] = []
        else:
            dirs[:] = [d for d in dirs if not d.startswith(".") or d == _EXTRACT_DIR_NAME]
    return None


def installed_client_exe(root_dir):
    """Path of the installed client.exe (game\\ first, then legacy names), or ''."""
    for name in (GAME_DIR_NAME, "Game", "Cyber Hunter", "Cyber Steam"):
        p = os.path.join(root_dir, name, "bin", "client.exe")
        if os.path.isfile(p):
            return p
    return ""


def _merge_move(src, dst):
    """Move src's contents into dst (same drive, so these are renames)."""
    os.makedirs(dst, exist_ok=True)
    for name in os.listdir(src):
        s = os.path.join(src, name)
        d = os.path.join(dst, name)
        if os.path.isdir(s) and os.path.isdir(d):
            _merge_move(s, d)
            try:
                os.rmdir(s)
            except OSError:
                pass
        else:
            if os.path.exists(d):
                if os.path.isdir(d):
                    shutil.rmtree(d, ignore_errors=True)
                else:
                    os.remove(d)
            os.replace(s, d)


def normalize_game_folder(root_dir):
    """Make sure the game lives at <root>\\game. Returns client.exe path or ''."""
    target = os.path.join(root_dir, GAME_DIR_NAME)
    if os.path.isfile(os.path.join(target, "bin", "client.exe")):
        return os.path.join(target, "bin", "client.exe")
    found = _find_client_exe(os.path.join(_tmp_dir(root_dir), _EXTRACT_DIR_NAME))
    if not found:
        # Older launcher builds extracted straight into the launcher folder.
        for name in os.listdir(root_dir):
            p = os.path.join(root_dir, name)
            if os.path.isdir(p) and name.lower() not in _PROTECTED_TOP and not name.startswith("."):
                if os.path.isfile(os.path.join(p, "bin", "client.exe")):
                    found = p
                    break
    if not found:
        return ""
    if os.path.normcase(os.path.abspath(found)) != os.path.normcase(os.path.abspath(target)):
        if not os.path.exists(target):
            os.replace(found, target)
        else:
            _merge_move(found, target)
            shutil.rmtree(found, ignore_errors=True)
    exe = os.path.join(target, "bin", "client.exe")
    return exe if os.path.isfile(exe) else ""


def _safe_extract(zip_path, dest, legacy_root=False):
    """extractall with explicit path checks. Raises zipfile.BadZipFile on corruption."""
    dest_abs = os.path.abspath(dest)
    with zipfile.ZipFile(zip_path, "r") as zf:
        for info in zf.infolist():
            name = info.filename.replace("\\", "/")
            parts = [p for p in name.split("/") if p not in ("", ".")]
            if not parts or ".." in parts or ":" in parts[0] or name.startswith("/"):
                continue
            if legacy_root and parts[0].lower() in _PROTECTED_TOP:
                continue
            out = os.path.abspath(os.path.join(dest_abs, *parts))
            if not (out == dest_abs or out.startswith(dest_abs + os.sep)):
                continue
            if info.is_dir():
                os.makedirs(out, exist_ok=True)
                continue
            os.makedirs(os.path.dirname(out), exist_ok=True)
            with zf.open(info) as src, open(out, "wb") as dst:
                shutil.copyfileobj(src, dst, _CHUNK)


class GameDownloader:
    _lock = threading.RLock()
    _worker_thread = None
    _pause_requested = threading.Event()
    _completed_parts = []
    _state = {
        "installed": False,
        "status": "idle",  # idle | downloading | paused | extracting | done | error
        "phase": "",
        "percent": 0.0,
        "part_current": 0,
        "part_total": len(_MANIFEST["parts"]),
        "received_bytes": 0,
        "total_bytes": sum(p["size"] for p in _MANIFEST["parts"]),
        "speed_bps": 0.0,
        "message": "",
        "game_path": "",
    }

    @classmethod
    def is_installed(cls, root_dir):
        exe = installed_client_exe(root_dir)
        with cls._lock:
            cls._state["installed"] = bool(exe)
            if exe:
                cls._state.update(status="done", percent=100.0, speed_bps=0.0, game_path=exe)
        return bool(exe)

    @classmethod
    def get_state(cls, root_dir=None):
        with cls._lock:
            if cls._worker_thread and cls._worker_thread.is_alive():
                return dict(cls._state)
            if root_dir and cls.is_installed(root_dir):
                return dict(cls._state)
            if root_dir:
                disk = _load_disk_state(root_dir)
                if disk:
                    st = disk.get("status", "idle")
                    if st in ("downloading", "extracting"):
                        st = "paused"
                        pct = disk.get("percent", 0.0)
                        disk["phase"] = "Download paused (%d%%) — Click Continue Download to resume" % int(pct)
                        disk["speed_bps"] = 0.0
                    disk["status"] = st
                    cls._completed_parts = list(disk.get("completed_parts", []))
                    cls._state.update({k: v for k, v in disk.items() if k in cls._state})
            return dict(cls._state)

    @classmethod
    def _set_state(cls, **kwargs):
        with cls._lock:
            cls._state.update(kwargs)

    @classmethod
    def _persist(cls, root_dir, **extra):
        with cls._lock:
            data = dict(cls._state)
            data["completed_parts"] = list(cls._completed_parts)
            data.update(extra)
        disk = _load_disk_state(root_dir)
        if "extract_dir" in disk and "extract_dir" not in data:
            data["extract_dir"] = disk["extract_dir"]
        _save_disk_state(root_dir, data)

    @classmethod
    def pause(cls, root_dir=None):
        with cls._lock:
            cls._pause_requested.set()
            cur_pct = cls._state.get("percent", 0.0)
            cls._state["status"] = "paused"
            cls._state["phase"] = "Download paused (%d%%) — Click Continue Download to resume" % int(cur_pct)
            cls._state["speed_bps"] = 0.0
        if root_dir:
            cls._persist(root_dir)
        return {"success": True, "message": "Download paused."}

    @classmethod
    def resume(cls, root_dir, auth_token=None, username=None):
        return cls.start(root_dir, auth_token=auth_token, username=username)

    @classmethod
    def start(cls, root_dir, auth_token=None, username=None):
        if not auth_token or not username:
            return {"success": False, "message": "Access Denied: Please sign in before downloading the game."}
        manifest = _load_manifest(username, auth_token)
        if not manifest:
            return {"success": False, "message": "Your session expired. Sign in again to download the game."}
        if cls.is_installed(root_dir):
            return {"success": False, "message": "Game is already installed."}

        parts = manifest["parts"]
        total = sum(p["size"] for p in parts)
        with cls._lock:
            if cls._worker_thread and cls._worker_thread.is_alive():
                return {"success": True, "message": "Download is already in progress."}
            cls._pause_requested.clear()
            disk = _load_disk_state(root_dir)
            cls._completed_parts = list(disk.get("completed_parts", []))

            # Disk space: what is left to download + room to extract one part.
            remaining = sum(p["size"] for p in parts if p["name"] not in cls._completed_parts)
            if remaining:
                need = remaining + max(p["size"] for p in parts)
                try:
                    free = shutil.disk_usage(root_dir).free
                    if free < need:
                        return {"success": False,
                                "message": "Not enough disk space: %.1f GB free, about %.1f GB needed."
                                           % (free / 1e9, need / 1e9)}
                except Exception:
                    pass

            done_bytes = sum(p["size"] for p in parts if p["name"] in cls._completed_parts)
            cls._state.update({
                "status": "downloading",
                "phase": "Connecting to download server...",
                "percent": min(85.0, done_bytes / float(total) * 85.0) if total else 0.0,
                "part_current": len(cls._completed_parts) + 1,
                "part_total": len(parts),
                "received_bytes": done_bytes,
                "total_bytes": total,
                "speed_bps": 0.0,
                "message": "",
            })
            cls._worker_thread = threading.Thread(target=cls._worker, args=(root_dir, manifest), daemon=True)
            cls._worker_thread.start()
        return {"success": True, "message": "Game download started."}

    @classmethod
    def _paused(cls, root_dir, done_bytes, total, idx, nparts):
        pct = min(85.0, done_bytes / float(total) * 85.0) if total else 0.0
        cls._set_state(status="paused",
                       phase="Download paused (%d%%) — Click Continue Download to resume" % int(pct),
                       percent=pct, part_current=idx, part_total=nparts,
                       received_bytes=done_bytes, speed_bps=0.0)
        cls._persist(root_dir)

    @classmethod
    def _download_part(cls, root_dir, url, dest, expected, done_before, total, idx, nparts):
        """Download one archive with Range resume. Returns False if paused."""
        existing = os.path.getsize(dest) if os.path.exists(dest) else 0
        if existing > expected:
            os.remove(dest)
            existing = 0
        if existing == expected:
            return True
        headers = {"User-Agent": _USER_AGENT, "Accept": "application/octet-stream"}
        if existing:
            headers["Range"] = "bytes=%d-" % existing
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            final_url = resp.geturl() or ""
            if not final_url.lower().startswith("https://"):
                raise RuntimeError("Download was redirected to an insecure URL.")
            mode = "ab"
            received = existing
            if existing and resp.status != 206:
                mode, received = "wb", 0   # server ignored Range: start over
            last_t, since, speed = time.time(), 0, 0.0
            with open(dest, mode) as out:
                while True:
                    if cls._pause_requested.is_set():
                        out.flush()
                        cls._paused(root_dir, done_before + received, total, idx, nparts)
                        return False
                    chunk = resp.read(_CHUNK)
                    if not chunk:
                        break
                    out.write(chunk)
                    received += len(chunk)
                    since += len(chunk)
                    now = time.time()
                    if now - last_t >= 0.5:
                        speed = since / (now - last_t)
                        last_t, since = now, 0
                    cur = done_before + received
                    cls._set_state(percent=min(85.0, cur / float(total) * 85.0) if total else 0.0,
                                   received_bytes=cur, speed_bps=speed)
        if received != expected:
            raise RuntimeError("Download of %s was cut off (%d of %d bytes). Click Continue Download to retry."
                               % (os.path.basename(dest), received, expected))
        return True

    @classmethod
    def _worker(cls, root_dir, manifest):
        parts = manifest["parts"]
        total = sum(p["size"] for p in parts)
        nparts = len(parts)
        tmp = _tmp_dir(root_dir)
        os.makedirs(tmp, exist_ok=True)

        disk = _load_disk_state(root_dir)
        cls._completed_parts = list(disk.get("completed_parts", []))
        # Parts already extracted by an older build went straight into the
        # launcher folder; keep using that so one install is never split.
        legacy = bool(cls._completed_parts) and "extract_dir" not in disk
        extract_dir = root_dir if legacy else os.path.join(tmp, _EXTRACT_DIR_NAME)
        os.makedirs(extract_dir, exist_ok=True)
        cls._persist(root_dir, extract_dir="root" if legacy else _EXTRACT_DIR_NAME)

        done = 0
        try:
            for idx, part in enumerate(parts, start=1):
                name, size = part["name"], part["size"]
                if name in cls._completed_parts:
                    done += size
                    continue
                if cls._pause_requested.is_set():
                    cls._paused(root_dir, done, total, idx, nparts)
                    return
                cls._set_state(status="downloading", part_current=idx, part_total=nparts,
                               phase="Downloading part %d/%d (%s)..." % (idx, nparts, name))
                dest = os.path.join(tmp, name)
                url = _part_url(root_dir, manifest, part)
                if not cls._download_part(root_dir, url, dest, size, done, total, idx, nparts):
                    return
                done += size

                if cls._pause_requested.is_set():
                    cls._paused(root_dir, done, total, idx, nparts)
                    return
                cls._set_state(status="extracting", speed_bps=0.0,
                               phase="Extracting part %d/%d (%s)..." % (idx, nparts, name))
                try:
                    _safe_extract(dest, extract_dir, legacy_root=legacy)
                except zipfile.BadZipFile:
                    try:
                        os.remove(dest)
                    except Exception:
                        pass
                    raise RuntimeError("%s was corrupted during download and has been removed. "
                                       "Click Continue Download to fetch it again." % name)
                cls._completed_parts.append(name)
                try:
                    os.remove(dest)   # free the space before the next part
                except Exception:
                    pass
                cls._set_state(percent=min(99.0, 85.0 + len(cls._completed_parts) / float(nparts) * 14.0))
                cls._persist(root_dir)

            cls._set_state(status="extracting", phase="Finalizing installation...", percent=99.0)
            exe = normalize_game_folder(root_dir)
            if not exe:
                cls._set_state(status="error", phase="Install failed",
                               message="Download finished, but bin\\client.exe was not found in the archives.")
                cls._persist(root_dir)
                return
            cls._set_state(status="done", phase="Installation complete! Ready to play.", percent=100.0,
                           received_bytes=total, speed_bps=0.0, installed=True, game_path=exe,
                           message="Game installed to %s" % os.path.dirname(os.path.dirname(exe)))
            shutil.rmtree(tmp, ignore_errors=True)
        except Exception as e:
            if cls._pause_requested.is_set():
                cls._paused(root_dir, done, total, cls._state.get("part_current", 1), nparts)
                return
            msg = str(e)
            if isinstance(e, urllib.error.HTTPError) and e.code in (401, 403, 404):
                msg = ("The download server refused the request (HTTP %d). The game files may not be "
                       "public yet - contact the Navy Games team." % e.code)
            elif isinstance(e, urllib.error.URLError):
                msg = "Can't reach the download server. Check your connection and click Continue Download."
            cls._set_state(status="error", phase="Download failed", message=msg[:300], speed_bps=0.0)
            cls._persist(root_dir)
