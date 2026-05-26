# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 80: Mega refactor (E2).

30 tur · 16 dosya/tur · 2400 sn bütçe — «mega refactor», «10+ dosya».
"""

from __future__ import annotations

import os
import re
import unicodedata
from typing import Any

FAZ80_VERSION = "programlama-faz80-v1-2026-05-26"
_MEGA_TURNS = 30
_MEGA_BUDGET_SEC = 2400.0
_MEGA_FILES_PER_TURN = 16

_MEGA_RE = re.compile(
    r"(?:mega\s*refactor|büyük\s*refactor|buyuk\s*refactor|10\+\s*dosya|"
    r"on\s*\+\s*dosya|tüm\s*repoyu|tum\s*repoyu|çok\s*dosyalı\s*refactor)",
    re.I,
)


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ80", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz80_enabled() -> bool:
    return _enabled()


def _ascii_fold(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


_MEGA_CTX: dict[str, str] = {}


def set_mega_context(message: str = "", goal: str = "") -> bool:
    """Ajan başında çağrılır — tur limitleri için."""
    active = wants_mega_refactor(message, goal)
    if active:
        _MEGA_CTX["message"] = (message or "")[:2000]
        _MEGA_CTX["goal"] = (goal or "")[:2000]
    else:
        _MEGA_CTX.clear()
    return active


def mega_context_active() -> bool:
    if not _MEGA_CTX:
        return False
    return wants_mega_refactor(
        _MEGA_CTX.get("message", ""),
        _MEGA_CTX.get("goal", ""),
    )


def wants_mega_refactor(message: str, goal: str = "") -> bool:
    if not _enabled():
        return False
    raw = _ascii_fold(f"{message} {goal}")
    return bool(_MEGA_RE.search(raw))


def agent_max_turns_mega() -> int:
    try:
        v = int(os.environ.get("RUZGAR_FAZ80_MAX_TURNS", str(_MEGA_TURNS)))
        return max(10, min(v, 40))
    except ValueError:
        return _MEGA_TURNS


def agent_budget_sec_mega() -> float:
    raw = os.environ.get("RUZGAR_FAZ80_BUDGET_SEC", "").strip()
    if raw:
        try:
            return max(300.0, float(raw))
        except ValueError:
            pass
    return _MEGA_BUDGET_SEC


def max_files_per_turn_mega() -> int:
    try:
        v = int(os.environ.get("RUZGAR_FAZ80_MAX_FILES", str(_MEGA_FILES_PER_TURN)))
        return max(8, min(v, 24))
    except ValueError:
        return _MEGA_FILES_PER_TURN


def effective_agent_limits(message: str, goal: str = "") -> dict[str, Any]:
    """Faz 39/56 için mega override."""
    if not wants_mega_refactor(message, goal):
        return {"mega": False}
    return {
        "mega": True,
        "max_turns": agent_max_turns_mega(),
        "budget_sec": agent_budget_sec_mega(),
        "max_files_per_turn": max_files_per_turn_mega(),
        "version": FAZ80_VERSION,
    }


def mega_refactor_directive(message: str = "") -> str:
    if not wants_mega_refactor(message):
        return ""
    lim = effective_agent_limits(message)
    return (
        "[FAZ 80 — MEGA REFACTOR]\n"
        f"Uzun görev: max {lim['max_turns']} tur · "
        f"{lim['max_files_per_turn']} dosya/tur · "
        f"{int(lim['budget_sec'])} sn bütçe.\n"
        "Önce dosya planı (madde madde), sonra read→write→verify.\n"
    )


def format_mega_status(scope_rel: str = "") -> str:
    lim = effective_agent_limits("mega refactor", scope_rel)
    return (
        f"Ümit abi, **mega refactor modu (Faz 80)** aktif.\n"
        f"Kapsam: `{scope_rel or '?'}` · "
        f"{lim['max_turns']} tur · {lim['max_files_per_turn']} dosya/tur.\n"
        f"({FAZ80_VERSION})"
    )


def faz80_directive() -> str:
    return (
        "[FAZ 80 — MEGA REFACTOR]\n"
        "«mega refactor» veya «10+ dosya» → 30 tur, 16 dosya/tur, 40 dk.\n"
    )


def enrich_health_build(build: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(build or {})
    out["programlama_faz80"] = faz80_enabled()
    out["mega_active"] = mega_context_active()
    return out


def multi_file_cap_nudge_mega(current_count: int, max_files: int) -> str | None:
    if current_count >= max_files:
        return (
            f"[Faz 80] Bu turda {max_files} dosya sınırına ulaşıldı — "
            "verify çalıştır, sonraki turda devam et."
        )
    return None
