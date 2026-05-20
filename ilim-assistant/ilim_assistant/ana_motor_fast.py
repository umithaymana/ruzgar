# Created by Ümit & Gökçenur
"""Ana Motor hızlı yollar — RAG/prefetch atlanır; doğrudan beyin zinciri."""

from __future__ import annotations

import os
from typing import Any, Iterator


def fast_paths_enabled() -> bool:
    return os.environ.get("RUZGAR_FAST_PATHS", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def fast_local_rag_first_enabled() -> bool:
    """Ansiklopedik soruda önce yerel indeks (TDK/tarih/nebula); LLM atlama kapalı."""
    return os.environ.get("RUZGAR_FAST_LOCAL_RAG_FIRST", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def bilgi_gemini_first_enabled() -> bool:
    """Kota dolunca kapalı tutun: Ollama/Groq önce (RUZGAR_FAST_BILGI_GEMINI=0)."""
    return os.environ.get("RUZGAR_FAST_BILGI_GEMINI", "0").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def should_fast_direct_llm(
    message: str,
    mode_norm: str,
    question_plan: Any | None = None,
) -> bool:
    """
    Hafızada yok / ansiklopedik bilgi: ağır prepare_turn yerine doğrudan LLM.
    Yerel Ollama → Groq → Gemini zinciri (RUZGAR_FREE_BRAIN).
    """
    if not fast_paths_enabled():
        return False
    if mode_norm not in ("genel", "uretim", "gelisim"):
        return False
    msg = (message or "").strip()
    if len(msg) < 4 or len(msg) > 500:
        return False

    primary = ""
    use_rag = True
    if question_plan is not None:
        primary = str(getattr(question_plan, "primary", "") or "").strip().lower()
        use_rag = bool(getattr(question_plan, "use_ilim_rag", True))

    try:
        from ilim_assistant.ana_motor_plan import (
            is_casual_conversation_turn,
            looks_like_encyclopedic_fact_question,
        )

        if is_casual_conversation_turn(msg, mode_norm, question_plan):
            return False
        if looks_like_encyclopedic_fact_question(msg):
            if fast_local_rag_first_enabled():
                return False
            return True
    except Exception:
        pass

    if primary == "bilgi" and len(msg) < 220:
        if fast_local_rag_first_enabled():
            return False
        return True
    if primary == "hafiza" and not use_rag:
        return True
    return False


def _try_gemini_fast_bilgi(
    message: str,
    history: list,
    *,
    mode_norm: str,
) -> Iterator[str] | None:
    """Gemini dene; kota/hata metnini kullanıcıya göstermeden None döner (Ollama yedeği)."""
    try:
        from ilim_assistant.gemini_quota_guard import gemini_cooldown_active
        from ilim_assistant.llm_gemini import (
            chat_completion_stream_gemini,
            gemini_configured,
            is_gemini_quota_or_rate_error,
        )

        if gemini_cooldown_active() or not gemini_configured():
            return None
    except Exception:
        return None

    from ilim_assistant.chat_core import pick_system, prior_messages_for_turn

    system = (
        pick_system(False, mode_norm)
        + "\n\n[TALİMAT — HIZLI BILGI / GEMINI]\n"
        "Tek paragraf, Türkçe, net; kaynak uydurma.\n"
    )
    user = (message or "").strip()
    prior = prior_messages_for_turn(history, mode_norm)
    buf = ""
    try:
        for piece in chat_completion_stream_gemini(
            system,
            user,
            prior_messages=prior[-6:] if prior else None,
            max_output_tokens=512,
            temperature=0.35,
        ):
            if piece:
                buf += piece
    except Exception as exc:
        try:
            from ilim_assistant.llm_gemini import format_gemini_user_error, is_gemini_quota_or_rate_error

            err = format_gemini_user_error(exc)
            if is_gemini_quota_or_rate_error(err):
                from ilim_assistant.gemini_quota_guard import mark_gemini_quota_hit

                mark_gemini_quota_hit()
            return None
        except Exception:
            return None

    if not buf.strip() or is_gemini_quota_or_rate_error(buf):
        try:
            from ilim_assistant.gemini_quota_guard import mark_gemini_quota_hit

            mark_gemini_quota_hit()
        except Exception:
            pass
        return None

    def _gen() -> Iterator[str]:
        yield buf

    return _gen()


def iter_fast_direct_llm_reply(
    message: str,
    history: list,
    *,
    mode_norm: str = "genel",
    question_plan: Any | None = None,
) -> Iterator[str]:
    from ilim_assistant.chat_core import pick_system, prior_messages_for_turn
    from ilim_assistant.llm_brain import stream_chat_with_brain

    primary = ""
    if question_plan is not None:
        primary = str(getattr(question_plan, "primary", "") or "").strip().lower()

    try:
        from ilim_assistant.ana_motor_plan import looks_like_encyclopedic_fact_question

        is_bilgi = looks_like_encyclopedic_fact_question(message) or primary == "bilgi"
    except Exception:
        is_bilgi = primary == "bilgi"

    if is_bilgi and bilgi_gemini_first_enabled():
        gem = _try_gemini_fast_bilgi(message, history, mode_norm=mode_norm)
        if gem is not None:
            yield from gem()
            return

    extra = ""
    if primary == "bilgi" or is_bilgi:
        extra = (
            "\n\n[TALİMAT — HIZLI BILGI]\n"
            "Tek paragraf veya 2–4 madde; Türkçe, net, kaynak uydurma. "
            "Emin değilsen kısaca belirt.\n"
        )
    elif primary == "hafiza":
        extra = (
            "\n\n[TALİMAT — HAFIZA SOHBET]\n"
            "Kullanıcı kişisel bir not paylaşıyor olabilir; kısa onay veya net soru.\n"
        )
    else:
        extra = (
            "\n\n[TALİMAT — HIZLI YANIT]\n"
            "Kısa, doğrudan Türkçe yanıt (2–5 cümle).\n"
        )

    system = pick_system(False, mode_norm) + extra
    user = (message or "").strip()
    prior = prior_messages_for_turn(history, mode_norm)
    for piece in stream_chat_with_brain(
        system,
        user,
        prior_messages=prior[-8:] if prior else None,
        mode_norm=mode_norm,
        message=message,
        question_plan=question_plan,
    ):
        if piece:
            yield piece
