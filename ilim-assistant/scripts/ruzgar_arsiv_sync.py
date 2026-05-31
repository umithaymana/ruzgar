#!/usr/bin/env python3
"""PC arşivini bulut volume'a kopyala (git dışı). rsync veya yerel hedef."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def _default_source() -> Path:
    root = Path(__file__).resolve().parents[1]
    return root / "arsiv"


def _run_rsync(src: Path, dst: str, *, dry_run: bool) -> int:
    exe = shutil.which("rsync")
    if not exe:
        print("rsync bulunamadi — Windows icin WSL/Git Bash veya yerel --target-dir kullanin.")
        return 2
    cmd = [
        exe,
        "-avh",
        "--progress",
        f"{src.as_posix()}/",
        dst if dst.endswith("/") else f"{dst}/",
    ]
    if dry_run:
        cmd.insert(1, "--dry-run")
    print(" ", " ".join(cmd))
    return subprocess.call(cmd)


def _copy_tree(src: Path, dst: Path, *, dry_run: bool) -> int:
    if not src.is_dir():
        print(f"Kaynak yok: {src}")
        return 1
    if dry_run:
        n = sum(1 for _ in src.rglob("*") if _.is_file())
        print(f"[dry-run] {n} dosya kopyalanacak: {src} -> {dst}")
        return 0
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.rglob("*"):
        rel = item.relative_to(src)
        target = dst / rel
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)
    print(f"OK kopyalandi: {src} -> {dst}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Rüzgar arşiv senkron (PC → bulut volume)")
    ap.add_argument("--source", type=Path, default=_default_source(), help="Yerel arşiv kökü")
    ap.add_argument(
        "--target-dir",
        type=Path,
        help="Yerel veya mount edilmiş hedef (örn. Z:/ruzgar-arsiv)",
    )
    ap.add_argument(
        "--rsync",
        metavar="USER@HOST:/path/arsiv/",
        help="Uzak rsync hedefi",
    )
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    src = args.source.resolve()
    if args.rsync:
        return _run_rsync(src, args.rsync, dry_run=args.dry_run)
    if args.target_dir:
        return _copy_tree(src, args.target_dir.resolve(), dry_run=args.dry_run)
    ap.print_help()
    print("\nOrnek:\n  python scripts/ruzgar_arsiv_sync.py --target-dir D:/bulut-arsiv --dry-run")
    print("  python scripts/ruzgar_arsiv_sync.py --rsync user@sunucu:/app/arsiv/")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
