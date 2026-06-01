# Created by Ümit & Gökçenur
"""Tercüme Faz 9 — çeviri çıktısı kalite skoru."""

from __future__ import annotations

import re
from typing import Any

QUALITY_VERSION = "tercume-translate-quality-v14b-2026-05-29"
QUALITY_PASS_SCORE = 55.0
QUALITY_WARN_SCORE = 75.0


def score_translation(
    source: str,
    output: str,
    *,
    tgt_lang: str = "tr",
) -> dict[str, Any]:
    from ilim_assistant.motorlar.tercume_atolye import translation_leaked_source_language

    src = (source or "").strip()
    out = (output or "").strip()
    issues: list[str] = []
    score = 100.0

    if not out:
        return {
            "ok": False,
            "score": 0,
            "issues": ["Boş çıktı"],
            "version": QUALITY_VERSION,
        }

    if len(out) < max(12, len(src) // 8):
        issues.append("Çok kısa çıktı")
        score -= 35

    if translation_leaked_source_language(out, tgt_lang):
        issues.append("Hedef dilde İngilizce sızıntı")
        score -= 30

    if re.search(r"\[HATA|something went wrong|I cannot translate", out, re.I):
        issues.append("Model hata metni")
        score -= 40

    ratio = len(out) / max(len(src), 1)
    if ratio > 3.5:
        issues.append("Kaynak metinden çok uzun — gereksiz ekleme olabilir")
        score -= 15

    score = max(0.0, min(100.0, score))
    ok = score >= QUALITY_PASS_SCORE and "Boş çıktı" not in issues
    return {
        "ok": ok,
        "score": round(score, 1),
        "issues": issues,
        "length_ratio": round(ratio, 2),
        "version": QUALITY_VERSION,
        "pass_threshold": QUALITY_PASS_SCORE,
    }


def summarize_chunk_qualities(outputs: list[dict[str, Any]]) -> dict[str, Any]:
    """Faz 14B — sayfa/parça kalite özetini job durumuna yazar."""
    scores: list[float] = []
    low_pages: list[str] = []
    for o in outputs:
        if not isinstance(o, dict) or not o.get("ok"):
            continue
        raw = o.get("quality_score")
        if raw is None:
            continue
        try:
            sc = float(raw)
        except (TypeError, ValueError):
            continue
        scores.append(sc)
        if sc < QUALITY_PASS_SCORE:
            low_pages.append(str(o.get("page") or "?"))
    if not scores:
        return {
            "avg_score": None,
            "min_score": None,
            "low_count": 0,
            "pages_scored": 0,
            "low_pages": [],
            "version": QUALITY_VERSION,
        }
    return {
        "avg_score": round(sum(scores) / len(scores), 1),
        "min_score": round(min(scores), 1),
        "low_count": len(low_pages),
        "pages_scored": len(scores),
        "low_pages": low_pages[:12],
        "pass_threshold": QUALITY_PASS_SCORE,
        "version": QUALITY_VERSION,
    }
