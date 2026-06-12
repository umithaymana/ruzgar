# Created by Ümit & Gökçenur
"""
Ana Motor — Faz F: bilgi_hybrid (bulut hız + kısa yerel RAG özeti).
"""

from __future__ import annotations

import os
from typing import Any, Iterator


BILGI_HYBRID_VERSION = "bilgi-hybrid-v1-2026-06-11"


def bilgi_hybrid_enabled() -> bool:
    return os.environ.get("RUZGAR_BILGI_HYBRID", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _hybrid_rag_top_k() -> int:
    try:
        return max(1, min(int(os.environ.get("RUZGAR_BILGI_HYBRID_RAG_K", "3")), 6))
    except ValueError:
        return 3


def fetch_hybrid_rag_snippet(message: str, *, mode_norm: str = "genel") -> str:
    """Hızlı yerel parça özeti — tam retrieval yerine."""
    if not bilgi_hybrid_enabled():
        return ""
    msg = (message or "").strip()
    if len(msg) < 6:
        return ""
    try:
        from ilim_assistant.main_engine import run_retrieval_with_status_events

        bundle, _events = run_retrieval_with_status_events(
            msg,
            mode_norm,
            weather_q=False,
            ilim_rag=True,
            rag_top_k=_hybrid_rag_top_k(),
        )
        hits = list(getattr(bundle, "hits", None) or [])
        if not hits:
            return ""
        parts: list[str] = []
        for h in hits[:_hybrid_rag_top_k()]:
            if not isinstance(h, dict):
                continue
            src = str(h.get("source") or h.get("path") or "")[:80]
            body = str(h.get("text") or h.get("content") or "")[:420].strip()
            if body:
                parts.append(f"- [{src}] {body}")
        if not parts:
            return ""
        return "\n".join(parts)[:1800]
    except Exception:
        return ""


def iter_bilgi_hybrid_reply(
    message: str,
    history: list,
    *,
    mode_norm: str = "genel",
    question_plan: Any | None = None,
) -> Iterator[str]:
    from ilim_assistant.ana_motor_fast import iter_bilgi_cloud_fast_reply

    rag = fetch_hybrid_rag_snippet(message, mode_norm=mode_norm)
    if not rag:
        yield from iter_bilgi_cloud_fast_reply(
            message,
            history,
            mode_norm=mode_norm,
            question_plan=question_plan,
        )
        return

    from ilim_assistant.chat_core import pick_system, prior_messages_for_turn
    from ilim_assistant.llm_brain import stream_ilim_cloud_reply

    primary = ""
    if question_plan is not None:
        primary = str(getattr(question_plan, "primary", "") or "").strip().lower()
    topic = "bilim/tarih" if primary == "bilim" else "bilgi"
    extra = (
        f"\n\n[TALİMAT — {topic.upper()} — HİBRİT]\n"
        "Aşağıdaki yerel kaynak özetini kullan; uydurma yapma. "
        "Türkçe, yapılandırılmış yanıt. Ümit abi'ye hitap et.\n\n"
        f"[Yerel kaynak özeti]\n{rag}\n"
    )
    system = pick_system(False, mode_norm) + extra
    user = (message or "").strip()
    prior = prior_messages_for_turn(history, mode_norm)
    yield from stream_ilim_cloud_reply(
        system,
        user,
        prior[-6:] if prior else None,
    )


def bilgi_hybrid_status() -> dict[str, object]:
    return {
        "enabled": bilgi_hybrid_enabled(),
        "version": BILGI_HYBRID_VERSION,
        "rag_top_k": _hybrid_rag_top_k(),
    }
