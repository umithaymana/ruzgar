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


def match_kavram_row(
    msg: str,
    rows: list[dict[str, Any]],
    *,
    min_score: int = 55,
) -> Optional[dict[str, Any]]:
    """En iyi kavram satırını döndür.

    Kurallar:
    - eşleşme kelime sınırında (``bilim`` ``bilgisayar`` içinde tutmaz)
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
        for k in keys:
            if not k:
                continue
            if k == low or low == f"{k} nedir" or low.startswith(f"{k} nedir"):
                score = max(score, 100)
            elif " " not in k and len(k) < 6:
                continue
            elif _key_bounded(k, low) and (len(k) >= 6 or " " in k):
                score = max(score, 60 + min(20, len(k)))
            else:
                parts = [p for p in k.split() if len(p) >= 4]
                if len(parts) >= 2 and all(_key_bounded(p, low) for p in parts):
                    score = max(score, 55 + min(15, len(k)))
        if score > best_score:
            best_score = score
            best = row
    if best_score >= min_score:
        return best
    return None
