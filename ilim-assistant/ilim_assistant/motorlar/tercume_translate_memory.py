# Created by Ümit & Gökçenur
"""Tercüme Faz 4 — parçalar arası terim tutarlılığı (bellek)."""

from __future__ import annotations

import os
import re
import threading
from typing import Any

TERCUME_MEMORY_VERSION = "tercume-translate-memory-v4-faz4-2026-05-31"
_TAIL_MAX = 480
_PAIR_MAX = 28

_lock = threading.Lock()
_sessions: dict[str, dict[str, Any]] = {}


def tercume_memory_enabled() -> bool:
    return os.environ.get("RUZGAR_TERCUME_MEMORY", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _key(source_file: str) -> str:
    raw = (source_file or "inline").strip().replace("\\", "/").lower()
    return raw or "inline"


def _pairs_block(pairs: list[dict[str, str]], tgt_lang: str) -> str:
    if not pairs:
        return ""
    lines = ["TERİM TUTARLILIĞI (önceki bölümlerle aynı çeviriyi kullan):"]
    for p in pairs[-16:]:
        src = p.get("src") or ""
        tgt = p.get("tgt") or ""
        if src and tgt:
            lines.append(f"- «{src}» → {tgt}")
    lines.append(f"({TERCUME_MEMORY_VERSION})\n")
    return "\n".join(lines)


def consistency_block(source_file: str, *, tgt_lang: str = "tr") -> str:
    if not tercume_memory_enabled():
        return ""
    key = _key(source_file)
    with _lock:
        st = _sessions.get(key) or {}
    parts: list[str] = []
    tail = str(st.get("tail") or "").strip()
    if tail:
        parts.append(
            "ÖNCEKİ BÖLÜM SONU (üslup ve terimleri sürdür):\n"
            f"…{tail[-_TAIL_MAX:]}\n"
        )
    pairs = st.get("pairs") or []
    if isinstance(pairs, list) and pairs:
        parts.append(_pairs_block(pairs, tgt_lang))
    return "\n".join(parts).strip()


def seed_pairs_from_glossary(source_file: str, text: str, *, tgt_lang: str) -> None:
    """Glossary eşleşen terimleri belleğe sabitle."""
    if not tercume_memory_enabled():
        return
    from ilim_assistant.motorlar.tercume_glossary import glossary_term_pairs

    pairs = glossary_term_pairs(text, source_file=source_file, tgt_lang=tgt_lang)
    if not pairs:
        return
    key = _key(source_file)
    with _lock:
        st = _sessions.setdefault(key, {"pairs": [], "tail": ""})
        existing = {p.get("src", "").lower() for p in st.get("pairs") or [] if isinstance(p, dict)}
        for src, tgt in pairs:
            sl = src.lower()
            if sl in existing:
                continue
            st["pairs"].append({"src": src, "tgt": tgt})
            existing.add(sl)
            if len(st["pairs"]) > _PAIR_MAX:
                st["pairs"] = st["pairs"][-_PAIR_MAX:]


def record_translation(
    source_file: str,
    *,
    source_text: str,
    translated: str,
    tgt_lang: str = "tr",
) -> None:
    if not tercume_memory_enabled():
        return
    key = _key(source_file)
    tail = (translated or "").strip()
    if not tail:
        return
    seed_pairs_from_glossary(source_file, source_text, tgt_lang=tgt_lang)
    with _lock:
        st = _sessions.setdefault(key, {"pairs": [], "tail": ""})
        st["tail"] = tail[-_TAIL_MAX:]


def clear_session(source_file: str) -> None:
    key = _key(source_file)
    with _lock:
        _sessions.pop(key, None)


def session_snapshot(source_file: str) -> dict[str, Any]:
    key = _key(source_file)
    with _lock:
        st = dict(_sessions.get(key) or {})
    return {
        "ok": True,
        "source_file": source_file or "",
        "pairs": len(st.get("pairs") or []),
        "has_tail": bool(st.get("tail")),
        "version": TERCUME_MEMORY_VERSION,
    }
