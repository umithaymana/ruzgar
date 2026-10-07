# -*- coding: utf-8 -*-
"""Rüzgar — klasik nefs/psikoloji anlık cevap.

Kaynak: knowledge/ortak_kaynak/alanlar/psikoloji/
Klinik teşhis değildir. Fetva yok.
"""
from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

_ROOT = Path(__file__).resolve().parents[1]
_DIR = _ROOT / "knowledge" / "ortak_kaynak" / "alanlar" / "psikoloji"
_KAV = _DIR / "kavramlar_psikoloji.jsonl"

_CUES = (
    "psikoloji",
    "nefs",
    "nefis",
    "nefs ilmi",
    "ilm-i nefs",
    "sifa nafs",
    "şifâ nefs",
    "shifa nafs",
    "marifat nafs",
    "mizan amal",
    "mizanul amal",
    "mîzân",
    "nâtıka",
    "natika nefs",
    "nefs gucler",
    "nefis güç",
    "idrak",
    "tahayyul",
    "vehim",
    "ahlak nefs",
    "nefs terbiye",
    "klinik",
    "modern psikoloji",
    "duygu",
    "isk",
    "işk",
    "akil nefs",
    "akıl nefs",
)


def _fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower().strip()


def looks_like_psikoloji_question(msg: str) -> bool:
    low = _fold(msg)
    return any(c in low for c in _CUES)


def _norm_query(msg: str) -> str:
    low = _fold(msg)
    low = re.sub(r"[-_/]+", " ", low)
    return re.sub(r"\s+", " ", low).strip()


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

    return match_kavram_row(msg, _load_kavramlar())


def format_psikoloji_reply(row: dict[str, Any]) -> str:
    title = (row.get("baslik") or row.get("id") or "psikoloji").strip()
    body = (row.get("metin") or "").strip()
    note = (row.get("kaynak_notu") or "").strip()
    parts = [f"**{title}**", "", body]
    if note:
        parts.extend(["", f"_{note}_"])
    return "\n".join(parts).strip()


def try_psikoloji_reply(msg: str) -> Optional[str]:
    if not (msg or "").strip():
        return None
    low = _fold(msg)
    is_cue = looks_like_psikoloji_question(msg)
    ask = any(p in low for p in ("nedir", "ne demek", "anlat", "kimdir", "hangi"))
    if not is_cue and not ask:
        return None
    from ilim_assistant.ruzgar_kavram_match import match_kavram_row

    row = match_kavram_row(msg, _load_kavramlar(), min_score=55 if is_cue else 70)
    if row:
        return format_psikoloji_reply(row)
    if is_cue and ask:
        for r in _load_kavramlar():
            if r.get("id") == "psikoloji":
                return format_psikoloji_reply(r)
    return None
