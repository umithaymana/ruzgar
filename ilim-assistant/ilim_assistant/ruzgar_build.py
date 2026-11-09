"""Rüzgar build rev — tek kaynak (ruzgar_build_rev.txt)."""
from __future__ import annotations

from pathlib import Path

_FALLBACK = "2026-06-15-ruzgar-programlama-pro-v4"
_REV_FILE = Path(__file__).resolve().parent.parent / "ruzgar_build_rev.txt"


def canonical_build_rev() -> str:
    if _REV_FILE.is_file():
        # utf-8-sig BOM'u yer; PowerShell Set-Content -Encoding utf8 BOM yazar
        raw = _REV_FILE.read_text(encoding="utf-8-sig")
        line = raw.strip().splitlines()
        if line and line[0].strip():
            return line[0].strip().lstrip("\ufeff")
    return _FALLBACK
