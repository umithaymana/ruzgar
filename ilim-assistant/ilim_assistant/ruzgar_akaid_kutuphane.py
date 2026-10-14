# -*- coding: utf-8 -*-
"""Rüzgar — akaid / kelâm anlık cevap (kavram + eser tanıma).

Fetva vermez. Kaynak: knowledge/ilim/din/04_akaid/kavramlar_akaid.jsonl
Arapça corpus RAG üzerinden sohbet boru hattında kullanılır.
"""
from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

_ROOT = Path(__file__).resolve().parents[1]
_DIR = _ROOT / "knowledge" / "ilim" / "din" / "04_akaid"
_KAV = _DIR / "kavramlar_akaid.jsonl"

_AKAID_CUES = (
    "akaid",
    "akâid",
    "itikad",
    "itikât",
    "kelam",
    "kelâm",
    "maturidi",
    "mâtürîdî",
    "matüridi",
    "esari",
    "eşari",
    "eş'arî",
    "ashari",
    "tevhid",
    "tevhîd",
    "kader",
    "kesb",
    "rüyet",
    "ru'yet",
    "sifat",
    "sıfat",
    "nübüvvet",
    "nubuvvet",
    "ehl-i sünnet",
    "ehli sunnet",
    "kitabu't-tevhid",
    "kitabü't-tevhid",
    "el-luma",
    "makalat",
    "makâlât",
)


def _fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower().strip()


def looks_like_akaid_question(msg: str) -> bool:
    low = _fold(msg)
    if any(c in low for c in _AKAID_CUES):
        return True
    if re.search(r"\b(iman|küfür|kufur|şirk|shirk)\b", low) and any(
        x in low for x in ("nedir", "ne demek", "tanım", "anlat")
    ):
        return True
    return False


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


def format_akaid_reply(row: dict[str, Any]) -> str:
    title = (row.get("baslik") or row.get("id") or "akaid").strip()
    body = (row.get("metin") or "").strip()
    note = (row.get("kaynak_notu") or "").strip()
    parts = [f"**{title}**", "", body]
    if note:
        parts.extend(["", f"_{note}_"])
    return "\n".join(parts).strip()


def try_akaid_reply(msg: str) -> Optional[str]:
    """Akaid niyeti + kavram eşleşmesi varsa anlık cevap."""
    if not (msg or "").strip():
        return None
    if not looks_like_akaid_question(msg):
        # Hâlâ doğrudan kavram sorusu olabilir: «maturidi nedir»
        row = _match_kavram(msg)
        if row and any(
            p in _fold(msg) for p in ("nedir", "ne demek", "kimdir", "anlat", "nelerdir")
        ):
            return format_akaid_reply(row)
        return None
    row = _match_kavram(msg)
    if not row:
        # Genel akaid sorusu — ana madde
        for r in _load_kavramlar():
            if r.get("id") == "akaid":
                return format_akaid_reply(r)
        return None
    return format_akaid_reply(row)
