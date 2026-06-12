# Created by Ümit & Gökçenur
"""Ana Motor — Faz K/L: sesli tur döngüsü + VAD ince ayarı."""

from __future__ import annotations

import os

SESLI_TUR_FAZ_K_VERSION = "sesli-tur-faz-l-v1-2026-06-11"


def sesli_tur_enabled() -> bool:
    return os.environ.get("RUZGAR_SESLI_TUR_FAZ_K", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _int_env(name: str, default: int, *, lo: int, hi: int) -> int:
    try:
        v = int(os.environ.get(name, str(default)).strip())
    except ValueError:
        v = default
    return max(lo, min(v, hi))


def sesli_tur_vad_config() -> dict[str, int]:
    """Sürekli sesli turda daha kısa sessizlik eşiği (Faz L)."""
    return {
        "silence_end_ms": _int_env("RUZGAR_SESLI_VAD_SILENCE_MS", 620, lo=350, hi=1400),
        "min_rec_ms": _int_env("RUZGAR_SESLI_VAD_MIN_REC_MS", 850, lo=500, hi=2500),
        "quiet_avg": _int_env("RUZGAR_SESLI_VAD_QUIET_AVG", 9, lo=4, hi=18),
        "resume_delay_ms": _int_env("RUZGAR_SESLI_TUR_RESUME_MS", 380, lo=150, hi=1200),
    }


def sesli_tur_status() -> dict[str, object]:
    return {
        "enabled": sesli_tur_enabled(),
        "version": SESLI_TUR_FAZ_K_VERSION,
        "hint": "Konuşunca gönder + sesli yanıt açıkken TTS sonrası mikrofon yeniden dinler",
        "vad": sesli_tur_vad_config(),
    }
