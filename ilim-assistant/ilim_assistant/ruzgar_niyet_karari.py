# Created by Ümit & Gökçenur
"""
Madde 1.2 — Tek niyet kararı (ince iskelet, 2026-11-22).

Amaç: aynı mesajı birden fazla ezber/kapı farklı yorumlamasın.
Bu sürüm bilinçli olarak dar: sohbet / canlı hava / emin değil.
Diğer kapılar sonraki sprintte aynı nesneye bağlanır; şimdilik
mevcut RAG/LLM borusunu bozmamak için dokunulmaz.
"""

from __future__ import annotations

import os
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any

NIYET_KARARI_VERSION = "ruzgar-niyet-karari-v1-2026-11-22"


def niyet_karari_enabled() -> bool:
    return os.environ.get("RUZGAR_NIYET_KARARI", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def _fold(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.replace("İ", "i").replace("I", "i").lower()
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


@dataclass
class IntentDecision:
    kind: str  # sohbet | canli_hava | bilgi | emin_degil | diger
    confidence: float
    place: str | None = None
    needs_clarify: bool = False
    clarify_question: str | None = None
    reasons: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "confidence": round(float(self.confidence), 3),
            "place": self.place,
            "needs_clarify": self.needs_clarify,
            "clarify_question": self.clarify_question,
            "reasons": list(self.reasons),
            "version": NIYET_KARARI_VERSION,
        }


_SOCIAL = re.compile(
    r"^(?:selam|merhaba|slm|hey|naber|ne\s+haber|nasilsin|iyi\s+misin|"
    r"gunaydin|iyi\s+aksam|iyi\s+geceler|tesekkur|sagol|eyvallah|"
    r"ben\s+geldim|geldim|hosca\s+kal|gorusuruz)"
    r"(?:\s+.*)?$",
    re.I,
)


def decide_intent(
    message: str,
    history: list | None = None,
) -> IntentDecision:
    """Tek tur niyet özeti — ezber cevap üretmez."""
    raw = (message or "").strip()
    if not raw:
        return IntentDecision(
            kind="emin_degil",
            confidence=0.0,
            needs_clarify=True,
            clarify_question="Ümit abi, ne hakkında konuşalım?",
            reasons=["empty"],
        )

    folded = _fold(raw)
    reasons: list[str] = []

    # 1) Canlı hava — araç niyeti (cevap ezberi değil)
    try:
        from ilim_assistant.weather_live import (
            _ask_place_reply,
            _extract_city_from_history,
            _extract_city_from_message,
            is_weather_query,
        )

        weather = is_weather_query(raw)
        # chat_core ağır — yalnız kısa takip ipucunda import (donma/kopma riski)
        if not weather and history and len(raw) <= 48:
            _follow = _fold(raw)
            if re.search(
                r"\b(?:yarin|bugun|peki|ya\b|orada|ayn[iı]|degil|değil|orasi|orası)\b",
                _follow,
            ):
                try:
                    from ilim_assistant.chat_core import (
                        _weather_follow_up,
                        _weather_intent,
                    )

                    weather = bool(
                        _weather_intent(raw) or _weather_follow_up(raw, history)
                    )
                except Exception:
                    weather = False
        if weather:
            place = _extract_city_from_message(raw) or _extract_city_from_history(history)
            if not place:
                return IntentDecision(
                    kind="canli_hava",
                    confidence=0.86,
                    place=None,
                    needs_clarify=True,
                    clarify_question=_ask_place_reply(),
                    reasons=["weather_no_place"],
                )
            return IntentDecision(
                kind="canli_hava",
                confidence=0.92,
                place=place,
                reasons=["weather", f"place:{place}"],
            )
    except Exception as exc:
        reasons.append(f"weather_err:{type(exc).__name__}")

    # 2) Kısa sosyal sohbet — ezber YOK; kind=sohbet → LLM üretecek
    if len(raw) <= 80 and _SOCIAL.match(folded):
        # Bilgi kokusu varsa sohbet sayma
        if re.search(r"\b(?:nedir|kimdir|nasil\s+yap|anlat|acikla|hava)\b", folded):
            reasons.append("social_but_infoish")
        else:
            return IntentDecision(
                kind="sohbet",
                confidence=0.9,
                reasons=["social_short"],
            )

    # 3) Açık bilgi sorusu
    if re.search(
        r"\b(?:nedir|kimdir|ne\s+demek|anlat|acikla|hakkinda|neden|nasil\s+olur|"
        r"kac\s+yil|hangi\s+yil|kim\s+dir)\b",
        folded,
    ):
        return IntentDecision(
            kind="bilgi",
            confidence=0.75,
            reasons=["info_cue"] + reasons,
        )

    if len(raw) <= 2:
        return IntentDecision(
            kind="emin_degil",
            confidence=0.4,
            needs_clarify=True,
            clarify_question="Ümit abi, kısaca ne demek istediğini açar mısın?",
            reasons=["too_short"] + reasons,
        )

    return IntentDecision(
        kind="diger",
        confidence=0.55,
        reasons=["fallback"] + reasons,
    )


def niyet_karari_status() -> dict[str, Any]:
    return {
        "enabled": niyet_karari_enabled(),
        "version": NIYET_KARARI_VERSION,
        "env": "RUZGAR_NIYET_KARARI",
    }
