# -*- coding: utf-8 -*-
"""Ortak kavram eşleştirme — kısa alias'ların kelime içi yanlış vuruşunu keser.

Örn. teknoloji alias ``os`` → ``atmosfer`` içinde ``os`` geçmesin.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any, Optional


def fold_query(s: str) -> str:
    t = unicodedata.normalize("NFKD", s or "")
    t = "".join(c for c in t if not unicodedata.combining(c))
    return t.lower().strip()


def norm_query(msg: str) -> str:
    low = fold_query(msg)
    low = re.sub(r"[-_/]+", " ", low)
    return re.sub(r"\s+", " ", low).strip()


def _key_bounded(key: str, low: str) -> bool:
    """Anahtar, daha uzun bir kelimenin içine gizlenmesin (bilim/bilgisayar)."""
    return bool(re.search(rf"(?<![\w'’]){re.escape(key)}(?![\w'’])", low))


# «hicreti / fotosentezi / osmanlıyı anlat» — durum eki kelime sınırını kırıyordu (C1).
_TR_CASE_AFTER = (
    r"(?:y?[ıiuü]|y?[ae]|n[ıiuü]n|n[ae]n|d[ae]|t[ae]|l[ae]r[ıiuü]?)?"
)


def _key_in_query(key: str, low: str) -> bool:
    """Kelime sınırı veya Türkçe durum ekiyle («hicreti») eşle."""
    if not key:
        return False
    if _key_bounded(key, low):
        return True
    return bool(
        re.search(
            rf"(?<![\w'’]){re.escape(key)}{_TR_CASE_AFTER}(?![\w'’])",
            low,
        )
    )


def match_kavram_row(
    msg: str,
    rows: list[dict[str, Any]],
    *,
    min_score: int = 55,
) -> Optional[dict[str, Any]]:
    """En iyi kavram satırını döndür.

    Kurallar:
    - eşleşme kelime sınırında (``bilim`` ``bilgisayar`` içinde tutmaz)
    - durum ekli biçim OK (``hicreti``, ``fotosentezi``)
    - 6 harften kısa tek kelime yalnız «kavram» veya «kavram nedir» ise
    - uzun cümledeki ``alan`` gibi kısa alias kart açmaz
    """
    low = norm_query(msg)
    if not low:
        return None
    best: Optional[dict[str, Any]] = None
    best_score = 0
    for row in rows:
        keys = [norm_query(row.get("baslik") or "")]
        keys.extend(norm_query(a) for a in (row.get("aliases") or []))
        score = 0
        q_particles = (
            " nedir",
            " ne demek",
            " ne zaman",
            " nerede",
            " kimdir",
            " kim kurdu",
            " anlat",
            " acikla",
            " açıkla",
        )
        explain_cues = (
            "anlat",
            "acikla",
            "açıkla",
            "daha acik",
            "daha açık",
            "biraz",
            "detay",
        )
        for k in keys:
            if not k:
                continue
            if k == low or low == f"{k} nedir" or low.startswith(f"{k} nedir"):
                score = max(score, 100)
            elif any(low == (k + p).strip() or low.startswith(k + p) for p in q_particles):
                score = max(score, 95)
            elif " " not in k and len(k) < 6:
                continue
            elif _key_in_query(k, low) and (len(k) >= 6 or " " in k):
                base = 60 + min(20, len(k))
                # «hicret ne zaman» / «hicreti daha açık anlat»
                if any(p.strip() in low for p in q_particles) or any(
                    c in low for c in explain_cues
                ):
                    base = max(base, 75)
                score = max(score, base)
            else:
                parts = [p for p in k.split() if len(p) >= 4]
                if len(parts) >= 2 and all(_key_in_query(p, low) for p in parts):
                    score = max(score, 55 + min(15, len(k)))
                # «karadeniz nedir» ↔ «karadeniz bolgesi»
                head = parts[0] if parts else ""
                if head and len(head) >= 5 and _key_in_query(head, low):
                    if low == head or low == f"{head} nedir" or any(
                        low == (head + p).strip() or low.startswith(head + p)
                        for p in q_particles
                    ):
                        score = max(score, 85)
                    elif any(c in low for c in explain_cues):
                        score = max(score, 80)
        if score > best_score:
            best_score = score
            best = row
    if best_score >= min_score:
        return best
    return None
