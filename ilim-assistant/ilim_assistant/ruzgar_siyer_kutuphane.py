# -*- coding: utf-8 -*-
"""Rüzgar — siyer anlık cevap.

Fetva yok. Kaynak: knowledge/ilim/din/08_siyer/
"""
from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

_ROOT = Path(__file__).resolve().parents[1]
_DIR = _ROOT / "knowledge" / "ilim" / "din" / "08_siyer"
_KAV = _DIR / "kavramlar_siyer.jsonl"

_CUES = (
    "siyer",
    "sîre",
    "siret",
    "sira nabi",
    "peygamber hayatı",
    "hz muhammed hayatı",
    "megazi",
    "megâzî",
    "magazi",
    "maghazi",
    "gazve",
    "seriyye",
    "bi'set",
    "biset",
    "hicret",
    "bedir",
    "uhud",
    "hendek",
    "ahzab",
    "mekke fethi",
    "feth-i mekke",
    "veda haccı",
    "veda hutbesi",
    "ibn hisham",
    "ibn hişam",
    "ibn hisâm",
    "vakidi",
    "vâkıdî",
    "ibn sad",
    "ibn sa'd",
    "tabakat",
    "tabakât",
    "taberi tarih",
    "taberî",
)


def _fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower().strip()


def looks_like_siyer_question(msg: str) -> bool:
    low = _fold(msg)
    return any(c in low for c in _CUES)


@lru_cache(maxsize=1)
def _load_kavramlar() -> list[dict[str, Any]]:
    if not _KAV.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in _KAV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def _match_kavram(msg: str) -> Optional[dict[str, Any]]:
    from ilim_assistant.ruzgar_kavram_match import match_kavram_row

    return match_kavram_row(msg, _load_kavramlar(), min_score=70)


def format_siyer_reply(row: dict[str, Any]) -> str:
    title = (row.get("baslik") or row.get("id") or "siyer").strip()
    body = (row.get("metin") or "").strip()
    note = (row.get("kaynak_notu") or "").strip()
    parts = [f"**{title}**", "", body]
    if note:
        parts.extend(["", f"_{note}_"])
    return "\n".join(parts).strip()


def try_siyer_reply(msg: str) -> Optional[str]:
    if not (msg or "").strip():
        return None
    low = _fold(msg)
    is_cue = looks_like_siyer_question(msg)
    ask = any(p in low for p in ("nedir", "ne demek", "anlat", "nelerdir", "hangi", "kimdir"))
    if not is_cue and not ask:
        return None
    row = _match_kavram(msg)
    if row:
        return format_siyer_reply(row)
    if is_cue and ask:
        for r in _load_kavramlar():
            if r.get("id") == "siyer":
                return format_siyer_reply(r)
    return None
