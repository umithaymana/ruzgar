# Created by Ümit & Gökçenur
"""Ana Motor Faz Z3 — multi-hop RAG (ikinci tur genişletilmiş sorgu)."""

from __future__ import annotations

import os
import re
from typing import Any

FAZ_Z_MULTIHOP_VERSION = "ana-motor-multihop-z3-2026-06-10"

_TERM_RE = re.compile(r"[\wçğıöşüÇĞİÖŞÜ]{4,}", re.UNICODE)


def multihop_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_MULTIHOP_RAG", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _max_extra_hits() -> int:
    try:
        return max(1, min(int(os.environ.get("RUZGAR_ANA_MULTIHOP_EXTRA_K", "2")), 4))
    except ValueError:
        return 2


def expand_query_from_hits(
    message: str,
    hits: list[tuple[str, str, float]] | None,
    *,
    term_limit: int = 6,
) -> str:
    """İlk tur isabetlerinden anahtar terim çıkarıp sorguyu genişletir."""
    base = (message or "").strip()
    terms: list[str] = []
    for item in hits or []:
        if not isinstance(item, (list, tuple)) or len(item) < 1:
            continue
        text = str(item[0] or "")
        for tok in _TERM_RE.findall(text):
            low = tok.lower()
            if low in base.lower():
                continue
            if tok[0].isupper() or len(tok) >= 5:
                terms.append(tok)
            if len(terms) >= term_limit:
                break
        if len(terms) >= term_limit:
            break
    if not terms:
        return base
    uniq: list[str] = []
    seen: set[str] = set()
    for t in terms:
        k = t.lower()
        if k in seen:
            continue
        seen.add(k)
        uniq.append(t)
    return f"{base} {' '.join(uniq[:term_limit])}".strip()


def apply_multihop_rag(
    message: str,
    hits: list[tuple[str, str, float]] | None,
    *,
    primary: str = "",
) -> tuple[list[tuple[str, str, float]], dict[str, Any]]:
    """
    İkinci RAG turu: mevcut isabetlerden genişletilmiş sorgu ile ek parça getirir.
    """
    meta: dict[str, Any] = {"applied": False, "version": FAZ_Z_MULTIHOP_VERSION}
    current = list(hits or [])
    if not multihop_enabled():
        meta["reason"] = "disabled"
        return current, meta
    if not current:
        meta["reason"] = "no_first_hits"
        return current, meta
    prim = (primary or "").strip().lower()
    if prim and prim not in ("bilgi", "bilim", "dilbilgisi"):
        meta["reason"] = "primary_skip"
        return current, meta
    if len(current) >= 8:
        meta["reason"] = "enough_hits"
        return current, meta

    expanded = expand_query_from_hits(message, current)
    if expanded == (message or "").strip():
        meta["reason"] = "no_expansion"
        return current, meta

    try:
        from ilim_assistant.main_engine import _merge_hits_dedupe
        from ilim_assistant.rag_store import search as rag_search

        extra_k = _max_extra_hits()
        hop2 = rag_search(expanded, top_k=extra_k + 2)
        merged = _merge_hits_dedupe(current, hop2)
        added = max(0, len(merged) - len(current))
        meta.update(
            {
                "applied": added > 0,
                "expanded_query": expanded[:240],
                "added_hits": added,
                "total_hits": len(merged),
            }
        )
        return merged, meta
    except Exception as exc:
        meta["reason"] = "error"
        meta["error"] = str(exc)[:160]
        return current, meta
