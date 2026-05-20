# Created by Ümit & Gökçenur
"""Gemini kota / hız sınırı — geçici soğuma ve zincirden atlama."""

from __future__ import annotations

import os
import time
from pathlib import Path

_COOLDOWN_UNTIL: float = 0.0


def _cooldown_sec() -> int:
    try:
        return max(60, int(os.environ.get("RUZGAR_GEMINI_COOLDOWN_SEC", "2700")))
    except ValueError:
        return 2700


def gemini_cooldown_active() -> bool:
    """Kota vurulduktan sonra Gemini'yi zincirden çıkar (varsayılan 45 dk)."""
    if os.environ.get("RUZGAR_GEMINI_COOLDOWN", "1").strip().lower() in (
        "0",
        "false",
        "no",
    ):
        return False
    return time.monotonic() < _COOLDOWN_UNTIL


def mark_gemini_quota_hit() -> None:
    global _COOLDOWN_UNTIL
    _COOLDOWN_UNTIL = time.monotonic() + float(_cooldown_sec())
    try:
        stamp = Path(os.environ.get("TEMP", ".")) / "ruzgar-gemini-cooldown.txt"
        stamp.write_text(str(_COOLDOWN_UNTIL), encoding="utf-8")
    except OSError:
        pass


def _restore_cooldown_from_disk() -> None:
    global _COOLDOWN_UNTIL
    try:
        stamp = Path(os.environ.get("TEMP", ".")) / "ruzgar-gemini-cooldown.txt"
        if stamp.is_file():
            _COOLDOWN_UNTIL = max(_COOLDOWN_UNTIL, float(stamp.read_text(encoding="utf-8").strip()))
    except (OSError, ValueError):
        pass


_restore_cooldown_from_disk()
