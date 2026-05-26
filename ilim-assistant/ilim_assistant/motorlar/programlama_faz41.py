# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 41: Uzun görev bütçesi (15 tur / 15 dk).

SSE'de kalan süre; erken dur yalnızca 3 boş tur + keşif yok.
"""

from __future__ import annotations

import os
import time
from typing import Any

FAZ41_VERSION = "programlama-faz41-v1-2026-05-25"
_LONG_BUDGET_DEFAULT = 900.0
_LONG_MAX_TURNS_DEFAULT = 15
_EMPTY_STREAK_DEFAULT = 3


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ41", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def long_task_enabled() -> bool:
    return _enabled()


def long_task_budget_sec() -> float:
    try:
        from ilim_assistant.motorlar.programlama_faz80 import (
            agent_budget_sec_mega,
            mega_context_active,
        )

        if mega_context_active():
            return agent_budget_sec_mega()
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz56 import (
            long_task_v2_enabled,
            agent_budget_sec_v2,
        )

        if long_task_v2_enabled():
            return agent_budget_sec_v2()
    except Exception:
        pass
    if not _enabled():
        try:
            from ilim_assistant.motorlar.programlama_faz23 import (
                resolve_code_agent_budget_sec,
            )

            return resolve_code_agent_budget_sec()
        except Exception:
            return 300.0
    raw = os.environ.get("RUZGAR_CODE_AGENT_BUDGET_SEC", "").strip()
    if raw:
        try:
            return max(60.0, float(raw))
        except ValueError:
            pass
    return _LONG_BUDGET_DEFAULT


def long_task_max_turns() -> int:
    try:
        from ilim_assistant.motorlar.programlama_faz56 import (
            long_task_v2_enabled,
            agent_max_turns_v2,
        )

        if long_task_v2_enabled():
            return agent_max_turns_v2()
    except Exception:
        pass
    if not _enabled():
        try:
            from ilim_assistant.motorlar.programlama_faz39 import (
                code_agent_max_turns_effective,
            )

            return code_agent_max_turns_effective()
        except Exception:
            try:
                from ilim_assistant.motorlar.programlama_faz14 import (
                    code_agent_max_turns,
                )

                return code_agent_max_turns()
            except Exception:
                return 8
    try:
        v = int(
            os.environ.get(
                "RUZGAR_CODE_AGENT_MAX_TURNS",
                str(_LONG_MAX_TURNS_DEFAULT),
            )
        )
        return max(3, min(v, 25))
    except ValueError:
        return _LONG_MAX_TURNS_DEFAULT


def long_task_empty_streak_max() -> int:
    if not _enabled():
        try:
            from ilim_assistant.motorlar.programlama_faz19 import (
                code_agent_empty_streak_max,
            )

            return code_agent_empty_streak_max()
        except Exception:
            return 2
    try:
        return max(2, min(int(os.environ.get("RUZGAR_CODE_AGENT_EMPTY_STREAK", "3")), 6))
    except ValueError:
        return _EMPTY_STREAK_DEFAULT


def turn_had_discovery(tool_results: list[dict[str, Any]] | None) -> bool:
    discovery = frozenset({"read", "grep", "symbol", "goto"})
    for r in tool_results or []:
        if r.get("ok") and str(r.get("tool") or "").lower() in discovery:
            return True
    return False


def should_abort_empty_streak(
    state: Any,
    *,
    last_tool_results: list[dict[str, Any]] | None = None,
) -> tuple[bool, str]:
    """Faz 41: keşif varsa boş tur erken durma yumuşatılır."""
    limit = long_task_empty_streak_max()
    if state.total_writes > 0:
        return False, ""
    if state.empty_streak < limit:
        return False, ""
    if _enabled() and turn_had_discovery(last_tool_results):
        if state.empty_streak < limit + 1:
            return (
                False,
                "Faz 41: keşif yapıldı — boş tur limiti uzatıldı.",
            )
    return (
        True,
        f"{limit} tur üst üste dosya yazılmadı — görev durdu (Faz 41).",
    )


class TaskBudgetTracker:
    """Görev süresi — SSE code_agent alanları."""

    def __init__(self, start_mono: float, budget_sec: float) -> None:
        self.start_mono = float(start_mono)
        self.budget_sec = float(budget_sec)

    def elapsed_sec(self) -> float:
        return time.perf_counter() - self.start_mono

    def remaining_sec(self) -> float:
        return max(0.0, self.budget_sec - self.elapsed_sec())

    def enrich_sse(self, event: dict[str, Any] | None) -> dict[str, Any] | None:
        if not (_enabled() or _faz56_budget_on()) or not event or event.get("type") != "agent_step":
            return event
        out = dict(event)
        ca = dict(out.get("code_agent") or {})
        ca["budget_remaining_sec"] = int(self.remaining_sec())
        ca["budget_elapsed_sec"] = int(self.elapsed_sec())
        ca["budget_total_sec"] = int(self.budget_sec)
        ca["faz41"] = True
        try:
            from ilim_assistant.motorlar.programlama_faz56 import long_task_v2_enabled

            if long_task_v2_enabled():
                ca["faz56"] = True
        except Exception:
            pass
        out["code_agent"] = ca
        return out

    def status_suffix(self) -> str:
        rem = int(self.remaining_sec())
        return f" · kalan {rem} sn"


def create_budget_tracker(start_mono: float) -> TaskBudgetTracker | None:
    if not _enabled() and not _faz56_budget_on():
        return None
    return TaskBudgetTracker(start_mono, long_task_budget_sec())


def _faz56_budget_on() -> bool:
    try:
        from ilim_assistant.motorlar.programlama_faz56 import long_task_v2_enabled

        return long_task_v2_enabled()
    except Exception:
        return False


def format_long_task_status(scope_rel: str) -> str:
    b = int(long_task_budget_sec())
    t = long_task_max_turns()
    return (
        f"Uzun görev (Faz 41) — `{scope_rel}` · "
        f"max {t} tur · bütçe {b} sn ({b // 60} dk)"
    )


def faz41_directive() -> str:
    return (
        "[UZUN GÖREV — Faz 41]\n"
        f"Varsayılan: {long_task_max_turns()} tur, {int(long_task_budget_sec())} sn.\n"
        "SSE'de kalan süre görünür. Erken dur: 3 boş tur (keşif varsa tolerans).\n"
        "Kapat: RUZGAR_FAZ41=0\n"
    )
