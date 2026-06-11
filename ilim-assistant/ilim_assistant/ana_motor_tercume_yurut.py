# Created by Ümit & Gökçenur
"""Ana Motor Faz W1 — kısa metin çeviri (sohbet içi backend yürütme)."""

from __future__ import annotations

import os
from typing import Any


def tercume_instant_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_TERCUME_INSTANT", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _max_chars() -> int:
    try:
        return max(80, min(int(os.environ.get("RUZGAR_ANA_TERCUME_INSTANT_MAX_CHARS", "500")), 2000))
    except ValueError:
        return 500


def is_instant_translate_message(message: str) -> bool:
    """Kısa sohbet içi çeviri — RAG/LLM turu atlanabilir."""
    if not tercume_instant_enabled():
        return False
    from ilim_assistant.motorlar.tercume_faz74 import classify_tercume_intent
    from ilim_assistant.ruzgar_motor_kernel import INTENT_DO

    intent = classify_tercume_intent((message or "").strip(), mode_norm="tercume")
    return intent.get("intent") == INTENT_DO and intent.get("reason") == "translate_text"


def maybe_run_instant_translate(message: str) -> dict[str, Any]:
    """Kısa çeviri metnini LLM ile üret; panel açmadan sohbete döner."""
    if not tercume_instant_enabled():
        return {"ok": True, "handled": False, "reason": "tercume_instant_disabled"}

    from ilim_assistant.motorlar.tercume_faz74 import (
        classify_tercume_intent,
        ensure_kernel_registered,
        extract_translate_text,
        lang_label,
        parse_language_pair,
    )
    from ilim_assistant.ruzgar_motor_kernel import INTENT_DO

    ensure_kernel_registered()
    raw = (message or "").strip()
    if not raw:
        return {"ok": True, "handled": False, "reason": "empty"}

    intent = classify_tercume_intent(raw, mode_norm="tercume")
    if intent.get("intent") != INTENT_DO or intent.get("reason") != "translate_text":
        return {"ok": True, "handled": False, "reason": "not_translate"}

    body = str(intent.get("text") or extract_translate_text(raw) or "").strip()
    if not body:
        return {"ok": True, "handled": False, "reason": "no_text"}

    limit = _max_chars()
    if len(body) > limit:
        return {
            "ok": True,
            "handled": False,
            "reason": "text_too_long",
            "char_count": len(body),
            "limit": limit,
        }

    src = str(intent.get("src") or "auto")
    tgt = str(intent.get("tgt") or "en")

    try:
        from ilim_assistant.motorlar.tercume_atolye import translate_chunk

        tr = translate_chunk(body, src_lang=src, tgt_lang=tgt, cloud_first=True)
    except Exception as exc:
        return {"ok": False, "handled": False, "error": str(exc)[:200]}

    if not tr.get("ok") or not tr.get("text"):
        return {
            "ok": False,
            "handled": False,
            "error": str(tr.get("error") or tr.get("hint_tr") or "Çeviri üretilemedi.")[:200],
        }

    translated = str(tr.get("text") or "").strip()
    reply = f"Ümit abi, **{lang_label(src)} → {lang_label(tgt)}** çeviri:\n\n{translated}"
    return {
        "ok": True,
        "handled": True,
        "reply": reply,
        "channel": "tercume_instant",
        "src": src,
        "tgt": tgt,
        "char_count": len(body),
    }
