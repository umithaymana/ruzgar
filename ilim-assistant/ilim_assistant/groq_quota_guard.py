# Created by Ümit & Gökçenur
"""Groq kota / hız sınırı — geçici soğuma ve zincirden atlama."""

from __future__ import annotations

import os
import time
from pathlib import Path

_COOLDOWN_UNTIL: float = 0.0
_LEGACY_MONOTONIC_STAMP_MAX = 10_000_000.0


def _cooldown_sec() -> int:
    try:
        return max(120, int(os.environ.get("RUZGAR_GROQ_COOLDOWN_SEC", "900")))
    except ValueError:
        return 900


def groq_cooldown_active() -> bool:
    if os.environ.get("RUZGAR_GROQ_COOLDOWN", "1").strip().lower() in (
        "0",
        "false",
        "no",
    ):
        return False
    return time.time() < _COOLDOWN_UNTIL


def mark_groq_quota_hit() -> None:
    global _COOLDOWN_UNTIL
    _COOLDOWN_UNTIL = max(_COOLDOWN_UNTIL, time.time() + float(_cooldown_sec()))
    try:
        stamp = Path(os.environ.get("TEMP", ".")) / "ruzgar-groq-cooldown.txt"
        stamp.write_text(str(_COOLDOWN_UNTIL), encoding="utf-8")
    except OSError:
        pass


def _restore_cooldown_from_disk() -> None:
    global _COOLDOWN_UNTIL
    try:
        stamp = Path(os.environ.get("TEMP", ".")) / "ruzgar-groq-cooldown.txt"
        if not stamp.is_file():
            return
        val = float(stamp.read_text(encoding="utf-8").strip())
        now = time.time()
        if val < _LEGACY_MONOTONIC_STAMP_MAX:
            stamp.unlink(missing_ok=True)
            return
        if val > now:
            _COOLDOWN_UNTIL = max(_COOLDOWN_UNTIL, val)
        else:
            stamp.unlink(missing_ok=True)
    except (OSError, ValueError):
        pass


_restore_cooldown_from_disk()
