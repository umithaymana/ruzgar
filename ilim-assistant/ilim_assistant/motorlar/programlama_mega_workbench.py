# Created by Ümit & Gökçenur
"""Blok G — mega görev workbench özeti (UI + API)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

MEGA_WORKBENCH_VERSION = "programlama-mega-workbench-v1-2026-05-29"
_E2_TARGET = 0.90


def e2_target_rate() -> float:
    try:
        return max(0.5, min(0.99, float(os.environ.get("RUZGAR_E2_TARGET_RATE", str(_E2_TARGET)))))
    except ValueError:
        return _E2_TARGET


def build_mega_workbench_payload(workspace_root: str | Path | None) -> dict[str, Any]:
    from ilim_assistant.motorlar.programlama_faz14 import load_agent_state
    from ilim_assistant.motorlar.programlama_faz16 import build_pending_bundle
    from ilim_assistant.motorlar.programlama_faz55 import compute_task_stats
    from ilim_assistant.motorlar.programlama_faz80 import (
        effective_agent_limits,
        mega_context_active,
    )

    st = load_agent_state(workspace_root)
    goal = str(st.get("goal") or "")
    msg = str(st.get("message") or goal)
    mega_lim = effective_agent_limits(msg or "mega refactor", goal)
    mega_active = mega_context_active() or bool(mega_lim.get("mega"))

    touched = list(st.get("touched_files") or [])
    if not touched and isinstance(st.get("touched"), list):
        touched = list(st.get("touched"))

    bundle = build_pending_bundle(workspace_root)
    paths = [p for p in (bundle.get("paths") or []) if p]
    patch_preview = paths[:16]

    status = str(st.get("status") or "idle")
    turn = int(st.get("turn") or 0)
    max_turns = int(st.get("max_turns") or mega_lim.get("max_turns") or 12)
    can_resume = (
        bool(goal)
        and turn > 0
        and turn < max_turns
        and status not in ("idle", "done", "completed", "success")
    )

    verify = {
        "ok": st.get("last_verify_ok"),
        "detail": str(st.get("last_verify_detail") or st.get("last_fail_snippet") or "")[:400],
    }

    stats = {}
    try:
        stats = compute_task_stats(workspace_root, window_days=30)
    except Exception:
        pass
    e2 = stats.get("e2") if isinstance(stats, dict) else None
    rolling = stats.get("rolling_20") if isinstance(stats, dict) else None
    e2_rate = float((e2 or {}).get("success_rate") or (rolling or {}).get("success_rate") or 0)
    e2_total = int((e2 or {}).get("total") or (rolling or {}).get("total") or 0)

    return {
        "ok": True,
        "version": MEGA_WORKBENCH_VERSION,
        "mega": {
            "active": mega_active,
            "limits": mega_lim if mega_lim.get("mega") else {
                "mega": False,
                "max_turns": max_turns,
                "max_files_per_turn": 8,
                "budget_sec": 900,
            },
        },
        "agent": {
            "status": status,
            "scope_rel": st.get("scope_rel"),
            "goal": goal[:500] if goal else "",
            "turn": turn,
            "max_turns": max_turns,
            "can_resume": can_resume,
            "resume_hint": (
                f"görev: {st.get('scope_rel', 'projects')} {goal[:200]}"
                if can_resume and goal
                else ""
            ),
        },
        "touched_files": touched[:32],
        "touched_count": len(touched),
        "patch_plan": {
            "count": int(bundle.get("count") or 0),
            "pending": int((bundle.get("counts") or {}).get("pending") or 0),
            "paths_preview": patch_preview,
        },
        "verify": verify,
        "e2": {
            "target_rate": e2_target_rate(),
            "current_rate": e2_rate,
            "sample_total": e2_total,
            "meets_target": e2_total >= 5 and e2_rate >= e2_target_rate(),
        },
    }
