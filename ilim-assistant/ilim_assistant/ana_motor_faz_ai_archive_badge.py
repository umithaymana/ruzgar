# Created by Ümit & Gökçenur
"""Ana Motor — Faz AI1: jsonl arşivinden gelen yanıta «Arşivden» rozeti."""

from __future__ import annotations

import os
import re
from typing import Any

FAZ_AI_ARCHIVE_BADGE_VERSION = "archive-badge-faz-ai-v1-2026-06-13"


def archive_badge_enabled() -> bool:
    return os.environ.get("RUZGAR_ARCHIVE_BADGE", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _recall_kind(message: str) -> str:
    try:
        from ilim_assistant.ana_motor_sohbet_gecmis import (
            _extract_recall_terms,
            _looks_like_generic_past_summary,
            _looks_like_question_list_request,
            _normalize_query,
        )
    except Exception:
        return "generic"
    if _looks_like_question_list_request(message):
        return "question_list"
    terms = _extract_recall_terms(message)
    blob = _normalize_query(message)
    if (
        not _looks_like_generic_past_summary(message)
        and (terms or re.search(r"(?:hakkında|hakkinda)\s+konu", blob, re.I))
    ):
        return "topic"
    if _looks_like_generic_past_summary(message):
        return "summary"
    return "generic"


def resolve_archive_recall_turn(
    message: str,
    *,
    client_history: list | None = None,
) -> dict[str, Any] | None:
    """Arşiv geri çağırma turu — yanıt + rozet meta."""
    if not archive_badge_enabled():
        return None
    try:
        from ilim_assistant.ana_motor_sohbet_gecmis import try_past_conversation_reply
    except Exception:
        return None
    reply = try_past_conversation_reply(message, client_history=client_history)
    if not reply:
        return None
    kind = _recall_kind(message)
    labels = {
        "topic": "Arşivden · konu",
        "question_list": "Arşivden · soru listesi",
        "summary": "Arşivden · özet",
        "generic": "Arşivden",
    }
    return {
        "ok": True,
        "reply": reply,
        "source": "chat_archive",
        "recall_kind": kind,
        "badge_tr": labels.get(kind, "Arşivden"),
        "version": FAZ_AI_ARCHIVE_BADGE_VERSION,
    }


def archive_badge_status() -> dict[str, Any]:
    return {
        "enabled": archive_badge_enabled(),
        "version": FAZ_AI_ARCHIVE_BADGE_VERSION,
        "badge_tr": "Arşivden",
    }
