#!/usr/bin/env python3
"""Blok E47 — projects/smoke-autonomy-* ve *-site bench artıklarını temizle."""
from __future__ import annotations

import argparse
import shutil
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

WORKSPACE = _ROOT.parent
_PREFIXES = ("smoke-autonomy-",)


def _is_bench_artifact(name: str) -> bool:
    low = name.lower()
    if any(low.startswith(p) for p in _PREFIXES):
        return True
    if low.startswith("smoke-autonomy-") and low.endswith("-site"):
        return True
    # faz99 static companion: smoke-autonomy-12345-site
    if "-site" in low and "smoke-autonomy" in low:
        return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser(description="Eski Faz99 bench klasörlerini sil")
    ap.add_argument("--days", type=int, default=7, help="Bu günden eski (mtime)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--workspace",
        default="",
        help="Repo kökü (varsayılan: ilim-assistant üstü)",
    )
    args = ap.parse_args()
    root = Path(args.workspace.strip() or str(WORKSPACE)).resolve()
    projects = root / "projects"
    if not projects.is_dir():
        print(f"projects/ yok: {projects}")
        return 0

    cutoff = time.time() - max(1, int(args.days)) * 86400
    removed: list[str] = []
    for child in sorted(projects.iterdir()):
        if not child.is_dir():
            continue
        if not _is_bench_artifact(child.name):
            continue
        try:
            mtime = child.stat().st_mtime
        except OSError:
            continue
        if mtime >= cutoff:
            continue
        removed.append(child.name)
        if args.dry_run:
            print(f"[dry-run] silinecek: {child}")
        else:
            shutil.rmtree(child, ignore_errors=True)
            print(f"silindi: {child.name}")

    print(f"toplam: {len(removed)} klasör")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
