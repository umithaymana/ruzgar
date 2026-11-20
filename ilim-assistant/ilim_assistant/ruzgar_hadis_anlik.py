# -*- coding: utf-8 -*-
"""Rüzgar — meşhur hadis anlık doğru cevap (LLM uydurmasını keser).

İlk kart: Sahîh-i Buhârî niyet hadisi (hadis no. 1).
"""
from __future__ import annotations

import re
import unicodedata


def _fold(s: str) -> str:
    t = unicodedata.normalize("NFKD", s or "")
    t = "".join(c for c in t if not unicodedata.combining(c))
    return t.lower().strip()


def _looks_niyet_hadis(msg: str) -> bool:
    low = _fold(msg)
    if not low:
        return False
    # açık Arapça metin
    raw = msg or ""
    if "إنما الأعمال" in raw or "الاعمال بالني" in raw.replace("أ", "ا"):
        return True
    has_niyet = "niyet" in low
    has_hadis = any(k in low for k in ("hadis", "hadith", "rivayet"))
    has_buhari = any(k in low for k in ("buhari", "buhar", "sahih"))
    # «niyet hadisi» / «buhari niyet»
    if has_niyet and (has_hadis or has_buhari):
        return True
    if has_niyet and re.search(r"\b(?:nedir|nasil|nasıl|gecer|geçer|anlat|soyle|söyle)\b", low):
        return True
    if "ameller niyet" in low or "niyetlere gore" in low or "niyetlere göre" in low:
        return True
    return False


def try_hadis_instant_reply(message: str) -> str | None:
    """Eşleşirse sabit doğru metin + karşılaştırma teklifi; yoksa None.

    Tek politika (hadis_kutuphane ile): bilgi/karşılaştır/anlat → RAG'e bırak.
    Kısa niyet hatırlatması (nedir/anlat yok) hâlâ anlık kalabilir.
    """
    if not _looks_niyet_hadis(message):
        return None
    # Derin soru / çok kaynak — anlık kart yok (Faz 1 orkestra)
    try:
        from ilim_assistant.ruzgar_library_instant_registry import forces_library_rag

        if forces_library_rag(message):
            return None
    except Exception:
        pass
    low = _fold(message)
    if any(
        k in low
        for k in (
            "karsilastir",
            "karşılaştır",
            "diger kaynak",
            "diğer kaynak",
            "tirmizi",
            "tirmizî",
            "muslim",
            "müslim",
            "nesai",
            "nesâî",
            "serh",
            "şerh",
            "rivayetler",
            "nedir",
            "ne demek",
            "anlat",
            "acikla",
            "açıkla",
        )
    ):
        return None
    offer = (
        "İstersen diğer kaynaklardaki rivayet ve şerhlerle de karşılaştırabilirim."
    )
    try:
        from ilim_assistant.ruzgar_cok_kaynak_sentez import comparison_offer_line

        offer = comparison_offer_line(message, None) or offer
    except Exception:
        pass
    return (
        "Ümit abi — Sahîh-i Buhârî’deki meşhur **niyet hadisi** şöyledir:\n\n"
        "Arapça: «إِنَّمَا الْأَعْمَالُ بِالنِّيَّاتِ، وَإِنَّمَا لِكُلِّ امْرِئٍ مَا نَوَى»\n\n"
        "Türkçe meal: «Ameller niyetlere göredir; herkese niyet ettiği vardır.»\n\n"
        "Kaynak: Sahîh-i Buhârî, Kitâbü’l-Îmân (Îman kitabı), hadis no. 1 "
        "(Buhârî’nin ilk hadisi). "
        "Uydurma cilt/kitap numarası veya başka metin söylemem.\n\n"
        f"{offer}"
    )
