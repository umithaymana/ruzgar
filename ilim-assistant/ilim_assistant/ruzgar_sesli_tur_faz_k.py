# Created by Ümit & Gökçenur
"""Ana Motor — Faz K: sesli tur döngüsü (TTS bitince mikrofon)."""

from __future__ import annotations

import os

SESLI_TUR_FAZ_K_VERSION = "sesli-tur-faz-k-v1-2026-06-11"


def sesli_tur_enabled() -> bool:
    return os.environ.get("RUZGAR_SESLI_TUR_FAZ_K", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def sesli_tur_status() -> dict[str, object]:
    return {
        "enabled": sesli_tur_enabled(),
        "version": SESLI_TUR_FAZ_K_VERSION,
        "hint": "Konuşunca gönder + sesli yanıt açıkken TTS sonrası mikrofon yeniden dinler",
    }
