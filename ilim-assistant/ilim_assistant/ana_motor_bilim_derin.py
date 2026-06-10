# Created by Ümit & Gökçenur
"""Faz D / 9.3 — Bilim ve tarih derin mod: arşiv öncelikli, geniş RAG, tam sentez."""

from __future__ import annotations

import os
import re
import unicodedata
from typing import Any


def _fold(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def bilim_derin_enabled() -> bool:
    return os.environ.get("RUZGAR_BILIM_DERIN", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def bilim_derin_use_70b() -> bool:
    return os.environ.get("RUZGAR_BILIM_DERIN_USE_70B", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _plan_primary(question_plan: Any | None) -> str:
    if question_plan is None:
        return ""
    if hasattr(question_plan, "primary"):
        return str(getattr(question_plan, "primary", "") or "").strip().lower()
    if isinstance(question_plan, dict):
        return str(question_plan.get("primary") or "").strip().lower()
    return ""


_DEEP_CUES = (
    "detayli",
    "detaylı",
    "derinlemesine",
    "kapsamli",
    "kapsamlı",
    "acikla",
    "açıkla",
    "mekanizma",
    "nasil olus",
    "nasıl oluş",
    "kanit",
    "kanıt",
    "bilimsel",
    "teorisi",
    "deney",
    "fizik",
    "kimya",
    "biyoloji",
    "astronomi",
    "evrim",
    "molekul",
    "molekül",
    "kuantum",
    "genetik",
    "arastir",
    "araştır",
    "kaynakli",
    "kaynaklı",
    "tarihsel",
    "kronoloji",
    "donem",
    "dönem",
    "padisah",
    "padişah",
    "imparatorluk",
    "medeniyet",
)

_TARIH_CUES = (
    "tarih",
    "osmanli",
    "osmanlı",
    "selcuk",
    "selçuk",
    "bizans",
    "roma",
    "padisah",
    "padişah",
    "devlet",
    "imparator",
    "kurulus",
    "kuruluş",
    "yüzyil",
    "yuzyil",
    "yüzyıl",
)


def _has_deep_cue(text: str) -> bool:
    low = _fold(text)
    if len(low) >= 28 and any(c in low for c in _DEEP_CUES):
        return True
    if re.search(r"\b(nedir|nasil|nasıl|niçin|niye|kimdir)\b", low) and len(low) >= 22:
        return True
    return False


def is_bilim_derin_turn(
    question_plan: Any | None,
    message: str,
    mode_norm: str = "genel",
) -> bool:
    """Bilim/tarih sorularında arşiv derin turu (hızlı indeks atlanır)."""
    if not bilim_derin_enabled():
        return False
    if mode_norm not in ("genel", "uretim", "gelisim", "okuma", "hafiza"):
        return False
    primary = _plan_primary(question_plan)
    msg = (message or "").strip()
    if not msg:
        return False
    low = _fold(msg)
    if primary == "bilim":
        return _has_deep_cue(msg) or len(low) >= 18
    if primary == "bilgi":
        if any(t in low for t in _TARIH_CUES) and _has_deep_cue(msg):
            return True
        if any(t in low for t in ("nobel", "kuantum", "evrim", "fotosentez", "dna")):
            return True
    return False


def should_skip_bilim_fast_index(
    question_plan: Any | None,
    message: str,
    mode_norm: str = "genel",
) -> bool:
    """Gemini/indeks hızlı yolunu atla — arşiv derin turu."""
    return is_bilim_derin_turn(question_plan, message, mode_norm)


def apply_bilim_derin_rag_top_k(
    base_k: int,
    question_plan: Any | None,
    message: str | None = None,
    mode_norm: str = "genel",
) -> int:
    if not is_bilim_derin_turn(question_plan, message or "", mode_norm):
        return base_k
    try:
        boost = int(os.environ.get("RUZGAR_BILIM_DERIN_RAG_TOP_K", "8"))
    except ValueError:
        boost = 8
    return max(base_k, boost, 1)


def append_bilim_deep_directive(
    user_payload: str,
    question_plan: Any | None,
    message: str,
    mode_norm: str = "genel",
) -> str:
    if not is_bilim_derin_turn(question_plan, message, mode_norm):
        return user_payload
    block = (
        "\n\n[TALİMAT — BİLİM/TARİH DERİN MOD — Ümit & Gökçenur]\n"
        "Bu tur **derin bilim/tarih** sorusu: arşiv ve indeks kaynaklarını birleştirerek "
        "**kapsamlı, kaynaklı ve sıralı** yanıt ver.\n"
        "- Güçlü arşiv eşleşmesi varsa önce onu kullan; eksikse web/indeks ile tamamla.\n"
        "- Mekanizma, kronoloji veya liste isteniyorsa **eksiksiz** sun; tek cümleyle geçiştirme.\n"
        "- Çelişkili kaynaklarda dürüstçe belirt; sonunda **Güven:** satırı zorunlu.\n"
    )
    return user_payload.rstrip() + block
