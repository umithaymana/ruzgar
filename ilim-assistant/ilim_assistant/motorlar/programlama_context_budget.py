# Created by Ümit & Gökçenur
"""
Programlama motoru — bağlam bütçe yöneticisi.

Öncelik sırasıyla parçaları birleştirir; üst karakter sınırını aşmaz.
Varsayılan: RUZGAR_PROG_CONTEXT_MAX_CHARS=14000
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

PROG_CONTEXT_BUDGET_VERSION = "programlama-context-budget-v2-2026-06-16"


@dataclass
class ContextPart:
    key: str
    text: str
    priority: int = 50
    max_chars: int | None = None


@dataclass
class BudgetReport:
    total_chars: int
    budget_chars: int
    dropped_keys: list[str] = field(default_factory=list)
    trimmed_keys: list[str] = field(default_factory=list)


def context_budget_enabled() -> bool:
    return os.environ.get("RUZGAR_PROG_CONTEXT_BUDGET", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def max_context_chars() -> int:
    try:
        return max(2000, int(os.environ.get("RUZGAR_PROG_CONTEXT_MAX_CHARS", "14000")))
    except ValueError:
        return 14000


def max_file_read_chars() -> int:
    """Tek dosya okuma üst sınırı (Adım 5). Env: LOCAL_TOOLS_FILE_MAX_CHARS."""
    try:
        return max(500, int(os.environ.get("LOCAL_TOOLS_FILE_MAX_CHARS", "12000")))
    except ValueError:
        return 12000


def parallel_read_cap() -> int:
    """Paralel keşif — dosya başına okuma (toplam bütçenin ~yarısı tavan)."""
    return min(max_file_read_chars(), max(4000, max_context_chars() // 2))


def _trim(text: str, cap: int) -> tuple[str, bool]:
    t = (text or "").strip()
    if len(t) <= cap:
        return t, False
    return t[: cap - 20].rstrip() + "\n…[kısaltıldı]", True


def assemble_context(parts: list[ContextPart]) -> tuple[str, BudgetReport]:
    """Öncelik yüksekten düşüğe; bütçe dolunca düşük öncelikli parçalar atılır."""
    budget = max_context_chars()
    ordered = sorted(parts, key=lambda p: (-int(p.priority), p.key))
    kept: list[tuple[str, str, int]] = []
    used = 0
    dropped: list[str] = []
    trimmed: list[str] = []

    for part in ordered:
        cap = part.max_chars if part.max_chars is not None else budget
        body, was_trimmed = _trim(part.text, min(cap, budget - used))
        if not body:
            dropped.append(part.key)
            continue
        need = len(body) + (4 if kept else 0)
        if used + need > budget:
            dropped.append(part.key)
            continue
        if was_trimmed:
            trimmed.append(part.key)
        kept.append((part.key, body, part.priority))
        used += need

    lines = [body for _, body, _ in kept]
    report = BudgetReport(
        total_chars=sum(len(x) for x in lines),
        budget_chars=budget,
        dropped_keys=dropped,
        trimmed_keys=trimmed,
    )
    return "\n\n".join(lines), report


def budget_wrap_light_context(raw: str, *, meta: dict[str, Any] | None = None) -> str:
    """Faz 21 çıktısını bütçe altında tut."""
    if not context_budget_enabled():
        return raw
    parts = [
        ContextPart(key="core", text=raw, priority=100, max_chars=max_context_chars()),
    ]
    if meta:
        hint = str(meta.get("route") or meta.get("scope") or "").strip()
        if hint:
            parts.append(ContextPart(key="route", text=f"[ROUTE] {hint}", priority=90, max_chars=200))
    out, rep = assemble_context(parts)
    if rep.dropped_keys or rep.trimmed_keys:
        out += (
            f"\n\n({PROG_CONTEXT_BUDGET_VERSION} · "
            f"{rep.total_chars}/{rep.budget_chars} karakter"
        )
        if rep.trimmed_keys:
            out += f" · kısaltılan: {', '.join(rep.trimmed_keys[:4])}"
        if rep.dropped_keys:
            out += f" · atılan: {', '.join(rep.dropped_keys[:4])}"
        out += ")"
    return out


def directive_priority_map() -> dict[str, int]:
    """Directive öncelikleri — yüksek = korunur."""
    return {
        "system": 100,
        "usta": 95,
        "session": 90,
        "summary": 88,
        "handoff": 86,
        "import_chain": 87,
        "context_v3": 85,
        "active_file": 84,
        "editor": 83,
        "index": 80,
        "symbol": 78,
        "tools": 75,
        "patch": 74,
        "explore": 72,
        "faz20": 70,
        "faz14": 68,
        "faz98": 65,
        "misc_directive": 40,
        "user": 100,
    }
