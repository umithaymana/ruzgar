# Created by Ümit & Gökçenur
"""Masaüstü SSE/WS: Ana motor retrieval durumları + prepare_turn ile tek RAG turu (çift arama yok)."""

from __future__ import annotations

import os
from typing import Any, Iterator

from ilim_assistant.chat_core import (
    _NO_RAG_MODES,
    _weather_follow_up,
    _weather_intent,
    normalize_mode,
)
from ilim_assistant.main_engine import (
    RetrievalBundle,
    iter_archive_first_decision,
    run_retrieval_with_status_events,
)


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


def _prefetch_params(
    message: str,
    history: list,
    mode: str,
    question_plan: Any | None = None,
) -> tuple[str, str, bool, bool, int, str] | None:
    """(msg, mode_norm, weather_q, ilim_rag, rag_k, search_msg) veya None."""
    msg = (message or "").strip()
    if not msg:
        return None
    mode_norm = normalize_mode(mode)
    weather_q = bool(_weather_intent(msg) or _weather_follow_up(msg, history))
    if mode_norm in _NO_RAG_MODES or weather_q:
        return None
    ilim_rag = _ilim_rag_for_message(msg, question_plan)
    if not ilim_rag:
        return None
    try:
        from ilim_assistant.ana_motor_plan import rag_top_k_for_turn

        rag_k_clamped = rag_top_k_for_turn(mode_norm, question_plan, message=msg)
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
    return msg, mode_norm, weather_q, ilim_rag, rag_k_clamped, search_msg


def iter_main_engine_retrieval_stream(
    message: str,
    history: list,
    mode: str,
    question_plan: Any | None = None,
    upload_ids: list[str] | None = None,
) -> Iterator[dict[str, Any]]:
    """
    Faz E5 — retrieval sırasında canlı status yield; son olay bundle döner.

    Yield:
      - {"type": "status", "phase": str, "text": str}
      - {"type": "retrieval_bundle", "bundle": RetrievalBundle}
    """
    empty = RetrievalBundle(
        hits=[],
        suppress_main_web_search=False,
        archive_was_primary=False,
        ilim_citation_tail="",
    )
    params = _prefetch_params(message, history, mode, question_plan)
    if params is None:
        yield {"type": "retrieval_bundle", "bundle": empty}
        return
    msg, mode_norm, weather_q, ilim_rag, rag_k_clamped, search_msg = params
    bundle: RetrievalBundle | None = None
    for ev in iter_archive_first_decision(
        msg,
        mode_norm=mode_norm,
        weather_q=weather_q,
        ilim_rag=ilim_rag,
        rag_top_k=rag_k_clamped,
        question_plan=question_plan,
        search_text=search_msg,
        upload_ids=upload_ids,
    ):
        if ev.get("kind") == "status":
            yield {
                "type": "status",
                "phase": str(ev.get("phase") or "retrieval"),
                "text": str(ev.get("text") or ""),
            }
        elif ev.get("kind") == "result":
            bundle = ev["bundle"]
    if bundle is None:
        bundle = empty
    yield {"type": "retrieval_bundle", "bundle": bundle}


def prefetch_main_engine_bundle_for_stream(
    message: str,
    history: list,
    mode: str,
    question_plan: Any | None = None,
    upload_ids: list[str] | None = None,
) -> tuple[RetrievalBundle, list[dict[str, Any]]]:
    """
    Ana motor (main_engine) retrieval + durum satırları.
    `prepare_turn(..., reuse_main_engine_bundle=bundle)` ile birlikte kullanılmalıdır.
    """
    empty = RetrievalBundle(
        hits=[],
        suppress_main_web_search=False,
        archive_was_primary=False,
        ilim_citation_tail="",
    )
    events: list[dict[str, Any]] = []
    bundle = empty
    for item in iter_main_engine_retrieval_stream(
        message, history, mode, question_plan=question_plan, upload_ids=upload_ids
    ):
        if item.get("type") == "retrieval_bundle":
            bundle = item.get("bundle") or empty
        elif item.get("type") == "status":
            events.append(item)
    return bundle, events
