# Created by Ümit & Gökçenur
"""Gemini kota / hız sınırı — geçici soğuma ve zincirden atlama."""

from __future__ import annotations

import os
import time
from pathlib import Path

# Mutlak bitiş zamanı (time.time() — disk ve bellek aynı birim)
_COOLDOWN_UNTIL: float = 0.0

# Eski sürüm monotonic() yazıyordu; yeniden başlatınca saatler/günler süren sahte soğuma
_LEGACY_MONOTONIC_STAMP_MAX = 10_000_000.0


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
    return time.time() < _COOLDOWN_UNTIL


def mark_gemini_quota_hit() -> None:
    global _COOLDOWN_UNTIL
    # Aynı oturumda tekrar API çağrısı yapılmasın — anında soğuma
    _COOLDOWN_UNTIL = max(_COOLDOWN_UNTIL, time.time() + float(_cooldown_sec()))
    try:
        stamp = Path(os.environ.get("TEMP", ".")) / "ruzgar-gemini-cooldown.txt"
        stamp.write_text(str(_COOLDOWN_UNTIL), encoding="utf-8")
    except OSError:
        pass


def _restore_cooldown_from_disk() -> None:
    global _COOLDOWN_UNTIL
    try:
        stamp = Path(os.environ.get("TEMP", ".")) / "ruzgar-gemini-cooldown.txt"
        if not stamp.is_file():
            return
        raw = stamp.read_text(encoding="utf-8").strip()
        val = float(raw)
        now = time.time()
        if val < _LEGACY_MONOTONIC_STAMP_MAX:
            # Eski monotonic damgası — süresiz sahte soğuma; temizle
            stamp.unlink(missing_ok=True)
            return
        if val > now:
            _COOLDOWN_UNTIL = max(_COOLDOWN_UNTIL, val)
        else:
            stamp.unlink(missing_ok=True)
    except (OSError, ValueError):
        pass


_restore_cooldown_from_disk()
