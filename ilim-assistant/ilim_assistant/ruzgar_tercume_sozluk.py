# Created by Ümit & Gökçenur
"""Motor C — kısa sabit ilim ifadeleri (yanlış LLM çevirisini keser)."""

from __future__ import annotations

import re
import unicodedata

# kaynak fold → (tr, ar_osmanlı_görünüm, not)
_GLOSSARY: list[tuple[str, str, str]] = [
    (
        "bismillahirrahmanirrahim",
        "Rahman ve Rahim olan Allah'ın adıyla",
        "Besmele — standart Türkçe karşılık",
    ),
    (
        "bismillahi rrahmani rrahim",
        "Rahman ve Rahim olan Allah'ın adıyla",
        "Besmele",
    ),
    (
        "bismillah",
        "Allah'ın adıyla",
        "Kısa besmele",
    ),
    (
        "alhamdulillah",
        "Hamd Allah'a mahsustur",
        "",
    ),
    (
        "subhanallah",
        "Allah'ı tüm noksanlıklardan tenzih ederim",
        "",
    ),
    (
        "allahu akbar",
        "Allah en büyüktür",
        "",
    ),
    (
        "astaghfirullah",
        "Allah'tan bağışlanma dilerim",
        "",
    ),
    (
        "la ilaha illallah",
        "Allah'tan başka ilah yoktur",
        "Kelime-i tevhid (öz)",
    ),
]


def _fold(s: str) -> str:
    t = unicodedata.normalize("NFKD", s or "")
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def lookup_fixed_phrase(text: str) -> dict[str, str] | None:
    raw = (text or "").strip()
    if not raw or len(raw) > 120:
        return None
    # komut öneklerini soy
    body = re.sub(
        r"(?is)^(?:(?:arapça|arapca|osmanlı|osmanli|farsça|farsca|ingilizce)\s*)?"
        r"(?:(?:den|dan|ye|ya|e|a)\s+)?"
        r"(?:çevir|cevir|tercüme|tercume)\s*[:：]?\s*",
        "",
        raw,
    ).strip()
    body = re.sub(
        r"(?is)\s+(?:ifadesini|cümlesini|cumlesini)?\s*"
        r"(?:türkçeye|turkceye|türkçeye\s+çevir|cevir).*$",
        "",
        body,
    ).strip()
    # "X ifadesini türkçeye çevir" → X
    m = re.search(
        r"(?is)^(.+?)\s+ifadesini\s+(?:türkçeye|turkceye)",
        raw,
    )
    if m:
        body = m.group(1).strip()
    fold = _fold(body)
    fold2 = fold.replace(" ", "")
    # aralıklı latin: "bismillah i rahman i rahim"
    if "bismillah" in fold2 and "rahman" in fold2 and "rahim" in fold2:
        return {
            "source": body or raw,
            "tr": "Rahman ve Rahim olan Allah'ın adıyla",
            "note": "Besmele — standart Türkçe karşılık",
            "key": "bismillahirrahmanirrahim",
        }
    for key, tr, note in _GLOSSARY:
        k = _fold(key).replace(" ", "")
        if fold2 == k or (fold2.startswith(k) and len(fold2) <= len(k) + 8):
            return {"source": body or raw, "tr": tr, "note": note, "key": key}
    return None


def format_fixed_reply(hit: dict[str, str]) -> str:
    note = hit.get("note") or ""
    extra = f"\n({note})" if note else ""
    return (
        f"**Kaynak:** {hit.get('source')}\n"
        f"**Türkçe:** {hit.get('tr')}"
        f"{extra}\n"
        f"— Motor C sabit ilim sözlüğü (LLM tahminine bırakılmadı)."
    )
