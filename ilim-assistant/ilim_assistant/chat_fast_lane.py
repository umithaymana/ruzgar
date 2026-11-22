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
    """Selam / teşekkür / kısa nezaket — LLM/RAG/thread pool yok.

    Madde 1 (2026-11-22): varsayılan kapalı — ezber metin yok, beyin üretir.
    Eski şerit: RUZGAR_EZBER_INSTANT=1
    """
    if mode_norm not in ("genel", "gelisim", "uretim"):
        return None
    raw = (message or "").strip()
    if not raw or len(raw) > 120:
        return None
    # Tek yüz / atölye önekleri — selam kelimesi içinde olsa bile fast-lane ezmesin
    _a = _ascii(_norm(raw))
    if re.match(
        r"^(?:seste|ses\s+atolyesinde|ses\s+paneline|"
        r"hafizada|hafiza\s+atolyesinde|hafiza\s+paneline|"
        r"mimarda|mimar\s+atolyesinde|mimar\s+paneline|"
        r"fotograf\s+paneli|tasarimda|"
        r"gorev\s*:|programlamada|videoda|video\s+atolyesinde|"
        r"tercumede|tercume\s+atolyesinde|sesle\s+oku|"
        r"hizirda|hizir\s+atolyesinde|hizir\s+paneline)\b",
        _a,
    ):
        return None
    try:
        from ilim_assistant.motorlar.programlama_proje_masasi import tarif_cumlesi

        if tarif_cumlesi(raw):
            return None
    except Exception:
        pass
    # Atölye koruması yukarıda bitti; ezber şerit kapalıysa LLM yoluna bırak
    try:
        from ilim_assistant.ruzgar_ezber_instant import ezber_instant_enabled

        if not ezber_instant_enabled():
            return None
    except Exception:
        return None
    blob = _norm(raw) + " " + _ascii(raw)

    if re.search(
        r"\b(?:iyi\s+geceler|hosca\s+kal|hoşça\s+kal|görüşürüz|gorusuruz|ara\s+verec)\w*\b",
        blob,
    ):
        return (
            "İyi geceler Ümit abi. Dinlen, kafan dağınık kalmasın. "
            "Yarın yine buradayım; kaldığımız yerden devam ederiz."
        )

    if re.fullmatch(
        r"(?:çok|cok)\s+iyi|güzel|guzel|harika|süper|super|mükemmel|mukemmel|güzelmiş|guzelmis",
        _norm(raw),
    ):
        return "Sevindim Ümit abi. İstersen bunu biraz daha açalım, istersen başka konuya geçelim."

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
