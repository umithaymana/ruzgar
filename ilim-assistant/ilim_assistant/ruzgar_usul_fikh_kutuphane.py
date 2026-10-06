# -*- coding: utf-8 -*-
"""Rüzgar — usûl-i fıkıh anlık cevap.

Fetva yok. Kaynak: knowledge/ilim/din/07_usul_fikh/
"""
from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

_ROOT = Path(__file__).resolve().parents[1]
_DIR = _ROOT / "knowledge" / "ilim" / "din" / "07_usul_fikh"
_KAV = _DIR / "kavramlar_usul_fikh.jsonl"

_CUES = (
    "usul fıkıh",
    "usûl-i fıkıh",
    "usulü fıkıh",
    "fıkıh usulü",
    "usul-i fikh",
    "usûl",
    "usul nedir",
    "kıyas",
    "kiyas",
    "icma",
    "icmâ",
    "istihsan",
    "istihsân",
    "nesih",
    "nesh",
    "âm hâs",
    "amm hass",
    "emir nehiy",
    "kavaid",
    "kavâid",
    "varakat",
    "varakât",
    "mustasfa",
    "mustasfâ",
    "burhan usul",
    "el burhan",
    "pezdevi",
    "pezdervî",
    "bazdawi",
    "serahsi usul",
    "ihkam",
    "ihkâm",
    "bahru muhit",
    "bahru'l-muhit",
    "edille",
    "şer'i delil",
    "haber-i vahid",
    "müctehid",
    "ictihad",
    "içtihat",
)


def _fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower().strip()


def looks_like_usul_question(msg: str) -> bool:
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


def format_usul_reply(row: dict[str, Any]) -> str:
    title = (row.get("baslik") or row.get("id") or "usûl").strip()
    body = (row.get("metin") or "").strip()
    note = (row.get("kaynak_notu") or "").strip()
    parts = [f"**{title}**", "", body]
    if note:
        parts.extend(["", f"_{note}_"])
    return "\n".join(parts).strip()


def try_usul_fikh_reply(msg: str) -> Optional[str]:
    if not (msg or "").strip():
        return None
    low = _fold(msg)
    is_cue = looks_like_usul_question(msg)
    ask = any(p in low for p in ("nedir", "ne demek", "anlat", "nelerdir", "farkı", "hangi"))
    if not is_cue and not ask:
        return None
    # «fıkıh nedir» furû'ya gitmeli — usûl cue yoksa dokunma
    if "fıkıh" in low and "usul" not in low and "usûl" not in low and not any(
        c in low for c in ("kıyas", "kiyas", "icma", "icmâ", "varakat", "mustasfa", "kavaid", "kavâid")
    ):
        if not is_cue:
            return None
    row = _match_kavram(msg)
    if row:
        return format_usul_reply(row)
    if is_cue and ask:
        for r in _load_kavramlar():
            if r.get("id") == "usul_fikh":
                return format_usul_reply(r)
    return None
