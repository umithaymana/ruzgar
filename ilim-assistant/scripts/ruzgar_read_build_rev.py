#!/usr/bin/env python3
"""Tek kaynak build rev — launcher ve UI senkronu."""
from __future__ import annotations

import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_REV_FILE = _ROOT / "ruzgar_build_rev.txt"
_FALLBACK = "2026-06-15-ruzgar-programlama-pro-v4"


def read_build_rev() -> str:
    if _REV_FILE.is_file():
        line = _REV_FILE.read_text(encoding="utf-8").strip().splitlines()[0].strip()
        if line:
            return line
    ds = _ROOT / "desktop_server.py"
    if ds.is_file():
        m = re.search(r'"rev"\s*:\s*"([^"]+)"', ds.read_text(encoding="utf-8"))
        if m:
            return m.group(1).strip()
    return _FALLBACK


def main() -> int:
    sys.stdout.write(read_build_rev())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
