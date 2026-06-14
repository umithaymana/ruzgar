# Created by Ümit & Gökçenur
"""Ana Motor — Faz AK2: arşiv turunu sohbet balonu olarak hatırlat."""

from __future__ import annotations

import os
from typing import Any

FAZ_AK_ARSIV_HATIRLAT_VERSION = "arsiv-hatirlat-faz-ak-v1-2026-06-13"


def arsiv_hatirlat_enabled() -> bool:
    return os.environ.get("RUZGAR_ARSIV_HATIRLAT", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def build_archive_recall_card(item: dict[str, Any] | None) -> dict[str, Any]:
    """Arşiv satırından sohbet balonu içeriği."""
    if not arsiv_hatirlat_enabled():
        return {"ok": False, "enabled": False, "version": FAZ_AK_ARSIV_HATIRLAT_VERSION}
    if not item or not isinstance(item, dict):
        return {"ok": False, "error": "oge_yok", "version": FAZ_AK_ARSIV_HATIRLAT_VERSION}
    user = str(item.get("user_snippet") or item.get("user") or "").strip()
    assistant = str(item.get("assistant_snippet") or item.get("assistant") or "").strip()
    if not user and not assistant:
        return {"ok": False, "error": "bos", "version": FAZ_AK_ARSIV_HATIRLAT_VERSION}
    body_lines = [
        "**Arşivden hatırlatma**",
        "",
        f"**Sen:** {user[:240]}" if user else "",
        f"**Rüzgar:** {assistant[:360]}" if assistant else "",
        "",
        "*(Bu balon jsonl arşivinden okundu — kalıcı hafıza korunur.)*",
    ]
    body = "\n".join(line for line in body_lines if line).strip()
    return {
        "ok": True,
        "enabled": True,
        "version": FAZ_AK_ARSIV_HATIRLAT_VERSION,
        "body_md": body,
        "badge_tr": "Arşivden · hatırlat",
        "recall_kind": "archive_card",
    }


def arsiv_hatirlat_status() -> dict[str, Any]:
    return {
        "enabled": arsiv_hatirlat_enabled(),
        "version": FAZ_AK_ARSIV_HATIRLAT_VERSION,
        "hint_tr": "Arşiv satırında Hatırlat → sohbete balon",
    }
