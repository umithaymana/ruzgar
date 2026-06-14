# Created by Ümit & Gökçenur
"""Ana Motor — Faz AJ1: arşiv önizlemeden soruyu yazı alanına yapıştırma."""

from __future__ import annotations

import os
from typing import Any

FAZ_AJ_ARSIV_YAPISTIR_VERSION = "arsiv-yapistir-faz-aj-v1-2026-06-13"


def arsiv_yapistir_enabled() -> bool:
    return os.environ.get("RUZGAR_ARSIV_YAPISTIR", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def resolve_archive_insert_text(item: dict[str, Any] | None) -> dict[str, Any]:
    """Tek arşiv satırından yazı alanına gidecek metin."""
    if not arsiv_yapistir_enabled():
        return {"ok": False, "enabled": False, "version": FAZ_AJ_ARSIV_YAPISTIR_VERSION}
    if not item or not isinstance(item, dict):
        return {"ok": False, "error": "oge_yok", "version": FAZ_AJ_ARSIV_YAPISTIR_VERSION}
    user = str(item.get("user_snippet") or item.get("user") or "").strip()
    assistant = str(item.get("assistant_snippet") or item.get("assistant") or "").strip()
    if not user:
        return {"ok": False, "error": "bos_soru", "version": FAZ_AJ_ARSIV_YAPISTIR_VERSION}
    insert = user
    hint = assistant[:120] if assistant else ""
    return {
        "ok": True,
        "enabled": True,
        "version": FAZ_AJ_ARSIV_YAPISTIR_VERSION,
        "insert_text": insert[:500],
        "assistant_preview": hint,
        "mode": item.get("mode"),
    }


def arsiv_yapistir_status() -> dict[str, Any]:
    return {
        "enabled": arsiv_yapistir_enabled(),
        "version": FAZ_AJ_ARSIV_YAPISTIR_VERSION,
        "hint_tr": "Arşiv satırına tıklayınca soru yazı alanına gelir",
    }
