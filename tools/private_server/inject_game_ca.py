#!/usr/bin/env python3
"""Append private patch CA to game ca_certificates.crt (embedded Python SSL bundle)."""
from __future__ import annotations

import argparse
import hashlib
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CA_PATH = ROOT / "certs" / "ca.cert.pem"
MARKER = b"# CyberHunter private patch CA"
DEFAULT_GAME_DIRS = [
    ROOT.parent.parent / "game",
    ROOT.parent.parent,
    Path(r"C:\Program Files (x86)\Cyber Hunter"),
]


def cert_fingerprint(pem: bytes) -> str:
    body = b"".join(line for line in pem.splitlines() if not line.startswith(b"-----"))
    return hashlib.sha256(body).hexdigest()[:16]


def inject_bundle(bundle_path: Path, ca_pem: bytes, dry_run: bool = False) -> str:
    if not bundle_path.is_file():
        return "missing"

    original = bundle_path.read_bytes()
    fp = cert_fingerprint(ca_pem)
    if ca_pem.strip() in original:
        return "already_present"
    if MARKER in original:
        # A CA from an older server install is in the bundle. The old check
        # stopped at the marker and never added the new CA, so the game's
        # embedded Python kept rejecting the server after a CA change.
        head, _sep, rest = original.partition(MARKER)
        end = rest.find(b"-----END CERTIFICATE-----")
        if end != -1:
            rest = rest[end + len(b"-----END CERTIFICATE-----"):]
            original = head.rstrip() + b"\n" + rest.lstrip(b"\r\n")

    backup = bundle_path.with_suffix(bundle_path.suffix + ".bak")
    if not dry_run and not backup.exists():
        try:
            shutil.copy2(bundle_path, backup)
        except OSError as exc:
            return f"permission_denied: {exc}"

    addition = b"\n" + MARKER + b"\n" + ca_pem.strip() + b"\n"
    if dry_run:
        return "would_inject"

    try:
        bundle_path.write_bytes(original.rstrip() + addition)
    except OSError as exc:
        return f"permission_denied: {exc}"
    return f"injected (backup: {backup.name}, fp={fp})"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("game_dirs", nargs="*", type=Path, help="game roots (default: mirror + Program Files)")
    args = parser.parse_args()

    if not CA_PATH.is_file():
        print(f"CA missing: {CA_PATH} (run generate_certs.py first)")
        return 1

    ca_pem = CA_PATH.read_bytes()
    dirs = args.game_dirs or DEFAULT_GAME_DIRS
    any_ok = False
    for game_dir in dirs:
        bundle = Path(game_dir) / "ca_certificates.crt"
        result = inject_bundle(bundle, ca_pem, dry_run=args.dry_run)
        print(f"{bundle}: {result}")
        if result.startswith(("injected", "already_present", "would_inject")):
            any_ok = True

    return 0 if any_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
