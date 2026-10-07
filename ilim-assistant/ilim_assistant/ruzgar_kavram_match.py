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


def match_kavram_row(
    msg: str,
    rows: list[dict[str, Any]],
    *,
    min_score: int = 55,
) -> Optional[dict[str, Any]]:
    """En iyi kavram satırını döndür.

    Kurallar:
    - ``k in low`` yalnızca len(k) >= 4 (kısa alias substring tuzağı yok)
    - tek-token eşleşme yalnızca tam token (len >= 3)
    """
    low = norm_query(msg)
    if not low:
        return None
    tokens = set(re.findall(r"[\w'’]+", low, flags=re.UNICODE))
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
            elif len(k) >= 4 and k in low:
                score = max(score, 60 + min(20, len(k)))
            elif len(k) >= 3 and k in tokens:
                score = max(score, 50)
            else:
                parts = [p for p in k.split() if len(p) >= 3]
                if len(parts) >= 2 and all(p in tokens or p in low for p in parts):
                    score = max(score, 55 + min(15, len(k)))
        if score > best_score:
            best_score = score
            best = row
    if best_score >= min_score:
        return best
    return None
