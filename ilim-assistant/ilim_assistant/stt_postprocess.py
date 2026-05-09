# Created by Ümit & Gökçenur
"""
STT sonrası metin cilası — niyet ve cümle akışı (heuristik), sabit zaman O(n).

Yerel LLM / HTTP yok; Rüzgar cevap hattına ek gecikme eklemez (Zero Latency hedefi).
"""

from __future__ import annotations

import re
import unicodedata

_PHRASE_FIXES: tuple[tuple[str, str], ...] = (
    (r"\brüz\s+gar\b", "Rüzgar"),
    (r"\brüz\s*zar\b", "Rüzgar"),
    (r"\brüzgar\b", "Rüzgar"),
    (r"\bru\s*z\s*gar\b", "Rüzgar"),
    (r"\briz\s*gar\b", "Rüzgar"),
    (r"\bruz\s*gar\b", "Rüzgar"),
    (r"\brizgar\b", "Rüzgar"),
    (r"\bruzgar\b", "Rüzgar"),
    (r"\bümit\s+abi\b", "Ümit abi"),
    (r"\bgök\s*ço\s*nur\b", "Gökçenur"),
    (r"\bgokcenur\b", "Gökçenur"),
)

_SUFFIX_RUZGAR: tuple[tuple[str, str], ...] = (
    (r"(?i)\brüzgara\b", "Rüzgara"),
    (r"(?i)\brüzgardan\b", "Rüzgar'dan"),
    (r"(?i)\brüzgarla\b", "Rüzgar'la"),
    (r"(?i)\brüzgarda\b", "Rüzgar'da"),
    (r"(?i)\brüzgardır\b", "Rüzgar'dır"),
    (r"(?i)\brüzgarım\b", "Rüzgar'ım"),
    (r"(?i)\brüzgardı\b", "Rüzgar'dı"),
)

_DISFLUENCY = re.compile(r"(?i)\b(eee|eee+|ııı|aaa|hıı|mmm|şey\s+işte)\b")


def cilala_stt_metni(text: str, language: str | None = None) -> str:
    """Konuşma metnini cümle akışına göre cilala (anlık, kural tabanlı)."""
    if not text or not str(text).strip():
        return (text or "").strip()

    t = unicodedata.normalize("NFC", str(text).strip())
    t = t.replace("\u00a0", " ").replace("\r\n", "\n").replace("\r", "\n")
    t = re.sub(r"[ \t]{2,}", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)

    for pat, rep in _PHRASE_FIXES:
        t = re.sub(pat, rep, t, flags=re.IGNORECASE)

    for pat, rep in _SUFFIX_RUZGAR:
        t = re.sub(pat, rep, t)

    t = re.sub(r"\s+([.,!?;:])", r"\1", t)
    t = re.sub(r"([.,!?;:])(?=[^\s\d])", r"\1 ", t)
    t = re.sub(r"\.{4,}", "...", t)
    t = re.sub(r"\?{2,}", "?", t)
    t = re.sub(r"!{2,}", "!", t)

    t = _DISFLUENCY.sub("", t)
    t = re.sub(r"\s{2,}", " ", t).strip()

    # Ümit kelimesi günlük Türkçede “ümit”; yalnızca “ümit abi” yukarıda düzeltilir.
    for name in ("Rüzgar", "Gökçenur"):
        t = re.sub(rf"\b{re.escape(name)}\b", name, t, flags=re.IGNORECASE)

    return t.strip()
