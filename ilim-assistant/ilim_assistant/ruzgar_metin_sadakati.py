# Created by Ümit & Gökçenur
"""
Rüzgar — metin / özel isim sadakati (2026-11-12).

Tarih, siyer, din: uydurma ve yanlış okuma (Kınık→Sınık gibi) yasak.
Kaynakta yoksa uydurma; emin değilse söyle.

Kapat: RUZGAR_METIN_SADAKATI=0
"""

from __future__ import annotations

import os
import re
import unicodedata
from typing import Iterable

VERSION = "ruzgar-metin-sadakati-v1-2026-11-12"

# Bilinen model/OCR zehirleri → doğru biçim (bağlam ipucu ile)
_NAME_FIXES: tuple[tuple[re.Pattern[str], str, re.Pattern[str] | None], ...] = (
    # Selçuklu: Oğuz Kınık boyu — «Sınık» uydurma/yanlış okuma
    (
        re.compile(r"\b[Ss]ınık\b"),
        "Kınık",
        re.compile(r"sel[cç]uk|o[gğ]uz|boy", re.I),
    ),
    (
        re.compile(r"\b[Ss]inik\b"),
        "Kınık",
        re.compile(r"sel[cç]uk|o[gğ]uz|boy", re.I),
    ),
)


def metin_sadakati_enabled() -> bool:
    return os.environ.get("RUZGAR_METIN_SADAKATI", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def _fold(s: str) -> str:
    t = unicodedata.normalize("NFKD", s or "")
    t = "".join(c for c in t if not unicodedata.combining(c))
    return t.casefold()


def looks_like_tarih_ilim_turn(message: str) -> bool:
    low = _fold(message)
    cues = (
        "tarih",
        "selcuk",
        "selçuk",
        "osmanli",
        "osmanlı",
        "hilafet",
        "halife",
        "siyer",
        "gazve",
        "fetret",
        "hadis",
        "fikih",
        "fıkıh",
        "tefsir",
        "akaid",
        "sahabe",
        "imparator",
        "devlet",
        "boyu",
        "oğuz",
        "oguz",
        "kinik",
        "kınık",
        "sinik",
        "sınık",
    )
    return any(c in low for c in cues)


def fidelity_directive(message: str) -> str:
    if not metin_sadakati_enabled():
        return ""
    if not looks_like_tarih_ilim_turn(message):
        # Genele hafif kural
        return (
            "\n\n[TALİMAT — METİN SADAKATİ]\n"
            "Özel isim, boy, yer, tarih, ayet/hadis numarası **uydurma**. "
            "Bağlamda net görmediysen yazma; emin değilsen «emin değilim / kaynağa bakayım» de. "
            "Yanlış okuma (harf kaydırma) yapma.\n"
        )
    return (
        "\n\n[TALİMAT — METİN SADAKATİ / TARİH-İLİM — ZORUNLU]\n"
        "Bu konular hata götürmez. Kurallar:\n"
        "1) Özel isim (boy, kişi, yer, eser, ayet/hadis) yalnız bağlamda **harf harf** gördüğün "
        "biçimiyle yaz. Tahmin etme, benzer kelime uydurma.\n"
        "2) Örnek yasak: Selçuklu Oğuz boyu **Kınık** iken «Sınık» yazmak — yanlış okuma/uydurma.\n"
        "3) Kaynakta yoksa genel model bilginle doldurma; «Ümit abi, net kaynağımda bulamadım» de.\n"
        "4) Şamile derin çekirdek eserlerinde sayfa/satır atlama yok: pasajı doğru oku, analiz et, "
        "sonra sohbet dilinde anlat.\n"
        "5) İç talimat / RAG etiketi yazma.\n"
    )


def scrub_proper_name_poison(text: str, *, message: str = "") -> str:
    """Cevaptaki bilinen zehir isimleri düzelt."""
    if not metin_sadakati_enabled() or not text:
        return text
    out = text
    ctx = f"{message}\n{text}"
    for pat, good, need in _NAME_FIXES:
        if need is not None and not need.search(ctx):
            continue
        out = pat.sub(good, out)
    return out


def is_auto_learn_poison(cevap: str) -> bool:
    """Otomatik öğrenmeye zehir yazılmasın."""
    if not cevap:
        return False
    low = cevap.casefold()
    if re.search(r"\bsınık\b|\bsinik\b", low) and re.search(
        r"sel[cç]uk|o[gğ]uz", low
    ):
        return True
    return False


def context_has_name(blocks: Iterable[str], name: str) -> bool:
    needle = _fold(name)
    if not needle:
        return False
    for b in blocks:
        if needle in _fold(b or ""):
            return True
    return False
