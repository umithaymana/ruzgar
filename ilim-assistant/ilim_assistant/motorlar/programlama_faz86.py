# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 86: Canlı görev pili (E1 ölçümü).

Offline hızlı yol + şablon senaryoları çalıştırır; başarı oranını task_outcomes'a yazar.
Komut: «canlı görev test» · API: GET /api/programlama/live-task-battery
"""

from __future__ import annotations

import os
import re
import time
import unicodedata
from pathlib import Path
from typing import Any

FAZ86_VERSION = "programlama-faz86-v1-2026-05-27"
_BATTERY_RE = re.compile(
    r"(?:canli\s+gorev\s+test|canlı\s+görev\s+test|live\s+task\s+battery|gorev\s+pili|görev\s+pili)",
    re.I,
)


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ86", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz86_enabled() -> bool:
    return _enabled()


def wants_live_task_battery(message: str) -> bool:
    return _enabled() and bool(_BATTERY_RE.search((message or "").strip()))


def maybe_instant_faz86(
    message: str,
    workspace_root: str | Path | None = None,
) -> str | None:
    if not wants_live_task_battery(message):
        return None
    report = run_live_task_battery(workspace_root)
    return format_live_battery_report(report)


def inject_turn1_preflight_context(
    base: str,
    workspace_root: str | Path | None,
    scope_rel: str,
    goal: str,
) -> str:
    """Tur 1 LLM öncesi zorunlu keşif — E1 yazım öncesi bağlam."""
    if not _enabled():
        return base
    try:
        from ilim_assistant.motorlar.programlama_faz34 import (
            discovery_tool_specs,
            run_tool_specs,
            tool_first_enabled,
        )

        if not tool_first_enabled():
            return base
        specs = discovery_tool_specs(
            workspace_root, scope_rel, goal=goal, max_reads=3
        )
        if not specs:
            return base
        results, block = run_tool_specs(
            specs, workspace_root, scope_rel=scope_rel
        )
        if not block.strip():
            return base
        n = len(results)
        return (
            base.rstrip()
            + f"\n\n[Tur 1 ön keşif — Faz 86]\n"
            f"{n} araç çalıştı (read/grep).\n{block[:8000]}"
        )
    except Exception:
        return base


def _run_scenario(
    workspace_root: str | Path | None,
    *,
    name: str,
    scope_rel: str,
    goal: str,
    setup_broken_health: bool = False,
) -> dict[str, Any]:
    t0 = time.perf_counter()
    detail_parts: list[str] = []
    writes_ok = 0

    if setup_broken_health:
        try:
            from ilim_assistant.motorlar.programlama_faz6 import run_scaffold

            slug = scope_rel.split("/")[-1]
            service = slug.replace("-", "_")
            sc = run_scaffold("fastapi_api", slug, workspace_root, force=True)
            if not sc.get("ok"):
                return {
                    "name": name,
                    "ok": False,
                    "detail": f"setup scaffold: {sc.get('error')}",
                    "elapsed_sec": time.perf_counter() - t0,
                }
            from ilim_assistant.motorlar.programlama_motoru import ProgramlamaAraclari

            rel = f"{scope_rel}/app/main.py"
            broken = f'''"""FastAPI — battery."""
from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health() -> dict[str, str]:
    return {{"ok": "false", "service": "{service}"}}
'''
            w = ProgramlamaAraclari(workspace_root).write(rel, broken)
            if not w.ok:
                return {
                    "name": name,
                    "ok": False,
                    "detail": w.detail,
                    "elapsed_sec": time.perf_counter() - t0,
                }
            detail_parts.append("setup: health ok=false")
        except Exception as exc:
            return {
                "name": name,
                "ok": False,
                "detail": str(exc)[:120],
                "elapsed_sec": time.perf_counter() - t0,
            }

    try:
        from ilim_assistant.motorlar.programlama_faz85 import try_fast_deterministic_task

        fast = try_fast_deterministic_task(
            workspace_root, scope_rel, goal, allow_agent_fallback=False
        )
    except Exception as exc:
        return {
            "name": name,
            "ok": False,
            "detail": str(exc)[:120],
            "elapsed_sec": time.perf_counter() - t0,
        }

    elapsed = time.perf_counter() - t0
    if fast is None:
        return {
            "name": name,
            "ok": False,
            "detail": "hızlı yol uygun değil (ajan gerekir)",
            "elapsed_sec": elapsed,
            "source": "none",
        }

    ok = bool(fast.get("ok"))
    writes_ok = int(fast.get("writes_ok") or 0)
    detail_parts.append(str(fast.get("detail") or ""))
    source = str(fast.get("source") or "fast")

    try:
        from ilim_assistant.motorlar.programlama_faz55 import record_task_outcome

        record_task_outcome(
            workspace_root,
            scope_rel=scope_rel,
            goal=goal[:200],
            success=ok,
            turns_used=0,
            verify_ok=bool(fast.get("verify_ok")),
            writes_ok=writes_ok,
            elapsed_sec=elapsed,
            source=f"live_battery_{source}",
            detail=f"[{name}] " + " ".join(detail_parts)[:200],
        )
    except Exception:
        pass

    return {
        "name": name,
        "ok": ok,
        "detail": "\n".join(detail_parts),
        "elapsed_sec": round(elapsed, 2),
        "source": source,
        "writes_ok": writes_ok,
        "verify_ok": bool(fast.get("verify_ok")),
    }


def run_live_task_battery(workspace_root: str | Path | None) -> dict[str, Any]:
    """Üç senaryo — tamamı LLM'siz hızlı yol üzerinden (E1 proxy)."""
    if not _enabled():
        return {"ok": False, "error": "faz86 kapalı"}
    stamp = int(time.time())
    scenarios = [
        {
            "name": "scaffold+health+version",
            "scope_rel": f"projects/live-bat-{stamp}-a",
            "goal": "yeni api yap health endpointine version ekle pytest geçir",
            "setup_broken_health": False,
        },
        {
            "name": "fix-health-ok",
            "scope_rel": f"projects/live-bat-{stamp}-b",
            "goal": "health düzelt ok false pytest geçir",
            "setup_broken_health": True,
        },
        {
            "name": "verify-only",
            "scope_rel": f"projects/live-bat-{stamp}-a",
            "goal": "tüm testleri çalıştır pytest geçir",
            "setup_broken_health": False,
        },
    ]
    rows: list[dict[str, Any]] = []
    for spec in scenarios:
        rows.append(
            _run_scenario(
                workspace_root,
                name=spec["name"],
                scope_rel=spec["scope_rel"],
                goal=spec["goal"],
                setup_broken_health=bool(spec.get("setup_broken_health")),
            )
        )

    ok_count = sum(1 for r in rows if r.get("ok"))
    total = len(rows)
    rate = ok_count / total if total else 0.0
    try:
        from ilim_assistant.motorlar.programlama_faz55 import compute_task_stats

        stats = compute_task_stats(workspace_root, window_days=7)
    except Exception:
        stats = {}

    try:
        from ilim_assistant.motorlar.programlama_faz82 import build_weakness_report

        wr = build_weakness_report(workspace_root)
    except Exception:
        wr = {}

    return {
        "ok": True,
        "version": FAZ86_VERSION,
        "generated_at": time.time(),
        "total": total,
        "success_count": ok_count,
        "success_rate": rate,
        "meets_target_70": rate >= 0.7,
        "scenarios": rows,
        "task_stats_7d": stats,
        "weakness": wr,
    }


def format_live_battery_report(report: dict[str, Any]) -> str:
    if not report.get("ok"):
        return f"Canlı görev pili çalışmadı: {report.get('error', '?')}"
    lines = [
        "**Canlı görev pili (Faz 86)** — LLM'siz senaryolar",
        "",
        f"Sonuç: **{report.get('success_count')}/{report.get('total')}** "
        f"(**{int(float(report.get('success_rate', 0)) * 100)}%**)",
    ]
    if report.get("meets_target_70"):
        lines.append("Hedef >=%70: **evet**")
    else:
        lines.append("Hedef >=%70: **hayir** (ajan dongusu ile devam onerilir)")
    lines.append("")
    for row in report.get("scenarios") or []:
        mark = "OK" if row.get("ok") else "KIRMIZI"
        det = str(row.get("detail") or "")[:120].replace("\n", " ")
        lines.append(
            f"- **{row.get('name')}** [{mark}] "
            f"({row.get('elapsed_sec')}s · {row.get('source', '?')}) — {det}"
        )
    ts = report.get("task_stats_7d") or {}
    if ts.get("total", 0) > 0:
        pct = int(float(ts.get("success_rate", 0)) * 100)
        lines.append("")
        lines.append(
            f"Son 7 gün canlı görev KPI: **{pct}%** "
            f"({ts.get('success_count')}/{ts.get('total')})"
        )
    lines.append(f"\n({FAZ86_VERSION})")
    return "\n".join(lines)


def faz86_directive() -> str:
    return (
        "[Faz 86 — canlı görev pili]\n"
        "Komut: `canlı görev test` — hızlı yol senaryolarını ölçer.\n"
        f"Kapat: RUZGAR_FAZ86=0 · {FAZ86_VERSION}\n"
    )


def enrich_health_build(build: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(build or {})
    out["programlama_faz86"] = faz86_enabled()
    return out
