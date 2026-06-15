# Created by Ümit & Gökçenur
"""
Programlama motoru — S7 gerçek monorepo canlı gate.

`ilim-assistant/` paketi üzerinde cerrahi patch + import doğrulama + havuz okuma.
Yalnızca tests/monorepo_live/probe_marker.py dosyasına dokunur.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from typing import Any

from ilim_assistant.motorlar.programlama_motoru import repo_root

MONOREPO_LIVE_VERSION = "programlama-monorepo-live-v1-2026-06-15"
_PROBE_REL = "ilim-assistant/tests/monorepo_live/probe_marker.py"
_PROBE_V1 = 'MARKER = "live-v1"\n'
_PROBE_V2 = 'MARKER = "live-v2"\n'


def monorepo_live_enabled() -> bool:
    return os.environ.get("RUZGAR_PROG_MONOREPO_LIVE", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _probe_path(workspace_root: str | Path | None) -> Path | None:
    root = repo_root(workspace_root)
    if root is None:
        return None
    return root / _PROBE_REL.replace("/", os.sep)


def _reset_probe(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_PROBE_V1, encoding="utf-8")


def _import_marker(path: Path) -> str:
    spec = importlib.util.spec_from_file_location("ruzgar_monorepo_probe", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("probe import spec yok")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return str(getattr(mod, "MARKER", ""))


def run_monorepo_live_gate(workspace_root: str | Path | None) -> dict[str, Any]:
    """
    Canlı monorepo görevi (deterministik, LLM yok):
    1) probe v1 yaz
    2) cerrahi patch → v2
    3) import doğrula
    4) havuz yaz/oku doğrula
    5) stack import smoke
    """
    checks: dict[str, bool] = {}
    detail_parts: list[str] = []
    if not monorepo_live_enabled():
        return {
            "ok": False,
            "detail": "RUZGAR_PROG_MONOREPO_LIVE=0",
            "checks": checks,
            "version": MONOREPO_LIVE_VERSION,
        }

    probe = _probe_path(workspace_root)
    root = repo_root(workspace_root)
    if probe is None or root is None:
        return {
            "ok": False,
            "detail": "workspace_root bulunamadı",
            "checks": checks,
            "version": MONOREPO_LIVE_VERSION,
        }

    try:
        _reset_probe(probe)
        checks["probe_reset"] = probe.read_text(encoding="utf-8") == _PROBE_V1
    except OSError as exc:
        return {
            "ok": False,
            "detail": f"probe_reset: {exc}",
            "checks": checks,
            "version": MONOREPO_LIVE_VERSION,
        }

    msg = (
        f"@@patch {_PROBE_REL}\n"
        "```search-replace\n"
        "<<<SEARCH\n"
        'MARKER = "live-v1"\n'
        "===\n"
        'MARKER = "live-v2"\n'
        ">>>REPLACE\n"
        "```"
    )
    try:
        from ilim_assistant.motorlar.programlama_patch import apply_patch_jobs

        reps = apply_patch_jobs(msg, root)
        checks["patch_ok"] = bool(reps) and reps[0].ok
        if not checks["patch_ok"]:
            detail_parts.append(reps[0].detail if reps else "patch yok")
    except Exception as exc:
        checks["patch_ok"] = False
        detail_parts.append(f"patch: {exc}")

    try:
        checks["import_v2"] = _import_marker(probe) == "live-v2"
    except Exception as exc:
        checks["import_v2"] = False
        detail_parts.append(f"import: {exc}")

    try:
        from ilim_assistant.motorlar.programlama_havuz_bridge import record_tool_outcome

        record_tool_outcome(
            root,
            patches=[_PROBE_REL],
            pytest_ok=True,
            goal="S7 monorepo live gate",
            scope_rel="ilim-assistant/tests/monorepo_live",
        )
        checks["havuz_write"] = True
    except Exception:
        checks["havuz_write"] = False

    try:
        from ilim_assistant.ana_motor_programlama_havuz import (
            build_programlama_havuz_context_block,
            read_programlama_havuz_snapshot,
        )

        snap = read_programlama_havuz_snapshot()
        blk = build_programlama_havuz_context_block(mode_norm="programlama", message="devam")
        checks["havuz_read"] = isinstance(snap.get("last_tool_outcome"), dict) and bool(blk)
    except Exception:
        checks["havuz_read"] = False

    try:
        from ilim_assistant.motorlar.programlama_router import (
            PROG_ROUTER_VERSION,
            classify_route,
            run_monorepo_router_smoke,
        )
        from ilim_assistant.motorlar.programlama_context_budget import assemble_context, ContextPart
        from ilim_assistant.motorlar.programlama_parallel_explore import parallel_explore_enabled

        checks["router_import"] = bool(PROG_ROUTER_VERSION)
        checks["router_classify"] = classify_route("görev: demo test", "programlama").value == "agent"
        checks["budget_ok"] = len(assemble_context([ContextPart("t", "x", 50)])[0]) > 0
        checks["explore_flag"] = parallel_explore_enabled()
        smoke = run_monorepo_router_smoke(root)
        checks["stack_smoke"] = bool(smoke.get("ok"))
    except Exception as exc:
        checks["stack_smoke"] = False
        detail_parts.append(f"stack: {exc}")

    ok = all(checks.values()) if checks else False
    return {
        "ok": ok,
        "detail": "; ".join(detail_parts) if detail_parts else "monorepo live gate",
        "checks": checks,
        "probe_rel": _PROBE_REL,
        "version": MONOREPO_LIVE_VERSION,
    }
