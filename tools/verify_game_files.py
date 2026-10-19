# coding: utf-8
"""Quarantine a `game/Documents/` script+data overlay that black-screens the client.

`game/` is ~11 GB of proprietary NPKs and is not in git, so every machine
supplies its own. That means a bad overlay fixed on one PC is still broken on
everyone else's, which is exactly what happened: commit 43a51f7 reverted the
2023 patch layer here and the next developer still booted to a black window.

## What goes wrong

NeoX mounts `game/Documents/` at depth 0, *before* `game/`, so anything there
wins. `Documents/res/*.npk` is fine -- those are art overlays and the client
falls back for anything they do not carry. `Documents/data.npk`,
`Documents/patch.npk` and `Documents/script.npk` are not: they replace the
client's data and script tables wholesale, and data and script have to agree.

A 2023-era overlay on a 2021 base gives you `staticdata/info_cocos_canvas`
(overlay data) asking for `cocos_const.CANVAS_ID_ESCAPE_LOBBY_GUIDE` (base
script), which does not exist. Recorded on a developer machine, verbatim:

    [STATICDATA]: load module = info_cocos_canvas is error.
    reason is 'module' object has no attribute 'CANVAS_ID_ESCAPE_LOBBY_GUIDE'
    ...
    File "common\\module_cache.py", line 99, in get_canvas_module
    ImportError: No module named None      # module_path : ui.canvas.None
    File "game_init.py", line 257, in start_game
    File "init.py", line 114, in patching

`data_mgr._load` swallows the missing attribute and returns None, so
`get_canvas_module` imports `ui.canvas.None`, `ui_mgr.init()` raises, and
`game_init.start_game()` never returns. `patching` is `render.logic`, so that
raise repeats every frame and `g_state` never advances -- a black window with
no dialog, forever.

## The rule

This is deliberately version-agnostic. We do not detect "the 2023 layer"; the
next bad overlay will have a different stamp. The proven-good configuration is
base-only script and data, so ANY `data/patch/script` NPK under `Documents/`
is renamed aside. Art overlays under `Documents/res/` are left alone.

Renaming, never deleting: the file is someone's 11 GB download, and a rename is
reversible by hand.

    python tools\\verify_game_files.py            # repair, used by the launcher
    python tools\\verify_game_files.py --check    # report only, exit 1 if bad
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Only these three replace script/data wholesale. Documents/res/* art overlays
# are additive and safe -- the 2024 art layer in commit f28fd32 lives there.
OVERLAY_NAMES = ("data.npk", "patch.npk", "script.npk")
SUFFIX = ".disabled_by_launcher"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def content_mode(cli: str | None = None) -> str:
    """'latest' or 'legacy' -- REVIVAL_CLIENT_CONTENT in revival_config.env.

    latest  run the 2024 client content: game/Documents/{data,script,patch}.npk
            (version 1.258623.258360.2407261501, matches the 2024 client.exe)
            are kept ACTIVE -- new outfits, Wardrobe Plan, new events.
    legacy  the old behaviour: those packs are renamed aside and the 2021
            base tables in game/ win.
    """
    if cli in ("latest", "legacy"):
        return cli
    for name in ("revival_config.env", "revival_config.env.example"):
        cfg = repo_root() / name
        if not cfg.is_file():
            continue
        try:
            for line in cfg.read_text(encoding="utf-8-sig", errors="replace").splitlines():
                line = line.strip()
                if line.startswith("REVIVAL_CLIENT_CONTENT="):
                    v = line.split("=", 1)[1].strip().strip('"').strip("'").lower()
                    if v in ("latest", "legacy"):
                        return v
        except OSError:
            pass
        break
    return "legacy"


def _pack_pair_ok(npk_path: Path, info_path: Path) -> bool:
    """A pack and its .info_ext must describe the same entries (else black screen)."""
    import pickle
    import struct
    import zlib
    try:
        with npk_path.open("rb") as fh:
            magic, count = struct.unpack("<4sI", fh.read(8))
        if magic != b"NXPK":
            return False
        _blob, names = pickle.loads(zlib.decompress(info_path.read_bytes()), encoding="latin-1")
        return len(names) == count
    except Exception:
        return False


def enable_latest_logic(game: Path) -> bool:
    """Re-activate the 2024 Documents logic packs that legacy mode renamed aside.

    All three packs (and their .info_ext) must be present and self-consistent;
    a partial set is exactly the mismatched-tables black screen, so in that case
    nothing is touched and the caller falls back to legacy.
    """
    docs = game / "Documents"
    plan = []
    for name in OVERLAY_NAMES:
        # patch.npk is the updater, which the offline payload stubs out. The
        # shipped 2024 patch.npk also carries a stale .info_ext (46 vs 45
        # entries), so it is optional: base patch.npk is used when it fails.
        optional = (name == "patch.npk")
        live, live_info = docs / name, docs / (name + ".info_ext")
        if live.is_file() and live_info.is_file():
            if not _pack_pair_ok(live, live_info):
                if optional:
                    # set it aside so the base updater pack is used
                    quarantine([live, live_info])
                    print("game files: set aside mismatched Documents/%s" % name)
                    continue
                print("game files: Documents/%s does not match its .info_ext" % name)
                return False
            continue
        off, off_info = docs / (name + SUFFIX), docs / (name + ".info_ext" + SUFFIX)
        if not (off.is_file() and off_info.is_file()):
            if optional:
                continue
            print("game files: latest content needs Documents/%s (+ .info_ext); not found" % name)
            return False
        if not _pack_pair_ok(off, off_info):
            if optional:
                print("game files: keeping base %s (2024 copy does not match its .info_ext)" % name)
                continue
            print("game files: Documents/%s%s does not match its .info_ext" % (name, SUFFIX))
            return False
        plan.append((off, live))
        plan.append((off_info, live_info))
    for src, dst in plan:
        if dst.exists():
            print("game files: %s already exists, leaving %s aside" % (dst.name, src.name))
            continue
        src.rename(dst)
        print("game files: re-enabled %s" % dst.name)
    return True


def find_overlays(game: Path, include_logic: bool = True) -> list[Path]:
    """Script/data NPKs directly under game/Documents/, plus their sidecars.
    Also detects hollow stub NPKs (< 2 KB) under game/Documents/res/ that
    shadow real game/res packs wholesale (e.g. 150-byte texture.npk or shader.npk
    which causes missing water/shore textures rendering as bright pink).
    """
    docs = game / "Documents"
    if not docs.is_dir():
        return []
    found = []
    for name in (OVERLAY_NAMES if include_logic else ()):
        npk = docs / name
        if npk.is_file():
            found.append(npk)
            # NeoX reads <name>.info_ext beside the pack; leaving it behind
            # makes the pack look present to some code paths.
            sidecar = docs / (name + ".info_ext")
            if sidecar.is_file():
                found.append(sidecar)
    # Check hollow stub NPKs under Documents/res/
    docs_res = docs / "res"
    if docs_res.is_dir():
        for item in docs_res.glob("*.npk"):
            if item.is_file() and not item.name.endswith(SUFFIX):
                try:
                    if item.stat().st_size < 2048:
                        found.append(item)
                        sidecar = docs_res / (item.name + ".info_ext")
                        if sidecar.is_file():
                            found.append(sidecar)
                except OSError:
                    pass
    return found


def overlay_version(game: Path) -> str | None:
    v = game / "Documents" / "version"
    if v.is_file():
        try:
            return v.read_text(encoding="utf-8", errors="replace").strip()
        except OSError:
            return None
    return None


def find_empty_overlay_dirs(game: Path) -> list[Path]:
    """Empty Documents/res (and data/script/patch) dirs that shadow live packs.

    NeoX mounts Documents/ ahead of game/. A Documents pack replaces the live
    pack wholesale -- there is no per-file fallback. An empty Documents/res
    directory is the worst case of that: the overlay root is present and
    carries nothing. Pack-bearing overlays are left alone (and so is
    res_overlay_kept).
    """
    docs = game / "Documents"
    found = []
    if not docs.is_dir():
        return found
    for name in ("res", "data", "script", "patch"):
        p = docs / name
        if not p.is_dir():
            continue
        try:
            next(p.iterdir())
        except StopIteration:
            found.append(p)
        except OSError:
            continue
    return found


def clear_empty_overlay_dirs(game: Path) -> list[Path]:
    """rmdir empty overlay folders. Never deletes a pack or res_overlay_kept."""
    removed = []
    for p in find_empty_overlay_dirs(game):
        try:
            p.rmdir()
            removed.append(p)
        except OSError:
            continue
    return removed


def clear_repair_flags(game: Path) -> bool:
    """Drop leftover Repair Client flags so the next boot does not exit.

    repair_confirm_panel writes force_cmp_files then game3d.exit(). The next
    Play then starts cmp_files and can die before lobby_ready. Never
    quarantines any pack -- only rewrites game/patch_dat booleans.
    """
    path = game / "patch_dat"
    if not path.is_file():
        return False
    try:
        import json
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return False
    if not isinstance(data, dict):
        return False
    changed = False
    if data.get("force_cmp_files"):
        data["force_cmp_files"] = False
        changed = True
    if data.get("force_cleanup"):
        data["force_cleanup"] = 0
        changed = True
    if data.get("repair_by"):
        data["repair_by"] = ""
        changed = True
    if not changed:
        return False
    path.write_text(json.dumps(data), encoding="utf-8")
    return True


def quarantine(paths: list[Path]) -> list[tuple[Path, Path]]:
    moved = []
    for p in paths:
        dst = p.with_name(p.name + SUFFIX)
        n = 1
        while dst.exists():
            dst = p.with_name("%s%s.%d" % (p.name, SUFFIX, n))
            n += 1
        try:
            p.rename(dst)
            moved.append((p, dst))
        except OSError as e:
            print("game files: cannot quarantine %s (%s) -- close client to repair" % (p.name, e))
    return moved


def repair_zip_flags(game: Path) -> list[str]:
    """Fix NPK records that claim lz4 (zip_flag=2) but hold raw bytes.

    A repack of res/ui_patch.npk swapped in custom patch-screen PNGs but kept
    the ORIGINAL record flags: 22 entries say "lz4, decompress me" while their
    block is a plain PNG with clen == olen. The engine lz4-decodes PNG bytes
    into a buffer sized olen -- garbage at best, a heap overrun at worst. That
    is the 0xC0000005 / 0xC0000374 / 0xC0000409 crash the moment the patch
    screen loads (and "File not found: ui_patch/.../image_patching_progress.png").

    An lz4 block is never exactly as long as its output, so zip_flag==2 with
    clen==olen is always this mistake. Only the 28-byte index records (and the
    identical copy inside .info_ext) are rewritten; no data block moves.
    """
    import pickle
    import struct
    import zlib
    rec = struct.Struct("<6I2H")
    fixed = []
    roots = [game / "res", game / "Documents" / "res"]
    for root in roots:
        if not root.is_dir():
            continue
        for npk in root.rglob("*.npk"):
            try:
                with npk.open("r+b") as fh:
                    head = fh.read(24)
                    if len(head) < 24 or head[:4] != b"NXPK":
                        continue
                    count, _a, _b, _mode, idx = struct.unpack_from("<5I", head, 4)
                    if count <= 0 or count > 2000000:
                        continue
                    fh.seek(idx)
                    old = fh.read(count * rec.size)
                    if len(old) != count * rec.size:
                        continue
                    table = bytearray(old)
                    n_bad = 0
                    for i in range(count):
                        r = list(rec.unpack_from(table, i * rec.size))
                        # sign, offset, clen, olen, zcrc, crc, zip_flag, file_flag
                        if r[6] == 2 and r[2] == r[3] and r[2] > 0:
                            r[6] = 0
                            rec.pack_into(table, i * rec.size, *r)
                            n_bad += 1
                    if not n_bad:
                        continue
                    fh.seek(idx)
                    fh.write(bytes(table))
                info = npk.with_name(npk.name + ".info_ext")
                if info.is_file():
                    try:
                        blob, names = pickle.loads(zlib.decompress(info.read_bytes()), encoding="latin-1")
                        raw = blob.encode("latin-1") if isinstance(blob, str) else blob
                        if raw == old:
                            new_blob = bytes(table) if isinstance(blob, bytes) else bytes(table).decode("latin-1")
                            info.write_bytes(zlib.compress(pickle.dumps([new_blob, names], protocol=2)))
                    except Exception as e:
                        print("game files: %s index not updated (%s)" % (info.name, e))
                fixed.append("%s (%d records)" % (npk.relative_to(game).as_posix(), n_bad))
            except OSError as e:
                print("game files: cannot check %s (%s) -- close the client" % (npk.name, e))
    return fixed


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="report only; exit 1 when an overlay is present")
    ap.add_argument("--game", default=None, help="game directory (default: <repo>/game)")
    ap.add_argument("--content", choices=("latest", "legacy"), default=None,
                    help="override REVIVAL_CLIENT_CONTENT from revival_config.env")
    args = ap.parse_args(argv)
    mode = content_mode(args.content)

    game = Path(args.game) if args.game else repo_root() / "game"
    if not game.is_dir():
        print("game files: %s not present (supplied per machine) - skipping" % game)
        return 0

    overlays = find_overlays(game, include_logic=(mode == "legacy"))
    empty_dirs = find_empty_overlay_dirs(game)
    if args.check:
        if not overlays and not empty_dirs:
            print("game files OK: no script/data overlay under game/Documents")
            return 0
        ver = overlay_version(game)
        if overlays:
            print("game files: %d script/data overlay file(s) under game/Documents%s"
                  % (len(overlays), (" (version %s)" % ver) if ver else ""))
            for p in overlays:
                print("  %s" % p.name)
            print("These replace the client's script and data tables and will "
                  "black-screen the boot. Run: python tools\\verify_game_files.py")
        if empty_dirs:
            print("game files: %d empty Documents overlay dir(s) that shadow live packs"
                  % len(empty_dirs))
            for p in empty_dirs:
                print("  %s/" % p.name)
        return 1

    for line in repair_zip_flags(game):
        print("game files: fixed raw-data-marked-lz4 records in %s" % line)

    if clear_repair_flags(game):
        print("game files: cleared leftover Repair Client flags in patch_dat")

    for p in clear_empty_overlay_dirs(game):
        print("game files: removed empty overlay dir %s/" % p.name)

    if mode == "latest":
        if enable_latest_logic(game):
            print("game files: LATEST client content active (Documents version %s)"
                  % (overlay_version(game) or "?"))
        else:
            print("game files: latest content incomplete -> falling back to legacy tables")
            mode = "legacy"

    overlays = find_overlays(game, include_logic=(mode == "legacy"))
    if not overlays:
        print("game files OK (%s content)" % mode)
        return 0

    ver = overlay_version(game)
    print("game files: %d script/data overlay file(s) under game/Documents%s"
          % (len(overlays), (" (version %s)" % ver) if ver else ""))
    for p in overlays:
        print("  %s" % p.name)

    for src, dst in quarantine(overlays):
        print("  quarantined -> %s" % dst.name)
    print("game files repaired: base game/ script and data now win. "
          "Rename the files back by hand if you ever need that overlay.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
