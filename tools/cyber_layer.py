# coding: utf-8
"""Cyber Royale texture store (standard library only).

Cyber Royale is the Classic BR island re-skinned as a future city, chosen per
match from its own box in the main lobby (next to Battle Royale).  The game
reads every resource through C_file's loaders, and the FIRST loader is the
loose folder <game>/Documents/res/compatibility -- ahead of every pack
(live probe 2026-11-13: a file put there is served instead of the packed one
at once, and removing it brings the pack copy back).  So no pack is touched:

  * tools/build_cyber_layer.py makes <game>/reawakening/cyber_royale.zip
    (resource path -> DDS, deflated, plus a night sky variant).
  * prepare() (the launcher runs it at Play, while the game is closed)
    extracts it once into <game>/reawakening/cyber_royale_store/.
  * the payload (lobby_full_payload.py, _lf_cyber_set) renames those files
    into Documents/res/compatibility when the Cyber Royale box is clicked and
    back when the Battle Royale box is clicked -- instant, same volume.

Same map, layout, collision, vehicles and loot as Battle Royale.

An earlier build of this feature patched the packs themselves (a launcher
switch).  remove_legacy() takes that version off again; it reuses
tools/snow_layer.py's pack code as an independent module instance.

    python tools\\cyber_layer.py status  [game_dir]
    python tools\\cyber_layer.py prepare [game_dir]
    python tools\\cyber_layer.py sync    [game_dir] [runtime_dir]
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import sys
import zipfile

_HERE = os.path.dirname(os.path.abspath(__file__))
LAYER_DIR = "reawakening"
ZIP_NAME = "cyber_royale.zip"
STORE = "cyber_royale_store"
ACTIVE = "_active.json"         # written by the payload while Cyber is on
NIGHT_PREFIX = "_night/"


def _game_dir(arg=None):
    if arg:
        return os.path.abspath(arg)
    return os.path.join(os.path.dirname(_HERE), "game")


def paths(game):
    d = os.path.join(game, LAYER_DIR)
    return {
        "zip": os.path.join(d, ZIP_NAME),
        "store": os.path.join(d, STORE),
        "compat": os.path.join(game, "Documents", "res", "compatibility"),
    }


# ---- the player city pack (2026-11-14: Heist Royale ships to players) ------
# A player install gets the whole Cyber store (models, scenes, textures, the
# night variants, plus extra/ art the payload reads) as ONE zip on the dist
# repo's "cyber-city-live" release. game/ is outside the updater's ALLOW list,
# so this file (which the updater ships) moves it:
#   fetch  background, any time: download the zip if the remote one is newer
#          (resumable, sha256 checked) -> <game>/reawakening/cyber_city_pack.zip
#   sync   at Play, game closed: install a downloaded pack into the store
# Dev checkouts (AGENTS.md) build the store themselves and never install a pack.
#   pack   (dev) python tools/cyber_layer.py pack -> cyber_city_pack.zip + .json
PACK_URL = os.environ.get("CYBER_CITY_PACK_URL",
                          "https://github.com/navygames/cyber-hunter-dist/releases/download/cyber-city-live/")
PACK_NAME = "cyber_city_pack.zip"
PACK_META = "cyber_city_pack.json"
PACK_STAMP = "pack_version.json"        # in the store: the pack it was installed from
_REPO = os.path.dirname(_HERE)
# art the payload reads from <store>/extra/ on player installs (dev: client/frida)
PACK_EXTRA = [("client/frida/cyber_royale/heist_loading.jpg", "extra/heist_loading.jpg"),
              ("client/frida/cyber_royale/text_lobby_main_mode_item_cyber.png", "extra/text_lobby_main_mode_item_cyber.png"),
              ("client/frida/cyber_royale/image_lobby_main_mode_item_cyber_title.png",
               "extra/image_lobby_main_mode_item_cyber_title.png"),
              ("client/frida/cyber_royale/image_lobby_main_mode_item_cyber_title_zh.png",
               "extra/image_lobby_main_mode_item_cyber_title_zh.png")]


def _dev_checkout():
    return os.path.isfile(os.path.join(_REPO, "AGENTS.md"))


def _sha256(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def build_pack(game=None):
    """(dev) Zip the whole Cyber store into reawakening/cyber_city_pack.zip + its
    .json (version, sha256, size). Files the payload moved into the
    compatibility folder are read from there."""
    game = _game_dir(game)
    p = paths(game)
    man = _store_manifest(p["store"])
    if not man or not man.get("files"):
        raise SystemExit("cyber pack: no store manifest - build the city first")
    rels = set(man.get("files") or ()) | set((man.get("night") or {}).values())
    act = {}
    try:
        with open(os.path.join(p["store"], ACTIVE), "r", encoding="utf-8") as fh:
            act = (json.load(fh) or {}).get("moved") or {}
    except Exception:
        act = {}
    live_of = {src: rel for rel, src in act.items()}
    out = os.path.join(game, LAYER_DIR, PACK_NAME)
    tmp = out + ".tmp"
    n = 0
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        zf.writestr("manifest.json", json.dumps(man, indent=1))
        for rel in sorted(rels):
            src = os.path.join(p["store"], *rel.split("/"))
            if not os.path.isfile(src) and rel in live_of:
                src = os.path.join(p["compat"], *live_of[rel].split("/"))
            if not os.path.isfile(src):
                src = os.path.join(p["compat"], *rel.split("/"))
            if not os.path.isfile(src):
                raise SystemExit("cyber pack: missing %s (in neither the store nor compatibility)" % rel)
            zf.write(src, rel)
            n += 1
        for src_rel, dst in PACK_EXTRA:
            zf.write(os.path.join(_REPO, *src_rel.split("/")), dst)
        cine = os.path.join(_REPO, "client", "frida", "assets", "cine")
        for fn in sorted(os.listdir(cine)):
            if fn.endswith(".png"):
                zf.write(os.path.join(cine, fn), "extra/cine/" + fn)
    os.replace(tmp, out)
    sha = _sha256(out)
    meta = {"version": sha[:16], "sha256": sha, "size": os.path.getsize(out), "files": n,
            "layer_id": man.get("layer_id"), "name": PACK_NAME}
    with open(os.path.join(game, LAYER_DIR, PACK_META), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=1)
    print("cyber pack: %d files, %.0f MB, version %s -> %s" % (n, meta["size"] / 1e6, meta["version"], out))
    return meta


def _installed_pack(store):
    try:
        with open(os.path.join(store, PACK_STAMP), "r", encoding="utf-8") as fh:
            return json.load(fh) or {}
    except Exception:
        return {}


def fetch(game=None, url=None):
    """Download the remote city pack when it differs from the installed / already
    downloaded one. Resumable (.part + HTTP Range); sha256 checked."""
    import urllib.request
    game = _game_dir(game)
    if _dev_checkout():
        print("cyber pack: dev checkout - not fetching")
        return 0
    base = (url or PACK_URL).rstrip("/") + "/"
    if not base.lower().startswith("https://"):
        raise SystemExit("cyber pack: the pack URL must be https")
    ua = {"User-Agent": "CyberHunterLauncher/2.0 (cyber pack)"}
    with urllib.request.urlopen(urllib.request.Request(base + PACK_META, headers=ua), timeout=30) as r:
        meta = json.loads(r.read().decode("utf-8"))
    p = paths(game)
    if _installed_pack(p["store"]).get("sha256") == meta["sha256"]:
        print("cyber pack: up to date (%s)" % meta["version"])
        return 0
    d = os.path.join(game, LAYER_DIR)
    os.makedirs(d, exist_ok=True)
    out = os.path.join(d, PACK_NAME)
    if os.path.isfile(out) and os.path.getsize(out) == int(meta["size"]) and _sha256(out) == meta["sha256"]:
        _mark_for_launcher(d)
        print("cyber pack: %s already downloaded - installs at the next Play" % meta["version"])
        return 0
    part = out + ".part"
    lock = out + ".lock"                        # one download at a time (Play may start another)
    try:
        if os.path.isfile(lock) and __import__("time").time() - os.path.getmtime(lock) > 3 * 3600:
            os.remove(lock)                     # stale: a crashed / killed download
        os.close(os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
    except OSError:
        print("cyber pack: another download is running")
        return 0
    try:
        return _fetch_body(meta, base, ua, d, out, part)
    finally:
        try:
            os.remove(lock)
        except OSError:
            pass


def _fetch_body(meta, base, ua, d, out, part):
    import urllib.request
    have = os.path.getsize(part) if os.path.isfile(part) else 0
    if have > int(meta["size"]):
        os.remove(part)
        have = 0
    hdr = dict(ua)
    if have:
        hdr["Range"] = "bytes=%d-" % have
    with urllib.request.urlopen(urllib.request.Request(base + meta.get("name", PACK_NAME), headers=hdr),
                                timeout=60) as r:
        if have and getattr(r, "status", 200) != 206:
            have = 0                                   # server ignored the range: start over
        with open(part, "ab" if have else "wb") as fh:
            while True:
                b = r.read(1 << 20)
                if not b:
                    break
                fh.write(b)
    if os.path.getsize(part) != int(meta["size"]) or _sha256(part) != meta["sha256"]:
        os.remove(part)
        raise SystemExit("cyber pack: download corrupt - will retry next time")
    os.replace(part, out)
    with open(os.path.join(d, PACK_META), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=1)
    _mark_for_launcher(d)
    print("cyber pack: downloaded %s (%.0f MB) - installs at the next Play" % (meta["version"], meta["size"] / 1e6))
    return 1


def _mark_for_launcher(d):
    """The launcher in players' hands (CyberHunterLauncher.exe) runs
    `cyber_layer.py sync` at Play only when reawakening/cyber_royale.zip exists.
    An EMPTY file of that name is the marker; prepare() ignores it."""
    zp = os.path.join(d, ZIP_NAME)
    if not os.path.isfile(zp):
        open(zp, "wb").close()


def install_pack(game=None):
    """Game closed: put a downloaded pack in place as the store."""
    game = _game_dir(game)
    if _dev_checkout():
        return 0
    p = paths(game)
    d = os.path.join(game, LAYER_DIR)
    zp = os.path.join(d, PACK_NAME)
    if not os.path.isfile(zp):
        return 0
    try:
        with open(os.path.join(d, PACK_META), "r", encoding="utf-8") as fh:
            meta = json.load(fh)
    except Exception:
        meta = {}
    sha = meta.get("sha256") or _sha256(zp)
    if _installed_pack(p["store"]).get("sha256") == sha:
        return 0
    deactivate(game)
    tmp = p["store"] + ".tmp"
    if os.path.isdir(tmp):
        shutil.rmtree(tmp)
    with zipfile.ZipFile(zp) as zf:
        zf.extractall(tmp)
    with open(os.path.join(tmp, PACK_STAMP), "w", encoding="utf-8") as fh:
        json.dump({"sha256": sha, "version": meta.get("version", sha[:16])}, fh)
    if os.path.isdir(p["store"]):
        shutil.rmtree(p["store"])
    os.replace(tmp, p["store"])
    os.remove(zp)                                      # the store holds it now (saves ~0.5 GB)
    print("cyber pack: installed %s" % meta.get("version", sha[:16]))
    return 1


def _manifest_from_zip(zp):
    with zipfile.ZipFile(zp) as zf:
        return json.loads(zf.read("manifest.json").decode("utf-8"))


def _store_manifest(store):
    try:
        with open(os.path.join(store, "manifest.json"), "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def deactivate(game=None):
    """Move any Cyber textures left in the compatibility folder back into the
    store (the game crashed or was closed while Cyber Royale was on)."""
    game = _game_dir(game)
    p = paths(game)
    act_p = os.path.join(p["store"], ACTIVE)
    try:
        with open(act_p, "r", encoding="utf-8") as fh:
            act = json.load(fh) or {}
    except Exception:
        return 0
    n = 0
    for rel, src in (act.get("moved") or {}).items():
        live = os.path.join(p["compat"], *rel.split("/"))
        back = os.path.join(p["store"], *src.split("/"))
        if os.path.isfile(live):
            os.makedirs(os.path.dirname(back), exist_ok=True)
            if os.path.isfile(back):
                os.remove(live)
            else:
                os.replace(live, back)
            n += 1
    os.remove(act_p)
    print("cyber royale: %d textures put back in the store" % n)
    return n


def prepare(game=None):
    """Extract cyber_royale.zip into the store when it is new or changed."""
    game = _game_dir(game)
    p = paths(game)
    if not os.path.isfile(p["zip"]):
        print("cyber royale: %s not built - run tools\\build_cyber_layer.py" % p["zip"])
        return 0
    if os.path.getsize(p["zip"]) == 0:          # player city pack marker (_mark_for_launcher)
        return 0
    deactivate(game)
    man = _manifest_from_zip(p["zip"])
    have = _store_manifest(p["store"])
    if have and have.get("layer_id") == man.get("layer_id") and all(
            os.path.isfile(os.path.join(p["store"], *f.split("/"))) for f in man.get("files", [])):
        return 0
    tmp = p["store"] + ".tmp"
    if os.path.isdir(tmp):
        shutil.rmtree(tmp)
    n = 0
    with zipfile.ZipFile(p["zip"]) as zf:
        for info in zf.infolist():
            if info.filename.endswith("/"):
                continue
            dst = os.path.join(tmp, *info.filename.split("/"))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with zf.open(info) as src, open(dst, "wb") as out:
                shutil.copyfileobj(src, out, 1 << 20)
            n += 1
    # model / scene assets (tools/build_cyber_assets.py, listed under "assets"
    # in the store manifest) are not in the zip: carry them over
    assets = list((have or {}).get("assets") or [])
    kept = []
    for f in assets:
        src = os.path.join(p["store"], *f.split("/"))
        if not os.path.isfile(src) or f in set(man.get("files", [])):
            continue
        dst = os.path.join(tmp, *f.split("/"))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        kept.append(f)
    if kept:
        mp = os.path.join(tmp, "manifest.json")
        with open(mp, "r", encoding="utf-8") as fh:
            nm = json.load(fh)
        nm["files"] = sorted(set(nm.get("files", [])) | set(f for f in kept if not f.startswith(NIGHT_PREFIX)))
        nm["assets"] = sorted(kept)
        an = {rp: src for rp, src in ((have or {}).get("asset_night") or {}).items() if src in kept}
        if an:                                   # day / night kit textures (build_cyber_assets.py)
            nm["night"] = dict(nm.get("night") or {}, **an)
            nm["asset_night"] = an
        with open(mp, "w", encoding="utf-8") as fh:
            json.dump(nm, fh, indent=1)
        print("cyber royale: %d model/scene assets kept" % len(kept))
    if os.path.isdir(p["store"]):
        shutil.rmtree(p["store"])
    os.replace(tmp, p["store"])
    print("cyber royale: store ready (%d files)" % n)
    return n


# ---- the earlier pack-patching version -------------------------------------

def _legacy_impl():
    spec = importlib.util.spec_from_file_location("_cyber_pack_impl", os.path.join(_HERE, "snow_layer.py"))
    impl = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(impl)
    impl.LAYER_ZIP = "cyber_city.zip"
    impl.STATE = "cyber_city_state.json"
    impl.BAK = ".orig_cyber"
    impl.print = lambda *a, **k: print(*(str(x).replace("snow layer", "cyber city (old pack layer)")
                                         for x in a), **k)
    return impl


def legacy_installed(game=None):
    return os.path.isfile(os.path.join(_game_dir(game), LAYER_DIR, "cyber_city_state.json"))


def remove_legacy(game=None):
    """Restore the packs if the old always-on Cyber City layer is installed."""
    game = _game_dir(game)
    if not legacy_installed(game):
        return False
    return _legacy_impl().remove(game)


def sync(game=None, runtime=None, mode=None):
    """Launcher / weather_packs entry point (game closed): old pack layer off,
    Cyber Royale store ready."""
    game = _game_dir(game)
    remove_legacy(game)
    install_pack(game)                     # player installs: a downloaded city pack
    return prepare(game)


def status(game=None):
    game = _game_dir(game)
    p = paths(game)
    man = _manifest_from_zip(p["zip"]) if os.path.isfile(p["zip"]) else None
    st = _store_manifest(p["store"])
    print("cyber royale: built=%s files=%d store=%s active=%s legacy_pack_layer=%s" % (
        bool(man), len(man.get("files", [])) if man else 0,
        bool(st and man and st.get("layer_id") == man.get("layer_id")),
        os.path.isfile(os.path.join(p["store"], ACTIVE)), legacy_installed(game)))


def client_running():
    if not sys.platform.startswith("win"):
        return False
    try:
        import subprocess
        out = subprocess.check_output(["tasklist", "/FI", "IMAGENAME eq client.exe"],
                                      creationflags=0x08000000, text=True, errors="ignore")
        return "client.exe" in out.lower()
    except Exception:
        return False


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    cmd = args[0] if args else "status"
    g = args[1] if len(args) > 1 else None
    if cmd in ("prepare", "sync") and client_running() and "--force" not in sys.argv:
        print("cyber royale: client.exe is running - close the game first")
        sys.exit(1)
    if cmd == "prepare":
        prepare(g)
    elif cmd == "sync":
        sync(g)
    elif cmd == "fetch":                   # background download (game may be running)
        if "--log" in sys.argv:            # started hidden by the game: no console to print to
            lp = sys.argv[sys.argv.index("--log") + 1]
            sys.stdout = sys.stderr = open(lp, "a", encoding="utf-8")
            print("---- %s" % __import__("time").strftime("%Y-%m-%d %H:%M:%S"))
        try:
            fetch(g)
        except SystemExit:
            raise
        except Exception as e:             # offline / GitHub down: try again next Play
            print("cyber pack: fetch failed (%s)" % e)
            sys.exit(2)
        sys.exit(0)
    elif cmd == "pack":                    # dev: build the player city pack
        build_pack(g)
        sys.exit(0)
    status(g)
