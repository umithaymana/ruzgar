# Created by Ümit & Gökçenur
"""Masaüstü SSE/WS: Ana motor retrieval durumları + prepare_turn ile tek RAG turu (çift arama yok)."""

from __future__ import annotations

import os
from typing import Any

from ilim_assistant.chat_core import (
    _NO_RAG_MODES,
    _weather_follow_up,
    _weather_intent,
    normalize_mode,
)
from ilim_assistant.main_engine import RetrievalBundle, run_retrieval_with_status_events


def _ilim_rag_for_message(msg: str, question_plan: Any | None = None) -> bool:
    if question_plan is not None and hasattr(question_plan, "use_ilim_rag"):
        return bool(question_plan.use_ilim_rag)
    if isinstance(question_plan, dict):
        return bool(question_plan.get("use_ilim_rag", True))

    local_rag_always_on = os.environ.get("RUZGAR_LOCAL_RAG_ALWAYS_ON", "1").strip().lower()
    if local_rag_always_on in ("0", "false", "no"):
        try:
            from ilim_assistant.intent_router import should_use_ilim_rag

            return should_use_ilim_rag(msg)
        except Exception:
            return True
    return True


def prefetch_main_engine_bundle_for_stream(
    message: str,
    history: list,
    mode: str,
    question_plan: Any | None = None,
) -> tuple[RetrievalBundle, list[dict[str, Any]]]:
    """
    Ana motor (main_engine) retrieval + durum satırları.
    `prepare_turn(..., reuse_main_engine_bundle=bundle)` ile birlikte kullanılmalıdır.
    """
    msg = (message or "").strip()
    empty = RetrievalBundle(
        hits=[],
        suppress_main_web_search=False,
        archive_was_primary=False,
        ilim_citation_tail="",
    )
    if not msg:
        return empty, []
    mode_norm = normalize_mode(mode)
    weather_q = bool(_weather_intent(msg) or _weather_follow_up(msg, history))
    if mode_norm in _NO_RAG_MODES or weather_q:
        return empty, []

    ilim_rag = _ilim_rag_for_message(msg, question_plan)
    if not ilim_rag:
        return empty, []

    try:
        from ilim_assistant.ana_motor_plan import rag_top_k_for_turn

        rag_k_clamped = rag_top_k_for_turn(mode_norm, question_plan)
    except Exception:
        try:
            rag_k = int(os.environ.get("RAG_TOP_K", "2"))
        except ValueError:
            rag_k = 2
        rag_k_clamped = max(1, min(rag_k, 12))

    search_msg = msg
    try:
        from ilim_assistant.ana_motor_plan import rag_search_query_for_turn

        search_msg = rag_search_query_for_turn(msg, question_plan)
    except Exception:
        search_msg = msg

    return run_retrieval_with_status_events(
        msg,
        mode_norm,
        weather_q=weather_q,
        ilim_rag=ilim_rag,
        rag_top_k=rag_k_clamped,
        question_plan=question_plan,
        search_text=search_msg,
    )
