# Created by Ümit & Gökçenur
"""Ana Motor — Faz AG1: sohbet paneli + sunucu geçmişi temizleme."""

from __future__ import annotations

import os
from typing import Any

FAZ_AG_SOHBET_TEMIZ_VERSION = "sohbet-temiz-faz-ag-v1-2026-06-13"


def sohbet_temiz_enabled() -> bool:
    return os.environ.get("RUZGAR_SOHBET_TEMIZ", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def clear_ana_motor_chat_history(
    *,
    mode: str | None = None,
    session_id: str | None = None,
    all_modes: bool = False,
) -> dict[str, Any]:
    """UI sohbet temizle — yalnızca istekle jsonl arşivini sıfırla (varsayılan: dokunma)."""
    if not sohbet_temiz_enabled():
        return {
            "ok": False,
            "enabled": False,
            "version": FAZ_AG_SOHBET_TEMIZ_VERSION,
            "error": "sohbet_temiz_kapali",
        }
    try:
        from ilim_assistant.ana_motor_sohbet_gecmis import clear_chat_history

        if all_modes or not (mode or "").strip():
            out = clear_chat_history()
        else:
            out = clear_chat_history(mode=mode, session_id=session_id)
        return {
            **out,
            "enabled": True,
            "version": FAZ_AG_SOHBET_TEMIZ_VERSION,
        }
    except Exception as exc:
        return {
            "ok": False,
            "enabled": True,
            "error": str(exc)[:200],
            "version": FAZ_AG_SOHBET_TEMIZ_VERSION,
        }


def sohbet_temiz_status() -> dict[str, Any]:
    return {
        "enabled": sohbet_temiz_enabled(),
        "version": FAZ_AG_SOHBET_TEMIZ_VERSION,
        "api": "POST /api/ana-motor/chat-history/clear",
    }
