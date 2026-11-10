# coding: utf-8
"""Discord Rich Presence forwarder for Cyber Hunter Reawakening (Python 3).

Started by run_offline_python.ps1 right after client.exe, one per Play.
The in-game payload writes client/runtime/discord_presence.json every few
seconds (see _lf_discord_tick in client/frida/lobby_full_payload.py):

    {"state": "lobby"}
    {"state": "matching", "mode": "Classic BR Solo", "players": 3}
    {"state": "in_match", "mode": "Rapid Duel", "alive": 37}

This script turns that into a Discord activity over Discord's local IPC pipe
(\\\\.\\pipe\\discord-ipc-N). Stdlib only, no pypresence. If Discord is not
running it just retries quietly. It exits (and clears the status) when
client.exe exits.

Config (revival_config.env, all optional):
    DISCORD_PRESENCE=0          turn it off
    DISCORD_CLIENT_ID=...       Discord application id (Developer Portal);
                                its name is the "Playing ..." title
    DISCORD_LARGE_IMAGE=...     override the launcher icon (art key or https URL)
    DISCORD_SMALL_IMAGE=...     override the CH badge
    DISCORD_BUTTON_LABEL/URL    override the first (DISCORD) button
"""
import argparse
import json
import os
import struct
import sys
import time
import uuid

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FEED = os.path.join(ROOT, "client", "runtime", "discord_presence.json")
CONFIG = os.path.join(ROOT, "revival_config.env")
LOG = os.path.join(ROOT, "client", "runtime", "discord_presence.log")

# Navy Games' Discord application. Override with DISCORD_CLIENT_ID.
DEFAULT_CLIENT_ID = "1569728647969902713"

STALE_S = 45.0          # payload heartbeats every 15 s


def log(msg):
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write("%s %s\n" % (time.strftime("%H:%M:%S"), msg))
    except OSError:
        pass


def read_config():
    cfg = {}
    try:
        with open(CONFIG, "r", encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip().strip('"')
    except OSError:
        pass
    return cfg


def pid_alive(pid):
    if not pid:
        return True
    if os.name == "nt":
        import ctypes
        k32 = ctypes.windll.kernel32
        h = k32.OpenProcess(0x1000, False, int(pid))  # QUERY_LIMITED_INFORMATION
        if not h:
            return False
        code = ctypes.c_ulong()
        ok = k32.GetExitCodeProcess(h, ctypes.byref(code))
        k32.CloseHandle(h)
        return bool(ok) and code.value == 259  # STILL_ACTIVE
    try:
        os.kill(int(pid), 0)
        return True
    except OSError:
        return False


class DiscordIPC(object):
    """Minimal Discord RPC client: handshake + SET_ACTIVITY."""

    def __init__(self, client_id):
        self.client_id = client_id
        self.pipe = None

    def connect(self):
        for i in range(10):
            path = (r"\\.\pipe\discord-ipc-%d" % i) if os.name == "nt" else \
                os.path.join(os.environ.get("XDG_RUNTIME_DIR", "/tmp"), "discord-ipc-%d" % i)
            try:
                if os.name == "nt":
                    self.pipe = open(path, "r+b", buffering=0)
                else:
                    import socket
                    s = socket.socket(socket.AF_UNIX)
                    s.connect(path)
                    self.pipe = s.makefile("rwb", buffering=0)
            except OSError:
                continue
            try:
                self._send(0, {"v": 1, "client_id": self.client_id})
                op, data = self._recv()
                if data.get("evt") == "READY":
                    log("connected to %s as %s" % (path, (data.get("data") or {}).get("user", {}).get("username")))
                    return True
                log("handshake refused: %r" % data)
            except (OSError, ValueError, struct.error) as e:
                log("handshake %s: %s" % (path, e))
            self.close()
        return False

    def _send(self, op, payload):
        body = json.dumps(payload).encode("utf-8")
        self.pipe.write(struct.pack("<II", op, len(body)) + body)

    def _read_exact(self, n):
        buf = b""
        while len(buf) < n:
            chunk = self.pipe.read(n - len(buf))
            if not chunk:
                raise OSError("discord pipe closed")
            buf += chunk
        return buf

    def _recv(self):
        op, length = struct.unpack("<II", self._read_exact(8))
        return op, json.loads(self._read_exact(length).decode("utf-8"))

    def set_activity(self, activity):
        self._send(1, {"cmd": "SET_ACTIVITY",
                       "args": {"pid": os.getpid(), "activity": activity},
                       "nonce": str(uuid.uuid4())})
        op, data = self._recv()
        if data.get("evt") == "ERROR":
            log("SET_ACTIVITY error: %r" % data.get("data"))

    def close(self):
        try:
            if self.pipe:
                self.pipe.close()
        except OSError:
            pass
        self.pipe = None


TEAM_NAMES = {1: "Solo", 2: "Duo", 4: "Squad"}
DIST = "https://raw.githubusercontent.com/navygames/cyber-hunter-dist/main/Launcher/ui/assets/"
DEFAULT_LARGE_IMAGE = DIST + "app-icon.png"     # the launcher icon
DEFAULT_SMALL_IMAGE = DIST + "ch-logo.png"      # the CH game logo
DEFAULT_BUTTONS = (("DISCORD", "https://discord.gg/uXc8frbz5Y"),
                   ("PLAY", "https://chreawakening.vercel.app/"))


def build_activity(feed, since, cfg):
    """Discord card, e.g.
        Cyber Hunter Reawakening
        Rapid Duel - Duo
        Searching for a match (2 of 2)
        00:52
    """
    state = feed.get("state") or "lobby"
    mode = feed.get("mode") or "Cyber Hunter"
    pmax = int(feed.get("party_max") or 0)
    party = int(feed.get("party") or 0)
    details = mode
    if pmax in TEAM_NAMES and mode in ("Classic BR", "Rapid Duel"):
        details = "%s · %s" % (mode, TEAM_NAMES[pmax])
    act = {"details": details, "timestamps": {"start": int(since)}}

    if state == "matching":
        act["state"] = "Searching for a match"
    elif state == "in_match":
        if feed.get("alive"):
            act["state"] = "In match · %d alive" % int(feed["alive"])
        elif feed.get("score"):
            act["state"] = "In match · %s" % feed["score"]
        else:
            act["state"] = "In match"
    else:
        act["state"] = "In lobby"
    if pmax > 1 and party > 0:
        act["party"] = {"id": "party-%d" % os.getpid(), "size": [min(party, pmax), pmax]}

    act["assets"] = {
        "large_image": cfg.get("DISCORD_LARGE_IMAGE") or DEFAULT_LARGE_IMAGE,
        "large_text": "Cyber Hunter Reawakening",
        "small_image": cfg.get("DISCORD_SMALL_IMAGE") or DEFAULT_SMALL_IMAGE,
        "small_text": cfg.get("REVIVAL_SERVER_NAME") or "Cyber Hunter Reawakening",
    }
    buttons = list(DEFAULT_BUTTONS)
    lbl, url = cfg.get("DISCORD_BUTTON_LABEL"), cfg.get("DISCORD_BUTTON_URL")
    if lbl and url and url.startswith("https://"):
        buttons = [(lbl, url)] + buttons[1:]
    act["buttons"] = [{"label": l[:32], "url": u} for l, u in buttons[:2]]
    return act


def read_feed():
    try:
        with open(FEED, "r", encoding="utf-8") as f:
            d = json.load(f)
        if time.time() - float(d.get("updated") or 0) > STALE_S:
            return None
        return d
    except (OSError, ValueError):
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pid", type=int, default=0, help="client.exe pid; exit when it exits")
    ap.add_argument("--once", action="store_true", help="push the current feed once and exit (testing)")
    args = ap.parse_args()

    cfg = read_config()
    if cfg.get("DISCORD_PRESENCE", "1").lower() in ("0", "false", "off", "no"):
        return 0
    client_id = cfg.get("DISCORD_CLIENT_ID") or DEFAULT_CLIENT_ID
    if not client_id:
        log("no DISCORD_CLIENT_ID set - Discord status disabled")
        return 0

    ipc = DiscordIPC(client_id)
    last_key, since, sent_key = None, time.time(), None
    next_connect = 0.0
    while pid_alive(args.pid):
        feed = read_feed() or {"state": "lobby"}
        key = (feed.get("state"), feed.get("mode"))
        if key != last_key:
            last_key, since = key, time.time()
        act = build_activity(feed, since, cfg)
        akey = json.dumps(act, sort_keys=True)
        if ipc.pipe is None and time.time() >= next_connect:
            if not ipc.connect():
                next_connect = time.time() + 15.0
            sent_key = None
        if ipc.pipe is not None and akey != sent_key:
            try:
                ipc.set_activity(act)
                sent_key = akey
            except (OSError, ValueError, struct.error) as e:
                log("lost discord: %s" % e)
                ipc.close()
                next_connect = time.time() + 5.0
        if args.once:
            break
        time.sleep(2.0)

    if ipc.pipe is not None:
        try:
            ipc.set_activity(None)
        except (OSError, ValueError, struct.error):
            pass
        ipc.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
