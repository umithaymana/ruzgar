# Created by Ümit & Gökçenur
"""Ana Motor — Faz AI2: sohbet aramasında arşiv önizleme satırları."""

from __future__ import annotations

import os
from typing import Any

FAZ_AI_ARSIV_ONIZLEME_VERSION = "arsiv-onizleme-faz-ai-v1-2026-06-13"


def arsiv_onizleme_enabled() -> bool:
    return os.environ.get("RUZGAR_ARSIV_ONIZLEME", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def build_archive_search_preview(
    query: str,
    *,
    limit: int = 4,
    mode: str | None = None,
) -> dict[str, Any]:
    """Arama kutusu altında gösterilecek arşiv önizlemesi."""
    if not arsiv_onizleme_enabled():
        return {
            "ok": False,
            "enabled": False,
            "version": FAZ_AI_ARSIV_ONIZLEME_VERSION,
            "preview_tr": "",
            "items": [],
            "count": 0,
        }
    q = (query or "").strip()
    if len(q) < 2:
        return {
            "ok": True,
            "enabled": True,
            "version": FAZ_AI_ARSIV_ONIZLEME_VERSION,
            "preview_tr": "",
            "items": [],
            "count": 0,
        }
    try:
        from ilim_assistant.ana_motor_sohbet_gecmis import search_chat_history

        data = search_chat_history(q, limit=limit, mode=mode)
    except Exception as exc:
        return {
            "ok": False,
            "enabled": True,
            "error": str(exc)[:160],
            "version": FAZ_AI_ARSIV_ONIZLEME_VERSION,
            "items": [],
            "count": 0,
        }

    items = list(data.get("items") or [])
    lines: list[str] = []
    for i, row in enumerate(items[:limit], 1):
        u = str(row.get("user_snippet") or row.get("user") or "").strip()
        a = str(row.get("assistant_snippet") or row.get("assistant") or "").strip()
        if not u:
            continue
        tail = f" → {a[:72]}…" if len(a) > 72 else (f" → {a}" if a else "")
        lines.append(f"{i}. {u[:96]}{tail}")

    preview = "\n".join(lines)
    if not preview:
        preview = "Arşivde eşleşme yok — ekranda aramayı da deneyin"

    return {
        "ok": True,
        "enabled": True,
        "version": FAZ_AI_ARSIV_ONIZLEME_VERSION,
        "query": q,
        "count": len(items),
        "items": items,
        "preview_tr": preview[:900],
        "summary_tr": f"{len(items)} arşiv eşleşmesi" if items else "Arşivde yok",
    }


def arsiv_onizleme_status() -> dict[str, Any]:
    return {
        "enabled": arsiv_onizleme_enabled(),
        "version": FAZ_AI_ARSIV_ONIZLEME_VERSION,
    }
