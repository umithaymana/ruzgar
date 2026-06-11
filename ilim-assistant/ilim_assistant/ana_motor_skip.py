# Created by Ümit & Gökçenur
"""Ağır prefetch / agent atlama — 120 sn zaman aşımını önler."""

from __future__ import annotations

from typing import Any


def should_skip_stream_prefetch(
    message: str,
    history: list,
    mode_norm: str,
    *,
    coding: bool = False,
    question_plan: Any | None = None,
) -> bool:
    """`prefetch_main_engine_bundle_for_stream` atlanmalı mı?"""
    if coding or mode_norm in ("programlama", "hafiza", "ses", "uretim", "video", "hizli"):
        return True
    msg = (message or "").strip()
    if not msg:
        return True
    try:
        from ilim_assistant.chat_core import _tarih_intent, _weather_intent, _weather_follow_up

        if _tarih_intent(msg):
            return True
        if _weather_intent(msg) or _weather_follow_up(msg, history):
            return True
    except Exception:
        pass
    try:
        from ilim_assistant.ana_motor_tercume_yurut import is_instant_translate_message

        if is_instant_translate_message(msg):
            return True
    except Exception:
        pass
    try:
        from ilim_assistant.ana_motor_fast import should_bilgi_cloud_fast

        if should_bilgi_cloud_fast(msg, mode_norm, question_plan):
            return True
    except Exception:
        pass
    try:
        from ilim_assistant.ana_motor_plan import (
            is_casual_conversation_turn,
            looks_like_fast_llm_fact_question,
        )

        if is_casual_conversation_turn(msg, mode_norm, question_plan):
            return True
        if looks_like_fast_llm_fact_question(msg):
            return True
    except Exception:
        pass
    try:
        from ilim_assistant.ana_motor_fast import fast_paths_enabled, should_fast_direct_llm

        if fast_paths_enabled() and should_fast_direct_llm(msg, mode_norm, question_plan):
            return True
    except Exception:
        pass
    primary = ""
    if question_plan is not None:
        primary = str(getattr(question_plan, "primary", "") or "").strip().lower()
    if primary in ("gundelik", "islem", "hafiza"):
        return True
    return False


def should_skip_agent_workspace(
    message: str,
    mode_norm: str,
    *,
    coding: bool = False,
    question_plan: Any | None = None,
) -> bool:
    if coding or mode_norm not in ("genel", "uretim", "gelisim"):
        return True
    try:
        from ilim_assistant.chat_core import _tarih_intent

        if _tarih_intent(message):
            return True
    except Exception:
        pass
    if question_plan is not None:
        p = str(getattr(question_plan, "primary", "") or "").strip().lower()
        if p in ("gundelik", "islem"):
            return True
    return False
