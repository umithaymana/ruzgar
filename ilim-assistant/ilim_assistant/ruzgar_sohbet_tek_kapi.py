# Created by Ümit & Gökçenur
"""
Sohbet tutarlılığı — tek selam / anlık kapı (Faz T1).

Politika B (hız + tutarlılık):
- Saf kısa selam/teşekkür → tek kanonik metin (fast_lane + plan aynı kaynak).
- Sohbet Önce / Faz91: saf selamı LLM'e zorlamaz; doğal muhabbet LLM'de kalır.
- Boş oturumda «dün konuştuk» yok.

Kapat: RUZGAR_SOHBET_TEK_KAPI=0 (eski dağınık yollar — yalnız acil geri alma).
"""

from __future__ import annotations

import os
import re
import unicodedata
from typing import Any

VERSION = "sohbet-tek-kapi-v1-2026-11-20"


def tek_kapi_enabled() -> bool:
    return os.environ.get("RUZGAR_SOHBET_TEK_KAPI", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def _fold(s: str) -> str:
    t = unicodedata.normalize("NFKD", s or "")
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    for a, b in (
        ("ı", "i"),
        ("ğ", "g"),
        ("ü", "u"),
        ("ş", "s"),
        ("ö", "o"),
        ("ç", "c"),
    ):
        t = t.replace(a, b)
    return re.sub(r"\s+", " ", t).strip()


def history_has_prior_turns(history: list | None, *, min_msgs: int = 2) -> bool:
    """Gerçek önceki tur var mı — boş oturumda süreklilik uydurma."""
    if not history:
        return False
    n = 0
    for m in history:
        if not isinstance(m, dict):
            continue
        role = str(m.get("role") or "")
        content = str(m.get("content") or "").strip()
        if role in ("user", "assistant") and content:
            n += 1
            if n >= min_msgs:
                return True
    return False


def looks_like_pure_greeting(message: str) -> bool:
    raw = (message or "").strip()
    if not raw or len(raw) > 80:
        return False
    if len(raw.split()) > 6:
        return False
    low = _fold(raw)
    if any(
        x in low
        for x in (
            "nedir",
            "kimdir",
            "anlat",
            "acikla",
            "kod",
            "yaz",
            "test",
            "proje",
            "kac ",
            "ne zaman",
        )
    ):
        return False
    return bool(
        re.search(
            r"^(?:selam|merhaba|slm|hey|gunaydin|iyi\s+aksam|iyi\s+geceler)"
            r"(?:\s+(?:ruzgar|abi|ümit|umit))?[\s!.?]*$",
            low,
        )
        or re.fullmatch(
            r"(?:selam|merhaba|gunaydin)(?:\s+ruzgar)?",
            low,
        )
    )


def canonical_selam_reply(
    message: str,
    *,
    history: list | None = None,
    has_prior_session: bool | None = None,
) -> str:
    """Tek selam metni — fast_lane ve ana_motor_plan aynı kaynağı kullanır."""
    from ilim_assistant.ruzgar_umed_kurallari import (
        SELAM_RUZGAR,
        SELAM_STANDART,
        SELAM_WITH_RESUME,
    )

    prior = (
        bool(has_prior_session)
        if has_prior_session is not None
        else history_has_prior_turns(history)
    )
    low = _fold(message or "")
    named = bool(re.search(r"\bruzgar\b", low))
    if prior:
        return SELAM_WITH_RESUME
    if named:
        return SELAM_RUZGAR
    return SELAM_STANDART


def allow_instant_greeting_shortcut(
    message: str,
    mode_norm: str,
    *,
    question_plan: Any | None = None,
) -> bool:
    """
    True → şablon selam serbest (Faz91 skip etmesin).
    Sohbet Önce açıkken bile saf selam anlık kalır.
    """
    if not tek_kapi_enabled():
        return False
    if mode_norm not in ("genel", "uretim", "gelisim"):
        return False
    if looks_like_pure_greeting(message):
        return True
    try:
        from ilim_assistant.ana_motor_plan import looks_like_instant_social_ack

        if looks_like_instant_social_ack(message):
            return True
    except Exception:
        pass
    return False


def public_meta() -> dict[str, Any]:
    return {
        "version": VERSION,
        "enabled": tek_kapi_enabled(),
        "policy": "B-fast-lane-canonical",
        "brain_note": "RUZGAR_SOHBET_TARZ uslup; zincir = Faz90/umed",
    }
