# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 18: kalite, SLO ve birleşik üstayol raporu.

SLO (varsayılan):
  - scaffold < 30 sn
  - basit patch zinciri (offline) < 120 sn
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

FAZ18_VERSION = "programlama-faz18-v1-2026-05-25"

DEFAULT_SLO_SCAFFOLD_SEC = 30.0
DEFAULT_SLO_SIMPLE_TASK_SEC = 120.0


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ18", "1").strip().lower() not in ("0", "false", "no")


def slo_scaffold_sec() -> float:
    try:
        return float(os.environ.get("RUZGAR_SLO_SCAFFOLD_SEC", str(DEFAULT_SLO_SCAFFOLD_SEC)))
    except ValueError:
        return DEFAULT_SLO_SCAFFOLD_SEC


def slo_simple_task_sec() -> float:
    try:
        return float(
            os.environ.get("RUZGAR_SLO_SIMPLE_TASK_SEC", str(DEFAULT_SLO_SIMPLE_TASK_SEC))
        )
    except ValueError:
        return DEFAULT_SLO_SIMPLE_TASK_SEC


def usta_plan_enabled() -> bool:
    return os.environ.get("RUZGAR_USTA_PLAN", "1").strip().lower() not in ("0", "false", "no")


@dataclass
class SloCheck:
    id: str
    label: str
    ok: bool
    elapsed_sec: float = 0.0
    budget_sec: float = 0.0
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "ok": self.ok,
            "elapsed_sec": round(self.elapsed_sec, 3),
            "budget_sec": self.budget_sec,
            "detail": self.detail,
        }


@dataclass
class QualityRunReport:
    ok: bool
    checks: list[SloCheck] = field(default_factory=list)
    scenarios: list[dict[str, Any]] = field(default_factory=list)
    orchestra: list[dict[str, str]] = field(default_factory=list)
    version: str = FAZ18_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "checks": [c.to_dict() for c in self.checks],
            "scenarios": self.scenarios,
            "orchestra": self.orchestra,
            "slo": {
                "scaffold_budget_sec": slo_scaffold_sec(),
                "simple_task_budget_sec": slo_simple_task_sec(),
            },
            "version": self.version,
        }


def _slug_unique(prefix: str) -> str:
    return f"{prefix}-{int(time.time()) % 100000}"


def run_offline_slo_scenarios(
    workspace_root: str | Path | None,
) -> QualityRunReport:
    """Scaffold → patch onay → delege (zaman ölçümü, API/LLM yok)."""
    from ilim_assistant.motorlar.programlama_faz10 import (
        clear_pending,
        should_delegate_to_programlama,
    )
    from ilim_assistant.motorlar.programlama_faz16 import (
        apply_pending_selective,
        set_job_status,
        stage_pending_enriched,
    )

    checks: list[SloCheck] = []
    scenarios: list[dict[str, Any]] = []
    t0_all = time.monotonic()

    # 1 — Scaffold
    name = _slug_unique("smoke-slo")
    t0 = time.monotonic()
    try:
        from ilim_assistant.motorlar.programlama_faz6 import run_scaffold

        res = run_scaffold("cli_python", name, workspace_root, force=True)
        elapsed = time.monotonic() - t0
        budget = slo_scaffold_sec()
        ok = bool(res.get("ok")) and elapsed <= budget
        checks.append(
            SloCheck(
                "scaffold",
                "Şablon scaffold (cli_python)",
                ok,
                elapsed,
                budget,
                str(res.get("base_dir") or res.get("error") or "")[:120],
            )
        )
        scenarios.append(
            {"id": "scaffold", "ok": res.get("ok"), "elapsed_sec": elapsed, "name": name}
        )
    except Exception as exc:
        elapsed = time.monotonic() - t0
        checks.append(
            SloCheck("scaffold", "Şablon scaffold", False, elapsed, slo_scaffold_sec(), str(exc)[:120])
        )

    # 2 — Patch zinciri
    t0 = time.monotonic()
    scope_rel = f"projects/{name}"
    patch_text = (
        f"@@write {scope_rel}/main.py\n```python\nprint('slo')\n```\n"
    )
    try:
        staged = stage_pending_enriched(patch_text, workspace_root)
        set_job_status(workspace_root, f"{scope_rel}/main.py", "accepted")
        applied = apply_pending_selective(
            workspace_root, mode="accepted", run_verify=False
        )
        elapsed = time.monotonic() - t0
        budget = slo_simple_task_sec()
        ok = bool(staged.get("ok")) and bool(applied.get("ok")) and elapsed <= budget
        checks.append(
            SloCheck(
                "patch_chain",
                "Patch stage → kabul → uygula",
                ok,
                elapsed,
                budget,
                f"applied={applied.get('applied')}",
            )
        )
        scenarios.append({"id": "patch_chain", "ok": ok, "elapsed_sec": elapsed})
    except Exception as exc:
        checks.append(
            SloCheck(
                "patch_chain",
                "Patch zinciri",
                False,
                time.monotonic() - t0,
                slo_simple_task_sec(),
                str(exc)[:120],
            )
        )
    clear_pending(workspace_root)

    # 3 — Delege
    ok_del = should_delegate_to_programlama(
        f"{scope_rel}/main.py pytest duzelt", "genel"
    )
    checks.append(
        SloCheck(
            "delegate",
            "Ana Motor → programlama delege",
            ok_del,
            0.0,
            0.0,
            "genel mod kod isteği",
        )
    )
    scenarios.append({"id": "delegate", "ok": ok_del})

    elapsed_all = time.monotonic() - t0_all
    checks.append(
        SloCheck(
            "offline_total",
            "Offline SLO paketi toplam",
            elapsed_all <= slo_simple_task_sec() * 1.5,
            elapsed_all,
            slo_simple_task_sec() * 1.5,
        )
    )

    orchestra: list[dict[str, str]] = []
    try:
        from ilim_assistant.motorlar.programlama_faz11 import build_programlama_orchestra_steps

        orchestra = build_programlama_orchestra_steps(
            "smoke slo",
            workspace_root,
            phase="done",
            patch_meta={
                "action": "applied",
                "applied": [f"{scope_rel}/main.py"],
            },
        )
    except Exception:
        pass

    ok_all = all(c.ok for c in checks)
    return QualityRunReport(
        ok=ok_all,
        checks=checks,
        scenarios=scenarios,
        orchestra=orchestra,
    )


def merge_live_timings(
    report: QualityRunReport,
    live_rows: list[dict[str, Any]],
) -> QualityRunReport:
    for row in live_rows:
        sid = str(row.get("id") or "")
        elapsed = float(row.get("elapsed_sec") or 0)
        ok = bool(row.get("ok"))
        budget = float(row.get("budget_sec") or 0)
        if sid == "api_scaffold":
            budget = budget or slo_scaffold_sec()
        report.checks.append(
            SloCheck(
                sid,
                str(row.get("label") or sid),
                ok and (not budget or elapsed <= budget),
                elapsed,
                budget,
                str(row.get("detail") or "")[:120],
            )
        )
        report.scenarios.append(row)
    report.ok = all(c.ok for c in report.checks)
    return report


def build_usta_plan_block(report: QualityRunReport) -> str:
    if not usta_plan_enabled():
        return ""
    lines = [
        "[ÜSTAYOL — Faz 18 kalite]",
        "Akis: scaffold -> patch onay -> test/delege -> (istege bagli) commit",
        "",
        "SLO özeti:",
    ]
    for c in report.checks:
        mark = "OK" if c.ok else "FAIL"
        if c.budget_sec > 0:
            lines.append(
                f"  {mark} {c.label}: {c.elapsed_sec:.2f}s / {c.budget_sec:.0f}s"
            )
        else:
            lines.append(f"  {mark} {c.label}: {c.detail or 'ok'}")
    if report.orchestra:
        lines.append("")
        lines.append("Orkestra (Faz 11):")
        for st in report.orchestra:
            lines.append(f"  - {st.get('label')} [{st.get('status')}]")
    return "\n".join(lines)


def format_quality_report(report: QualityRunReport) -> str:
    lines = [
        "Ümit abi, **programlama kalite raporu** (Faz 18):",
        "",
    ]
    for c in report.checks:
        mark = "OK" if c.ok else "FAIL"
        if c.budget_sec > 0:
            lines.append(
                f"{mark} **{c.label}** - {c.elapsed_sec:.2f}s (limit {c.budget_sec:.0f}s)"
            )
        else:
            lines.append(f"{mark} **{c.label}** - {c.detail}")
    block = build_usta_plan_block(report)
    if block:
        lines.extend(["", block])
    lines.append(f"\n({FAZ18_VERSION})")
    overall = "GECTI" if report.ok else "KIRMIZI"
    lines.insert(2, f"Sonuç: **{overall}**")
    return "\n".join(lines)


def faz18_directive() -> str:
    return (
        "[KALİTE — Faz 18]\n"
        f"SLO: scaffold < {int(slo_scaffold_sec())}s · basit görev < {int(slo_simple_task_sec())}s.\n"
        "CI: `python scripts/programlama_smoke.py --ci` veya `--live URL`.\n"
    )
