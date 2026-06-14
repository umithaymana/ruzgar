# Created by Ümit & Gökçenur
"""Tek beyin Faz N — soru niyeti analizi ve basit gerçek yanıtları (LLM yok)."""

from __future__ import annotations

import os
import re
import unicodedata
from typing import Any, Optional

TEK_BEYIN_ANALIZ_VERSION = "tek-beyin-analiz-v1-2026-06-13-faz-n"

# (pattern, answer_fn or static answer)
_SIMPLE_FACTS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(
            r"(?:senede|y[ıi]lda|bir\s+y[ıi]lda|yillik)\s+ka[cç]\s+ay",
            re.I,
        ),
        "Ümit abi, bir senede **12 ay** vardır — Ocak'tan Aralık'a kadar.",
    ),
    (
        re.compile(
            r"(?:haftada|bir\s+haftada)\s+ka[cç]\s+g[üu]n",
            re.I,
        ),
        "Ümit abi, bir haftada **7 gün** vardır.",
    ),
    (
        re.compile(
            r"(?:g[üu]nde|bir\s+g[üu]nde)\s+ka[cç]\s+saat",
            re.I,
        ),
        "Ümit abi, bir günde **24 saat** vardır (gece-gündüz döngüsü).",
    ),
    (
        re.compile(
            r"(?:dakikada|bir\s+dakikada)\s+ka[cç]\s+saniye",
            re.I,
        ),
        "Ümit abi, bir dakikada **60 saniye** vardır.",
    ),
    (
        re.compile(
            r"(?:saatte|bir\s+saatte)\s+ka[cç]\s+dakika",
            re.I,
        ),
        "Ümit abi, bir saatte **60 dakika** vardır.",
    ),
    (
        re.compile(
            r"^ka[cç]\s+tane\s+ay\s+var\s*$|^aylar\s+ka[cç]\s+tane\s*$",
            re.I,
        ),
        "Ümit abi, takvim yılında **12 ay** vardır.",
    ),
    (
        re.compile(
            r"(?:d[üu]nyada|dunyada)\s+ka[cç]\s+k[ıi]ta",
            re.I,
        ),
        "Ümit abi, Dünya'da genelde **6 kıta** sayılır (bazı kaynaklarda 7 — Antarktika ayrı sayılırsa).",
    ),
    (
        re.compile(
            r"(?:tr|t[üu]rkiye(?:'?de|de)?)\s+ka[cç]\s+il",
            re.I,
        ),
        "Ümit abi, Türkiye'de **81 il** vardır.",
    ),
)

_TEMPORAL_NOW = re.compile(
    r"(?:"
    r"bug[üu]n\s+hangi\s+ay|"
    r"[şs]u\s+an\s+hangi\s+ay|"
    r"hangi\s+ayday[ıi]z|"
    r"hangi\s+ay[ıi]z|"
    r"ka[cç][ıi]nc[ıi]\s+ayday[ıi]z"
    r")",
    re.I,
)


def tek_beyin_analiz_enabled() -> bool:
    if os.environ.get("RUZGAR_TEK_BEYIN", "1").strip().lower() in ("0", "false", "no"):
        return False
    return os.environ.get("RUZGAR_TEK_BEYIN_ANALIZ", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _norm(text: str) -> str:
    t = unicodedata.normalize("NFKC", (text or "").strip().lower())
    return re.sub(r"\s+", " ", t)


def classify_question_intent(message: str) -> dict[str, Any]:
    """
    Soru niyeti — plan ve erken yol seçimi için.
    intent: simple_fact | temporal_now | personal | meta_feedback | web_cmd | bilgi | sohbet
    """
    raw = (message or "").strip()
    out: dict[str, Any] = {
        "intent": "bilgi",
        "confidence": 0.5,
        "skip_web": False,
        "skip_rag": False,
        "direct_answer": None,
    }
    if not raw:
        out["intent"] = "sohbet"
        return out
    try:
        from ilim_assistant.ruzgar_tek_beyin import resolve_effective_user_query

        effective = resolve_effective_user_query(raw)
    except Exception:
        effective = raw
    blob = _norm(effective)
    try:
        from ilim_assistant.ruzgar_tek_beyin_konusma_akisi import (
            looks_like_meta_feedback,
            looks_like_web_research_command,
        )

        if looks_like_meta_feedback(raw):
            out.update(intent="meta_feedback", confidence=0.95)
            return out
        if looks_like_web_research_command(raw):
            out.update(intent="web_cmd", confidence=0.92)
            return out
    except Exception:
        pass
    try:
        from ilim_assistant.ruzgar_tek_beyin import (
            matches_known_circle_name,
            should_use_personal_hafiza_first,
        )

        if should_use_personal_hafiza_first(effective) or matches_known_circle_name(effective):
            out.update(intent="personal", confidence=0.9, skip_web=True, skip_rag=True)
            return out
    except Exception:
        pass
    try:
        from ilim_assistant.ana_motor_plan import looks_like_current_geopolitics_question

        if looks_like_current_geopolitics_question(effective):
            out.update(intent="bilgi", confidence=0.92, skip_web=False, skip_rag=False)
            return out
    except Exception:
        pass
    try:
        from ilim_assistant.ruzgar_otomatik_ogrenme import lookup_bilgi_kutuphane_hint

        ku = lookup_bilgi_kutuphane_hint(effective)
        if ku and float(ku.get("skor") or 0) >= 0.68:
            out.update(
                intent="bilgi_kutuphane",
                confidence=0.93,
                skip_web=True,
                skip_rag=True,
                direct_answer=str(ku.get("cevap") or ""),
            )
            return out
    except Exception:
        pass
    if _TEMPORAL_NOW.search(blob):
        out.update(intent="temporal_now", confidence=0.88)
        return out
    if tek_beyin_analiz_enabled():
        ans = try_simple_factual_reply(raw)
        if ans:
            out.update(
                intent="simple_fact",
                confidence=0.98,
                skip_web=True,
                skip_rag=True,
                direct_answer=ans,
            )
            return out
    try:
        from ilim_assistant.ana_motor_plan import looks_like_casual_social_chat

        if looks_like_casual_social_chat(raw):
            out.update(intent="sohbet", confidence=0.85, skip_web=True, skip_rag=True)
            return out
    except Exception:
        pass
    if re.search(r"\b(kimdir|nedir|ne zaman|ka[cç]|nasıl|nerede)\b", blob):
        out.update(intent="bilgi", confidence=0.75)
    return out


def try_temporal_now_reply(message: str) -> Optional[str]:
    """Şu anki tarih/ay — güncel takvim."""
    if not tek_beyin_analiz_enabled():
        return None
    raw = (message or "").strip()
    if not _TEMPORAL_NOW.search(_norm(raw)):
        return None
    try:
        from datetime import datetime

        now = datetime.now()
        aylar = (
            "Ocak",
            "Şubat",
            "Mart",
            "Nisan",
            "Mayıs",
            "Haziran",
            "Temmuz",
            "Ağustos",
            "Eylül",
            "Ekim",
            "Kasım",
            "Aralık",
        )
        ay = aylar[now.month - 1]
        return (
            f"Ümit abi, bugün **{now.day} {ay} {now.year}** — "
            f"şu an **{ay}** ayındayız."
        )
    except Exception:
        return None


def try_simple_factual_reply(message: str) -> Optional[str]:
    """Evrensel kısa gerçekler — tarih/bağlam karıştırmadan."""
    if not tek_beyin_analiz_enabled():
        return None
    raw = (message or "").strip()
    if not raw or len(raw) > 120:
        return None
    if _TEMPORAL_NOW.search(_norm(raw)):
        return None
    for pat, ans in _SIMPLE_FACTS:
        if pat.search(_norm(raw)):
            return ans
    return None


def build_analiz_system_addon(message: str) -> str:
    """LLM turuna niyet ipucu — yanlış bağlam kaymasını azalt."""
    intent = classify_question_intent(message)
    it = str(intent.get("intent") or "bilgi")
    lines = [
        "\n[TALİMAT — SORU NİYETİ ANALİZİ (Faz N)]",
        f"Algılanan niyet: **{it}**.",
    ]
    if it == "simple_fact":
        lines.append(
            "Bu evrensel/kısa bir gerçek sorusu — bugünün tarihi veya oturum bağlamına "
            "kayma; doğrudan net sayıyı/kuralı söyle."
        )
    elif it == "temporal_now":
        lines.append(
            "Kullanıcı **şu anki** tarih/ay soruyor — güncel takvime göre yanıtla."
        )
    elif it == "bilgi":
        lines.append(
            "Bilgi sorusu — önce sorunun özünü yanıtla; gereksiz sohbet veya "
            "alakasız konuya atlama."
        )
    elif it == "personal":
        lines.append(
            "Kişisel hafıza sorusu — ansiklopedi/web uydurma; kayıtlı bilgiyi kullan."
        )
    return "\n".join(lines) + "\n"


def tek_beyin_analiz_status() -> dict[str, Any]:
    return {
        "enabled": tek_beyin_analiz_enabled(),
        "version": TEK_BEYIN_ANALIZ_VERSION,
        "simple_facts_count": len(_SIMPLE_FACTS),
    }
