# -*- coding: utf-8 -*-
"""Rüzgar — tasavvuf / ahlâk anlık cevap.

Fetva yok. Kaynak: knowledge/ilim/din/09_ahlak_tasavvuf/
"""
from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

_ROOT = Path(__file__).resolve().parents[1]
_DIR = _ROOT / "knowledge" / "ilim" / "din" / "09_ahlak_tasavvuf"
_KAV = _DIR / "kavramlar_tasavvuf.jsonl"

_CUES = (
    "tasavvuf",
    "sufi",
    "sufizm",
    "ihya",
    "ihyâ",
    "gazali",
    "gazzali",
    "gazâlî",
    "kimya saadet",
    "kimya-yı",
    "geylani",
    "geylânî",
    "abdulkadir",
    "abdülkadir",
    "futuh gayb",
    "fütûhu'l-gayb",
    "feth rabbani",
    "fethu'r",
    "mevlana",
    "mevlânâ",
    "mesnevi",
    "mesnevî",
    "divan kebir",
    "divân-ı kebîr",
    "imam rabbani",
    "rabbânî",
    "sirhindi",
    "mektubat",
    "mektûbât",
    "ibn arabi",
    "ibnü'l-arabi",
    "ibnul arabi",
    "fusus",
    "fusûs",
    "futuhat",
    "fütûhât",
    "kalbin hastal",
    "kalp hastal",
)


def _fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower().strip()


def looks_like_tasavvuf_question(msg: str) -> bool:
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
    low = _fold(msg)
    tokens = set(re.findall(r"[\w'’]+", low, flags=re.UNICODE))
    best: Optional[dict[str, Any]] = None
    best_score = 0
    for row in _load_kavramlar():
        keys = [_fold(row.get("baslik") or "")]
        keys.extend(_fold(a) for a in (row.get("aliases") or []))
        score = 0
        for k in keys:
            if not k:
                continue
            if k == low or low == f"{k} nedir" or low.startswith(f"{k} nedir"):
                score = max(score, 100)
            elif k in low:
                score = max(score, 60 + min(20, len(k)))
            elif k in tokens:
                score = max(score, 40)
        if score > best_score:
            best_score = score
            best = row
    if best_score >= 40:
        return best
    return None


def format_tasavvuf_reply(row: dict[str, Any]) -> str:
    title = (row.get("baslik") or row.get("id") or "tasavvuf").strip()
    body = (row.get("metin") or "").strip()
    note = (row.get("kaynak_notu") or "").strip()
    parts = [f"**{title}**", "", body]
    if note:
        parts.extend(["", f"_{note}_"])
    try:
        from ilim_assistant.ruzgar_ortak_kaynak import format_atif, lookup_kaynak

        kid_map = {
            "ihya": "gazali_ihya",
            "kimya saadet": "gazali_kimya_saadet",
            "mesnevi": "mevlana_mesnevi",
            "divan kebir": "mevlana_divan_kebir",
            "mektubat": "imam_rabbani_mektubat",
            "futuh gayb": "geylani_futuh_gayb",
            "feth rabbani": "geylani_feth_rabbani",
            "fusus": "ibn_arabi_fusus",
            "futuhat": "ibn_arabi_futuhat",
        }
        kid = kid_map.get(_fold(title))
        if kid:
            atif = format_atif(lookup_kaynak(kid))
            if atif:
                parts.extend(["", atif])
    except Exception:
        pass
    return "\n".join(parts).strip()


def try_tasavvuf_reply(msg: str) -> Optional[str]:
    if not (msg or "").strip():
        return None
    low = _fold(msg)
    is_cue = looks_like_tasavvuf_question(msg)
    ask = any(p in low for p in ("nedir", "ne demek", "anlat", "nelerdir", "hangi", "kimdir", "gore"))
    if not is_cue and not ask:
        return None
    row = _match_kavram(msg)
    if row:
        return format_tasavvuf_reply(row)
    if is_cue and ask:
        for r in _load_kavramlar():
            if r.get("id") == "tasavvuf":
                return format_tasavvuf_reply(r)
    return None
