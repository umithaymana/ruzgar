# Created by Ümit & Gökçenur
"""Tarih dedektifliği — kronoloji, karşılaştırma ve kaynak ilişkisine dair ipucu bağlamı (temel)."""

from __future__ import annotations

import os
from typing import Any


def tarih_dedektifligi_enabled() -> bool:
    return os.environ.get("RUZGAR_TARIH_DEDEKTIF", "0").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def build_tarih_dedektif_context(
    query: str,
    rag_hits: list[tuple[str, str, float]],
    *,
    invoke_via_arsiv_ileri: bool = False,
) -> str:
    """
    RAG alıntılarından kısa bir tarih / isnat ipucu üretir.
    Şimdilik yalnızca etkinleştirildiğinde kısa bir çerçeve verir; ayrıntılı çıkarım ileride.
    """
    if not invoke_via_arsiv_ileri and not tarih_dedektifligi_enabled():
        return ""
    q = (query or "").strip()
    if not q or not rag_hits:
        return ""
    top_src = (rag_hits[0][1] or "").strip()[:200]
    return (
        "\n\n[TALİMAT — Tarih dedektifliği — taslak]\n"
        "Aşağıdaki kaynak satırını tarihî metin veya isnat çerçevesinde değerlendirmeye al; "
        "tarih uydurma, kesin tarih iddiası olmadan dürüstçe belirt.\n"
        f"Öncelikli kaynak izi: {top_src}\n"
    )


def normalize_hijri_gregorian_hint(text: str) -> dict[str, Any]:
    """İleride Hicrî–Milâdî dönüşüm ve metin içi yıl çıkarma için."""
    _ = text
    return {}
