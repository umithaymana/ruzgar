# Created by Ümit & Gökçenur
"""Anında sohbet yanıtları — ağır import yok (UI thread pool tıkanmasını keser)."""

from __future__ import annotations

import re
import unicodedata
from typing import Any

FAST_LANE_VERSION = "chat-fast-lane-v1-2026-06-19"


def _norm(s: str) -> str:
    t = unicodedata.normalize("NFKC", (s or "").strip().lower())
    return re.sub(r"\s+", " ", t)


def _ascii(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii").lower()


def mode_norm_from_request(mode: Any) -> str:
    m = str(mode or "genel").strip().lower()
    return m if m in ("genel", "gelisim", "uretim") else "genel"


def try_instant_reply(message: str, mode_norm: str = "genel") -> str | None:
    """Selam / teşekkür / kısa nezaket — LLM/RAG/thread pool yok."""
    if mode_norm not in ("genel", "gelisim", "uretim"):
        return None
    raw = (message or "").strip()
    if not raw or len(raw) > 120:
        return None
    blob = _norm(raw) + " " + _ascii(raw)

    if re.search(r"\b(?:teşekkür|tesekkur|sağol|sagol|eyvallah|rica\s+ederim)\b", blob):
        return (
            "Rica ederim Ümit abi — ne demek. "
            "Başka bir konuda da yanındayım."
        )

    if re.search(r"\b(?:naber|ne\s+haber|nas[ıi]ls[ıi]n|nasilsin|iyi\s+misin)\b", blob):
        return (
            "İyiyim, teşekkür ederim — Rüzgar burada, Ümit abi için hazırım. "
            "Sen nasılsın, keyfin nasıl?"
        )

    if re.search(
        r"\b(?:selam|merhaba|günayd[ıi]n|gunaydin|iyi\s+akşam|iyi\s+aksam|iyi\s+geceler)\b",
        blob,
    ):
        return (
            "Selam Ümit abi — Rüzgar burada, seninle konuşmaya hazırım. "
            "Nasılsın, ne konuşalım?"
        )

    if re.search(
        r"\b(?:neredesin|nerede\s+sin|sen\s+nerede|burada\s+m[ıi]s[ıi]n|"
        r"beni\s+duyuyor|duyuyor\s+musun|sesimi\s+duy|var\s+m[ıi]s[ıi]n|"
        r"sen\s+nerelerdesin|hala\s+orada)\b",
        blob,
    ):
        return (
            "Buradayım Ümit abi — Rüzgar, Ana Motor'dayım. "
            "Seni duyuyorum; yazabilir veya konuşabilirsin."
        )

    if re.search(r"ka[cç]\s+ay", blob) and re.search(
        r"(?:bir\s+)?senede|y[ıi]lda|takvim",
        blob,
    ):
        return "Ümit abi, bir senede **12 ay** vardır — Ocak'tan Aralık'a kadar."

    if re.search(r"^ka[cç]\s+ay\s+var", _ascii(raw)):
        return "Ümit abi, takvim yılında **12 ay** vardır."

    return None
