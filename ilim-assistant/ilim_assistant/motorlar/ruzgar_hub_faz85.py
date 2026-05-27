# Created by Ümit & Gökçenur
"""
Rüzgar — Faz 85: Hub cila (U10).

- Hızır delege: pazar tara → tam mod (Faz 84 düzeltmesi ile)
- Video arama önbelleği kalıcı (.ruzgar/video_search_last.json)
"""

from __future__ import annotations

import os
from typing import Any

FAZ85_VERSION = "ruzgar-hub-faz85-v1-2026-05-26"


def _enabled() -> bool:
    return os.environ.get("RUZGAR_HUB_FAZ85", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz85_enabled() -> bool:
    return _enabled()


def hub_delegate_directive_extra(target: str, message: str) -> str:
    """Hub delege mesajına ek not."""
    if not _enabled():
        return ""
    mid = (target or "").strip().lower()
    if mid == "hizir":
        return (
            "[FAZ 85 — HIZIR DELEGE]\n"
            "Bu tur Hızır operasyon merkezi bağlamıyla yanıtlanır; "
            "pazar/ürün taraması için OPERASYON MERKEZİ verisini kullan.\n"
        )
    if mid == "video":
        from ilim_assistant.motorlar.video_faz84 import wants_video_search

        if wants_video_search(message):
            return (
                "[FAZ 85 — VİDEO ARA]\n"
                "Liste geldiyse kullanıcı «N numarayı indir» diyebilir; "
                "önbellek sunucu yeniden başlasa da kalır.\n"
            )
    return ""


def enrich_health_build(build: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(build or {})
    out["hub_faz85"] = faz85_enabled()
    return out
