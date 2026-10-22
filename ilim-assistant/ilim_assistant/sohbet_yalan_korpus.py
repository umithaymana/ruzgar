"""
S0 — Yalan/uydurma ölçüm korpusu (Faz S).

Tek kaynak: data/sohbet_yalan_korpus_s0.json
S1+ SourceRouter smoke’ları bu case alanlarına bağlanır.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

S0_VERSION = "sohbet-yalan-korpus-s0-v1-2026-10-23"
_DATA = Path(__file__).resolve().parent / "data" / "sohbet_yalan_korpus_s0.json"

_REQUIRED = (
    "id",
    "message",
    "tip",
    "needs_live",
    "needs_number",
    "library_ok",
    "allow_parametric",
    "expected_source",
    "forbid",
)


@lru_cache(maxsize=1)
def load_yalan_korpus() -> dict[str, Any]:
    raw = json.loads(_DATA.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or "cases" not in raw:
        raise ValueError("korpus kökü geçersiz")
    return raw


def list_yalan_cases() -> list[dict[str, Any]]:
    return list(load_yalan_korpus().get("cases") or [])


def get_yalan_case(case_id: str) -> dict[str, Any] | None:
    for c in list_yalan_cases():
        if c.get("id") == case_id:
            return c
    return None


def cases_needing_live() -> list[dict[str, Any]]:
    return [c for c in list_yalan_cases() if c.get("needs_live")]


def cases_needing_number() -> list[dict[str, Any]]:
    return [c for c in list_yalan_cases() if c.get("needs_number")]


def validate_korpus() -> list[str]:
    """Boş liste = geçerli."""
    errs: list[str] = []
    try:
        data = load_yalan_korpus()
    except Exception as exc:
        return [str(exc)]
    cases = data.get("cases") or []
    if len(cases) < 20:
        errs.append(f"case sayısı {len(cases)} < 20")
    if len(cases) > 40:
        errs.append(f"case sayısı {len(cases)} > 40 (şişme)")
    ids: set[str] = set()
    for i, c in enumerate(cases):
        if not isinstance(c, dict):
            errs.append(f"case[{i}] dict değil")
            continue
        for k in _REQUIRED:
            if k not in c:
                errs.append(f"{c.get('id', i)} eksik alan: {k}")
        cid = str(c.get("id") or "")
        if not cid:
            errs.append(f"case[{i}] id boş")
        elif cid in ids:
            errs.append(f"duplicate id {cid}")
        else:
            ids.add(cid)
        if not str(c.get("message") or "").strip():
            errs.append(f"{cid} message boş")
        if not isinstance(c.get("forbid"), list):
            errs.append(f"{cid} forbid list değil")
        for b in ("needs_live", "needs_number", "library_ok", "allow_parametric"):
            if not isinstance(c.get(b), bool):
                errs.append(f"{cid} {b} bool değil")
    return errs
