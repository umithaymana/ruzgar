# Created by Ümit & Gökçenur
"""
Ümit abi kesin emri — cevap öncelik sırası ve süre bütçesi.

Güncelleme 2026-05-27: Ümit abi onayı ile genel sohbet local-first (Faz 90).
Ollama (denge/hizli) hafıza/RAG sonrası birincil LLM; Gemini/Groq yedek.

Sıra (genel sohbet):
  1) Kendi hafızası (eğitim rafı + ruzgar_genel_hafiza)
  2) Yerel hafıza (RAG / arşiv / indeks)
  3) Yerel Ollama (denge / hizli) — Faz 90
  4) Gemini
  5) Groq
  6) Web (kısa, ikincil — süre kalırsa)
  → Süre dolunca veya zincir boşsa: «bulamadım, öğret»
"""

from __future__ import annotations

import contextvars
import os
import re
import time
from typing import Any

from ilim_assistant.ruzgar_umed_kurallari import MISS_PHRASE

EMRI_VERSION = "umed-cevap-emri-v2-2026-05-27"
EMRI_FROZEN = True

_DEFAULT_BUDGET_SEC = 15.0
_ILIM_BUDGET_SEC = 22.0

_turn_deadline: contextvars.ContextVar[float | None] = contextvars.ContextVar(
    "umed_turn_deadline", default=None
)

PRIORITY_LABELS = (
    "kendi_hafiza",
    "yerel_hafiza",
    "ollama_yerel",
    "gemini",
    "groq",
    "web_ikincil",
    "ogret_bekle",
)


def umed_emri_enabled() -> bool:
    """Kesin emir açık (varsayılan: açık). Kapatmak için RUZGAR_UMED_CEVAP_EMRI=0."""
    if not EMRI_FROZEN:
        return False
    return os.environ.get("RUZGAR_UMED_CEVAP_EMRI", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def umed_emri_applies(*, mode_norm: str, coding_mode: bool) -> bool:
    if not umed_emri_enabled():
        return False
    if coding_mode or mode_norm == "programlama":
        return False
    return mode_norm in ("genel", "uretim", "gelisim", "hafiza")


def is_ilim_heavy_question(message: str) -> bool:
    low = (message or "").strip().lower()
    if len(low) < 8:
        return False
    markers = (
        "nedir",
        "kimdir",
        "nasıl",
        "neden",
        "tarih",
        "hadis",
        "ayet",
        "kuran",
        "mektubat",
        "tasavvuf",
        "felsefe",
        "bilim",
        "açıkla",
        "acikla",
        "anlat",
    )
    return any(m in low for m in markers)


def turn_budget_sec(message: str = "", *, mode_norm: str = "genel") -> float:
    try:
        from ilim_assistant.ruzgar_dogal_sohbet_faz91 import turn_budget_for_message

        ext = turn_budget_for_message(message, mode_norm)
        if ext is not None:
            return ext
    except Exception:
        pass
    if is_ilim_heavy_question(message):
        try:
            return float(os.environ.get("RUZGAR_UMED_ILIM_BUDGET_SEC", str(_ILIM_BUDGET_SEC)))
        except ValueError:
            return _ILIM_BUDGET_SEC
    try:
        return float(os.environ.get("RUZGAR_UMED_BUDGET_SEC", str(_DEFAULT_BUDGET_SEC)))
    except ValueError:
        return _DEFAULT_BUDGET_SEC


def set_turn_deadline(deadline_monotonic: float | None) -> None:
    _turn_deadline.set(deadline_monotonic)


def get_turn_deadline() -> float | None:
    return _turn_deadline.get()


def begin_turn_budget(message: str, *, mode_norm: str = "genel") -> float:
    budget = turn_budget_sec(message, mode_norm=mode_norm)
    deadline = time.monotonic() + budget
    set_turn_deadline(deadline)
    return budget


def remaining_sec() -> float:
    d = get_turn_deadline()
    if d is None:
        return 9999.0
    return max(0.0, d - time.monotonic())


def deadline_exceeded() -> bool:
    return remaining_sec() <= 0.0


def umed_miss_reply() -> str:
    return MISS_PHRASE


def brain_chain_ids_for_emri() -> list[str]:
    """Genel sohbet LLM zinciri — Faz 90 local-first (Ollama -> Gemini -> Groq)."""
    try:
        from ilim_assistant.ruzgar_genel_faz90 import build_genel_brain_chain_ids

        return build_genel_brain_chain_ids()
    except Exception:
        pass
    ids = ["gemini", "groq"]
    try:
        from ilim_assistant.llm_ollama import ollama_reachable

        if ollama_reachable():
            ids = ["denge", "hizli"] + ids
    except Exception:
        pass
    return ids


def should_skip_fast_bypass_paths() -> bool:
    """Hızlı LLM / casual yolları emir sırasını bozar."""
    return umed_emri_enabled()


def should_disable_casual_fast_path(message: str = "") -> bool:
    """
    Ümit emri açıkken bile sohbet/empati turunda hızlı yola izin ver.
    Yalnızca açık bilgi araştırması (nedir/kimdir…) için hızlı yolu kapat.
    """
    if not umed_emri_enabled():
        return False
    raw = (message or "").strip()
    if len(raw) < 6:
        return False
    try:
        from ilim_assistant.ana_motor_plan import (
            is_casual_conversation_turn,
            looks_like_casual_social_chat,
        )
        from ilim_assistant.ruzgar_bilissel_analiz import is_anlama_empati_sorusu

        if looks_like_casual_social_chat(raw):
            return False
        if is_anlama_empati_sorusu(raw):
            return False
        if re.search(
            r"(?:kendini|kendin)\s+nasil\s+hissed|nasil\s+hissediyorsun|"
            r"nasil\s+hissediyorsun|duygularini|duygularını)",
            raw,
            re.I,
        ):
            return False
        if is_casual_conversation_turn(raw, "genel", None):
            return False
    except Exception:
        pass
    low = raw.lower()
    if re.search(r"\b(?:bilir\s*misin|bilirmisin)\b", low):
        return True
    return any(
        k in low
        for k in (
            " nedir",
            "nedir ",
            "kimdir",
            "ne zaman",
            "nerede",
            " kaç ",
            " kac ",
        )
    )


def should_defer_web_to_rest() -> bool:
    """Web, Gemini/Groq sonrası ikincil adım."""
    return umed_emri_enabled()


def public_meta(message: str = "") -> dict[str, Any]:
    return {
        "version": EMRI_VERSION,
        "frozen": EMRI_FROZEN,
        "budget_sec": turn_budget_sec(message),
        "priority": list(PRIORITY_LABELS),
        "miss_phrase": MISS_PHRASE,
    }
