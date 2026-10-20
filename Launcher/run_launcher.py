"""
Cyber Hunter Reawakening - Aesthetic Game Launcher Backend
Powered by pywebview (Edge WebView2) & Python Native IPC
"""

import os
import sys
import json
import subprocess
import threading
import time
import urllib.request
import socket
import webbrowser
import ctypes
import tkinter as tk
from tkinter import filedialog
import webview

if getattr(sys, 'frozen', False):
    BUNDLE_DIR = sys._MEIPASS
    ROOT_DIR = os.path.dirname(sys.executable)
    CONFIG_DIR = ROOT_DIR
else:
    BUNDLE_DIR = os.path.dirname(os.path.abspath(__file__))
    ROOT_DIR = os.path.abspath(os.path.join(BUNDLE_DIR, ".."))
    CONFIG_DIR = BUNDLE_DIR

# Support both clean Public Test layout (Game/ + Runtime/ + Config/) and canonical repo layout:
GAME_DIR = os.path.join(ROOT_DIR, "Game") if os.path.exists(os.path.join(ROOT_DIR, "Game")) else os.path.join(ROOT_DIR, "game")
CYBER_STEAM_DIR = os.path.join(ROOT_DIR, "Cyber Steam")
CYBER_HUNTER_DIR = GAME_DIR if os.path.exists(os.path.join(GAME_DIR, "bin", "client.exe")) else (
    CYBER_STEAM_DIR if os.path.exists(os.path.join(CYBER_STEAM_DIR, "bin", "client.exe")) else GAME_DIR
)
CLIENT_EXE = os.path.join(CYBER_HUNTER_DIR, "bin", "client.exe")
LAUNCHER_EXE = os.path.join(CYBER_HUNTER_DIR, "launcher.exe")


def _refresh_game_paths():
    """Re-resolve where client.exe lives (the downloader can install it while
    the launcher runs) and point launcher_config.json's game_path at it."""
    global GAME_DIR, CYBER_HUNTER_DIR, CLIENT_EXE, LAUNCHER_EXE
    GAME_DIR = os.path.join(ROOT_DIR, "Game") if os.path.exists(os.path.join(ROOT_DIR, "Game", "bin", "client.exe")) else os.path.join(ROOT_DIR, "game")
    CYBER_HUNTER_DIR = GAME_DIR if os.path.exists(os.path.join(GAME_DIR, "bin", "client.exe")) else (
        CYBER_STEAM_DIR if os.path.exists(os.path.join(CYBER_STEAM_DIR, "bin", "client.exe")) else GAME_DIR
    )
    CLIENT_EXE = os.path.join(CYBER_HUNTER_DIR, "bin", "client.exe")
    LAUNCHER_EXE = os.path.join(CYBER_HUNTER_DIR, "launcher.exe")
    return CLIENT_EXE if os.path.isfile(CLIENT_EXE) else ""


RUNTIME_DIR = os.path.join(ROOT_DIR, "Runtime", "runtime") if os.path.exists(os.path.join(ROOT_DIR, "Runtime", "runtime")) else (
    os.path.join(ROOT_DIR, "Runtime") if os.path.isdir(os.path.join(ROOT_DIR, "Runtime")) and not os.path.isdir(os.path.join(ROOT_DIR, "client", "runtime"))
    else os.path.join(ROOT_DIR, "client", "runtime")
)
STATUS_FILE = os.path.join(RUNTIME_DIR, "offline_lobby_status.json")
LOG_FILE = os.path.join(RUNTIME_DIR, "lobby_full.log")

FRIDA_DIR = os.path.join(ROOT_DIR, "Runtime", "frida") if os.path.exists(os.path.join(ROOT_DIR, "Runtime", "frida")) else os.path.join(ROOT_DIR, "client", "frida")
OFFLINE_PS1 = os.path.join(ROOT_DIR, "client", "launchers", "run_offline_python.ps1")
if not os.path.exists(OFFLINE_PS1) and os.path.exists(os.path.join(ROOT_DIR, "Runtime", "launchers", "run_offline_python.ps1")):
    OFFLINE_PS1 = os.path.join(ROOT_DIR, "Runtime", "launchers", "run_offline_python.ps1")
PRIVATE_SERVER_DIR = os.path.join(ROOT_DIR, "Runtime", "tools") if os.path.exists(os.path.join(ROOT_DIR, "Runtime", "tools")) else os.path.join(ROOT_DIR, "tools", "private_server")
INSTALLER_PY = os.path.join(ROOT_DIR, "Installer", "run_installer.py")
ACCOUNT_MANAGER_PY = os.path.join(ROOT_DIR, "account_manager.py")

try:
    from game_downloader import GameDownloader
except ImportError:
    try:
        from Launcher.game_downloader import GameDownloader
    except ImportError:
        GameDownloader = None

# Native boot (docs/NATIVE_SCRIPTS.md): the offline brain as compiled .nxs,
# loaded by client.exe itself. Player installs ship only this, no Frida.
NATIVE_SCRIPT_DIR = os.path.join(ROOT_DIR, "Runtime", "native", "script") if os.path.exists(os.path.join(ROOT_DIR, "Runtime", "native", "script")) else os.path.join(ROOT_DIR, "client", "native", "build", "script")
NATIVE_PACK = os.path.join(NATIVE_SCRIPT_DIR, "reawakening", "pack.nxs")
FRIDA_OFFLINE_PATHS = [
    os.path.join(ROOT_DIR, "client", "frida", "lobby_full.js"),
    os.path.join(ROOT_DIR, "client", "frida", "lobby_full_payload.py"),
    os.path.join(ROOT_DIR, "client", "frida", "offline_account_db.py"),
]


def boot_mode(cfg=None):
    """launcher_config.json "boot_mode" if set, else native when the compiled
    pack is installed, else frida (older installs, dev checkouts without a
    build)."""
    want = str((cfg or {}).get("boot_mode") or "").strip().lower()
    if want in ("frida", "native"):
        return want
    return "native" if os.path.isfile(NATIVE_PACK) else "frida"


REQUIRED_OFFLINE_PATHS = [
    OFFLINE_PS1,
    os.path.join(PRIVATE_SERVER_DIR, "patch_server.py"),
    os.path.join(PRIVATE_SERVER_DIR, "http_stub.py"),
    os.path.join(PRIVATE_SERVER_DIR, "gateway_stub.py"),
]
CONTROL_PANEL_BACKEND = os.path.join(ROOT_DIR, "ControlPanel", "server_backend.py")
REVIVAL_CONFIG_FILE = os.path.join(ROOT_DIR, "Config", "revival_config.env") if os.path.exists(os.path.join(ROOT_DIR, "Config", "revival_config.env")) else os.path.join(ROOT_DIR, "revival_config.env")
REVIVAL_CONFIG_EXAMPLE = os.path.join(ROOT_DIR, "revival_config.env.example")
CONFIG_FILE = os.path.join(CONFIG_DIR, "launcher_config.json")
UI_INDEX_PATH = os.path.join(BUNDLE_DIR, "ui", "index.html")

for _tp in [os.path.join(ROOT_DIR, "Runtime", "tools"), PRIVATE_SERVER_DIR, ROOT_DIR]:
    if _tp and os.path.isdir(_tp) and _tp not in sys.path:
        sys.path.insert(0, _tp)

try:
    from ban_service import ban_service, token_service
except ImportError:
    try:
        from tools.private_server.ban_service import ban_service, token_service
    except ImportError:
        ban_service = None
        token_service = None

server_proc = None

launch_pipeline_running = False

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

def get_revival_config():
    cfg = {
        "server_ip": "127.0.0.1",
        "server_name": "Cyber Hunter Reawakening",
        "patch_port": 443,
        "gateway_port": 10001,
        "gameapi_port": 3000,
        "control_panel_port": 8888,
        "referee_port": 10777,
    }
    cfg_path = REVIVAL_CONFIG_FILE if os.path.exists(REVIVAL_CONFIG_FILE) else REVIVAL_CONFIG_EXAMPLE
    if os.path.exists(cfg_path):
        try:
            # utf-8-sig: Notepad saves with a BOM, which used to glue itself
            # onto the first key and silently drop REVIVAL_SERVER_IP.
            with open(cfg_path, "r", encoding="utf-8-sig") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'").strip()
                        if k == "REVIVAL_SERVER_IP" and v:
                            cfg["server_ip"] = v
                        elif k == "REVIVAL_SERVER_NAME" and v:
                            cfg["server_name"] = v
                        elif k == "REVIVAL_PATCH_PORT" and v.isdigit():
                            cfg["patch_port"] = int(v)
                        elif k == "REVIVAL_GATEWAY_PORT" and v.isdigit():
                            cfg["gateway_port"] = int(v)
                        elif k == "REVIVAL_GAMEAPI_PORT" and v.isdigit():
                            cfg["gameapi_port"] = int(v)
                        elif k == "REVIVAL_CONTROL_PANEL_PORT" and v.isdigit():
                            cfg["control_panel_port"] = int(v)
                        elif k == "REVIVAL_REFEREE_PORT" and v.isdigit():
                            cfg["referee_port"] = int(v)
        except Exception:
            pass
    return cfg

_proc_cache = {}


def is_process_running(proc_name, max_age=1.0):
    """Fast in-process check via Win32 Toolhelp32 snapshot (~0.01s, 0 subprocesses).
    Falls back to tasklist if ctypes is unavailable.
    """
    hit = _proc_cache.get(proc_name)
    now = time.time()
    if hit and (now - hit[0]) < max_age:
        return hit[1]
    alive = False
    if os.name == 'nt':
        try:
            from ctypes import wintypes
            class _PE32(ctypes.Structure):
                _fields_ = [
                    ('dwSize', wintypes.DWORD),
                    ('cntUsage', wintypes.DWORD),
                    ('th32ProcessID', wintypes.DWORD),
                    ('th32DefaultHeapID', ctypes.c_size_t),
                    ('th32ModuleID', wintypes.DWORD),
                    ('cntThreads', wintypes.DWORD),
                    ('th32ParentProcessID', wintypes.DWORD),
                    ('pcPriClassBase', wintypes.LONG),
                    ('dwFlags', wintypes.DWORD),
                    ('szExeFile', ctypes.c_char * 260)
                ]
            k32 = ctypes.windll.kernel32
            snap = k32.CreateToolhelp32Snapshot(2, 0)
            if snap and snap != -1:
                pe = _PE32()
                pe.dwSize = ctypes.sizeof(_PE32)
                target = proc_name.lower().encode('utf-8')
                if k32.Process32First(snap, ctypes.byref(pe)):
                    while True:
                        if pe.szExeFile.lower() == target:
                            alive = True
                            break
                        if not k32.Process32Next(snap, ctypes.byref(pe)):
                            break
                k32.CloseHandle(snap)
                _proc_cache[proc_name] = (now, alive)
                return alive
        except Exception:
            pass
    try:
        output = subprocess.check_output(
            ["tasklist", "/FI", f"IMAGENAME eq {proc_name}"],
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
            text=True
        )
        alive = proc_name.lower() in output.lower()
    except Exception:
        alive = False
    _proc_cache[proc_name] = (now, alive)
    return alive

def _suppress_debug_window_loop():
    if os.name != 'nt':
        return
    user32 = ctypes.windll.user32
    while True:
        try:
            hwnd = user32.FindWindowW(None, "Run-time Debug")
            if hwnd:
                user32.ShowWindow(hwnd, 0)
                user32.PostMessageW(hwnd, 0x0010, 0, 0)
        except Exception:
            pass
        time.sleep(0.3)

threading.Thread(target=_suppress_debug_window_loop, daemon=True).start()

# Launcher/ must be importable for `import accounts` regardless of cwd, and
# under PyInstaller the module lives in the bundle, not next to the exe.
for _p in (BUNDLE_DIR, CONFIG_DIR):
    if _p and _p not in sys.path:
        sys.path.insert(0, _p)


def get_default_config():
    rev = get_revival_config()
    server_ip = (rev.get("server_ip") or "127.0.0.1").strip()
    panel_port = rev.get("control_panel_port", 8888)
    remote = is_remote_mode()
    server_url = f"http://{server_ip}:{panel_port}" if remote else f"http://127.0.0.1:{panel_port}"
    return {
        "game_path": CLIENT_EXE if os.path.exists(CLIENT_EXE) else "",
        "server_url": server_url,
        "auto_server": not remote,
        "close_on_launch": False,
        "bgm_enabled": True,
        "env_mode": "auto",
        "auto_weather": True,
        "night_mode": False,
        "fov": 60,
        "graphic_quality": 2,
        "fps_limit": 120,
        "graphics_configured": False
    }

_LEGACY_SERVER_KEYS = (
    "server_mode", "reawakening_server_ip", "revival", "is_remote",
    "na_server_ip", "sea_server_ip", "selected_server_name", "servers_registry",
)


def load_config():
    cfg = None
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception:
            cfg = None
    if not isinstance(cfg, dict):
        cfg = get_default_config()
        save_config(cfg)
        return cfg
    # A saved game_path that is blank or names a file no longer on disk (the
    # config was written before the merged game/ layout, or the drive it
    # pointed at is gone) showed Settings an empty Game Path box while Play
    # quietly fell back to CLIENT_EXE -- two different answers to "where is the
    # client". Heal it here, the one place every caller reads, so the Settings
    # field, Play and Open Installation Folder all name the install we can see.
    # Older launcher builds (the frozen .exe files under dist/) kept their own
    # server picker in this file: server_mode / sea_server_ip / na_server_ip /
    # servers_registry / revival{...}. Those values competed with
    # revival_config.env and are why the client could be pointed at one
    # server while hosts/Frida used another. revival_config.env is the only
    # server source now; drop the stale copies so nothing reads them again.
    _dirty = False
    for _legacy in _LEGACY_SERVER_KEYS:
        if _legacy in cfg:
            cfg.pop(_legacy, None)
            _dirty = True
    if _dirty:
        save_config(cfg)
    if not cfg.get("game_path") or not os.path.exists(cfg["game_path"]):
        cfg["game_path"] = CLIENT_EXE if os.path.exists(CLIENT_EXE) else ""
    # Control Panel URL always follows revival_config.env. The old code only
    # replaced a 127.0.0.1 URL, so a URL saved for a previous VPS (e.g. the
    # retired NA box) stuck forever after the server moved.
    rev = get_revival_config()
    server_ip = (rev.get("server_ip") or "127.0.0.1").strip()
    panel_port = rev.get("control_panel_port", 8888)
    want_url = (f"http://{server_ip}:{panel_port}" if is_remote_mode()
                else f"http://127.0.0.1:{panel_port}")
    if cfg.get("server_url") != want_url:
        cfg["server_url"] = want_url
    if is_remote_mode():
        cfg["auto_server"] = False
    return cfg

def save_config(cfg):
    try:
        clean = {k: v for k, v in dict(cfg).items() if k not in _LEGACY_SERVER_KEYS}
        tmp = CONFIG_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(clean, f, indent=2)
        os.replace(tmp, CONFIG_FILE)  # atomic: a crash mid-write cannot blank the config
        return True
    except Exception as e:
        print("Failed saving config:", e)
        return False

def is_remote_mode():
    """revival_config.env is the single source of truth for where servers run.

    127.0.0.1 / localhost / unset -> local mode: the Launcher starts the
    Control Panel, game API and the patch/http/gateway stack on this PC.
    Any other IP -> remote mode: those already run there, so the Launcher only
    does the half that cannot be remote (hosts, CA, loopback, Frida attach).
    """
    ip = (get_revival_config().get("server_ip") or "").strip()
    return bool(ip) and ip not in ("127.0.0.1", "localhost", "::1")


def _port_open(host, port, timeout=0.25):
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        try:
            s.connect((host, port))
            return True
        except Exception:
            return False
        finally:
            s.close()
    except Exception:
        return False


# Well-known anycast endpoints used only to tell "no internet" apart from
# "the VPS is down". Plain TCP connects - nothing is sent.
_INTERNET_PROBES = (("1.1.1.1", 443), ("8.8.8.8", 53), ("9.9.9.9", 443))

OFFLINE_MESSAGE = "Can't connect. Please connect to the internet."


def _any_port_open(targets, timeout=2.5):
    """True as soon as any (host, port) in targets accepts a TCP connect.

    Probes run in parallel so the worst case is one timeout, not N of them.
    """
    targets = list(targets)
    if not targets:
        return False
    hit = threading.Event()
    done = threading.Semaphore(0)

    def _probe(host, port):
        try:
            if _port_open(host, int(port), timeout):
                hit.set()
        finally:
            done.release()

    for host, port in targets:
        threading.Thread(target=_probe, args=(host, port), daemon=True).start()
    deadline = time.time() + timeout + 0.5
    for _ in targets:
        if hit.is_set():
            break
        left = deadline - time.time()
        if left <= 0 or not done.acquire(timeout=left):
            break
    return hit.is_set()


def check_vps_connectivity():
    """Play gate: the lobby is VPS-only, so no internet / no VPS = no Play.

    Returns {"ok": bool, "reason": "ok"|"no_internet"|"server_down", "message": str}.
    Local mode (127.0.0.1) has no VPS to check and always passes.
    """
    if not is_remote_mode():
        return {"ok": True, "reason": "ok", "message": ""}
    rev = get_revival_config()
    ip = (rev.get("server_ip") or "").strip()
    vps_ports = [rev.get("gateway_port", 10001), rev.get("patch_port", 443),
                 rev.get("control_panel_port", 8888), rev.get("gameapi_port", 3000),
                 rev.get("referee_port", 10777)]
    if _any_port_open([(ip, p) for p in vps_ports]):
        return {"ok": True, "reason": "ok", "message": ""}
    if not _any_port_open(_INTERNET_PROBES):
        return {"ok": False, "reason": "no_internet", "message": OFFLINE_MESSAGE}
    name = rev.get("server_name") or "the game server"
    return {
        "ok": False,
        "reason": "server_down",
        "message": "Can't connect to %s. The server may be offline - please try again later." % name,
    }


def _ensure_suite_services(auto_server=True):
    """Start Control Panel (:8888) + Node game-server (:3000) if auto_server.

    No-op in remote mode: both are server-side and already run on the VPS.
    """
    started = []
    if not auto_server:
        return started
    if is_remote_mode():
        return started
    if os.path.exists(CONTROL_PANEL_BACKEND) and not _port_open("127.0.0.1", 8888):
        try:
            subprocess.Popen(
                [sys.executable, CONTROL_PANEL_BACKEND],
                cwd=os.path.dirname(CONTROL_PANEL_BACKEND),
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            started.append("control_panel:8888")
        except Exception as e:
            print("ControlPanel start:", e)
    gs = os.path.join(ROOT_DIR, "game-server")
    gs_entry = os.path.join(gs, "src", "index.js")
    if os.path.exists(gs_entry) and not _port_open("127.0.0.1", 3000):
        try:
            npm = "npm.cmd" if os.name == "nt" else "npm"
            if not os.path.isdir(os.path.join(gs, "node_modules")):
                try:
                    subprocess.run(
                        [npm, "install"],
                        cwd=gs,
                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                        timeout=180,
                    )
                except Exception as e:
                    print("npm install:", e)
            env = os.environ.copy()
            env.setdefault("PORT", "3000")
            subprocess.Popen(
                [npm, "start"],
                cwd=gs,
                env=env,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            started.append("game-server:3000")
        except Exception as e:
            print("game-server start:", e)
    return started


_NIGHT_ENV_XML = """<SceneEditorSettings
  Type = "1">
  <DefaultSceneConfig>
    <Env
      Time = "0"
      PTLightIntensity = "0"
      PTLightRange = "0"
      PTLightColor = "0,0,0,0"
      DIRLightForward = "-0.22,-0.88,-0.40"
      DIRLightColor = "255,90,120,170"
      DIRLightIntensity = "0.25"
      LightmapWeight0 = "1"
      LightmapWeight1 = "1"
      LightmapWeight2 = "0"
      BgColor = "255,4,8,16"
      WeatherIntensity0 = "0"
      WeatherIntensity1 = "0"
      WeatherIntensity2 = "0"
      EnvExposure = "0.80"
      AOFactor = "0.30"
      Ambient = "0.18,0.22,0.30,1"
      EnvExposureMetallic = "1"
      AmbientMetallic = "0.22,0.26,0.36,1"
      EnvUE4SHR = "-0.005,0.006,0.018,0.016"
      EnvUE4SHG = "-0.007,0.008,0.022,0.019"
      EnvUE4SHB = "-0.010,0.010,0.028,0.022">
      <Fog
        Culling = "false"
        Mode = "5"
        Color = "0,14,24,46"
        DistantColor = "0,10,18,34"
        Start = "80"
        End = "600"
        Distant = "3500"
        ShaderDensity = "2.2"
        Custom0 = "0"
        Custom1 = "-200"
        U4FogColor = "255,14,24,46"
        U4FogHeight = "5000"
        U4FogDensity = "0.048"
        U4FogHeightFalloff = "0.95"
        U4StartDistance = "90"
        U4MaxOpacity = "0.94"
        U4FogDirInscatteringColor = "255,22,35,68"
        U4DirInscatteringE = "8"
        U4DirInscatteringStart = "400"
        U4SkyRate = "0.04" />
      <LensFlare
        SchemeIdx = "4"
        Tex = "common\\textures\\flare_03.png"
        FadeBegin = "1"
        FadeLength = "1">
        <LensInfo Distance = "0" Intensity = "0" Size = "0" FlareColor = "0,0,0,0" FlareIdx = "1" Rotate = "false" Fade = "false" />
        <LensInfo Distance = "0.02" Intensity = "0" Size = "0" FlareColor = "0,0,0,0" FlareIdx = "2" Rotate = "false" Fade = "false" />
        <LensInfo Distance = "0.2" Intensity = "0" Size = "0" FlareColor = "0,0,0,0" FlareIdx = "2" Rotate = "false" Fade = "false" />
        <LensInfo Distance = "0.5" Intensity = "0" Size = "0" FlareColor = "0,0,0,0" FlareIdx = "2" Rotate = "false" Fade = "false" />
        <LensInfo Distance = "1.9" Intensity = "0" Size = "0" FlareColor = "0,0,0,0" FlareIdx = "3" Rotate = "false" Fade = "false" />
        <LensInfo Distance = "1.09" Intensity = "0" Size = "0" FlareColor = "0,0,0,0" FlareIdx = "4" Rotate = "false" Fade = "false" />
        <LensInfo Distance = "0.98" Intensity = "0" Size = "0" FlareColor = "0,0,0,0" FlareIdx = "4" Rotate = "false" Fade = "false" />
        <LensInfo Distance = "0.05" Intensity = "0" Size = "0" FlareColor = "0,0,0,0" FlareIdx = "5" Rotate = "false" Fade = "false" />
        <LensInfo Distance = "0" Intensity = "0" Size = "0" FlareColor = "0,0,0,0" FlareIdx = "6" Rotate = "false" Fade = "false" />
        <LensInfo Distance = "2" Intensity = "0" Size = "0" FlareColor = "0,0,0,0" FlareIdx = "6" Rotate = "false" Fade = "false" />
      </LensFlare>
      <SkyParamFloat>
        <HorizonFalloff Value = "25" />
        <background_intensity Value = "0.12" />
        <cloud_speed Value = "0.5" />
        <low_cloud_pow Value = "1.5" />
      </SkyParamFloat>
      <SkyParamColor>
        <HorizonColor Value = "0.012,0.020,0.045,1.0" />
        <ZenithColor Value = "0.003,0.006,0.015,1.0" />
        <overrall_color Value = "0.05,0.08,0.15,0.2" />
      </SkyParamColor>
      <WaterParamColor>
        <WaterColorCoast Value = "0.10,0.15,0.25,1" />
        <WaterColorDeep Value = "0.02,0.04,0.08,0" />
        <WaterColorShallow Value = "0.03,0.05,0.10,0.6" />
        <low_water_base_color Value = "0.05,0.08,0.15,0.7" />
        <shallowColor Value = "0.08,0.12,0.20,0.5" />
        <specColor Value = "0.15,0.25,0.40,0.3" />
      </WaterParamColor>
    </Env>
  </DefaultSceneConfig>
</SceneEditorSettings>"""

_DAWN_ENV_XML = """<SceneEditorSettings
  Type = "1">
  <DefaultSceneConfig>
    <Env
      Time = "0"
      PTLightIntensity = "0"
      PTLightRange = "0"
      PTLightColor = "0,0,0,0"
      DIRLightForward = "-0.75,-0.35,-0.55"
      DIRLightColor = "255,255,215,190"
      DIRLightIntensity = "2.3"
      LightmapWeight0 = "1"
      LightmapWeight1 = "1"
      LightmapWeight2 = "0"
      BgColor = "255,210,145,130"
      WeatherIntensity0 = "0"
      WeatherIntensity1 = "0"
      WeatherIntensity2 = "0"
      EnvExposure = "2.8"
      AOFactor = "0.33"
      Ambient = "0.62,0.55,0.60,1"
      EnvExposureMetallic = "1"
      AmbientMetallic = "0.75,0.70,0.65,1"
      EnvUE4SHR = "-0.015,0.025,0.080,0.070"
      EnvUE4SHG = "-0.022,0.020,0.075,0.060"
      EnvUE4SHB = "-0.025,0.018,0.085,0.065">
      <Fog
        Culling = "false"
        Mode = "5"
        Color = "0,230,175,160"
        DistantColor = "0,190,140,135"
        Start = "280"
        End = "1100"
        Distant = "6000"
        ShaderDensity = "1"
        Custom0 = "0"
        Custom1 = "-200"
        U4FogColor = "255,230,175,160"
        U4FogHeight = "4500"
        U4FogDensity = "0.009"
        U4FogHeightFalloff = "1.2"
        U4StartDistance = "500"
        U4MaxOpacity = "0.85"
        U4FogDirInscatteringColor = "255,255,200,170"
        U4DirInscatteringE = "10"
        U4DirInscatteringStart = "1200"
        U4SkyRate = "0.02" />
      <LensFlare
        SchemeIdx = "4"
        Tex = "common\\textures\\flare_03.png"
        FadeBegin = "1"
        FadeLength = "1">
        <LensInfo Distance = "0" Intensity = "1.2" Size = "1.5" FlareColor = "1.0,0.85,0.75,1" FlareIdx = "1" Rotate = "false" Fade = "true" />
        <LensInfo Distance = "0.02" Intensity = "0.25" Size = "0.35" FlareColor = "1.0,0.9,0.8,1" FlareIdx = "2" Rotate = "false" Fade = "true" />
        <LensInfo Distance = "0.2" Intensity = "0.5" Size = "0.35" FlareColor = "1.0,0.85,0.7,1" FlareIdx = "2" Rotate = "true" Fade = "true" />
        <LensInfo Distance = "0.5" Intensity = "0.15" Size = "0.8" FlareColor = "1.0,0.8,0.7,1" FlareIdx = "2" Rotate = "true" Fade = "true" />
        <LensInfo Distance = "1.9" Intensity = "1.5" Size = "1.0" FlareColor = "0.8,0.5,0.4,1" FlareIdx = "3" Rotate = "true" Fade = "true" />
        <LensInfo Distance = "1.09" Intensity = "0.1" Size = "0.4" FlareColor = "0.9,0.7,0.5,1" FlareIdx = "4" Rotate = "false" Fade = "true" />
        <LensInfo Distance = "0.98" Intensity = "0.15" Size = "0.3" FlareColor = "1.0,0.6,0.5,1" FlareIdx = "4" Rotate = "false" Fade = "true" />
        <LensInfo Distance = "0.05" Intensity = "0.3" Size = "0.5" FlareColor = "1.0,0.9,0.8,1" FlareIdx = "5" Rotate = "true" Fade = "true" />
      </LensFlare>
      <SkyParamFloat>
        <HorizonFalloff Value = "20" />
        <background_intensity Value = "1.0" />
        <cloud_speed Value = "0.8" />
        <low_cloud_pow Value = "1.1" />
      </SkyParamFloat>
      <SkyParamColor>
        <HorizonColor Value = "0.98,0.62,0.50,1.0" />
        <ZenithColor Value = "0.18,0.22,0.42,1.0" />
        <overrall_color Value = "0.95,0.70,0.60,0.35" />
      </SkyParamColor>
      <WaterParamColor>
        <WaterColorCoast Value = "0.6,0.45,0.50,1" />
        <WaterColorDeep Value = "0.15,0.10,0.18,0" />
        <WaterColorShallow Value = "0.35,0.25,0.30,0.65" />
        <low_water_base_color Value = "0.50,0.40,0.45,0.75" />
        <shallowColor Value = "0.75,0.55,0.50,0.5" />
        <specColor Value = "0.90,0.75,0.65,0.4" />
      </WaterParamColor>
    </Env>
  </DefaultSceneConfig>
</SceneEditorSettings>"""

_SUNSET_ENV_XML = """<SceneEditorSettings
  Type = "1">
  <DefaultSceneConfig>
    <Env
      Time = "0"
      PTLightIntensity = "0"
      PTLightRange = "0"
      PTLightColor = "0,0,0,0"
      DIRLightForward = "-0.85,-0.22,-0.45"
      DIRLightColor = "255,255,125,35"
      DIRLightIntensity = "2.4"
      LightmapWeight0 = "1"
      LightmapWeight1 = "1"
      LightmapWeight2 = "0"
      BgColor = "255,180,75,30"
      WeatherIntensity0 = "0"
      WeatherIntensity1 = "0"
      WeatherIntensity2 = "0"
      EnvExposure = "2.8"
      AOFactor = "0.33"
      Ambient = "0.58,0.45,0.38,1"
      EnvExposureMetallic = "1"
      AmbientMetallic = "0.75,0.60,0.45,1"
      EnvUE4SHR = "-0.010,0.030,0.095,0.080"
      EnvUE4SHG = "-0.018,0.015,0.055,0.045"
      EnvUE4SHB = "-0.028,0.010,0.040,0.035">
      <Fog
        Culling = "false"
        Mode = "5"
        Color = "0,190,85,30"
        DistantColor = "0,150,65,25"
        Start = "250"
        End = "1100"
        Distant = "6000"
        ShaderDensity = "1"
        Custom0 = "0"
        Custom1 = "-200"
        U4FogColor = "255,190,85,30"
        U4FogHeight = "4500"
        U4FogDensity = "0.01"
        U4FogHeightFalloff = "1.2"
        U4StartDistance = "500"
        U4MaxOpacity = "0.88"
        U4FogDirInscatteringColor = "255,255,110,25"
        U4DirInscatteringE = "10"
        U4DirInscatteringStart = "1200"
        U4SkyRate = "0.02" />
      <LensFlare
        SchemeIdx = "4"
        Tex = "common\\textures\\flare_03.png"
        FadeBegin = "1"
        FadeLength = "1">
        <LensInfo Distance = "0" Intensity = "1.6" Size = "1.8" FlareColor = "1.0,0.6,0.2,1" FlareIdx = "1" Rotate = "false" Fade = "true" />
        <LensInfo Distance = "0.02" Intensity = "0.3" Size = "0.4" FlareColor = "1.0,0.7,0.3,1" FlareIdx = "2" Rotate = "false" Fade = "true" />
        <LensInfo Distance = "0.2" Intensity = "0.6" Size = "0.4" FlareColor = "1.0,0.5,0.2,1" FlareIdx = "2" Rotate = "true" Fade = "true" />
        <LensInfo Distance = "0.5" Intensity = "0.2" Size = "1.0" FlareColor = "1.0,0.4,0.1,1" FlareIdx = "2" Rotate = "true" Fade = "true" />
        <LensInfo Distance = "1.9" Intensity = "2.0" Size = "1.3" FlareColor = "0.7,0.3,0.1,1" FlareIdx = "3" Rotate = "true" Fade = "true" />
        <LensInfo Distance = "1.09" Intensity = "0.12" Size = "0.5" FlareColor = "0.9,0.5,0.2,1" FlareIdx = "4" Rotate = "false" Fade = "true" />
        <LensInfo Distance = "0.98" Intensity = "0.2" Size = "0.35" FlareColor = "1.0,0.35,0.1,1" FlareIdx = "4" Rotate = "false" Fade = "true" />
        <LensInfo Distance = "0.05" Intensity = "0.4" Size = "0.6" FlareColor = "1.0,0.7,0.3,1" FlareIdx = "5" Rotate = "true" Fade = "true" />
      </LensFlare>
      <SkyParamFloat>
        <HorizonFalloff Value = "18" />
        <background_intensity Value = "1.1" />
        <cloud_speed Value = "0.8" />
        <low_cloud_pow Value = "1.0" />
      </SkyParamFloat>
      <SkyParamColor>
        <HorizonColor Value = "1.0,0.38,0.06,1.0" />
        <ZenithColor Value = "0.08,0.10,0.28,1.0" />
        <overrall_color Value = "1.0,0.48,0.12,0.45" />
      </SkyParamColor>
      <WaterParamColor>
        <WaterColorCoast Value = "0.65,0.35,0.20,1" />
        <WaterColorDeep Value = "0.18,0.08,0.05,0" />
        <WaterColorShallow Value = "0.40,0.20,0.10,0.65" />
        <low_water_base_color Value = "0.55,0.30,0.15,0.75" />
        <shallowColor Value = "0.80,0.45,0.20,0.5" />
        <specColor Value = "1.0,0.70,0.30,0.5" />
      </WaterParamColor>
    </Env>
  </DefaultSceneConfig>
</SceneEditorSettings>"""

_AUTUMN_ENV_XML = """<SceneEditorSettings
  Type = "1">
  <DefaultSceneConfig>
    <Env
      Time = "0"
      PTLightIntensity = "0"
      PTLightRange = "0"
      PTLightColor = "0,0,0,0"
      DIRLightForward = "-0.85,-0.22,-0.45"
      DIRLightColor = "255,250,135,28"
      DIRLightIntensity = "2.6"
      LightmapWeight0 = "1"
      LightmapWeight1 = "1"
      LightmapWeight2 = "0"
      BgColor = "255,200,85,25"
      WeatherIntensity0 = "0"
      WeatherIntensity1 = "0"
      WeatherIntensity2 = "0"
      EnvExposure = "2.9"
      AOFactor = "0.33"
      Ambient = "0.72,0.48,0.22,1"
      EnvExposureMetallic = "1"
      AmbientMetallic = "0.85,0.65,0.40,1"
      EnvUE4SHR = "-0.010,0.035,0.110,0.090"
      EnvUE4SHG = "-0.018,0.018,0.065,0.050"
      EnvUE4SHB = "-0.028,0.010,0.035,0.030">
      <Fog
        Culling = "false"
        Mode = "5"
        Color = "0,205,95,25"
        DistantColor = "0,165,75,20"
        Start = "250"
        End = "1100"
        Distant = "6000"
        ShaderDensity = "1"
        Custom0 = "0"
        Custom1 = "-200"
        U4FogColor = "255,205,95,25"
        U4FogHeight = "4500"
        U4FogDensity = "0.012"
        U4FogHeightFalloff = "1.2"
        U4StartDistance = "400"
        U4MaxOpacity = "0.88"
        U4FogDirInscatteringColor = "255,255,120,20"
        U4DirInscatteringE = "10"
        U4DirInscatteringStart = "1200"
        U4SkyRate = "0.02" />
      <LensFlare
        SchemeIdx = "4"
        Tex = "common\\textures\\flare_03.png"
        FadeBegin = "1"
        FadeLength = "1">
        <LensInfo Distance = "0" Intensity = "1.8" Size = "2.0" FlareColor = "1.0,0.65,0.18,1" FlareIdx = "1" Rotate = "false" Fade = "true" />
        <LensInfo Distance = "0.02" Intensity = "0.3" Size = "0.4" FlareColor = "1.0,0.75,0.25,1" FlareIdx = "2" Rotate = "false" Fade = "true" />
        <LensInfo Distance = "0.2" Intensity = "0.6" Size = "0.4" FlareColor = "1.0,0.55,0.18,1" FlareIdx = "2" Rotate = "true" Fade = "true" />
        <LensInfo Distance = "0.5" Intensity = "0.2" Size = "1.0" FlareColor = "1.0,0.45,0.12,1" FlareIdx = "2" Rotate = "true" Fade = "true" />
        <LensInfo Distance = "1.9" Intensity = "2.0" Size = "1.3" FlareColor = "0.75,0.35,0.1,1" FlareIdx = "3" Rotate = "true" Fade = "true" />
        <LensInfo Distance = "1.09" Intensity = "0.12" Size = "0.5" FlareColor = "0.95,0.55,0.18,1" FlareIdx = "4" Rotate = "false" Fade = "true" />
        <LensInfo Distance = "0.98" Intensity = "0.2" Size = "0.35" FlareColor = "1.0,0.38,0.1,1" FlareIdx = "4" Rotate = "false" Fade = "true" />
        <LensInfo Distance = "0.05" Intensity = "0.4" Size = "0.6" FlareColor = "1.0,0.75,0.25,1" FlareIdx = "5" Rotate = "true" Fade = "true" />
      </LensFlare>
      <SkyParamFloat>
        <HorizonFalloff Value = "18" />
        <background_intensity Value = "1.15" />
        <cloud_speed Value = "0.8" />
        <low_cloud_pow Value = "1.0" />
      </SkyParamFloat>
      <SkyParamColor>
        <HorizonColor Value = "1.0,0.42,0.06,1.0" />
        <ZenithColor Value = "0.10,0.08,0.24,1.0" />
        <overrall_color Value = "1.0,0.52,0.14,0.55" />
      </SkyParamColor>
      <WaterParamColor>
        <WaterColorCoast Value = "0.68,0.38,0.18,1" />
        <WaterColorDeep Value = "0.20,0.08,0.04,0" />
        <WaterColorShallow Value = "0.42,0.22,0.08,0.65" />
        <low_water_base_color Value = "0.55,0.28,0.12,0.75" />
        <shallowColor Value = "0.70,0.38,0.18,0.45" />
        <specColor Value = "1.0,0.70,0.30,0.85" />
      </WaterParamColor>
    </Env>
  </DefaultSceneConfig>
</SceneEditorSettings>"""

_DAY_ENV_XML = """<SceneEditorSettings
  Type = "1">
  <DefaultSceneConfig>
    <Env
      Time = "0"
      PTLightIntensity = "0"
      PTLightRange = "0"
      PTLightColor = "0,0,0,0"
      DIRLightForward = "-0.1269,-0.738,-0.6628"
      DIRLightColor = "255,227,217,199"
      DIRLightIntensity = "2.7"
      LightmapWeight0 = "1"
      LightmapWeight1 = "1"
      LightmapWeight2 = "0"
      BgColor = "255,98,116,144"
      WeatherIntensity0 = "0"
      WeatherIntensity1 = "0"
      WeatherIntensity2 = "0"
      EnvExposure = "2.8"
      AOFactor = "0.33"
      Ambient = "0.549,0.5686,0.6667,1"
      EnvExposureMetallic = "1"
      AmbientMetallic = "0.7451,0.7412,0.6235,1"
      EnvUE4SHR = "-0.0218,0.0213,0.0718,0.0618"
      EnvUE4SHG = "-0.0288,0.0233,0.0809,0.0653"
      EnvUE4SHB = "-0.0333,0.0269,0.093,0.067">
      <Fog
        Culling = "false"
        Mode = "5"
        Color = "0,159,199,247"
        DistantColor = "0,136,136,136"
        Start = "300"
        End = "1000"
        Distant = "6000"
        ShaderDensity = "1"
        Custom0 = "0"
        Custom1 = "-200"
        U4FogColor = "255,70,105,181"
        U4FogHeight = "4500"
        U4FogDensity = "0.01"
        U4FogHeightFalloff = "1.2"
        U4StartDistance = "600"
        U4MaxOpacity = "1"
        U4FogDirInscatteringColor = "255,105,131,225"
        U4DirInscatteringE = "10"
        U4DirInscatteringStart = "1200"
        U4SkyRate = "0.02" />
      <LensFlare
        SchemeIdx = "4"
        Tex = "common\\textures\\flare_03.png"
        FadeBegin = "1"
        FadeLength = "1">
        <LensInfo Distance = "0" Intensity = "1.5" Size = "1.7" FlareColor = "0.9276,0.5608,0.4275,1" FlareIdx = "1" Rotate = "false" Fade = "true" />
        <LensInfo Distance = "0.02" Intensity = "0.3" Size = "0.4" FlareColor = "0.9824,1,1,1" FlareIdx = "2" Rotate = "false" Fade = "true" />
        <LensInfo Distance = "0.2" Intensity = "0.6" Size = "0.4" FlareColor = "0.998,1,1,1" FlareIdx = "2" Rotate = "true" Fade = "true" />
        <LensInfo Distance = "0.5" Intensity = "0.2" Size = "1" FlareColor = "0.998,1,1,1" FlareIdx = "2" Rotate = "true" Fade = "true" />
        <LensInfo Distance = "1.9" Intensity = "2" Size = "1.2" FlareColor = "0.1252,0.1922,0.2902,1" FlareIdx = "3" Rotate = "true" Fade = "true" />
        <LensInfo Distance = "1.09" Intensity = "0.1" Size = "0.5" FlareColor = "0.1644,0.6471,0.2235,1" FlareIdx = "4" Rotate = "false" Fade = "true" />
        <LensInfo Distance = "0.98" Intensity = "0.2" Size = "0.35" FlareColor = "0.9785,0.2824,0.2824,1" FlareIdx = "4" Rotate = "false" Fade = "true" />
        <LensInfo Distance = "0.05" Intensity = "0.4" Size = "0.6" FlareColor = "0.998,1,1,1" FlareIdx = "5" Rotate = "true" Fade = "true" />
      </LensFlare>
      <SkyParamFloat>
        <HorizonFalloff Value = "20" />
        <background_intensity Value = "1" />
        <cloud_speed Value = "2" />
        <low_cloud_pow Value = "0.86" />
      </SkyParamFloat>
      <SkyParamColor>
        <HorizonColor Value = "0.5294,0.6824,0.9804,1" />
        <ZenithColor Value = "0.1412,0.2314,0.6902,1" />
        <overrall_color Value = "0.8157,0.8745,0.9098,0.1137" />
      </SkyParamColor>
      <WaterParamColor>
        <WaterColorCoast Value = "1,1,1,1" />
        <WaterColorDeep Value = "0.3569,0.3686,0.3804,0" />
        <WaterColorShallow Value = "0.1608,0.1922,0.2314,0.6902" />
        <low_water_base_color Value = "0.5294,0.6667,0.7686,0.7569" />
        <shallowColor Value = "0.9765,0.8235,0.6431,0.4902" />
        <specColor Value = "0.3137,0.4902,0.6275,0.2078" />
      </WaterParamColor>
    </Env>
  </DefaultSceneConfig>
</SceneEditorSettings>"""

_RAIN_ENV_XML = """<SceneEditorSettings
  Type = "1">
  <DefaultSceneConfig>
    <Env
      Time = "0"
      PTLightIntensity = "0"
      PTLightRange = "0"
      PTLightColor = "0,0,0,0"
      DIRLightForward = "-0.15,-0.85,-0.50"
      DIRLightColor = "200,140,150,165"
      DIRLightIntensity = "0.75"
      LightmapWeight0 = "1"
      LightmapWeight1 = "1"
      LightmapWeight2 = "0"
      BgColor = "255,65,72,80"
      WeatherIntensity0 = "1.0"
      WeatherIntensity1 = "1.0"
      WeatherIntensity2 = "0.0"
      EnvExposure = "1.6"
      AOFactor = "0.45"
      Ambient = "0.32,0.35,0.39,1"
      EnvExposureMetallic = "1.6"
      AmbientMetallic = "0.45,0.48,0.52,1"
      EnvUE4SHR = "-0.015,0.015,0.045,0.040"
      EnvUE4SHG = "-0.018,0.016,0.050,0.042"
      EnvUE4SHB = "-0.022,0.018,0.060,0.048">
      <Fog
        Culling = "false"
        Mode = "5"
        Color = "0,70,78,88"
        DistantColor = "0,55,62,70"
        Start = "150"
        End = "800"
        Distant = "4500"
        ShaderDensity = "1.5"
        Custom0 = "0"
        Custom1 = "-200"
        U4FogColor = "255,65,74,85"
        U4FogHeight = "3500"
        U4FogDensity = "0.035"
        U4FogHeightFalloff = "1.5"
        U4StartDistance = "200"
        U4MaxOpacity = "1.0"
        U4FogDirInscatteringColor = "255,80,90,105"
        U4DirInscatteringE = "8"
        U4DirInscatteringStart = "600"
        U4SkyRate = "0.05" />
      <SkyParamFloat>
        <HorizonFalloff Value = "12" />
        <background_intensity Value = "0.45" />
        <cloud_speed Value = "5.5" />
        <low_cloud_pow Value = "1.25" />
      </SkyParamFloat>
      <SkyParamColor>
        <HorizonColor Value = "0.38,0.42,0.46,1.0" />
        <ZenithColor Value = "0.18,0.22,0.26,1.0" />
        <overrall_color Value = "0.35,0.38,0.42,0.85" />
      </SkyParamColor>
      <WaterParamColor>
        <WaterColorCoast Value = "0.4,0.45,0.5,1" />
        <WaterColorDeep Value = "0.15,0.18,0.22,0" />
        <WaterColorShallow Value = "0.22,0.26,0.30,0.85" />
        <low_water_base_color Value = "0.35,0.40,0.45,0.8" />
        <shallowColor Value = "0.5,0.55,0.6,0.6" />
        <specColor Value = "0.9,0.95,1.0,0.7" />
      </WaterParamColor>
    </Env>
  </DefaultSceneConfig>
</SceneEditorSettings>"""

_RAINY_NIGHT_ENV_XML = """<SceneEditorSettings
  Type = "1">
  <DefaultSceneConfig>
    <Env
      Time = "0"
      PTLightIntensity = "0"
      PTLightRange = "0"
      PTLightColor = "0,0,0,0"
      DIRLightForward = "-0.22,-0.88,-0.40"
      DIRLightColor = "200,90,125,185"
      DIRLightIntensity = "0.38"
      LightmapWeight0 = "1"
      LightmapWeight1 = "1"
      LightmapWeight2 = "0"
      BgColor = "255,4,8,16"
      WeatherIntensity0 = "1.0"
      WeatherIntensity1 = "1.0"
      WeatherIntensity2 = "0.0"
      EnvExposure = "1.10"
      AOFactor = "0.35"
      Ambient = "0.16,0.20,0.28,1"
      EnvExposureMetallic = "1.20"
      AmbientMetallic = "0.26,0.32,0.44,1"
      EnvUE4SHR = "-0.006,0.008,0.022,0.020"
      EnvUE4SHG = "-0.009,0.010,0.026,0.022"
      EnvUE4SHB = "-0.012,0.012,0.034,0.028">
      <Fog
        Culling = "false"
        Mode = "5"
        Color = "0,20,32,54"
        DistantColor = "0,14,24,40"
        Start = "45"
        End = "450"
        Distant = "2800"
        ShaderDensity = "2.8"
        Custom0 = "0"
        Custom1 = "-200"
        U4FogColor = "255,18,30,50"
        U4FogHeight = "5200"
        U4FogDensity = "0.068"
        U4FogHeightFalloff = "0.90"
        U4StartDistance = "50"
        U4MaxOpacity = "0.97"
        U4FogDirInscatteringColor = "255,28,42,75"
        U4DirInscatteringE = "8"
        U4DirInscatteringStart = "300"
        U4SkyRate = "0.05" />
      <LensFlare
        SchemeIdx = "4"
        Tex = "common\\textures\\flare_03.png"
        FadeBegin = "1"
        FadeLength = "1">
        <LensInfo Distance = "0" Intensity = "0" Size = "0" FlareColor = "0,0,0,0" FlareIdx = "1" Rotate = "false" Fade = "false" />
        <LensInfo Distance = "0.02" Intensity = "0" Size = "0" FlareColor = "0,0,0,0" FlareIdx = "2" Rotate = "false" Fade = "false" />
        <LensInfo Distance = "0.2" Intensity = "0" Size = "0" FlareColor = "0,0,0,0" FlareIdx = "2" Rotate = "false" Fade = "false" />
        <LensInfo Distance = "0.5" Intensity = "0" Size = "0" FlareColor = "0,0,0,0" FlareIdx = "2" Rotate = "false" Fade = "false" />
        <LensInfo Distance = "1.9" Intensity = "0" Size = "0" FlareColor = "0,0,0,0" FlareIdx = "3" Rotate = "false" Fade = "false" />
        <LensInfo Distance = "1.09" Intensity = "0" Size = "0" FlareColor = "0,0,0,0" FlareIdx = "4" Rotate = "false" Fade = "false" />
        <LensInfo Distance = "0.98" Intensity = "0" Size = "0" FlareColor = "0,0,0,0" FlareIdx = "4" Rotate = "false" Fade = "false" />
        <LensInfo Distance = "0.05" Intensity = "0" Size = "0" FlareColor = "0,0,0,0" FlareIdx = "5" Rotate = "false" Fade = "false" />
        <LensInfo Distance = "0" Intensity = "0" Size = "0" FlareColor = "0,0,0,0" FlareIdx = "6" Rotate = "false" Fade = "false" />
        <LensInfo Distance = "2" Intensity = "0" Size = "0" FlareColor = "0,0,0,0" FlareIdx = "6" Rotate = "false" Fade = "false" />
      </LensFlare>
      <SkyParamFloat>
        <HorizonFalloff Value = "22" />
        <background_intensity Value = "0.25" />
        <cloud_speed Value = "5.0" />
        <low_cloud_pow Value = "1.3" />
      </SkyParamFloat>
      <SkyParamColor>
        <HorizonColor Value = "0.015,0.025,0.055,1.0" />
        <ZenithColor Value = "0.005,0.008,0.020,1.0" />
        <overrall_color Value = "0.06,0.10,0.20,0.3" />
      </SkyParamColor>
      <WaterParamColor>
        <WaterColorCoast Value = "0.12,0.18,0.30,1" />
        <WaterColorDeep Value = "0.03,0.05,0.10,0" />
        <WaterColorShallow Value = "0.05,0.08,0.15,0.7" />
        <low_water_base_color Value = "0.08,0.12,0.22,0.8" />
        <shallowColor Value = "0.10,0.16,0.28,0.5" />
        <specColor Value = "0.75,0.85,1.0,0.6" />
      </WaterParamColor>
    </Env>
  </DefaultSceneConfig>
</SceneEditorSettings>"""

_SNOW_ENV_XML = """<SceneEditorSettings
  Type = "1">
  <DefaultSceneConfig>
    <Env
      Time = "0"
      PTLightIntensity = "0"
      PTLightRange = "0"
      PTLightColor = "0,0,0,0"
      DIRLightForward = "-0.28,-0.92,-0.28"
      DIRLightColor = "255,235,242,255"
      DIRLightIntensity = "0.95"
      LightmapWeight0 = "1"
      LightmapWeight1 = "1"
      LightmapWeight2 = "0"
      BgColor = "255,190,210,230"
      WeatherIntensity0 = "0.0"
      WeatherIntensity1 = "1.0"
      WeatherIntensity2 = "0.95"
      EnvExposure = "1.25"
      AOFactor = "0.20"
      Ambient = "0.82,0.88,0.96,1"
      EnvExposureMetallic = "1.30"
      AmbientMetallic = "0.88,0.94,1.0,1"
      EnvUE4SHR = "-0.015,0.020,0.035,0.030"
      EnvUE4SHG = "-0.018,0.024,0.040,0.035"
      EnvUE4SHB = "-0.022,0.030,0.050,0.045">
      <Fog
        Culling = "false"
        Mode = "5"
        Color = "0,210,225,240"
        DistantColor = "0,185,205,225"
        Start = "250"
        End = "1400"
        Distant = "6000"
        ShaderDensity = "1.2"
        Custom0 = "0"
        Custom1 = "-200"
        U4FogColor = "255,215,230,245"
        U4FogHeight = "4000"
        U4FogDensity = "0.018"
        U4FogHeightFalloff = "1.0"
        U4StartDistance = "300"
        U4MaxOpacity = "0.80"
        U4FogDirInscatteringColor = "255,240,248,255"
        U4DirInscatteringE = "12"
        U4DirInscatteringStart = "1200"
        U4SkyRate = "0.05" />
      <LensFlare
        SchemeIdx = "4"
        Tex = "common\\textures\\flare_03.png"
        FadeBegin = "1"
        FadeLength = "1">
        <LensInfo Distance = "0" Intensity = "0" Size = "0" FlareColor = "0,0,0,0" FlareIdx = "1" Rotate = "false" Fade = "false" />
      </LensFlare>
      <SkyParamFloat>
        <HorizonFalloff Value = "18" />
        <background_intensity Value = "0.85" />
        <cloud_speed Value = "3.0" />
        <low_cloud_pow Value = "1.1" />
      </SkyParamFloat>
      <SkyParamColor>
        <HorizonColor Value = "0.78,0.85,0.92,1.0" />
        <ZenithColor Value = "0.65,0.75,0.88,1.0" />
        <overrall_color Value = "0.85,0.90,0.98,0.8" />
      </SkyParamColor>
      <WaterParamColor>
        <WaterColorCoast Value = "0.55,0.65,0.75,1" />
        <WaterColorDeep Value = "0.20,0.30,0.45,0" />
        <WaterColorShallow Value = "0.45,0.55,0.68,0.7" />
        <low_water_base_color Value = "0.40,0.50,0.65,0.8" />
        <shallowColor Value = "0.50,0.60,0.72,0.5" />
        <specColor Value = "0.90,0.95,1.0,0.9" />
      </WaterParamColor>
    </Env>
  </DefaultSceneConfig>
</SceneEditorSettings>"""

_SNOWY_NIGHT_ENV_XML = """<SceneEditorSettings
  Type = "1">
  <DefaultSceneConfig>
    <Env
      Time = "0"
      PTLightIntensity = "0"
      PTLightRange = "0"
      PTLightColor = "0,0,0,0"
      DIRLightForward = "-0.22,-0.88,-0.40"
      DIRLightColor = "220,120,165,225"
      DIRLightIntensity = "0.45"
      LightmapWeight0 = "1"
      LightmapWeight1 = "1"
      LightmapWeight2 = "0"
      BgColor = "255,10,18,30"
      WeatherIntensity0 = "0.0"
      WeatherIntensity1 = "1.0"
      WeatherIntensity2 = "0.95"
      EnvExposure = "1.15"
      AOFactor = "0.25"
      Ambient = "0.22,0.30,0.44,1"
      EnvExposureMetallic = "1.25"
      AmbientMetallic = "0.32,0.42,0.58,1"
      EnvUE4SHR = "-0.008,0.010,0.026,0.024"
      EnvUE4SHG = "-0.011,0.014,0.032,0.028"
      EnvUE4SHB = "-0.015,0.018,0.042,0.036">
      <Fog
        Culling = "false"
        Mode = "5"
        Color = "0,14,24,42"
        DistantColor = "0,8,16,30"
        Start = "200"
        End = "1000"
        Distant = "5000"
        ShaderDensity = "1.3"
        Custom0 = "0"
        Custom1 = "-200"
        U4FogColor = "255,16,28,48"
        U4FogHeight = "4000"
        U4FogDensity = "0.020"
        U4FogHeightFalloff = "1.2"
        U4StartDistance = "250"
        U4MaxOpacity = "0.85"
        U4FogDirInscatteringColor = "255,20,35,60"
        U4DirInscatteringE = "10"
        U4DirInscatteringStart = "900"
        U4SkyRate = "0.04" />
      <LensFlare
        SchemeIdx = "4"
        Tex = "common\\textures\\flare_03.png"
        FadeBegin = "1"
        FadeLength = "1">
        <LensInfo Distance = "0" Intensity = "0" Size = "0" FlareColor = "0,0,0,0" FlareIdx = "1" Rotate = "false" Fade = "false" />
      </LensFlare>
      <SkyParamFloat>
        <HorizonFalloff Value = "22" />
        <background_intensity Value = "0.30" />
        <cloud_speed Value = "4.0" />
        <low_cloud_pow Value = "1.3" />
      </SkyParamFloat>
      <SkyParamColor>
        <HorizonColor Value = "0.020,0.035,0.070,1.0" />
        <ZenithColor Value = "0.008,0.012,0.028,1.0" />
        <overrall_color Value = "0.08,0.14,0.26,0.4" />
      </SkyParamColor>
      <WaterParamColor>
        <WaterColorCoast Value = "0.15,0.22,0.36,1" />
        <WaterColorDeep Value = "0.04,0.07,0.14,0" />
        <WaterColorShallow Value = "0.08,0.12,0.22,0.7" />
        <low_water_base_color Value = "0.10,0.16,0.28,0.8" />
        <shallowColor Value = "0.14,0.22,0.36,0.5" />
        <specColor Value = "0.80,0.90,1.0,0.7" />
      </WaterParamColor>
    </Env>
  </DefaultSceneConfig>
</SceneEditorSettings>"""

def _ensure_rain_skybox(game_dir):
    try:
        rain_dds = os.path.join(game_dir, 'res', 'levelsets', '4k_diedai', 'skybox_diedai01_rain.dds')
        day_dds = os.path.join(game_dir, 'res', 'levelsets', '4k_diedai', 'skybox_diedai01_day.dds')
        if os.path.isfile(rain_dds) and os.path.getsize(rain_dds) > 1000:
            return rain_dds
        if not os.path.isfile(day_dds):
            return None
        with open(day_dds, 'rb') as f:
            hdr = f.read(128)
            raw = bytearray(f.read())
        for i in range(0, len(raw), 4):
            b = raw[i]; g = raw[i+1]; r = raw[i+2]
            y = (r * 77 + g * 150 + b * 29) >> 8
            raw[i]   = min(255, (y * 215) >> 8)
            raw[i+1] = min(255, (y * 200) >> 8)
            raw[i+2] = min(255, (y * 190) >> 8)
        os.makedirs(os.path.dirname(rain_dds), exist_ok=True)
        with open(rain_dds, 'wb') as f:
            f.write(hdr)
            f.write(raw)
        return rain_dds
    except Exception:
        return None

def _get_env_xml(mode):
    m = (mode or "").lower()
    if m == "night":
        return _NIGHT_ENV_XML
    elif m in ("rainy_night", "rainynight", "rain_night", "darkrain", "stormynight"):
        return _RAINY_NIGHT_ENV_XML
    elif m in ("snowy_night", "snowynight", "snow_night", "winternight"):
        return _SNOWY_NIGHT_ENV_XML
    elif m in ("snow", "snowy", "winter"):
        return _SNOW_ENV_XML
    elif m == "dawn":
        return _DAWN_ENV_XML
    elif m == "sunset":
        return _SUNSET_ENV_XML
    elif m in ("autumn", "fall", "harvest"):
        return _AUTUMN_ENV_XML
    elif m == "rain":
        return _RAIN_ENV_XML
    else:
        return _DAY_ENV_XML

def _normalize_env_mode(target_mode):
    if isinstance(target_mode, bool):
        return "night" if target_mode else "day"
    if not isinstance(target_mode, str) or target_mode.lower() not in (
            "auto", "day", "dawn", "sunset", "autumn", "night", "rain",
            "rainy_night", "snow", "snowy_night"):
        return "day" if not bool(target_mode) else "night"
    if target_mode.lower() == "auto":
        return "day"
    return target_mode.lower()


_ENV_NPK_STATE = os.path.join(RUNTIME_DIR, "env_npk_state.json")
_ENV_NPK_LOCK = threading.Lock()


def _atomic_copy(src, dst):
    tmp = dst + ".tmp_navy"
    import shutil
    shutil.copyfile(src, tmp)
    os.replace(tmp, dst)


def _restore_day_packs():
    """Put every pack/file the weather feature touched back to its original.

    'day' used to REBUILD Documents/res/common.npk from scratch (every entry
    decompressed, new offsets) and rewrite world4k.npk's index on every Play,
    while the pack's .info_ext still described the original layout. NeoX
    mounts Documents/ ahead of game/, so a bad rebuild there is read first.
    Restoring the pristine byte-for-byte backup removes that risk entirely.
    """
    docs_res = os.path.join(GAME_DIR, "Documents", "res")
    for rel in ("common.npk", os.path.join("levelsets", "4k_diedai.npk")):
        cur = os.path.join(docs_res, rel)
        bak = cur + ".orig_day"
        if os.path.isfile(bak):
            try:
                if (not os.path.isfile(cur)
                        or os.path.getsize(cur) != os.path.getsize(bak)
                        or _file_digest(cur) != _file_digest(bak)):
                    _atomic_copy(bak, cur)
                    print("restored original %s" % rel)
            except Exception as e:
                print("restore %s failed: %s" % (rel, e))
    # Loose overrides this launcher generated (never shipped with the game).
    loose = [os.path.join(docs_res, "levelsets", "4k_diedai", "skybox_diedai01.dds")]
    generated_xml = set()
    for m in ("day", "night", "rain", "rainy_night", "snow", "snowy_night", "dawn", "sunset", "autumn"):
        try:
            generated_xml.add(_get_env_xml(m).strip().encode("utf-8"))
        except Exception:
            pass
    for base in (os.path.join(GAME_DIR, "Documents", "res", "scene"), os.path.join(GAME_DIR, "res", "scene")):
        for sub in (os.path.join("world4k", "world4k_content"), "world4k_content"):
            for name in ("high.xml", "tiaosan.xml", "low.xml"):
                xp = os.path.join(base, sub, "env_info", name)
                try:
                    if os.path.isfile(xp):
                        with open(xp, "rb") as fh:
                            if fh.read().strip() in generated_xml:
                                loose.append(xp)
                except Exception:
                    pass
    for lp in loose:
        try:
            if os.path.isfile(lp):
                os.remove(lp)
        except Exception as e:
            print("remove %s failed: %s" % (lp, e))


def _file_digest(path):
    import hashlib
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _apply_day_night_npk_files(target_mode, wait=False):
    """Apply the launcher weather preset to the game packs - safely.

    * never while client.exe is running (it has these packs open; rewriting
      one under it is a native crash in the XML/texture loader)
    * only when the mode actually changes (it used to rewrite a 450 MB
      world4k.npk and rebuild common.npk on every Play and every settings save)
    * 'day'/'auto' restores the original files instead of rebuilding them
    """
    mode = _normalize_env_mode(target_mode)
    if not _ENV_NPK_LOCK.acquire(bool(wait)):
        return
    try:
        if is_process_running("client.exe", max_age=0):
            print("weather packs: client.exe is running - change applies next launch")
            return
        prev = None
        try:
            with open(_ENV_NPK_STATE, "r", encoding="utf-8") as fh:
                prev = (json.load(fh) or {}).get("mode")
        except Exception:
            prev = None
        if prev == mode:
            return
        if mode == "day":
            _restore_day_packs()
            if prev not in (None, "day") or os.path.isfile(
                    os.path.join(GAME_DIR, "Documents", "res", "scene", "world4k.npk.orig_day_xmls")):
                _apply_day_night_npk_files_impl("day", world4k_only=True)
        else:
            _apply_day_night_npk_files_impl(mode)
        try:
            os.makedirs(RUNTIME_DIR, exist_ok=True)
            with open(_ENV_NPK_STATE, "w", encoding="utf-8") as fh:
                json.dump({"mode": mode, "updated": time.time()}, fh)
        except Exception:
            pass
    finally:
        _ENV_NPK_LOCK.release()


def _apply_day_night_npk_files_impl(target_mode, world4k_only=False):
    import struct, zlib, shutil
    HEADER = struct.Struct('<4s5I')
    RECORD = struct.Struct('<6I2H')

    if isinstance(target_mode, bool):
        mode = "night" if target_mode else "day"
    elif not isinstance(target_mode, str) or target_mode.lower() not in ("auto", "day", "dawn", "sunset", "autumn", "night", "rain", "rainy_night", "snow", "snowy_night"):
        mode = "day" if not bool(target_mode) else "night"
    elif target_mode.lower() == "auto":
        mode = "day"
    else:
        mode = target_mode.lower()

    is_night = (mode in ("night", "rainy_night", "snowy_night"))
    is_rain = (mode in ("rain", "rainy_night"))
    is_snow = (mode in ("snow", "snowy_night"))

    def _build_npk(out_path, entries_dict):
        names = list(entries_dict.keys())
        data_blobs = [entries_dict[n] for n in names]
        file_count = len(names)
        off = HEADER.size
        records = []
        file_data = b''.join(data_blobs)
        for b in data_blobs:
            clen = len(b); olen = clen
            crc = zlib.crc32(b) & 0xffffffff
            records.append(RECORD.pack(0, off, clen, olen, crc, crc, 0, 0))
            off += clen
        hdr = HEADER.pack(b'NXPK', file_count, 0, 0, 2, off)
        index_bytes = b''.join(records)
        names_bytes = b''.join([n.encode('utf-8') + b'\x00' for n in names])
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        tmp_path = out_path + '.tmp_navy'
        with open(tmp_path, 'wb') as f:
            f.write(hdr); f.write(file_data); f.write(index_bytes); f.write(names_bytes)
        os.replace(tmp_path, out_path)  # never leave a half-written pack behind

    def _resolve_target_pack(rel_subpath):
        doc_p = os.path.join(GAME_DIR, 'Documents', 'res', rel_subpath)
        base_p = os.path.join(GAME_DIR, 'res', rel_subpath)
        if os.path.isfile(doc_p):
            return doc_p
        if os.path.isfile(base_p):
            try:
                os.makedirs(os.path.dirname(doc_p), exist_ok=True)
                shutil.copyfile(base_p, doc_p)
                return doc_p
            except Exception:
                return base_p
        return None

    # 1. 4k_diedai.npk (injects the starry skybox in night, overcast gray in rain, day for others)
    pk_4k_path = None if world4k_only else _resolve_target_pack(os.path.join('levelsets', '4k_diedai.npk'))
    if pk_4k_path:
        pk_4k_bak = pk_4k_path + '.orig_day'
        if os.path.isfile(pk_4k_path) and not os.path.isfile(pk_4k_bak):
            try: shutil.copyfile(pk_4k_path, pk_4k_bak)
            except Exception: pass

        if is_night:
            sky_src = os.path.join(GAME_DIR, 'res', 'levelsets', '4k_diedai', 'skybox_diedai01_night.dds')
        elif is_rain:
            _ensure_rain_skybox(GAME_DIR)
            sky_src = os.path.join(GAME_DIR, 'res', 'levelsets', '4k_diedai', 'skybox_diedai01_rain.dds')
            if not os.path.isfile(sky_src):
                sky_src = os.path.join(GAME_DIR, 'res', 'levelsets', '4k_diedai', 'skybox_diedai01_day.dds')
        else:
            sky_src = os.path.join(GAME_DIR, 'res', 'levelsets', '4k_diedai', 'skybox_diedai01_day.dds')
        if os.path.isfile(sky_src):
            try:
                with open(sky_src, 'rb') as f: sky_bytes = f.read()
                sig_bytes = b'levelsets_4k_diedai_signature\x00'
                if os.path.isfile(pk_4k_bak):
                    try:
                        import tools.npk as _npk
                        pk = _npk.Pack(pk_4k_bak)
                        hits = pk.find('levelsets_4k_diedai_signature')
                        if hits: sig_bytes = hits[0].raw()
                    except Exception: pass
                _build_npk(pk_4k_path, {
                    'levelsets_4k_diedai_signature': sig_bytes,
                    'skybox_diedai01.dds': sky_bytes
                })
                dst_loose = os.path.join(GAME_DIR, 'Documents', 'res', 'levelsets', '4k_diedai', 'skybox_diedai01.dds')
                os.makedirs(os.path.dirname(dst_loose), exist_ok=True)
                shutil.copyfile(sky_src, dst_loose)
            except Exception as e:
                print('Failed updating 4k_diedai.npk:', e)

    # 2. common.npk (sun & flare transparent in night mode, restored in day/dawn/sunset mode)
    pk_com_path = None if world4k_only else _resolve_target_pack('common.npk')
    if pk_com_path:
        pk_com_bak = pk_com_path + '.orig_day'
        if os.path.isfile(pk_com_path) and not os.path.isfile(pk_com_bak):
            try: shutil.copyfile(pk_com_path, pk_com_bak)
            except Exception: pass

        if os.path.isfile(pk_com_bak):
            try:
                import tools.npk as _npk
                pk_bak = _npk.Pack(pk_com_bak)
                entries = {e.path: e.raw() for e in pk_bak}
                if is_night:
                    pk_base = _npk.Pack(os.path.join(GAME_DIR, 'res', 'common.npk'))
                    sun_hit = pk_base.find('textures/clearsun.dds')
                    flare3_hit = pk_base.find('textures/flare_03.dds')
                    flare1_hit = pk_base.find('textures/flare01.dds')
                    if sun_hit:
                        raw = sun_hit[0].raw()
                        entries['textures/clearsun.dds'] = raw[:128] + b'\x00\x00\x00\x00\xff\xff\xff\xff' * ((len(raw)-128)//8)
                    if flare3_hit:
                        raw = flare3_hit[0].raw()
                        entries['textures/flare_03.dds'] = raw[:128] + b'\x00' * (len(raw)-128)
                    if flare1_hit:
                        raw = flare1_hit[0].raw()
                        entries['textures/flare01.dds'] = raw[:128] + b'\x00' * (len(raw)-128)
                _build_npk(pk_com_path, entries)
            except Exception as e:
                print('Failed updating common.npk:', e)

    # 3. Environment XML files (high.xml, tiaosan.xml, low.xml)
    try:
        if world4k_only:
            raise StopIteration  # day restore removes these instead
        xml_content = _get_env_xml(mode).strip().encode('utf-8')
        xml_targets = [
            os.path.join(GAME_DIR, 'Documents', 'res', 'scene', 'world4k', 'world4k_content', 'env_info', 'high.xml'),
            os.path.join(GAME_DIR, 'Documents', 'res', 'scene', 'world4k', 'world4k_content', 'env_info', 'tiaosan.xml'),
            os.path.join(GAME_DIR, 'Documents', 'res', 'scene', 'world4k', 'world4k_content', 'env_info', 'low.xml'),
            os.path.join(GAME_DIR, 'Documents', 'res', 'scene', 'world4k_content', 'env_info', 'high.xml'),
            os.path.join(GAME_DIR, 'Documents', 'res', 'scene', 'world4k_content', 'env_info', 'tiaosan.xml'),
            os.path.join(GAME_DIR, 'Documents', 'res', 'scene', 'world4k_content', 'env_info', 'low.xml'),
            os.path.join(GAME_DIR, 'res', 'scene', 'world4k', 'world4k_content', 'env_info', 'high.xml'),
            os.path.join(GAME_DIR, 'res', 'scene', 'world4k', 'world4k_content', 'env_info', 'tiaosan.xml'),
            os.path.join(GAME_DIR, 'res', 'scene', 'world4k', 'world4k_content', 'env_info', 'low.xml'),
            os.path.join(GAME_DIR, 'res', 'scene', 'world4k_content', 'env_info', 'high.xml'),
            os.path.join(GAME_DIR, 'res', 'scene', 'world4k_content', 'env_info', 'tiaosan.xml'),
            os.path.join(GAME_DIR, 'res', 'scene', 'world4k_content', 'env_info', 'low.xml'),
        ]
        for xp in xml_targets:
            try:
                os.makedirs(os.path.dirname(xp), exist_ok=True)
                with open(xp, 'wb') as f:
                    f.write(xml_content)
            except Exception: pass
    except StopIteration:
        pass
    except Exception as e:
        print('Failed writing env XMLs:', e)

    # 4. world4k.npk (inject environment directly into the pack)
    if world4k_only:
        _w4k_doc = os.path.join(GAME_DIR, 'Documents', 'res', 'scene', 'world4k.npk')
        pk_w4k_path = _w4k_doc if os.path.isfile(_w4k_doc) else None
    else:
        pk_w4k_path = _resolve_target_pack(os.path.join('scene', 'world4k.npk'))
    if pk_w4k_path and os.path.isfile(pk_w4k_path):
        try:
            bak_day_p = pk_w4k_path + '.orig_day_xmls'
            import pickle, tools.npk as _npk
            if not os.path.isfile(bak_day_p):
                pk_w4k = _npk.Pack(pk_w4k_path)
                h_hits = pk_w4k.find('world4k_content/env_info/high.xml')
                t_hits = pk_w4k.find('world4k_content/env_info/tiaosan.xml')
                l_hits = pk_w4k.find('world4k_content/env_info/low.xml')
                tl_hits = pk_w4k.find('world4k_content/env_info/tiaosan_low.xml')
                with open(bak_day_p, 'wb') as bf:
                    pickle.dump({
                        'world4k_content/env_info/high.xml': h_hits[0].raw() if h_hits else b'',
                        'world4k_content/env_info/tiaosan.xml': t_hits[0].raw() if t_hits else b'',
                        'world4k_content/env_info/low.xml': l_hits[0].raw() if l_hits else b'',
                        'world4k_content/env_info/tiaosan_low.xml': tl_hits[0].raw() if tl_hits else b'',
                    }, bf)

            def _update_npk_entries(target_npk, entries_dict):
                with open(target_npk, 'r+b') as fh:
                    magic, count, z1, z2, mode_val, idx = HEADER.unpack(fh.read(HEADER.size))
                    if magic != b'NXPK': return
                    fh.seek(idx)
                    raw_index = bytearray(fh.read(count * RECORD.size))
                    names_bytes = fh.read()
                    names = [n.decode('utf-8', 'replace').replace('\\', '/')
                             for n in names_bytes.split(b'\x00') if n]
                    name_to_idx = {name: i for i, name in enumerate(names)}
                    cur_off = idx
                    fh.seek(cur_off)
                    for n, data in entries_dict.items():
                        if n not in name_to_idx: continue
                        ix = name_to_idx[n]
                        fh.write(data)
                        d_len = len(data)
                        crc = zlib.crc32(data) & 0xffffffff
                        rec = RECORD.pack(0, cur_off, d_len, d_len, crc, crc, 0, 0)
                        raw_index[ix * RECORD.size : (ix + 1) * RECORD.size] = rec
                        cur_off += d_len
                    fh.write(raw_index)
                    fh.write(names_bytes)
                    fh.truncate()
                    fh.seek(20)
                    fh.write(struct.pack('<I', cur_off))

            if mode != "day":
                xml_b = _get_env_xml(mode).strip().encode('utf-8')
                _update_npk_entries(pk_w4k_path, {
                    'world4k_content/env_info/high.xml': xml_b,
                    'world4k_content/env_info/tiaosan.xml': xml_b,
                    'world4k_content/env_info/low.xml': xml_b,
                    'world4k_content/env_info/tiaosan_low.xml': xml_b,
                })
                print('world4k.npk updated to %s environment' % mode.upper())
            else:
                day_dict = {}
                if os.path.isfile(bak_day_p):
                    try:
                        with open(bak_day_p, 'rb') as bf: day_dict = pickle.load(bf)
                    except Exception: pass
                if not day_dict:
                    xml_day_b = _DAY_ENV_XML.strip().encode('utf-8')
                    day_dict = {
                        'world4k_content/env_info/high.xml': xml_day_b,
                        'world4k_content/env_info/tiaosan.xml': xml_day_b,
                        'world4k_content/env_info/low.xml': xml_day_b,
                        'world4k_content/env_info/tiaosan_low.xml': xml_day_b,
                    }
                _update_npk_entries(pk_w4k_path, day_dict)
                print('world4k.npk restored to DAY environment')
        except Exception as e:
            print('Failed updating world4k.npk env:', e)


class LauncherAPI:
    def __init__(self, window=None):
        self._window = window

    def set_window(self, window):
        self._window = window

    def get_config(self):
        cfg = load_config()
        cfg["revival"] = get_revival_config()
        return cfg

    def save_config(self, cfg):
        ok = save_config(cfg)
        env_mode = cfg.get("env_mode")
        if env_mode:
            target_mode = str(env_mode).lower().strip()
            is_auto = (target_mode == "auto")
            is_night = (target_mode in ("night", "rainy_night", "snowy_night"))
            is_rain = (target_mode in ("rain", "rainy_night"))
            is_snow = (target_mode in ("snow", "snowy_night"))
            try:
                os.makedirs(RUNTIME_DIR, exist_ok=True)
                st_file = os.path.join(RUNTIME_DIR, "daynight_state.json")
                with open(st_file, "w", encoding="utf-8") as f:
                    json.dump({
                        "mode": target_mode,
                        "auto_weather": is_auto,
                        "night": is_night,
                        "rain": is_rain,
                        "snow": is_snow,
                        "updated": time.time()
                    }, f, indent=2)
            except Exception:
                pass
            # Rewriting the weather packs can take a long time (world4k.npk is
            # ~450 MB); never block the Settings save on it. Play waits for it.
            threading.Thread(target=lambda m=target_mode: _apply_day_night_npk_files(m),
                             daemon=True).start()
            if self._client_pid() > 0:
                self.master_send_cmd("env " + target_mode)
                if is_rain:
                    self.master_send_cmd("rain on")
                elif not is_auto:
                    self.master_send_cmd("rain off")
                if is_snow:
                    self.master_send_cmd("snow on")
                elif not is_auto:
                    self.master_send_cmd("snow off")
        fov = cfg.get("fov")
        if fov is not None:
            try:
                fov_val = int(fov)
                fov_val = max(35, min(120, fov_val))
                os.makedirs(RUNTIME_DIR, exist_ok=True)
                fov_file = os.path.join(RUNTIME_DIR, "fov_setting.json")
                with open(fov_file, "w", encoding="utf-8") as f:
                    json.dump({"fov": fov_val, "updated": time.time()}, f, indent=2)
                if self._client_pid() > 0:
                    self.master_send_cmd("fov %d" % fov_val)
            except Exception as e:
                print("Failed saving fov:", e)
        gfx_quality = cfg.get("graphic_quality")
        fps_lim = cfg.get("fps_limit")
        if gfx_quality is not None or fps_lim is not None:
            try:
                q_val = int(gfx_quality) if gfx_quality is not None else 2
                f_val = int(fps_lim) if fps_lim is not None else 120
                os.makedirs(RUNTIME_DIR, exist_ok=True)
                gfx_file = os.path.join(RUNTIME_DIR, "graphics_setting.json")
                with open(gfx_file, "w", encoding="utf-8") as f:
                    json.dump({
                        "graphic_quality": q_val,
                        "fps_limit": f_val,
                        "graphics_configured": bool(cfg.get("graphics_configured", True)),
                        "updated": time.time()
                    }, f, indent=2)
                if self._client_pid() > 0:
                    self.master_send_cmd("graphics %d" % q_val)
                    self.master_send_cmd("fps %d" % f_val)
            except Exception as e:
                print("Failed saving graphics setting:", e)
        return ok

    def set_fov(self, fov):
        try:
            fov_val = int(fov)
            fov_val = max(35, min(120, fov_val))
            cfg = load_config()
            cfg["fov"] = fov_val
            save_config(cfg)
            os.makedirs(RUNTIME_DIR, exist_ok=True)
            fov_file = os.path.join(RUNTIME_DIR, "fov_setting.json")
            with open(fov_file, "w", encoding="utf-8") as f:
                json.dump({"fov": fov_val, "updated": time.time()}, f, indent=2)
            if self._client_pid() > 0:
                self.master_send_cmd("fov %d" % fov_val)
            return {"success": True, "fov": fov_val}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def get_graphics_settings(self):
        cfg = load_config()
        quality = cfg.get("graphic_quality", 2)
        fps = cfg.get("fps_limit", 120)
        configured = bool(cfg.get("graphics_configured", False))
        try:
            import accounts
            act = accounts.active()
            if act:
                if "graphic_quality" in act:
                    quality = act["graphic_quality"]
                if "fps_limit" in act:
                    fps = act["fps_limit"]
                if "graphics_configured" in act:
                    configured = bool(act["graphics_configured"])
        except Exception:
            pass
        return {
            "success": True,
            "graphic_quality": int(quality),
            "fps_limit": int(fps),
            "graphics_configured": configured
        }

    def save_graphics_settings(self, quality=2, fps=120, mark_configured=True):
        try:
            q_val = int(quality)
            q_val = max(0, min(3, q_val))
            fps_val = int(fps)
            if fps_val not in (60, 90, 120, 144, 240):
                fps_val = 120

            cfg = load_config()
            cfg["graphic_quality"] = q_val
            cfg["fps_limit"] = fps_val
            if mark_configured:
                cfg["graphics_configured"] = True
            save_config(cfg)

            # Persist to active account if signed in
            try:
                import accounts
                act = accounts.active()
                if act and act.get("username"):
                    accounts.set_account_graphics(act["username"], quality=q_val, fps=fps_val)
            except Exception as e:
                print("Failed updating account graphics:", e)

            # Write client/runtime/graphics_setting.json
            os.makedirs(RUNTIME_DIR, exist_ok=True)
            gfx_file = os.path.join(RUNTIME_DIR, "graphics_setting.json")
            with open(gfx_file, "w", encoding="utf-8") as f:
                json.dump({
                    "graphic_quality": q_val,
                    "fps_limit": fps_val,
                    "graphics_configured": True,
                    "updated": time.time()
                }, f, indent=2)

            # Send live commands if client is running
            if self._client_pid() > 0:
                self.master_send_cmd("graphics %d\nfps %d" % (q_val, fps_val))


            return {
                "success": True,
                "graphic_quality": q_val,
                "fps_limit": fps_val,
                "graphics_configured": True
            }
        except Exception as e:
            return {"success": False, "message": str(e)}

    # ------------------------------------------------------------------ accounts
    #
    # The game had no local identity offline -- the client was seeded with one
    # hardcoded player, so every install was the same person and progress had
    # nowhere of its own to live. accounts.py stores a PBKDF2 hash (never the
    # password) and gives each account its own save directory; the payload's
    # offline_account_db reads client/runtime/active_account.json to pick it up.

    def account_state(self):
        """What the login screen should show on open, including auto-login."""
        try:
            import accounts
        except Exception as e:
            return {"available": False, "message": "Account system unavailable: %s" % e}
        cfg = load_config()
        acc_list = accounts.list_accounts()
        state = {"available": True, "accounts": acc_list,
                 "signed_in": None, "is_dev": False}
        act = accounts.active()
        token = cfg.get("account_token") or ""
        if act and token:
            # Re-resume rather than trusting the file: the token is what proves
            # this launcher is still entitled to the session.
            res = accounts.resume(token)
            if res.get("success"):
                state["signed_in"] = res["account"]
                state["is_dev"] = bool(res["account"].get("is_dev"))
                state["ban"] = self._ban_for(res["account"])
                return state
            # Stale token -- drop it
            cfg["account_token"] = ""
            save_config(cfg)
        elif token:
            res = accounts.resume(token)
            if res.get("success"):
                state["signed_in"] = res["account"]
                state["is_dev"] = bool(res["account"].get("is_dev"))
                state["ban"] = self._ban_for(res["account"])
                return state

        return state

    def _ban_for(self, account, force=False):
        """Server ban status for the signed-in account (cached ~60 s)."""
        try:
            import accounts
            if not account or account.get("is_dev"):
                return {"banned": False}
            return accounts.check_ban(account.get("username"), force=force)
        except Exception:
            return {"banned": False}

    def _signed_user(self):
        try:
            import accounts
            tok = load_config().get("account_token") or ""
            return accounts.peek(tok)
        except Exception:
            pass
        return None

    def get_ban_status(self, force=False):
        acc = self._signed_user()
        if not acc:
            return {"banned": False, "signed_in": False}
        st = self._ban_for(acc, force=bool(force))
        st["signed_in"] = True
        return st

    def add_dev_account(self, username):
        try:
            import accounts
            me = self._signed_user() or {}
            if not me.get("is_dev"):
                return {"success": False, "message": "Developer privileges required."}
            return accounts.add_dev(username, as_user=me.get("username"))
        except Exception as e:
            return {"success": False, "message": str(e)}

    def remove_dev_account(self, username):
        try:
            import accounts
            me = self._signed_user() or {}
            if not me.get("is_dev"):
                return {"success": False, "message": "Developer privileges required."}
            return accounts.remove_dev(username, as_user=me.get("username"))
        except Exception as e:
            return {"success": False, "message": str(e)}

    def get_dev_list(self):
        try:
            import accounts
            return accounts.list_devs()
        except Exception:
            return ["yuzechua"]

    def account_signup(self, username, password, hero_name=None):
        try:
            import accounts
        except Exception as e:
            return {"success": False, "message": str(e)}
        res = accounts.signup(username, password, hero_name)
        if res.get("success"):
            self._remember(res.get("token"))
        return res

    def account_login(self, username, password, remember=True):
        try:
            import accounts
        except Exception as e:
            return {"success": False, "message": str(e)}
        res = accounts.login(username, password, remember=bool(remember))
        if res.get("success"):
            self._remember(res.get("token") if remember else "")
        return res

    def account_logout(self):
        try:
            import accounts
        except Exception as e:
            return {"success": False, "message": str(e)}
        cfg = load_config()
        res = accounts.logout(token=cfg.get("account_token") or "")
        self._remember("")
        return res

    def account_set_hero_name(self, username, hero_name):
        try:
            import accounts
        except Exception as e:
            return {"success": False, "message": str(e)}
        return accounts.set_hero_name(username, hero_name)

    def account_change_password(self, username, old_password, new_password, keep_logged_in=True):
        try:
            import accounts
        except Exception as e:
            return {"success": False, "message": str(e)}
        res = accounts.change_password(username, old_password, new_password, keep_logged_in=bool(keep_logged_in))
        if res.get("success"):
            self._remember(res.get("token") or "")
        return res

    def _remember(self, token):
        cfg = load_config()
        cfg["account_token"] = token or ""
        save_config(cfg)

    # ------------------------------------------------------------------ moderation & anti-cheat
    def get_device_id(self):
        cfg = load_config()
        dev_id = cfg.get("device_id")
        if not dev_id:
            import uuid
            dev_id = f"hwid_{uuid.uuid4().hex[:16]}"
            cfg["device_id"] = dev_id
            save_config(cfg)
        return dev_id

    def authorize_play(self, check_ban=True):
        """Authoritative pre-launch ban check and signed token generation."""
        cfg = load_config()
        st = self.account_state()
        signed = (st or {}).get("signed_in") or {}
        username = signed.get("username") or ""
        account_id = str(signed.get("uid") or signed.get("account_id") or "10001")
        device_id = self.get_device_id()

        # Server-authoritative ban (shared by every PC). Forced fresh at Play.
        if check_ban and signed and not signed.get("is_dev"):
            sb = self._ban_for(signed, force=True)
            if sb.get("banned"):
                bt = sb.get("ban_type") or "Permanent"
                return {
                    "authorized": False, "banned": True,
                    "reason": sb.get("reason") or "Cheating", "ban_type": bt,
                    "expires_at": sb.get("expires_at") or 0,
                    "message": "Your account is banned. You cannot launch Cyber Hunter Reawakening.",
                }

        if check_ban and ban_service and not is_remote_mode():
            is_banned, ban_rec = ban_service.check_ban(
                account_id=account_id,
                username=username,
                device_id=device_id
            )
            if is_banned:
                reason = ban_rec.get("reason", "Cheating") if ban_rec else "Cheating"
                ban_type = ban_rec.get("ban_type", "Permanent") if ban_rec else "Permanent"
                return {
                    "authorized": False,
                    "banned": True,
                    "reason": reason,
                    "ban_type": ban_type,
                    "message": "YOU ARE PERMANENTLY BANNED\n\nReason: Cheating\n\nAccess to Cyber Hunter Reawakening has been permanently restricted."
                }

        role = ban_service.get_role(username) if ban_service else "PLAYER"
        # Every Play gets a fresh token (TTL 1 h): the relay game_token cached
        # at sign-in goes stale and the in-game START check would refuse it.
        token = ""
        if token_service:
            try:
                token = token_service.create_token(
                    account_id=account_id, username=username,
                    hero_name=signed.get("hero_name", username),
                    role=role, device_id=device_id)
            except Exception:
                token = ""
        if not token:
            token = signed.get("game_token") or ""
        if not token:
            try:
                import accounts
                token = accounts.get_game_token(username) or ""
            except Exception:
                token = ""
        # Local minting is dev-only fallback when token_service is present
        if not token and token_service:
            token = token_service.create_token(
                account_id=account_id,
                username=username,
                hero_name=signed.get("hero_name", username),
                role=role,
                device_id=device_id
            )

        try:
            cand_dirs = [RUNTIME_DIR]
            cand_dirs.append(os.path.join(ROOT_DIR, "client", "runtime"))
            parent_root = os.path.dirname(ROOT_DIR)
            cand_dirs.append(os.path.join(parent_root, "client", "runtime"))
            for r_dir in set(d for d in cand_dirs if d):
                try:
                    os.makedirs(r_dir, exist_ok=True)
                    tok_path = os.path.join(r_dir, "session_token.json")
                    with open(tok_path, "w", encoding="utf-8") as tf:
                        json.dump({
                            "token": token,
                            "account_id": account_id,
                            "username": username,
                            "device_id": device_id,
                            "role": role,
                            "issued_at": time.time()
                        }, tf, indent=2)
                except Exception:
                    pass
        except Exception:
            pass

        return {
            "authorized": True,
            "banned": False,
            "token": token,
            "role": role,
            "message": "PLAY AUTHORIZED"
        }

    # Moderation is server-side (shared bans table on the VPS). The dev UI and
    # the in-console moderation buttons both use these.
    def _dev_or_error(self):
        me = self._signed_user() or {}
        if not me.get("is_dev"):
            return None, {"success": False, "message": "Unauthorized: Developer role required"}
        return me, None

    def moderation_search_players(self, query):
        me, err = self._dev_or_error()
        if err:
            return []
        import accounts
        return accounts.search_players(me["username"], query)

    def moderation_ban_player(self, account_id, in_game_name="", ban_type="Permanent", reason="Cheating", notes="", duration=0):
        me, err = self._dev_or_error()
        if err:
            return err
        import accounts
        secs = 0 if str(ban_type).lower().startswith("perm") else int(duration or 0)
        return accounts.ban_player(me["username"], str(account_id or in_game_name), reason=reason,
                                   duration_seconds=secs, notes=notes)

    def moderation_unban_player(self, ban_id, reason="Developer review"):
        me, err = self._dev_or_error()
        if err:
            return err
        import accounts
        return accounts.unban_player(me["username"], ban_id=ban_id, reason=reason)

    def moderation_get_bans(self):
        me, err = self._dev_or_error()
        if err:
            return []
        import accounts
        return accounts.list_bans(me["username"]).get("bans", [])

    def moderation_get_flags(self):
        if not ban_service:
            return []
        return ban_service.list_flags()

    def moderation_get_role(self):
        me = self._signed_user() or {}
        is_dev = bool(me.get("is_dev"))
        return {"role": "DEVELOPER" if is_dev else "PLAYER", "can_moderate": is_dev}

    # Settings > Ban Players
    def dev_ban_player(self, username, reason="Cheating", duration_hours=0, notes=""):
        me, err = self._dev_or_error()
        if err:
            return err
        import accounts
        try:
            secs = int(float(duration_hours or 0) * 3600)
        except (TypeError, ValueError):
            secs = 0
        if (username or "").strip().lower() == (me.get("username") or "").lower():
            return {"success": False, "message": "You can't ban yourself."}
        return accounts.ban_player(me["username"], username, reason=reason or "Cheating",
                                   duration_seconds=secs, notes=notes or "")

    def dev_unban_player(self, username="", ban_id="", reason="Developer review"):
        me, err = self._dev_or_error()
        if err:
            return err
        import accounts
        return accounts.unban_player(me["username"], username=username or None,
                                     ban_id=ban_id or None, reason=reason)

    def dev_list_bans(self):
        me, err = self._dev_or_error()
        if err:
            return dict(err, bans=[])
        import accounts
        return accounts.list_bans(me["username"])

    def list_tester_accounts(self):
        me, err = self._dev_or_error()
        if err:
            return dict(err, testers=[])
        import accounts
        return accounts.list_testers(me["username"])


    def minimize_window(self):
        if self._window:
            self._window.minimize()

    def close_window(self):
        if self._window:
            self._window.destroy()

    def open_external_url(self, url):
        try:
            webbrowser.open(url)
            return True
        except Exception as e:
            return False

    def open_game_directory(self):
        try:
            cfg = load_config()
            target = os.path.dirname(cfg.get("game_path", CLIENT_EXE))
            if not os.path.exists(target):
                target = CYBER_HUNTER_DIR
            if os.path.exists(target):
                os.startfile(target)
                return True
            return False
        except Exception as e:
            return False

    def browse_game_path(self):
        try:
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            selected = filedialog.askopenfilename(
                title="Select Cyber Hunter client.exe or launcher.exe",
                filetypes=[("Executable Files", "*.exe"), ("All Files", "*.*")],
                initialdir=CYBER_HUNTER_DIR if os.path.exists(CYBER_HUNTER_DIR) else ROOT_DIR
            )
            root.destroy()
            if selected:
                sel = os.path.normpath(selected)
                # Picking launcher.exe of the game folder: use its bin/client.exe.
                if os.path.basename(sel).lower() != "client.exe":
                    alt = os.path.join(os.path.dirname(sel), "bin", "client.exe")
                    if os.path.isfile(alt):
                        sel = alt
                cfg = load_config()
                cfg["game_path"] = sel
                save_config(cfg)
                return sel
            return ""
        except Exception as e:
            return ""

    def check_server_status(self):
        rev = get_revival_config()
        server_ip = (rev.get("server_ip") or "127.0.0.1").strip()
        is_remote = is_remote_mode()
        client_alive = is_process_running("client.exe")
        online = False

        # Liveness is decided purely by the ports the stack actually opens.
        # Polled every 5s by the UI. Four sequential connects at the old 0.6s
        # timeout could stall the API thread for 2.4s per poll.
        target_ip = server_ip if is_remote else "127.0.0.1"
        if not online:
            for port in (
                rev.get("gateway_port", 10001),
                rev.get("patch_port", 443),
                rev.get("control_panel_port", 8888),
                rev.get("gameapi_port", 3000),
                rev.get("referee_port", 10777),
            ):
                try:
                    import socket
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(0.35)
                    s.connect((target_ip, int(port)))
                    s.close()
                    online = True
                    break
                except Exception:
                    pass

        if not online and client_alive:
            online = True

        out = {
            "online": online,
            "server_ip": server_ip,
            "server_name": rev.get("server_name", "Cyber Hunter Reawakening"),
            "mode": "remote" if is_remote else "local",
            "is_remote": is_remote,
            "client_running": client_alive,
        }
        return out

    def get_launch_status(self):
        client_alive = is_process_running("client.exe")
        status_info = {
            "status": "idle",
            "step": "",
            "running": client_alive,
            "ready": False
        }
        if os.path.exists(STATUS_FILE):
            try:
                with open(STATUS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    status_info["status"] = data.get("status", "idle")
                    status_info["step"] = data.get("step", "")
                    st = str(data.get("status", ""))
                    # Stale status files survive after client.exe dies. Never report
                    # lobby_ready / ready unless the client process is actually up —
                    # otherwise Play stays stuck on "already running".
                    if client_alive and (
                        st in ("lobby_ready", "server_lobby_ready")
                        or "ready" in st
                        or data.get("ready") is True
                    ):
                        status_info["ready"] = True
                        status_info["status"] = "lobby_ready"
                    elif not client_alive and st in (
                        "lobby_ready", "server_lobby_ready", "armed", "launching", "running"
                    ):
                        status_info["status"] = "idle"
                        status_info["ready"] = False
                    if st == "failed":
                        status_info["error"] = data.get("error", "Launch failed")
            except Exception:
                pass

        if client_alive and not status_info["ready"]:
            if os.path.exists(LOG_FILE):
                try:
                    with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as lf:
                        tail = lf.read()[-4000:].lower()
                        if "lobby ready" in tail or "apexgamestudio auth armed" in tail:
                            status_info["ready"] = True
                            status_info["status"] = "lobby_ready"
                except Exception:
                    pass

        return status_info

    def launch_game(self, mode="client"):
        global launch_pipeline_running
        cfg = load_config()

        if mode == "control_panel":
            # Prefer Navy ControlPanel HTTP backend (:8888) + optional GUI
            started = []
            if os.path.exists(CONTROL_PANEL_BACKEND):
                subprocess.Popen(
                    [sys.executable, CONTROL_PANEL_BACKEND],
                    cwd=os.path.dirname(CONTROL_PANEL_BACKEND),
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                started.append("backend:8888")
            if started:
                return {"success": True, "message": "Control Panel launched (%s)" % ", ".join(started)}
            return {"success": False, "message": "ControlPanel/server_backend.py not found"}

        # Online-only: the lobby connects through the VPS, so refuse Play
        # before anything starts (hosts edits, Frida, client.exe) when this PC
        # is offline or the VPS is unreachable.
        if mode == "client":
            st = self.account_state()
            signed = (st or {}).get("signed_in")
            if not signed or not signed.get("username"):
                return {
                    "success": False,
                    "message": "Access Denied: Please sign in with your authorized account before playing."
                }
            # Server reachability and the ban check now run in-game when the
            # player presses START on the main menu (referee auth_check), so
            # Play launches the client immediately. Only refresh the local
            # session token here (no network).
            try:
                self.authorize_play(check_ban=False)
            except Exception as e:
                print("session token refresh failed: %s" % e)

        # Ban check moved in-game (main menu START -> referee auth_check).

        # Check the repo is complete FIRST. An incomplete clone is the root
        # problem: starting the suite and then blaming a missing client.exe
        # sends the user hunting for the wrong thing, and leaves services
        # running behind a launch that was never going to work.
        required = []
        _mode = boot_mode(self.get_config() if hasattr(self, "get_config") else None)
        for p in REQUIRED_OFFLINE_PATHS + ([NATIVE_PACK] if _mode == "native" else FRIDA_OFFLINE_PATHS):
            if is_remote_mode() and ("patch_server.py" in p or "gateway_stub.py" in p):
                continue
            if not os.path.exists(p):
                alt = p.replace(os.path.join(ROOT_DIR, "client", "frida"), FRIDA_DIR).replace(os.path.join(ROOT_DIR, "tools", "private_server"), PRIVATE_SERVER_DIR)
                if os.path.exists(alt):
                    continue
            required.append(p)
        missing = [p for p in required if not os.path.exists(p)]
        if missing:
            return {
                "success": False,
                "message": "Offline stack incomplete — missing: %s. Re-clone or `git pull`; see README.md."
                           % ", ".join(os.path.relpath(p, ROOT_DIR) for p in missing),
            }

        # Bind this Play to the Navy Launcher session. accounts.resume writes
        # active_account.json so the payload loads that account's save instead
        # of a seeded Hunter. The UI already called account_state on load;
        # this covers auto-Play and any other caller of launch_game.
        try:
            st = self.account_state()
            signed = (st or {}).get("signed_in")
            if signed:
                print("Play bound to Navy account %s" % (
                    signed.get("username") or signed.get("hero_name") or "?"))
        except Exception as e:
            print("Play account bind failed: %s" % e)

        # Validate executable presence
        game_path = cfg.get("game_path") or CLIENT_EXE
        if not os.path.exists(game_path):
            if os.path.exists(CLIENT_EXE):
                game_path = CLIENT_EXE
            elif os.path.exists(LAUNCHER_EXE):
                game_path = LAUNCHER_EXE
            else:
                return {
                    "success": False,
                    "message": f"Game executable not found at '{game_path}'. Install client under game\\bin\\client.exe or select it in Settings."
                }

        # Clear old status file before launch
        try:
            os.makedirs(RUNTIME_DIR, exist_ok=True)
            if os.path.exists(STATUS_FILE):
                os.remove(STATUS_FILE)
        except Exception:
            pass

        # This launcher is the only way in, so it runs the pipeline itself.
        work_dir = ROOT_DIR
        pipeline = ("powershell", [
            "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
            os.path.abspath(OFFLINE_PS1),
        ])
        # "frida" or "native" (client loads our compiled scripts itself, no
        # Frida; docs/NATIVE_SCRIPTS.md). See boot_mode().
        pipeline[1].extend(["-Boot", boot_mode(cfg)])

        if pipeline:
            kind, args = pipeline

            def _run_pipeline():
                global launch_pipeline_running
                launch_pipeline_running = True
                try:
                    # Started here, not on the API thread: this can block
                    # for minutes on a first-run `npm install`, and doing
                    # it inline froze the whole launcher window on Play.
                    _ensure_suite_services(bool(cfg.get("auto_server", True)))
                    # wait=True: a background rewrite started by Settings must
                    # finish before client.exe opens those packs.
                    _apply_day_night_npk_files(cfg.get("env_mode") or ("night" if cfg.get("night_mode", False) else "day"), wait=True)
                    if kind == "cmd":
                        if is_admin():
                            subprocess.run(
                                ["cmd.exe"] + args,
                                cwd=work_dir,
                                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
                            )
                        else:
                            ctypes.windll.shell32.ShellExecuteW(
                                None, "runas", "cmd.exe",
                                " ".join('"%s"' % a if " " in a else a for a in args),
                                work_dir, 1
                            )
                    else:
                        if is_admin():
                            subprocess.run(
                                ["powershell.exe"] + args,
                                cwd=work_dir,
                                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                            )
                        else:
                            ps_args = " ".join('"%s"' % a if " " in a else a for a in args)
                            ctypes.windll.shell32.ShellExecuteW(
                                None, "runas", "powershell.exe", ps_args, work_dir, 0
                            )
                except Exception as ex:
                    print("Pipeline launch exception:", ex)
                finally:
                    launch_pipeline_running = False

            threading.Thread(target=_run_pipeline, daemon=True).start()

            if cfg.get("close_on_launch", False):
                def _auto_close_watcher():
                    for _ in range(90):
                        time.sleep(2)
                        st = self.get_launch_status()
                        if st.get("ready") or st.get("status") in ("lobby_ready", "server_lobby_ready"):
                            time.sleep(3)
                            self.close_window()
                            break
                threading.Thread(target=_auto_close_watcher, daemon=True).start()

            rev = get_revival_config()
            remote = is_remote_mode()
            if remote:
                msg = "Connecting to %s..." % rev.get("server_name")
            else:
                msg = "Launching Cyber Hunter..."
            return {
                "success": True,
                "message": msg,
                "pipeline": True,
                "mode": "remote" if remote else "local",
                "server_ip": rev.get("server_ip"),
            }

        # Fallback direct launch if entrypoints missing
        try:
            subprocess.Popen([game_path], cwd=os.path.dirname(game_path))
            return {"success": True, "message": "Client launched directly (no offline pipeline)."}
        except Exception as e:
            return {"success": False, "message": f"Failed to start game: {str(e)}"}

    def open_installer(self):
        """Installer, from inside the Launcher (was Launch_Installer.bat)."""
        return self._spawn_tool(INSTALLER_PY, "Installer")

    def open_account_manager(self):
        """Account/character manager (was MANAGE_ACCOUNT.bat)."""
        return self._spawn_tool(ACCOUNT_MANAGER_PY, "Account Manager", console=True)

    def _spawn_tool(self, script, label, console=False):
        if not os.path.exists(script):
            return {"success": False,
                    "message": "%s not found at %s"
                               % (label, os.path.relpath(script, ROOT_DIR))}
        try:
            flags = 0
            exe = sys.executable
            if os.name == "nt":
                # account_manager.py is a console tool and is useless without
                # a window; the Installer draws its own.
                flags = (subprocess.CREATE_NEW_CONSOLE if console
                         else subprocess.CREATE_NO_WINDOW)
                if console:
                    # The Launcher itself runs under pythonw.exe, which has no
                    # console and never attaches stdio to one. Spawning a
                    # console tool with it opened an empty window that closed
                    # again, so Account Manager and Installer showed the
                    # "Opening..." toast and then nothing -- the tool had in
                    # fact started and died silently. Hand console tools the
                    # real python.exe beside it.
                    cand = os.path.join(os.path.dirname(exe), "python.exe")
                    if os.path.isfile(cand):
                        exe = cand
            subprocess.Popen([exe, script],
                             cwd=os.path.dirname(script) or ROOT_DIR,
                             creationflags=flags)
            return {"success": True, "message": "%s opened" % label}
        except Exception as e:
            return {"success": False, "message": "%s failed: %s" % (label, e)}

    def kill_game(self):
        try:
            subprocess.run(["taskkill", "/F", "/IM", "client.exe"], creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            return {"success": True, "message": "Game processes terminated."}
        except Exception as e:
            return {"success": False, "message": str(e)}

    # ------------------------------------------------------------------ Master Console
    # Operator panel attached to this launcher: live logs, suite status, and
    # Frida lobby_cmd overrides. Same channel as client/frida/cmd.ps1.

    _pid_cache = (0.0, 0)

    def _client_pid(self):
        """PID of OUR client.exe (under this install's game folder), else 0.

        Used to start PowerShell + Get-CimInstance on every call (0.5-2 s
        each, several per Settings save), and matched only paths containing
        "CyberHunter", so it never saw installs like E:\\CHReawakeningTest.
        Now: Toolhelp snapshot + QueryFullProcessImageName, cached 1 s."""
        if os.name != "nt":
            return 0
        now = time.time()
        ts, pid = LauncherAPI._pid_cache
        if now - ts < 1.0:
            return pid
        pid = 0
        try:
            from ctypes import wintypes
            k32 = ctypes.windll.kernel32

            class _PE32W(ctypes.Structure):
                _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD),
                            ("th32ProcessID", wintypes.DWORD), ("th32DefaultHeapID", ctypes.c_size_t),
                            ("th32ModuleID", wintypes.DWORD), ("cntThreads", wintypes.DWORD),
                            ("th32ParentProcessID", wintypes.DWORD), ("pcPriClassBase", wintypes.LONG),
                            ("dwFlags", wintypes.DWORD), ("szExeFile", ctypes.c_wchar * 260)]
            roots = set()
            for r in (GAME_DIR, CYBER_HUNTER_DIR, ROOT_DIR, os.path.dirname(os.path.dirname(load_config().get("game_path") or ""))):
                if r:
                    try:
                        roots.add(os.path.normcase(os.path.realpath(r)))
                    except Exception:
                        pass
            k32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
            snap = k32.CreateToolhelp32Snapshot(2, 0)
            if snap and snap != wintypes.HANDLE(-1).value:
                pe = _PE32W()
                pe.dwSize = ctypes.sizeof(_PE32W)
                ok = k32.Process32FirstW(snap, ctypes.byref(pe))
                best = (0, 0)
                while ok:
                    if pe.szExeFile.lower() == "client.exe":
                        h = k32.OpenProcess(0x1000, False, pe.th32ProcessID)  # QUERY_LIMITED_INFORMATION
                        path = ""
                        if h:
                            buf = ctypes.create_unicode_buffer(1024)
                            n = wintypes.DWORD(1024)
                            if k32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(n)):
                                path = buf.value
                            k32.CloseHandle(h)
                        mine = not path  # protected/elevated: can't tell, assume ours
                        if path:
                            rp = os.path.normcase(os.path.realpath(path))
                            mine = any(rp.startswith(r + os.sep) for r in roots)
                        if mine and pe.th32ProcessID > best[1]:
                            best = (1, pe.th32ProcessID)
                    ok = k32.Process32NextW(snap, ctypes.byref(pe))
                k32.CloseHandle(snap)
                pid = best[1]
        except Exception:
            pid = 0
        LauncherAPI._pid_cache = (now, pid)
        return pid

    def master_snapshot(self):
        """Suite + match + account snapshot for the Master Console header."""
        rev = get_revival_config()
        st = {}
        if os.path.exists(STATUS_FILE):
            try:
                with open(STATUS_FILE, "r", encoding="utf-8") as f:
                    st = json.load(f)
            except Exception:
                st = {}
        acct = {}
        acct_path = os.path.join(RUNTIME_DIR, "offline_account.json")
        if os.path.exists(acct_path):
            try:
                with open(acct_path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                # Keep it short — full bag dumps belong in a later tab.
                if isinstance(raw, dict):
                    acct = {
                        "hero_id": raw.get("hero_id") or raw.get("type_id"),
                        "name": raw.get("name") or raw.get("hero_name"),
                        "level": raw.get("level"),
                        "keys": sorted(list(raw.keys()))[:24],
                    }
            except Exception as e:
                acct = {"error": str(e)}
        pid = self._client_pid()
        target_ip = (rev.get("server_ip") or "127.0.0.1").strip() if is_remote_mode() else "127.0.0.1"
        ports = {
            "control_panel": _port_open(target_ip, int(rev.get("control_panel_port", 8888) or 8888)),
            "game_api": _port_open(target_ip, int(rev.get("gameapi_port", 3000) or 3000)),
            "patch": _port_open(target_ip, int(rev.get("patch_port", 443) or 443)),
            "http_stub": _port_open(target_ip, 80),
            "gateway": _port_open(target_ip, int(rev.get("gateway_port", 10001) or 10001)),
            "referee": _port_open(target_ip, int(rev.get("referee_port", 10777) or 10777)),
        }
        return {
            "success": True,
            "revival": {
                "server_ip": rev.get("server_ip") or rev.get("REVIVAL_SERVER_IP"),
                "server_name": rev.get("server_name"),
                "mode": "remote" if is_remote_mode() else "local",
            },
            "ports": ports,
            "launch": self.get_launch_status(),
            "status_file": st,
            "client_pid": pid,
            "account": acct,
            "log_paths": {
                "lobby": LOG_FILE,
                "status": STATUS_FILE,
                "requests": os.path.join(ROOT_DIR, "tools", "private_server", "logs", "requests.jsonl"),
                "game": os.path.join(CYBER_HUNTER_DIR, "logs", "log.txt"),
            },
        }

    def master_tail_log(self, which="lobby", offset=0, max_bytes=48000):
        """Tail a runtime log. offset is byte position; return new_offset + text."""
        paths = {
            "lobby": LOG_FILE,
            "status": STATUS_FILE,
            "requests": os.path.join(ROOT_DIR, "tools", "private_server", "logs", "requests.jsonl"),
            "game": os.path.join(CYBER_HUNTER_DIR, "logs", "log.txt"),
        }
        path = paths.get(str(which or "lobby"), LOG_FILE)
        if not os.path.exists(path):
            return {"success": True, "text": "", "offset": 0, "path": path, "missing": True}
        try:
            size = os.path.getsize(path)
            off = int(offset or 0)
            if off < 0 or off > size:
                # Rotated / truncated — restart from a window near the end.
                off = max(0, size - int(max_bytes or 48000))
            with open(path, "rb") as f:
                f.seek(off)
                chunk = f.read(int(max_bytes or 48000))
                new_off = f.tell()
            text = chunk.decode("utf-8", "replace")
            return {
                "success": True,
                "text": text,
                "offset": new_off,
                "size": size,
                "path": path,
                "missing": False,
            }
        except Exception as e:
            return {"success": False, "message": str(e), "text": "", "offset": int(offset or 0)}

    def master_command_catalog(self):
        """Curated Frida lobby_cmd verbs (same as cmd.ps1)."""
        return {
            "success": True,
            "commands": [
                {"cmd": "home", "group": "lobby", "desc": "Home / hall"},
                {"cmd": "classic", "group": "lobby", "desc": "Classic BR lobby"},
                {"cmd": "camp", "group": "lobby", "desc": "Camp / TDM lobby"},
                {"cmd": "escape", "group": "lobby", "desc": "Escape lobby"},
                {"cmd": "br", "group": "match", "desc": "Start Classic BR match"},
                {"cmd": "train", "group": "match", "desc": "Training ground"},
                {"cmd": "arena", "group": "match", "desc": "Arena / targets"},
                {"cmd": "loot", "group": "match", "desc": "Reseed BR loot (original tables)"},
                {"cmd": "doors", "group": "match", "desc": "Re-arm doors"},
                {"cmd": "bag", "group": "player", "desc": "Bag / interact refresh"},
                {"cmd": "stamina", "group": "player", "desc": "Refill stamina"},
                {"cmd": "cubes", "group": "player", "desc": "Sync quantum cubes"},
                {"cmd": "settle", "group": "match", "desc": "Force settle UI"},
                {"cmd": "unstick", "group": "player", "desc": "Unstick controls"},
                {"cmd": "fixctrl", "group": "player", "desc": "Repair input / loco"},
                {"cmd": "reexec", "group": "debug", "desc": "Hot-reload payload"},
                {"cmd": "stuck", "group": "debug", "desc": "Dump stuck diagnostics"},
                {"cmd": "night", "group": "match", "desc": "Switch BR to Night mode (stars & moon)"},
                {"cmd": "day", "group": "match", "desc": "Switch BR to Day mode (sun)"},
                {"cmd": "daynight", "group": "match", "desc": "Toggle Day / Night environment (F10)"},
                {"cmd": "hydrofoil", "group": "vehicle", "desc": "Spawn Flying Hydrofoil - Titanium"},
                {"cmd": "hydrofoil", "group": "test", "label": "Spawn Hydrofoil", "desc": "Spawn Flying Hydrofoil - Titanium"},
                {"cmd": "remove all bots", "group": "test", "label": "Remove All Bots", "desc": "Despawn bots & alive=1"},
                {"cmd": "remove all lootables", "group": "test", "label": "Remove All Lootables", "desc": "Despawn items & chests"},
                {"cmd": "remove safe zone", "group": "test", "label": "Remove Safe Zone", "desc": "Disable circle storm & damage"},
                {"cmd": "disable rain", "group": "test", "label": "Disable Rain", "desc": "Clear rain effects, audio & sky"},
                {"cmd": "mapper", "group": "tools", "desc": "Toggle F11 spawn mapper overlay"},
                {"cmd": "mapper mark chest", "group": "tools", "desc": "Mark chest at player pose"},
                {"cmd": "mapper mark vehicle", "group": "tools", "desc": "Mark vehicle at player pose"},
                {"cmd": "mapper export", "group": "tools", "desc": "Export marks to spawn_map_export.py"},
            ],
        }

    def remove_all_bots(self):
        """Despawn all bots and set match alive to 1."""
        return self.master_send_cmd("remove all bots")

    def remove_all_lootables(self):
        """Despawn all ground items and chests."""
        return self.master_send_cmd("remove all lootables")

    def remove_safe_zone(self):
        """Disable safe zone circle, poison storm, and damage."""
        return self.master_send_cmd("remove safe zone")

    def disable_rain(self):
        """Disable rain weather effects, droplets, audio and shaders."""
        return self.master_send_cmd("disable rain")

    def spawn_hydrofoil(self):
        """Spawn the flying Hydrofoil - Titanium in front of the player."""
        return self.master_send_cmd("hydrofoil")

    def master_send_cmd(self, command):
        """Write lobby_cmd_<pid>.txt — Frida payload picks it up next tick."""
        cmd = (command or "").strip()
        if not cmd:
            return {"success": False, "message": "Empty command"}
        # Block anything that would start a second Play pipeline.
        low = cmd.lower()
        if "run_offline_python" in low or low.endswith(".ps1"):
            return {"success": False, "message": "Refused — use Launcher Play, not pipeline scripts"}
        pid = self._client_pid()
        if pid <= 0:
            return {"success": False, "message": "No client.exe — click Play first"}
        try:
            os.makedirs(RUNTIME_DIR, exist_ok=True)
            path = os.path.join(RUNTIME_DIR, "lobby_cmd_%d.txt" % int(pid))
            with open(path, "a", encoding="utf-8") as f:
                f.write(cmd.strip() + "\n")
            return {
                "success": True,
                "message": "Sent to pid=%s: %s" % (pid, cmd),
                "pid": pid,
                "path": path,
            }
        except Exception as e:
            return {"success": False, "message": str(e)}

    def spawn_mapper_snapshot(self):
        """Live pose + mark table for the F11 Spawn Mapper overlay."""
        live_path = os.path.join(RUNTIME_DIR, "spawn_mapper_live.json")
        map_path = os.path.join(RUNTIME_DIR, "spawn_map.json")
        export_path = os.path.join(RUNTIME_DIR, "spawn_map_export.py")
        live = {}
        marks_doc = {"version": 1, "marks": []}
        try:
            if os.path.isfile(live_path):
                with open(live_path, "r", encoding="utf-8") as f:
                    live = json.load(f) or {}
        except Exception as e:
            live = {"error": str(e)}
        try:
            if os.path.isfile(map_path):
                with open(map_path, "r", encoding="utf-8") as f:
                    marks_doc = json.load(f) or marks_doc
        except Exception as e:
            marks_doc = {"version": 1, "marks": [], "error": str(e)}
        return {
            "success": True,
            "live": live,
            "doc": marks_doc,
            "paths": {
                "live": live_path,
                "map": map_path,
                "export": export_path,
            },
            "client_running": self._client_pid() > 0,
        }

    def spawn_mapper_cmd(self, command):
        """Send a mapper verb through lobby_cmd (same as Master Console)."""
        cmd = (command or "").strip()
        if not cmd:
            return {"success": False, "message": "Empty command"}
        if not cmd.lower().startswith("mapper"):
            cmd = "mapper " + cmd
        return self.master_send_cmd(cmd)

    def spawn_mapper_update_label(self, mark_id, label):
        """Edit a mark label in spawn_map.json without needing the game."""
        map_path = os.path.join(RUNTIME_DIR, "spawn_map.json")
        if not os.path.isfile(map_path):
            return {"success": False, "message": "No spawn_map.json yet — mark in-game first"}
        try:
            with open(map_path, "r", encoding="utf-8") as f:
                doc = json.load(f) or {}
            marks = doc.get("marks") or []
            found = False
            for row in marks:
                if str(row.get("id")) == str(mark_id):
                    row["label"] = label or ""
                    found = True
                    break
            if not found:
                return {"success": False, "message": "Mark %s not found" % mark_id}
            with open(map_path, "w", encoding="utf-8") as f:
                json.dump(doc, f, ensure_ascii=False, indent=2)
            return {"success": True, "message": "Label updated", "id": mark_id}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def spawn_mapper_delete_mark(self, mark_id):
        map_path = os.path.join(RUNTIME_DIR, "spawn_map.json")
        if not os.path.isfile(map_path):
            return {"success": False, "message": "No spawn_map.json"}
        try:
            with open(map_path, "r", encoding="utf-8") as f:
                doc = json.load(f) or {}
            before = len(doc.get("marks") or [])
            doc["marks"] = [m for m in (doc.get("marks") or [])
                            if str(m.get("id")) != str(mark_id)]
            after = len(doc["marks"])
            if after == before:
                return {"success": False, "message": "Mark %s not found" % mark_id}
            with open(map_path, "w", encoding="utf-8") as f:
                json.dump(doc, f, ensure_ascii=False, indent=2)
            return {"success": True, "message": "Deleted %s" % mark_id, "count": after}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def spawn_mapper_open_folder(self):
        try:
            os.makedirs(RUNTIME_DIR, exist_ok=True)
            if os.name == "nt":
                os.startfile(RUNTIME_DIR)
            else:
                subprocess.Popen(["xdg-open", RUNTIME_DIR])
            return {"success": True, "message": "Opened client/runtime"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def master_kill_client(self):
        """Stop client.exe only (suite services stay up)."""
        return self.kill_game()

    def get_day_night_state(self):
        """Query current BR environment mode (auto, day, dawn, sunset, autumn, night, rain, rainy_night, snow, snowy_night)."""
        st_file = os.path.join(RUNTIME_DIR, "daynight_state.json")
        mode = "auto"
        rain = False
        snow = False
        if os.path.exists(st_file):
            try:
                with open(st_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    mode = data.get("mode") or ("auto" if data.get("auto_weather", True) else ("night" if data.get("night", False) else "day"))
                    rain = bool(data.get("rain", mode in ("rain", "rainy_night")))
                    snow = bool(data.get("snow", mode in ("snow", "snowy_night")))
            except Exception:
                pass
        else:
            cfg = load_config()
            mode = cfg.get("env_mode") or ("auto" if cfg.get("auto_weather", True) else ("night" if cfg.get("night_mode", False) else "day"))
            rain = (mode in ("rain", "rainy_night")) or bool(cfg.get("rain_mode", False))
            snow = (mode in ("snow", "snowy_night")) or bool(cfg.get("snow_mode", False))
        if mode not in ("auto", "day", "dawn", "sunset", "autumn", "night", "rain", "rainy_night", "snow", "snowy_night"):
            mode = "auto"
        is_auto = (mode == "auto")
        is_night = (mode in ("night", "rainy_night", "snowy_night"))
        is_rain = ((mode in ("rain", "rainy_night")) or rain)
        is_snow = ((mode in ("snow", "snowy_night")) or snow)
        return {"success": True, "mode": mode, "auto": is_auto, "night": is_night, "rain": is_rain, "snow": is_snow}

    def toggle_rain(self, enable=None):
        """Toggle rain weather effects (gray sky, rain particles, wet road/character details)."""
        current_state = self.get_day_night_state()
        cur_rain = current_state.get("rain", False)
        target_rain = (not cur_rain) if enable is None else bool(enable)

        cfg = load_config()
        cfg["rain_mode"] = target_rain
        if target_rain and cfg.get("env_mode") not in ("rain", "rainy_night", "night", "dawn", "sunset", "autumn", "day", "snow", "snowy_night"):
            cfg["env_mode"] = "rain"
        save_config(cfg)

        target_mode = "rain" if target_rain else (cfg.get("env_mode") if cfg.get("env_mode") not in ("rain", "rainy_night") else "day")
        return self.toggle_day_night(mode=target_mode)

    def toggle_snow(self, enable=None):
        """Toggle snow weather effects (overcast/night sky, falling snowflakes, snow-covered world)."""
        current_state = self.get_day_night_state()
        cur_snow = current_state.get("snow", False)
        target_snow = (not cur_snow) if enable is None else bool(enable)

        cfg = load_config()
        cfg["snow_mode"] = target_snow
        if target_snow and cfg.get("env_mode") not in ("snow", "snowy_night", "night", "dawn", "sunset", "autumn", "day", "rain", "rainy_night"):
            cfg["env_mode"] = "snow"
        save_config(cfg)

        target_mode = "snow" if target_snow else (cfg.get("env_mode") if cfg.get("env_mode") not in ("snow", "snowy_night") else "day")
        return self.toggle_day_night(mode=target_mode)

    def toggle_day_night(self, mode=None):
        """Toggle or set Battle Royale environment mode: auto, day, dawn, sunset, autumn, night, rain, rainy_night, snow, snowy_night."""
        current_state = self.get_day_night_state()
        cur_mode = current_state.get("mode", "auto")

        cycle = ["auto", "day", "dawn", "sunset", "autumn", "night", "rain", "rainy_night", "snow", "snowy_night"]
        if mode is None:
            try:
                idx = cycle.index(cur_mode)
                target_mode = cycle[(idx + 1) % len(cycle)]
            except ValueError:
                target_mode = "auto"
        elif isinstance(mode, bool):
            target_mode = "night" if mode else "day"
        else:
            target_mode = str(mode).lower().strip()
            if target_mode in ("auto", "random", "ai", "dynamic", "autoweather"):
                target_mode = "auto"
            elif target_mode in ("rainynight", "rain_night", "darkrain", "stormynight"):
                target_mode = "rainy_night"
            elif target_mode in ("snowynight", "snow_night", "winternight"):
                target_mode = "snowy_night"
            elif target_mode in ("snowy", "winter"):
                target_mode = "snow"
            elif target_mode in ("autumn", "fall", "harvest"):
                target_mode = "autumn"
            if target_mode not in cycle:
                target_mode = "auto"

        is_auto = (target_mode == "auto")
        is_rain = (target_mode in ("rain", "rainy_night"))
        is_night = (target_mode in ("night", "rainy_night", "snowy_night"))
        is_snow = (target_mode in ("snow", "snowy_night"))

        # Update launcher config
        cfg = load_config()
        cfg["env_mode"] = target_mode
        cfg["auto_weather"] = is_auto
        cfg["night_mode"] = is_night
        cfg["rain_mode"] = is_rain
        cfg["snow_mode"] = is_snow
        save_config(cfg)

        # Write runtime state file
        try:
            os.makedirs(RUNTIME_DIR, exist_ok=True)
            st_file = os.path.join(RUNTIME_DIR, "daynight_state.json")
            with open(st_file, "w", encoding="utf-8") as f:
                json.dump({
                    "mode": target_mode,
                    "auto_weather": is_auto,
                    "night": is_night,
                    "rain": is_rain,
                    "snow": is_snow,
                    "updated": time.time()
                }, f, indent=2)
        except Exception:
            pass

        # Prepare all files: NPKs, textures, and XMLs
        _apply_day_night_npk_files(target_mode)

        # If client is currently running, send the real-time command
        client_running = self._client_pid() > 0
        if client_running:
            self.master_send_cmd("env " + target_mode)
            if is_rain:
                self.master_send_cmd("rain on")
            elif not is_auto:
                self.master_send_cmd("rain off")
            if is_snow:
                self.master_send_cmd("snow on")
            elif not is_auto:
                self.master_send_cmd("snow off")

        return {
            "success": True,
            "mode": target_mode,
            "auto": is_auto,
            "night": is_night,
            "rain": is_rain,
            "message": "Switched to %s mode" % ("AI AUTO WEATHER" if is_auto else target_mode.upper()),
            "client_running": client_running
        }

    # ------------------------------------------------------------------ AI Behavior Recording
    def get_recording_state(self):
        """Return active recording channels, sample count, and profile status."""
        rec_file = os.path.join(RUNTIME_DIR, "movement_record.json")
        samples_file = os.path.join(RUNTIME_DIR, "movement_samples.jsonl")
        profile_file = os.path.join(RUNTIME_DIR, "player_movement_profile.json")

        recording = False
        channels = []
        if os.path.exists(rec_file):
            try:
                with open(rec_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    recording = bool(data.get("recording", False))
                    channels = data.get("channels", [])
            except Exception: pass

        sample_count = 0
        if os.path.exists(samples_file):
            try:
                with open(samples_file, "r", encoding="utf-8") as f:
                    sample_count = sum(1 for line in f if line.strip())
            except Exception: pass

        has_profile = os.path.exists(profile_file)
        profile_info = {}
        if has_profile:
            try:
                with open(profile_file, "r", encoding="utf-8") as f:
                    pdata = json.load(f)
                    profile_info = {
                        "avg_speed": (pdata.get("movement") or {}).get("avg_speed", 0),
                        "combat_roll": ((pdata.get("bot_tuning") or {}).get("combat_roll_chance", 0)) * 100,
                        "samples": pdata.get("sample_count", 0)
                    }
            except Exception: pass

        return {
            "recording": recording,
            "channels": channels,
            "sample_count": sample_count,
            "has_profile": has_profile,
            "profile": profile_info
        }

    def toggle_recording(self, channel="all"):
        """Toggle telemetry recording for movement, countdown, combat, looting, plane_landing, or all."""
        rec_file = os.path.join(RUNTIME_DIR, "movement_record.json")
        cur_state = self.get_recording_state()
        cur_channels = set(cur_state.get("channels", []))
        is_rec = cur_state.get("recording", False)

        all_channels = ["movement", "countdown", "combat", "looting", "plane_landing"]
        target_ch = str(channel).lower().strip()

        if target_ch == "all":
            if is_rec:
                # Turn off all
                new_rec = False
                new_channels = []
            else:
                new_rec = True
                new_channels = all_channels
        else:
            if target_ch not in all_channels:
                target_ch = "movement"
            if target_ch in cur_channels:
                cur_channels.remove(target_ch)
            else:
                cur_channels.add(target_ch)
            new_channels = list(cur_channels)
            new_rec = bool(new_channels)

        os.makedirs(RUNTIME_DIR, exist_ok=True)
        try:
            with open(rec_file, "w", encoding="utf-8") as f:
                json.dump({
                    "recording": new_rec,
                    "channels": new_channels,
                    "session": int(time.time()),
                    "updated": time.time()
                }, f, indent=2)
        except Exception as e:
            return {"success": False, "message": "Failed updating recording file: %s" % e}

        msg = ("Recording enabled for: %s" % ", ".join(new_channels)) if new_rec else "Recording stopped"
        return {
            "success": True,
            "recording": new_rec,
            "channels": new_channels,
            "message": msg
        }

    def analyze_recordings(self):
        """Execute client/tools/analyze_movement.py and compile player behavior profile."""
        analyzer_script = os.path.join(ROOT_DIR, "client", "tools", "analyze_movement.py")
        if not os.path.exists(analyzer_script):
            return {"success": False, "message": "Analyzer script not found: %s" % analyzer_script}

        try:
            res = subprocess.run(
                [sys.executable, analyzer_script],
                cwd=ROOT_DIR,
                capture_output=True,
                text=True,
                timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            profile_file = os.path.join(RUNTIME_DIR, "player_movement_profile.json")
            if os.path.exists(profile_file):
                with open(profile_file, "r", encoding="utf-8") as f:
                    pdata = json.load(f)
                return {
                    "success": True,
                    "message": "AI profile compiled from %d samples! Applied to bot AI." % pdata.get("sample_count", 0),
                    "profile": pdata
                }
            return {"success": False, "message": "Analysis failed: %s" % res.stderr}
        except Exception as e:
            return {"success": False, "message": "Analysis error: %s" % e}

    def clear_recordings(self):
        """Clear recorded telemetry samples."""
        samples_file = os.path.join(RUNTIME_DIR, "movement_samples.jsonl")
        try:
            if os.path.exists(samples_file):
                os.remove(samples_file)
            return {"success": True, "message": "Recorded samples cleared."}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def verify_game_files(self):
        core_files = [
            "bin/client.exe", "neox.xml", "ca_certificates.crt",
            "res/scene/world4k.npk", "data.npk", "script.npk", "patch.npk",
        ]
        # Also accept Cyber Steam layout if game/ incomplete
        roots = [CYBER_HUNTER_DIR]
        if CYBER_STEAM_DIR not in roots and os.path.isdir(CYBER_STEAM_DIR):
            roots.append(CYBER_STEAM_DIR)
        found = 0
        missing = []
        for rel in core_files:
            ok = False
            for root in roots:
                p = os.path.join(root, rel.replace("/", os.sep))
                if os.path.exists(p) and os.path.getsize(p) > 0:
                    ok = True
                    break
            if ok:
                found += 1
            else:
                missing.append(rel)

        if missing:
            return {
                "success": False,
                "message": f"Verification: {found}/{len(core_files)} OK. Missing: {', '.join(missing)} (place client under game\\)"
            }
        return {
            "success": True,
            "message": f"All {found} core packages & client binaries verified."
        }

    # ------------------------------------------------------------------ Launcher/client updates
    # Manifest-based (Launcher/updater.py): downloads ONLY allow-listed player
    # files over HTTPS and verifies each one's SHA-256. No git, so nothing
    # else on the update branch (server code, configs) ever reaches a player.
    _updater = None
    _updater_lock = threading.Lock()

    def _get_updater(self):
        with self._updater_lock:
            if LauncherAPI._updater is None:
                try:
                    from updater import Updater
                except ImportError:
                    from Launcher.updater import Updater
                LauncherAPI._updater = Updater(ROOT_DIR)
            return LauncherAPI._updater

    def get_update_state(self):
        try:
            return self._get_updater().get()
        except Exception as e:
            return {"status": "unavailable", "message": str(e)}

    def check_for_update(self):
        try:
            return self._get_updater().check()
        except Exception as e:
            return {"status": "error", "message": "Update check failed: %s" % e}

    def start_update(self):
        if self._client_pid():
            return {"success": False, "message": "Close Cyber Hunter before updating."}
        try:
            return self._get_updater().start()
        except Exception as e:
            return {"success": False, "message": str(e)}

    def is_game_installed(self):
        cfg_exe = load_config().get("game_path") or ""
        if cfg_exe and os.path.isfile(cfg_exe) and os.path.basename(cfg_exe).lower() == "client.exe":
            return True
        if GameDownloader and GameDownloader.is_installed(ROOT_DIR):
            self._adopt_installed_game()
            return True
        return os.path.isfile(CLIENT_EXE)

    def get_game_download_state(self):
        if GameDownloader:
            st = GameDownloader.get_state(ROOT_DIR)
            if st.get("status") == "done" and st.get("installed"):
                self._adopt_installed_game()
                st["game_path"] = load_config().get("game_path", "")
            return st
        return {"status": "idle", "installed": os.path.isfile(CLIENT_EXE), "percent": 0.0}

    def _adopt_installed_game(self):
        """After a download: game/bin/client.exe beside the launcher becomes the Game Path."""
        exe = _refresh_game_paths()
        if not exe:
            return ""
        cfg = load_config()
        cur = cfg.get("game_path") or ""
        if not cur or not os.path.isfile(cur):
            cfg["game_path"] = os.path.normpath(exe)
            save_config(cfg)
        return exe

    def pause_game_download(self):
        if GameDownloader:
            return GameDownloader.pause(ROOT_DIR)
        return {"success": False, "message": "Downloader module unavailable."}

    def resume_game_download(self):
        return self.start_game_download()

    def start_game_download(self):
        st = self.account_state()
        signed = (st or {}).get("signed_in")
        if not signed or not signed.get("username"):
            return {"success": False, "message": "Access Denied: Please sign in before downloading the game."}
        
        username = signed.get("username")
        try:
            import accounts
        except ImportError:
            from Launcher import accounts
        
        cfg = load_config()
        token = cfg.get("account_token") or accounts.get_session_token(username) or ""
        if not accounts.verify_download_authorization(username, token):
            return {"success": False, "message": "Unauthorized: Valid authenticated session required."}

        if GameDownloader:
            return GameDownloader.start(ROOT_DIR, auth_token=token, username=username)
        return {"success": False, "message": "Downloader module unavailable."}

    def create_tester_account(self, username, password, hero_name=""):
        st = self.account_state()
        signed = (st or {}).get("signed_in")
        if not signed or not signed.get("is_dev"):
            return {"success": False, "message": "Developer privileges required to create tester accounts."}
        try:
            import accounts
        except ImportError:
            from Launcher import accounts
        return accounts.create_account(username, password, hero_name, created_by=signed.get("username"))

    def restart_launcher(self):
        """Relaunch through CyberHunter.bat (the single entry point) and close.

        A launcher .exe downloaded by the updater sits next to the old one as
        <name>.new; it is swapped in once this process has exited."""
        bat = os.path.join(ROOT_DIR, "CyberHunter.bat")
        try:
            swaps = []
            try:
                swaps = self._get_updater().staged_exes()
            except Exception:
                pass
            steps = ["ping -n 3 127.0.0.1 >nul"]
            for name in swaps:
                cur = os.path.join(ROOT_DIR, name)
                steps.append('move /y "%s.new" "%s" >nul' % (cur, cur))
            steps.append('start "" "%s"' % bat)
            # One command-line STRING: a list makes Python escape the inner
            # quotes as \" which cmd does not understand -> start runs "\\"
            # and Windows shows "Windows cannot find '\\'".
            subprocess.Popen('cmd /c ' + " & ".join(steps), cwd=ROOT_DIR,
                             creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        except Exception as e:
            return {"success": False, "message": str(e)}
        threading.Timer(0.4, lambda: os._exit(0)).start()
        return {"success": True}

    # ------------------------------------------------------------------ 1v1 Match System & Control Panel
    def _referee_tcp_cmd(self, packet, timeout=3.0):
        """Send a JSON command packet to referee server (port 10777) and return the response."""
        rev = get_revival_config()
        host = rev.get("server_ip") or rev.get("REVIVAL_SERVER_IP", "127.0.0.1") or "127.0.0.1"
        port = rev.get("referee_port", 10777)
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            s.connect((host, port))
            line = json.dumps(packet) + "\n"
            s.sendall(line.encode("utf-8"))
            data = b""
            while b"\n" not in data:
                chunk = s.recv(4096)
                if not chunk:
                    break
                data += chunk
            s.close()
            if not data:
                return {"success": False, "message": "No response received from referee server."}
            return json.loads(data.decode("utf-8").strip())
        except ConnectionRefusedError:
            return {"success": False, "message": "Referee server is not running on port 10777."}
        except socket.timeout:
            return {"success": False, "message": "Referee server response timed out."}
        except Exception as e:
            return {"success": False, "message": "Referee connection error: %s" % e}

    def one_on_one_check_opponent(self, opponent):
        """Verify if the entered username exists and is online/available for 1v1."""
        try:
            import accounts
        except Exception as e:
            return {"available": False, "reason": "Account subsystem error: %s" % e}

        act = accounts.active()
        my_name = (act.get("username") if act else "") or ""
        target = (opponent or "").strip()

        if not target:
            return {"available": False, "reason": "Please enter an opponent username."}
        if my_name and target.lower() == my_name.lower():
            return {"available": False, "reason": "You cannot match against yourself."}

        # Check account existence locally or in database
        if not accounts.account_exists(target):
            return {"available": False, "reason": f"User '{target}' does not exist."}

        # Query referee server for live status and availability
        res = self._referee_tcp_cmd({
            "op": "1v1_check_opponent",
            "username": my_name,
            "opponent": target
        })
        return res

    def one_on_one_match_now(self, opponent):
        """Trigger 1v1 match creation with an opponent."""
        try:
            import accounts
        except Exception as e:
            return {"success": False, "message": "Account subsystem error: %s" % e}

        act = accounts.active()
        my_name = (act.get("username") if act else "") or ""
        target = (opponent or "").strip()

        if not my_name:
            return {"success": False, "message": "Please log in to your account first."}
        if not target:
            return {"success": False, "message": "Please enter an opponent username."}
        if target.lower() == my_name.lower():
            return {"success": False, "message": "You cannot match against yourself."}

        pid = self._client_pid()
        if pid <= 0:
            return {"success": False, "message": "Your game client is not running. Please launch the game using Play first so you are connected."}

        res = self._referee_tcp_cmd({
            "op": "1v1_match_now",
            "username": my_name,
            "opponent": target
        })
        return res

    def one_on_one_get_status(self):
        """Query status of active 1v1 session for current player."""
        try:
            import accounts
            act = accounts.active()
            my_name = (act.get("username") if act else "") or ""
        except Exception:
            my_name = ""

        if not my_name:
            return {"active": False, "message": "Not logged in"}

        res = self._referee_tcp_cmd({
            "op": "1v1_get_status",
            "username": my_name
        }, timeout=2.0)

        if isinstance(res, dict) and res.get("op") == "1v1_status_ack":
            return res
        return {"active": False, "message": "No active 1v1 session"}

    def one_on_one_control_cmd(self, cmd, args=None):
        """Send authoritative 1v1 control command to referee server."""
        try:
            import accounts
            act = accounts.active()
            my_name = (act.get("username") if act else "") or ""
        except Exception:
            my_name = ""

        st = self.one_on_one_get_status()
        if not st.get("active") or not st.get("session_id"):
            return {"success": False, "message": "1v1 Control Panel is only active during an ongoing 1v1 match."}

        sid = st.get("session_id")
        res = self._referee_tcp_cmd({
            "op": "1v1_cmd",
            "session_id": sid,
            "username": my_name,
            "cmd": cmd,
            "args": args or {}
        })
        return res

    def one_on_one_end_session(self):
        """End the current 1v1 session and return both players safely to lobby."""
        return self.one_on_one_control_cmd("end_session")

WINDOW_TITLE = "Navy Games — Cyber Hunter Reawakening"


def _focus_existing_launcher():
    """Bring the running launcher to the front. True if one was found."""
    if os.name != "nt":
        return False
    try:
        user32 = ctypes.windll.user32
        hwnd = user32.FindWindowW(None, WINDOW_TITLE)
        if not hwnd:
            return False
        if user32.IsIconic(hwnd):
            user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        user32.SetForegroundWindow(hwnd)
        return True
    except Exception:
        return False


def _claim_single_instance():
    """Only one launcher may run at a time.

    Every press of start ran CyberHunter.bat, which opened another window, and
    nothing stopped a second or third from stacking up. The offline pipeline
    already guards itself with Global\\CyberHunterOfflineLauncher; the launcher
    that drives it did not. False means another instance owns the mutex.
    """
    if os.name != "nt":
        return True
    ERROR_ALREADY_EXISTS = 183
    try:
        kernel32 = ctypes.windll.kernel32
        # Kept on the module so it lives as long as the process. Windows frees
        # it on exit, so a crashed launcher cannot lock the user out.
        globals()["_instance_mutex"] = kernel32.CreateMutexW(
            None, False, "Global\\NavyGamesCyberHunterLauncher")
        return kernel32.GetLastError() != ERROR_ALREADY_EXISTS
    except Exception:
        return True


def _reset_webview_profile_if_needed(storage):
    """Wipe a corrupt Edge WebView2 user-data dir that paints only background_color.

    Elevated launches + a full disk have left half-written profiles under
    client/runtime/webview that never paint the HTML UI (all-black window).
    Bump WEBVIEW_PROFILE_VER when the UI shell changes enough that a clean
    profile is safer than migrating cookies.
    """
    import shutil
    ver = "4"
    marker = os.path.join(storage, ".navy_webview_profile_ver")
    try:
        cur = ""
        if os.path.isfile(marker):
            with open(marker, "r", encoding="utf-8") as fh:
                cur = (fh.read() or "").strip()
        if cur == ver and os.path.isdir(os.path.join(storage, "EBWebView")):
            return storage
        if os.path.isdir(storage):
            shutil.rmtree(storage, ignore_errors=True)
        os.makedirs(storage, exist_ok=True)
        with open(marker, "w", encoding="utf-8") as fh:
            fh.write(ver)
        print("Launcher WebView profile reset (ver %s)" % ver)
    except Exception as e:
        print("Launcher WebView profile reset failed: %s" % e)
    return storage


def _sweep_stale_profiles(runtime_dir):
    """Delete fallback profiles whose launcher is gone, so they cannot pile up."""
    import shutil
    try:
        for name in os.listdir(runtime_dir):
            if not name.startswith("webview_pid"):
                continue
            try:
                pid = int(name[len("webview_pid"):])
            except ValueError:
                continue
            if pid == os.getpid():
                continue
            # Renaming succeeds only once nothing holds the folder open.
            path = os.path.join(runtime_dir, name)
            gone = path + ".dead"
            try:
                os.rename(path, gone)
            except OSError:
                continue
            shutil.rmtree(gone, ignore_errors=True)
    except Exception:
        pass


def _webview_profile_free(storage):
    """False when another process still holds this WebView2 user-data folder.

    This is the real black window. WebView2 refuses to create its controller
    with 0x800700AA ("The requested resource is in use") when a second process
    opens the same user-data folder, pywebview logs the COM exception and
    carries on, and the window is left painting nothing but background_color
    -- an opaque #06050b rectangle with no error on screen. Captured verbatim:

        [pywebview] WebView2 initialization failed with exception:
          (0x800700AA): The requested resource is in use.
           at Microsoft.Web.WebView2.Core.CoreWebView2Environment
              .<CreateCoreWebView2ControllerAsync>d__21.MoveNext()

    A launcher that was killed rather than closed leaves its msedgewebview2.exe
    children holding the folder for a few seconds, so relaunching promptly --
    exactly what anyone debugging does -- lands in it every time.

    Windows will not rename a directory that has open handles beneath it, so
    renaming it aside and straight back is a reliable probe and needs no
    process enumeration.
    """
    _sweep_stale_profiles(os.path.dirname(storage))
    if not os.path.isdir(storage):
        return True
    probe = storage + ".inuse_probe"
    try:
        os.rename(storage, probe)
    except OSError:
        return False
    try:
        os.rename(probe, storage)
    except OSError:
        pass
    return True


def start_launcher():
    if not _claim_single_instance():
        _focus_existing_launcher()
        print("Navy Games launcher is already running; focused it instead.")
        return

    api = LauncherAPI()

    # file:// URI is more reliable than a raw Windows path for WebView2; a
    # relative/unresolved path has produced blank windows on some elevated runs.
    try:
        from pathlib import Path
        ui_url = Path(UI_INDEX_PATH).resolve().as_uri()
    except Exception:
        ui_url = UI_INDEX_PATH

    window = webview.create_window(
        title=WINDOW_TITLE,
        url=ui_url,
        js_api=api,
        width=1240,
        height=740,
        resizable=True,
        frameless=True,
        easy_drag=True,
        background_color='#06050b'
    )
    api.set_window(window)

    def _on_loaded():
        # If the DOM never mounts (corrupt profile / failed navigate), surface it
        # instead of leaving an opaque black frame.
        try:
            ok = window.evaluate_js(
                "!!(document.getElementById('btnPlayMain') && document.body && "
                "document.body.children.length > 0)"
            )
            if not ok:
                print("Launcher UI failed to mount (#btnPlayMain missing) — "
                      "delete client/runtime/webview and relaunch.")
                return
        except Exception as e:
            print("Launcher UI load check failed: %s" % e)
            return
        # Agent/operator one-shots (polled while this elevated window lives):
        #   navy_kill_client.flag  — stop client.exe (avoids Access Denied from
        #                            a non-elevated shell; Play started elevated)
        #   navy_auto_play.flag    — same path as clicking Play (#btnPlayMain)
        #   navy_restart_play.flag — kill then Play (fresh payload after a push)
        def _consume_kill_client():
            flag = os.path.join(RUNTIME_DIR, "navy_kill_client.flag")
            if not os.path.isfile(flag):
                return False
            try:
                os.remove(flag)
            except Exception:
                return False
            try:
                res = api.master_kill_client()
                print("Launcher kill-client flag: %s" % (res,))
            except Exception as e:
                print("Launcher kill-client flag failed: %s" % e)
            try:
                window.evaluate_js(
                    "(function(){try{"
                    "if(typeof isGameRunning!=='undefined') isGameRunning=false;"
                    "if(typeof isLaunching!=='undefined') isLaunching=false;"
                    "if(typeof setPlayButtonState==='function')"
                    " setPlayButtonState('idle');"
                    "return true;}catch(e){return String(e);}})()"
                )
            except Exception as e:
                print("Launcher kill-client UI reset %s" % e)
            return True

        def _consume_auto_play():
            flag = os.path.join(RUNTIME_DIR, "navy_auto_play.flag")
            if not os.path.isfile(flag):
                return False
            try:
                os.remove(flag)
            except Exception:
                return False
            # If a prior Play left isGameRunning stuck true, clear it so the
            # #btnPlayMain click is not toasted as "already running".
            try:
                window.evaluate_js(
                    "(function(){try{"
                    "if(typeof isGameRunning!=='undefined') isGameRunning=false;"
                    "if(typeof isLaunching!=='undefined') isLaunching=false;"
                    "return true;}catch(e){return String(e);}})()"
                )
            except Exception:
                pass
            try:
                ok = window.evaluate_js(
                    "(function(){try{"
                    "var b=document.getElementById('railBtnCH'); if(b) b.click();"
                    "var p=document.getElementById('btnPlayMain'); if(p) p.click();"
                    "return !!p;}catch(e){return String(e);}})()"
                )
            except Exception as e:
                ok = e
            if ok is True:
                print("Launcher auto-Play requested via navy_auto_play.flag")
                return True
            print("Launcher auto-Play JS result %r; falling back" % (ok,))
            try:
                print("Launcher auto-Play fallback launch_game: %s"
                      % api.launch_game())
            except Exception as e2:
                print("Launcher auto-Play launch_game failed: %s" % e2)
            return True

        def _consume_restart_play():
            flag = os.path.join(RUNTIME_DIR, "navy_restart_play.flag")
            if not os.path.isfile(flag):
                return False
            try:
                os.remove(flag)
            except Exception:
                return False
            print("Launcher restart-Play: kill then Play")
            try:
                api.master_kill_client()
            except Exception as e:
                print("Launcher restart-Play kill %s" % e)
            try:
                window.evaluate_js(
                    "(function(){try{"
                    "if(typeof isGameRunning!=='undefined') isGameRunning=false;"
                    "if(typeof isLaunching!=='undefined') isLaunching=false;"
                    "if(typeof setPlayButtonState==='function')"
                    " setPlayButtonState('idle');"
                    "return true;}catch(e){return String(e);}})()"
                )
            except Exception:
                pass
            # Brief settle so taskkill finishes before launch_game preflight.
            try:
                import time as _t
                _t.sleep(1.5)
            except Exception:
                pass
            try:
                open(os.path.join(RUNTIME_DIR, "navy_auto_play.flag"), "w").write(
                    "restart\n"
                )
            except Exception as e:
                print("Launcher restart-Play flag write %s" % e)
                try:
                    print("Launcher restart-Play direct: %s" % api.launch_game())
                except Exception as e2:
                    print("Launcher restart-Play launch_game failed: %s" % e2)
            return True

        def _auto_play():
            _consume_kill_client()
            _consume_restart_play()
            _consume_auto_play()

        def _poll_auto_play():
            try:
                _consume_kill_client()
                _consume_restart_play()
                _consume_auto_play()
            except Exception as e:
                print("Launcher auto-Play poll %s" % e)
            try:
                import threading
                threading.Timer(1.0, _poll_auto_play).start()
            except Exception:
                pass

        try:
            import threading
            threading.Timer(1.2, _auto_play).start()
            threading.Timer(2.0, _poll_auto_play).start()
        except Exception:
            _auto_play()
    try:
        window.events.loaded += _on_loaded
    except Exception:
        pass

    storage = os.path.join(RUNTIME_DIR, "webview")
    try:
        os.makedirs(RUNTIME_DIR, exist_ok=True)
        storage = _reset_webview_profile_if_needed(storage)
        if not _webview_profile_free(storage):
            # Render on a private profile rather than not at all. Cookies and
            # the remembered window state live in the pinned folder, so this
            # costs only those until the stale holder exits.
            storage = os.path.join(RUNTIME_DIR, "webview_pid%d" % os.getpid())
            print("Launcher WebView profile busy; using %s for this run."
                  % os.path.basename(storage))
    except Exception:
        storage = None
    if storage:
        webview.start(debug=False, private_mode=False, storage_path=storage)
    else:
        webview.start(debug=False)

if __name__ == "__main__":
    start_launcher()
