# Created by Ümit & Gökçenur
"""Tercüme Faz 9 — çeviri çıktısı kalite skoru."""

from __future__ import annotations

import re
from typing import Any

QUALITY_VERSION = "tercume-translate-quality-v9-faz9-2026-05-31"


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
    ok = score >= 55 and "Boş çıktı" not in issues
    return {
        "ok": ok,
        "score": round(score, 1),
        "issues": issues,
        "length_ratio": round(ratio, 2),
        "version": QUALITY_VERSION,
    }
