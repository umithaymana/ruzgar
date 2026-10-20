# Created by Ümit & Gökçenur
"""Blok G — mega görev workbench özeti (UI + API)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

MEGA_WORKBENCH_VERSION = "programlama-mega-workbench-v1.1-2026-10-20"
_E2_TARGET = 0.90


def e2_target_rate() -> float:
    try:
        return max(0.5, min(0.99, float(os.environ.get("RUZGAR_E2_TARGET_RATE", str(_E2_TARGET)))))
    except ValueError:
        return _E2_TARGET


def build_mega_workbench_payload(workspace_root: str | Path | None) -> dict[str, Any]:
    """E2 ürün kartı: tur · plan · touched · verify · devam · KPI."""
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
    e2: dict[str, Any] = {}
    try:
        from ilim_assistant.motorlar.programlama_faz103_e2 import compute_e2_stats

        e2 = compute_e2_stats(workspace_root, window_days=30)
    except Exception:
        e2 = stats.get("e2") if isinstance(stats, dict) else {}
        e2 = e2 if isinstance(e2, dict) else {}
    rolling = stats.get("rolling_20") if isinstance(stats, dict) else None
    e2_rate = float(
        e2.get("success_rate")
        or (rolling or {}).get("success_rate")
        or 0
    )
    e2_total = int(e2.get("total") or (rolling or {}).get("total") or 0)

    named_paths: list[str] = []
    multi_plan = ""
    path_hint = "idle"
    scope_rel = str(st.get("scope_rel") or "")
    try:
        from ilim_assistant.motorlar.programlama_faz56 import (
            build_multi_file_plan_block,
            extract_named_paths,
            looks_like_multi_file_task,
        )
        from ilim_assistant.motorlar.programlama_yuzey_bridge import _path_hint_for_goal

        if goal:
            path_hint = _path_hint_for_goal(goal)
            named_paths = extract_named_paths(goal)
            if looks_like_multi_file_task(goal) or path_hint.startswith("agent"):
                multi_plan = build_multi_file_plan_block(
                    workspace_root,
                    scope_rel=scope_rel,
                    message=msg or goal,
                    goal=goal,
                    turn=max(1, turn),
                    touched_files=touched,
                )
    except Exception:
        pass

    status_label = {
        "running": "çalışıyor",
        "done": "bitti",
        "completed": "bitti",
        "success": "başarılı",
        "idle": "bekliyor",
        "failed": "kırmızı",
        "error": "hata",
    }.get(status.lower(), status or "bekliyor")

    return {
        "ok": True,
        "version": MEGA_WORKBENCH_VERSION,
        "product": True,
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
            "status_label": status_label,
            "scope_rel": scope_rel,
            "goal": goal[:500] if goal else "",
            "turn": turn,
            "max_turns": max_turns,
            "can_resume": can_resume,
            "resume_hint": (
                f"görev: {scope_rel or 'projects'} {goal[:200]}"
                if can_resume and goal
                else ""
            ),
            "path_hint": path_hint,
            "named_paths": named_paths[:12],
        },
        "multi_file_plan": multi_plan[:1200] if multi_plan else "",
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
            "success_count": int(e2.get("success_count") or 0),
        },
    }
