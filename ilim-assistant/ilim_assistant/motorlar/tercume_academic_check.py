# Created by Umit & Gokcenur
"""Tercume calisma paneli icin akademik iddia/kanit hizli kontrolu."""

from __future__ import annotations

import re
from typing import Any

ACADEMIC_CHECK_VERSION = "tercume-academic-check-v1-2026-06-02"

_CITATION_RE = re.compile(
    r"(\[[0-9]{1,3}\]|\([A-ZÇĞİÖŞÜ][^)]+,\s*(?:19|20)\d{2}[a-z]?\)|doi:\s*10\.\d{4,9}/\S+|https?://\S+)",
    re.IGNORECASE,
)


def _split_paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n+", (text or "").strip()) if p.strip()]


def _looks_like_claim(para: str) -> bool:
    if len(para) < 70:
        return False
    if para.endswith(":"):
        return False
    return bool(re.search(r"\b(sonuc|goster|etki|ilisk|nedeni|bulgu|tespit|yaklasim|model|yontem)\b", para, re.I))


def analyze_academic_support(source_text: str, target_text: str) -> dict[str, Any]:
    src_ps = _split_paragraphs(source_text)
    tgt_ps = _split_paragraphs(target_text)
    claim_rows: list[dict[str, Any]] = []
    cited = 0
    uncited = 0
    for i, p in enumerate(tgt_ps[:180]):
        claim = _looks_like_claim(p)
        has_cite = bool(_CITATION_RE.search(p))
        if has_cite:
            cited += 1
        if claim and not has_cite:
            uncited += 1
        if claim or has_cite:
            claim_rows.append(
                {
                    "index": i,
                    "claim_like": claim,
                    "has_citation": has_cite,
                    "excerpt": p[:220],
                }
            )

    coverage = 100.0
    if claim_rows:
        coverage = round(100.0 * cited / max(len(claim_rows), 1), 1)
    risk = "low" if uncited == 0 else "medium" if uncited <= 4 else "high"
    hints: list[str] = []
    if uncited:
        hints.append("Kaynak atfi olmayan iddia benzeri paragraflari dipnot veya atifla destekleyin.")
    if not cited:
        hints.append("Metinde gorunur atif bulunmadi. [1] veya (Yazar, 2020) bicimi kullanin.")
    if len(tgt_ps) > len(src_ps) * 2 and len(src_ps) > 0:
        hints.append("Hedef metin kaynaktan cok uzun; yorum ekleri akademik atifla ayrilmali.")
    return {
        "ok": True,
        "version": ACADEMIC_CHECK_VERSION,
        "paragraphs": len(tgt_ps),
        "claim_rows": claim_rows[:120],
        "claims_total": len([r for r in claim_rows if r.get("claim_like")]),
        "citations_total": cited,
        "uncited_claims": uncited,
        "citation_coverage": coverage,
        "risk": risk,
        "hints": hints[:6],
    }
