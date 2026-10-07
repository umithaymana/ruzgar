# -*- coding: utf-8 -*-
"""Rüzgar — edebiyat anlık cevap (Faz 1 Arap + Faz 2 dil/dönem).

Kaynak: knowledge/ortak_kaynak/alanlar/edebiyat_sanat/
Fetva yok. Telifli modern tam metin yok.
"""
from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

_ROOT = Path(__file__).resolve().parents[1]
_DIR = _ROOT / "knowledge" / "ortak_kaynak" / "alanlar" / "edebiyat_sanat"
_KAV = _DIR / "kavramlar_edebiyat.jsonl"

_CUES = (
    "edebiyat",
    "adab",
    "kelile",
    "kalila",
    "makamat",
    "maqamat",
    "makâme",
    "hariri",
    "harîrî",
    "hemedani",
    "hamadhani",
    "bediuzzaman",
    "ebu temmam",
    "ebû temmâm",
    "abu tammam",
    "ibn kuteybe",
    "ibn qutayba",
    "şiir ve şair",
    "sir ve suara",
    "buhturi",
    "buhturî",
    "maarri",
    "maʿarrî",
    "el maarri",
    # Faz 2
    "divan",
    "aruz",
    "gazel",
    "kaside",
    "mesnevi",
    "fuzuli",
    "fuzûlî",
    "baki",
    "bâkî",
    "nedim",
    "yunus emre",
    "seyh galib",
    "şeyh gâlib",
    "tanzimat",
    "servet",
    "servet-i",
    "milli edebiyat",
    "millî edebiyat",
    "halk edebiyat",
    "cumhuriyet edebiyat",
    "bati edebiyat",
    "batı edebiyat",
    "homeros",
    "shakespeare",
    "romantizm",
    "realizm",
    "yakin donem",
    "yakın dönem",
    "cagdas edebiyat",
    "çağdaş edebiyat",
    "modernizm",
)


def _fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower().strip()


def looks_like_edebiyat_question(msg: str) -> bool:
    low = _fold(msg)
    return any(_fold(c) in low for c in _CUES)


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


def format_edebiyat_reply(row: dict[str, Any]) -> str:
    title = (row.get("baslik") or row.get("id") or "edebiyat").strip()
    body = (row.get("metin") or "").strip()
    note = (row.get("kaynak_notu") or "").strip()
    parts = [f"**{title}**", "", body]
    if note:
        parts.extend(["", f"_{note}_"])
    return "\n".join(parts).strip()


def try_edebiyat_reply(msg: str) -> Optional[str]:
    if not (msg or "").strip():
        return None
    low = _fold(msg)
    is_cue = looks_like_edebiyat_question(msg)
    ask = any(p in low for p in ("nedir", "ne demek", "anlat", "kimdir", "hangi"))
    if not is_cue and not ask:
        return None
    row = _match_kavram(msg)
    if row:
        return format_edebiyat_reply(row)
    if is_cue and ask:
        for r in _load_kavramlar():
            if r.get("id") == "edebiyat":
                return format_edebiyat_reply(r)
    return None
