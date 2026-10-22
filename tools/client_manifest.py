# coding: utf-8
r"""Pin the client every machine must be running, and check it on every Play.

`game/` is ~11 GB of proprietary NPKs and is not in git, so each developer
supplies their own. Nothing has ever verified that those copies agree, and
twice now that gap cost a whole session: a repair applied to game files here
never reached anyone else, and the next developer booted to a black window.

This ships the *identity* of the known-good client instead of the client.

## What identity means here

Hashing 8.5 GB on every launch is not acceptable, and size alone is a poor
test -- a pack can be larger and still be missing files, because patch layers
replace entries as well as add them (see tools/verify_asset_coverage.py).

So identity is the **entry table**: `<pack>.npk.info_ext` is a zlib-compressed
pickle naming every packed file, and it is what the client resolves lookups
against. Hashing all 144 of them takes ~2.4s. The three base packs that carry
script and data (`data.npk`, `script.npk`, `patch.npk`) are small enough to
hash whole, and they are the ones whose mismatch black-screens the boot.

A pack whose `.info_ext` hash matches is the same pack for every purpose the
client cares about. tools/verify_pack_pairs.py explains why the pack and its
index must travel together.

## Two tiers, because blocking play would be worse than the bug

REQUIRED  data/script/patch packs and their indexes. The client cannot boot
          coherently without these, and a mismatch here is the documented
          black-screen. Verification fails.
CONTENT   every other pack. A developer who never merged the Steam art
          legitimately has fewer, and they can still play. Reported, never
          fatal.

    python tools\client_manifest.py --write     # regenerate (reference PC)
    python tools\client_manifest.py             # verify, human readable
    python tools\client_manifest.py --strict    # exit 1 on CONTENT drift too
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

MANIFEST = Path("client") / "client_manifest.json"
# The packs whose disagreement stops the client booting, not merely thins it.
REQUIRED = ("data.npk", "script.npk", "patch.npk")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def scan(game: Path) -> dict:
    """Fingerprint game/. Whole-file hash for the base packs, index hash otherwise."""
    packs = {}
    for npk in sorted(game.rglob("*.npk")):
        rel = npk.relative_to(game).as_posix()
        row = {"size": npk.stat().st_size}
        idx = npk.with_name(npk.name + ".info_ext")
        if idx.is_file():
            row["index_sha256"] = _sha256(idx)
            row["index_size"] = idx.stat().st_size
        if rel in REQUIRED:
            row["sha256"] = _sha256(npk)
        packs[rel] = row
    return {
        "note": "Identity of the reference client. See tools/client_manifest.py.",
        "required": list(REQUIRED),
        "packs": packs,
    }


def compare(ref: dict, cur: dict) -> dict:
    """Classify every difference. Only `fatal` should ever stop a launch."""
    rp, cp = ref["packs"], cur["packs"]
    required = set(ref.get("required") or REQUIRED)
    fatal, content, extra = [], [], []

    for rel, want in sorted(rp.items()):
        got = cp.get(rel)
        bucket = fatal if rel in required else content
        if got is None:
            bucket.append("MISSING   %s" % rel)
            continue
        # The index is the identity. Compare it before size.
        if want.get("index_sha256") and got.get("index_sha256") \
                and want["index_sha256"] != got["index_sha256"]:
            bucket.append("INDEX     %s (entry table differs from reference)" % rel)
            continue
        if want.get("sha256") and got.get("sha256") and want["sha256"] != got["sha256"]:
            bucket.append("CONTENT   %s (base pack bytes differ)" % rel)
            continue
        if want["size"] != got["size"]:
            # Index matched, so the entry list agrees; ours may just be repacked.
            content.append("SIZE      %s (%d vs reference %d)"
                           % (rel, got["size"], want["size"]))

    for rel in sorted(set(cp) - set(rp)):
        extra.append("EXTRA     %s" % rel)
    return {"fatal": fatal, "content": content, "extra": extra}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true", help="regenerate the manifest")
    ap.add_argument("--strict", action="store_true", help="exit 1 on content drift too")
    ap.add_argument("--game", default=None)
    ap.add_argument("--manifest", default=None)
    args = ap.parse_args(argv)

    root = repo_root()
    game = Path(args.game) if args.game else root / "game"
    mpath = Path(args.manifest) if args.manifest else root / MANIFEST

    if not game.is_dir():
        print("client manifest: %s not present (game/ is supplied per machine) "
              "- skipping" % game)
        return 0

    if args.write:
        data = scan(game)
        mpath.parent.mkdir(parents=True, exist_ok=True)
        mpath.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n",
                         encoding="utf-8")
        print("client manifest written: %d packs -> %s"
              % (len(data["packs"]), mpath))
        return 0

    if not mpath.is_file():
        print("client manifest: %s missing - run --write on the reference PC" % mpath)
        return 0

    ref = json.loads(mpath.read_text(encoding="utf-8"))
    diff = compare(ref, scan(game))
    fatal, content, extra = diff["fatal"], diff["content"], diff["extra"]

    if not fatal and not content:
        print("client matches the reference manifest (%d packs)"
              % len(ref["packs"]))
        if extra:
            print("  %d extra pack(s) beyond the reference - fine" % len(extra))
        return 0

    if fatal:
        print("CLIENT MISMATCH - these stop the client booting coherently:")
        for line in fatal:
            print("  " + line)
        print("Your game/ base packs differ from the reference client. "
              "See docs/FRESH_CLONE_BOOT.md.")
    if content:
        print("client content differs from the reference (%d) - playable, "
              "but you have less/other content:" % len(content))
        for line in content[:20]:
            print("  " + line)
        if len(content) > 20:
            print("  ... and %d more" % (len(content) - 20))
    return 1 if (fatal or (args.strict and content)) else 0


if __name__ == "__main__":
    sys.exit(main())
