# -*- coding: utf-8 -*-
"""Anlık kütüphane / arşiv kapısı — lookup hızlı kalsın, sohbet LLM'e gitsin.

Kapat (eski davranış): RUZGAR_ANLIK_NIYET_GATE=0
"""
from __future__ import annotations

import os
import re
import unicodedata

_SYNTH_RE = re.compile(
    r"(?:"
    r"\banlat(?:ır\s*mısın|irmisin|sana)?\b|"
    r"\baçıkla(?:r\s*mısın|rmisin)?\b|\bacikla(?:r\s*misin|rmisin)?\b|"
    r"daha\s+açık|daha\s+acik|daha\s+uzun|detayl[ıi]|"
    r"kendi\s+cümle|kendi\s+cumle|"
    r"\bsohbet\b|\bkonuş(?:alım|alim)?\b|\bkonus(?:alim)?\b|"
    r"devam\s+et|anlamad[ıi]m|örnekle|ornekle|"
    r"doğal\s+konuş|dogal\s+konus|arkada[sş]\s+gibi|"
    r"panelde\s+aç|panelde\s+ac"  # kitap/UI; video paneli ayrı regex'te
    r")",
    re.I,
)

# Numaralı matın / kesin lookup — anlık koru
_STRICT_LOOKUP_RE = re.compile(
    r"(?:"
    r"\b(?:buhari|buhârî|muslim|müslim|tirmizi|ebu\s*davud|nesai|ibn\s*mace)\b"
    r".{0,20}\b\d{1,5}\b|"
    r"\b(?:hadis|ayet)\s*(?:no|numara|#)?\s*\d{1,5}\b|"
    r"^\s*[\w'’çğıöşüâîû\.\-]{2,40}\s+(?:nedir|ne\s+demek)\s*[?.!]?\s*$"
    r")",
    re.I,
)


def anlik_niyet_gate_enabled() -> bool:
    return os.environ.get("RUZGAR_ANLIK_NIYET_GATE", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _fold(s: str) -> str:
    t = unicodedata.normalize("NFKD", s or "")
    t = "".join(c for c in t if not unicodedata.combining(c))
    return t.lower().strip()


def is_strict_library_lookup(message: str) -> bool:
    """Kısa «X nedir» / numaralı hadis — anlık cevap korunsun."""
    raw = (message or "").strip()
    if not raw or len(raw) > 120:
        return False
    return bool(_STRICT_LOOKUP_RE.search(raw))


def should_defer_library_instant(message: str) -> bool:
    """
    True → din kütüphanesi / arşiv-fast anlık yolu atla; LLM sentezine bırak.
    False → mevcut anlık try_*_reply çalışsın.
    """
    if not anlik_niyet_gate_enabled():
        return False
    raw = (message or "").strip()
    if not raw:
        return False
    if is_strict_library_lookup(raw):
        return False
    if _SYNTH_RE.search(raw) or _SYNTH_RE.search(_fold(raw)):
        return True
    return False


def should_defer_archive_fast(message: str) -> bool:
    """Arşiv pasaj dump'ını sohbet/anlat niyetinde atla."""
    return should_defer_library_instant(message)
