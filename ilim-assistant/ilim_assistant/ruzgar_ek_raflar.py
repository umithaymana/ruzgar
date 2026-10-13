# -*- coding: utf-8 -*-
"""Eksik ilim rafları — anlık cevap. Sıra _ek_raf_sira.json ile gelir.

Teşhis, avukatlık, yatırım ve suç tarifi yok.
"""
from __future__ import annotations

import json
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

_ROOT = Path(__file__).resolve().parents[1]
_ALAN = _ROOT / "knowledge" / "ortak_kaynak" / "alanlar"
_SIRA = _ALAN / "_ek_raf_sira.json"

_ASK = ("nedir", "ne demek", "anlat", "acikla", "açıkla", "nasil", "nasıl", "farki", "farkı")


def _fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower().strip()


@lru_cache(maxsize=1)
def _order() -> tuple[str, ...]:
    if not _SIRA.is_file():
        return ()
    rows = json.loads(_SIRA.read_text(encoding="utf-8"))
    return tuple(str(r["id"]) for r in sorted(rows, key=lambda x: int(x["sira"])))


@lru_cache(maxsize=32)
def _load(raf_id: str) -> tuple[dict[str, Any], ...]:
    path = _ALAN / raf_id / "kavramlar.jsonl"
    if not path.is_file():
        return ()
    out: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return tuple(out)


def _format(row: dict[str, Any]) -> str:
    title = (row.get("baslik") or row.get("id") or "").strip()
    body = (row.get("metin") or "").strip()
    note = (row.get("kaynak_notu") or "").strip()
    parts = [f"**{title}**", "", body]
    if note:
        parts.extend(["", f"_{note}_"])
    return "\n".join(parts).strip()


def try_ek_raf_reply(msg: str) -> Optional[str]:
    raw = (msg or "").strip()
    if not raw:
        return None
    low = _fold(raw)
    ask = any(p in low for p in _ASK)
    from ilim_assistant.ruzgar_kavram_match import match_kavram_row

    for raf_id in _order():
        rows = list(_load(raf_id))
        if not rows:
            continue
        cue = False
        for row in rows:
            keys = [row.get("baslik") or "", *(row.get("aliases") or [])]
            if any(len(_fold(k)) >= 5 and _fold(k) in low for k in keys):
                cue = True
                break
        if not cue and not ask:
            continue
        hit = match_kavram_row(raw, rows, min_score=55 if cue else 70)
        if hit:
            return _format(hit)
    return None
