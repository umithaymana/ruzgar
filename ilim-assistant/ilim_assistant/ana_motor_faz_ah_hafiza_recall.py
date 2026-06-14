# Created by Ümit & Gökçenur
"""Ana Motor — Faz AH1: sohbet arşivi hafıza durumu + geri çağırma özeti."""

from __future__ import annotations

import os
from typing import Any

FAZ_AH_HAFIZA_RECALL_VERSION = "hafiza-recall-faz-ah-v1-2026-06-13"


def hafiza_recall_enabled() -> bool:
    return os.environ.get("RUZGAR_HAFIZA_RECALL", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def build_chat_memory_status() -> dict[str, Any]:
    """jsonl arşiv + hatırla köprüsü durumu."""
    if not hafiza_recall_enabled():
        return {
            "ok": True,
            "enabled": False,
            "version": FAZ_AH_HAFIZA_RECALL_VERSION,
            "summary_tr": "Sohbet hafıza durumu kapalı",
        }
    try:
        from ilim_assistant.ana_motor_sohbet_gecmis import chat_history_stats

        stats = chat_history_stats()
    except Exception as exc:
        return {
            "ok": False,
            "enabled": True,
            "error": str(exc)[:200],
            "version": FAZ_AH_HAFIZA_RECALL_VERSION,
        }

    n = int(stats.get("stored_turns") or 0)
    if not stats.get("enabled"):
        summary = "Sohbet arşivi kapalı (RUZGAR_ANA_CHAT_HISTORY=0)"
    elif n <= 0:
        summary = "Arşiv boş — konuşmalar kaydedildikçe «hatırla» ve geçmiş sorular çalışır"
    else:
        preview = str(stats.get("last_user_preview") or "").strip()
        tail = f" · son: {preview[:48]}…" if len(preview) > 48 else (f" · son: {preview}" if preview else "")
        summary = f"{n} tur arşivde{tail}"

    return {
        "ok": True,
        "enabled": True,
        "version": FAZ_AH_HAFIZA_RECALL_VERSION,
        "summary_tr": summary[:280],
        "stored_turns": n,
        "recall_active": bool(stats.get("recall_active")),
        "last_mode": stats.get("last_mode"),
        "max_store": stats.get("max_store"),
    }


def preview_recall_query(query: str, *, limit: int = 5) -> dict[str, Any]:
    """Arama kutusu için arşiv önizlemesi."""
    if not hafiza_recall_enabled():
        return {"ok": False, "enabled": False, "items": [], "count": 0}
    q = (query or "").strip()
    if len(q) < 2:
        return {"ok": True, "enabled": True, "items": [], "count": 0}
    try:
        from ilim_assistant.ana_motor_sohbet_gecmis import search_chat_history

        data = search_chat_history(q, limit=limit)
        items = list(data.get("items") or [])[:limit]
        return {
            "ok": True,
            "enabled": True,
            "count": len(items),
            "items": items,
            "version": FAZ_AH_HAFIZA_RECALL_VERSION,
        }
    except Exception as exc:
        return {"ok": False, "enabled": True, "error": str(exc)[:160], "items": []}


def hafiza_recall_status() -> dict[str, Any]:
    panel = build_chat_memory_status()
    return {
        "enabled": hafiza_recall_enabled(),
        "version": FAZ_AH_HAFIZA_RECALL_VERSION,
        "summary_tr": panel.get("summary_tr"),
        "stored_turns": panel.get("stored_turns"),
        "recall_active": panel.get("recall_active"),
    }
