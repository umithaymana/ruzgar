# -*- coding: utf-8 -*-
"""Rüzgar — fıkıh anlık cevap (kavram + mezhep tanıma).

Fetva vermez. Kaynak: knowledge/ilim/din/06_fikh/
"""
from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

_ROOT = Path(__file__).resolve().parents[1]
_DIR = _ROOT / "knowledge" / "ilim" / "din" / "06_fikh"
_KAV = _DIR / "kavramlar_fikh.jsonl"

_FIKH_CUES = (
    "fıkıh",
    "fikih",
    "fikh",
    "mezhep",
    "mezâhib",
    "ilmihal",
    "ilm-i hal",
    "hanefi",
    "hanefî",
    "maliki",
    "mâlikî",
    "şafii",
    "şâfiî",
    "safii",
    "hanbeli",
    "hanbelî",
    "hanbali",
    "ebu hanife",
    "ebû hanîfe",
    "imam malik",
    "imam şafii",
    "ahmed b. hanbel",
    "ahmed bin hanbel",
    "kuduri",
    "kudûrî",
    "minhac",
    "minhâc",
    "muğni",
    "mugni",
    "muvatta",
    "ibadet",
    "ibâdât",
    "muamelat",
    "muâmelât",
    "usul fıkıh",
    "usûl-i fıkıh",
    "içtihat",
    "ictihad",
    "fetva",
    "abdest",
    "taharet",
    "tahâret",
    "zekat",
    "zekât",
    "oruç",
    "namaz hükmü",
    "fıkhi",
    "fıkhî",
)


def _fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower().strip()


def looks_like_fikh_question(msg: str) -> bool:
    low = _fold(msg)
    if any(c in low for c in _FIKH_CUES):
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


def format_fikh_reply(row: dict[str, Any]) -> str:
    title = (row.get("baslik") or row.get("id") or "fıkıh").strip()
    body = (row.get("metin") or "").strip()
    note = (row.get("kaynak_notu") or "").strip()
    parts = [f"**{title}**", "", body]
    if note:
        parts.extend(["", f"_{note}_"])
    return "\n".join(parts).strip()


def try_fikh_reply(msg: str) -> Optional[str]:
    if not (msg or "").strip():
        return None
    low = _fold(msg)
    # Usûl-i fıkıh soruları 07 yoluna gitsin
    if ("usul" in low or "usûl" in low) and "furû" not in low and "furu " not in low:
        return None
    is_cue = looks_like_fikh_question(msg)
    ask = any(
        p in low
        for p in ("nedir", "ne demek", "kimdir", "anlat", "nelerdir", "ne demektir", "hangi")
    )
    if not is_cue and not ask:
        return None
    row = _match_kavram(msg)
    if row:
        return format_fikh_reply(row)
    if is_cue and ask:
        for r in _load_kavramlar():
            if r.get("id") == "fikh":
                return format_fikh_reply(r)
    # «hanefi ilmihal» gibi cue var ama kavram zayıf eşleştiyse mezhep maddesi
    if is_cue:
        for mid, needles in (
            ("hanafi", ("hanefi", "hanefî", "hanafi")),
            ("maliki", ("maliki", "mâlikî")),
            ("shafii", ("safii", "şafii", "şâfiî", "shafii")),
            ("hanbeli", ("hanbeli", "hanbelî", "hanbali")),
            ("ilmihal", ("ilmihal", "ilm-i hal")),
        ):
            if any(n in low for n in needles):
                for r in _load_kavramlar():
                    if r.get("id") == mid:
                        return format_fikh_reply(r)
    return None
