# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 60: Otomasyon kilidi.

- Build uyumsuzluğu tespiti (health expected_rev)
- Haftalık KPI JSON raporu (.ruzgar/weekly_kpi_*.json)
- CI: programlama_smoke --ci + parity full (haftada 1 veya zorla)
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

FAZ60_VERSION = "programlama-faz60-v1-2026-05-26"
_DEFAULT_EXPECTED_REV = "2026-05-26-programlama-faz64-v75"
_FAZ60_PATCH = "v71-hotfix1"
_LAST_FULL_PARITY_FILE = "last_parity_full_run.json"
_WEEKLY_KPI_PREFIX = "weekly_kpi_"


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ60", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz60_enabled() -> bool:
    return _enabled()


def expected_build_rev() -> str:
    return (
        os.environ.get("RUZGAR_EXPECTED_BUILD_REV", "").strip()
        or _DEFAULT_EXPECTED_REV
    )


def build_mismatch_info(server_rev: str | None) -> dict[str, Any]:
    exp = expected_build_rev()
    srv = (server_rev or "").strip()
    mismatch = bool(srv and exp and srv != exp)
    return {
        "ok": not mismatch,
        "server_rev": srv,
        "expected_rev": exp,
        "mismatch": mismatch,
        "restart_hint": (
            "Ruzgar_YenidenBaslat.bat veya .\\Ruzgar.ps1 -ForceRestart"
            if mismatch
            else ""
        ),
        "version": FAZ60_VERSION,
    }


def enrich_health_build(build: dict[str, Any] | None) -> dict[str, Any]:
    """Health yanıtına expected_rev + mismatch ekle."""
    out = dict(build or {})
    exp = expected_build_rev()
    srv = str(out.get("rev") or "").strip()
    out["expected_rev"] = exp
    out["build_mismatch"] = bool(srv and srv != exp)
    out["faz60"] = _enabled()
    if out.get("build_mismatch"):
        out["restart_recommended"] = True
        out["restart_hint"] = (
            "Atölyede «API'yi yeniden başlat» veya Ruzgar_YenidenBaslat.bat"
        )
        out["faz60_patch"] = _FAZ60_PATCH
    try:
        from ilim_assistant.motorlar.programlama_faz61 import enrich_health_build as _e61

        out = _e61(out)
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz62 import enrich_health_build as _e62

        out = _e62(out)
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz63 import enrich_health_build as _e63

        out = _e63(out)
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz64 import enrich_health_build as _e64

        out = _e64(out)
    except Exception:
        pass
    return out


def _ruzgar_cache(workspace_root: str | Path | None) -> Path | None:
    try:
        from ilim_assistant.motorlar.programlama_motoru import repo_root

        root = repo_root(workspace_root)
        if root is None:
            return None
        cache = root / ".ruzgar"
        cache.mkdir(parents=True, exist_ok=True)
        return cache
    except Exception:
        return None


def _iso_week_key(ts: float | None = None) -> str:
    t = datetime.fromtimestamp(ts or time.time(), tz=timezone.utc)
    return f"{t.isocalendar().year}-W{t.isocalendar().week:02d}"


def should_run_weekly_full_parity(
    workspace_root: str | Path | None,
    *,
    force: bool = False,
) -> bool:
    if force or os.environ.get("RUZGAR_FAZ60_FORCE_FULL_PARITY", "").strip() in (
        "1",
        "true",
        "yes",
    ):
        return True
    if not _enabled():
        return False
    cache = _ruzgar_cache(workspace_root)
    if cache is None:
        return True
    path = cache / _LAST_FULL_PARITY_FILE
    now = time.time()
    week = _iso_week_key(now)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if str(data.get("week")) == week and data.get("ok"):
            return False
    except (OSError, json.JSONDecodeError):
        pass
    return True


def record_full_parity_run(
    workspace_root: str | Path | None,
    *,
    ok: bool,
    passed: int = 0,
    total: int = 8,
) -> None:
    cache = _ruzgar_cache(workspace_root)
    if cache is None:
        return
    path = cache / _LAST_FULL_PARITY_FILE
    path.write_text(
        json.dumps(
            {
                "week": _iso_week_key(),
                "ts": time.time(),
                "ok": ok,
                "passed": passed,
                "total": total,
                "version": FAZ60_VERSION,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def run_parity_full_if_due(
    workspace_root: str | Path | None,
    *,
    force: bool = False,
) -> dict[str, Any]:
    """Parity full — haftada bir veya zorla."""
    if not should_run_weekly_full_parity(workspace_root, force=force):
        return {"ok": True, "skipped": True, "reason": "already_ran_this_week"}
    try:
        from ilim_assistant.motorlar.programlama_faz54 import (
            run_parity_smoke_and_persist,
        )

        report = run_parity_smoke_and_persist(workspace_root, mode="full")
        record_full_parity_run(
            workspace_root,
            ok=report.ok,
            passed=report.passed,
            total=report.total,
        )
        return {
            "ok": report.ok,
            "skipped": False,
            "passed": report.passed,
            "total": report.total,
            "mode": "full",
            "version": FAZ60_VERSION,
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:200], "version": FAZ60_VERSION}


def generate_weekly_kpi_report(
    workspace_root: str | Path | None,
) -> dict[str, Any]:
    """Haftalık KPI — görev, metin-only, parity, uyum."""
    week = _iso_week_key()
    rep: dict[str, Any] = {
        "ok": True,
        "week": week,
        "generated_at": time.time(),
        "version": FAZ60_VERSION,
    }
    try:
        from ilim_assistant.motorlar.programlama_faz55 import compute_task_stats

        rep["task_stats"] = compute_task_stats(workspace_root, window_days=7)
    except Exception:
        rep["task_stats"] = {}
    try:
        from ilim_assistant.motorlar.programlama_faz57 import compute_text_only_stats

        rep["text_only_stats"] = compute_text_only_stats(workspace_root, window_days=7)
    except Exception:
        rep["text_only_stats"] = {}
    try:
        from ilim_assistant.motorlar.programlama_faz54 import (
            build_kpi_dashboard,
            load_parity_smoke_json,
        )

        rep["kpi_dashboard"] = build_kpi_dashboard(workspace_root)
        rep["parity_last"] = load_parity_smoke_json()
    except Exception:
        rep["kpi_dashboard"] = {}
        rep["parity_last"] = {}
    cache = _ruzgar_cache(workspace_root)
    if cache is not None:
        out_path = cache / f"{_WEEKLY_KPI_PREFIX}{week}.json"
        out_path.write_text(
            json.dumps(rep, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        rep["saved_path"] = str(out_path)
    return rep


def format_weekly_kpi_report_text(report: dict[str, Any]) -> str:
    if not report.get("ok"):
        return "Haftalık KPI üretilemedi."
    ts = stats = report.get("task_stats") or {}
    to = report.get("text_only_stats") or {}
    lines = [
        f"**Haftalık KPI (Faz 60)** — `{report.get('week')}`",
        f"Görev başarısı: {int(float(stats.get('success_rate', 0)) * 100)}% "
        f"({stats.get('success_count', 0)}/{stats.get('total', 0)})",
        f"Metin-only: {float(to.get('text_only_rate', 0)) * 100:.1f}% "
        f"(hedef <{float(to.get('target_rate', 0.03)) * 100:.0f}%)",
    ]
    pl = report.get("parity_last") or {}
    if pl.get("passed") is not None:
        lines.append(f"Son parity: {pl.get('passed')}/{pl.get('total', 8)}")
    lines.append(f"({FAZ60_VERSION})")
    return "\n".join(lines)


def run_ci_automation(
    workspace_root: str | Path | None,
    *,
    live_url: str | None = None,
    force_full_parity: bool = False,
) -> dict[str, Any]:
    """
    CI paketi: parity quick her zaman; full haftalık.
    programlama_smoke --ci bu fonksiyonu çağırabilir.
    """
    results: dict[str, Any] = {"ok": True, "steps": [], "version": FAZ60_VERSION}
    try:
        from ilim_assistant.motorlar.programlama_faz54 import (
            run_parity_smoke_and_persist,
        )

        quick = run_parity_smoke_and_persist(workspace_root, mode="quick")
        results["steps"].append(
            {
                "name": "parity_quick",
                "ok": quick.ok,
                "passed": quick.passed,
                "total": quick.total,
            }
        )
        if not quick.ok:
            results["ok"] = False
    except Exception as exc:
        results["ok"] = False
        results["steps"].append({"name": "parity_quick", "ok": False, "error": str(exc)[:120]})

    full = run_parity_full_if_due(workspace_root, force=force_full_parity)
    results["steps"].append({"name": "parity_full", **full})
    if not full.get("ok") and not full.get("skipped"):
        results["ok"] = False

    if live_url:
        results["live_url"] = live_url
        results["live_note"] = "Canlı smoke programlama_smoke --ci --live ile"

    kpi = generate_weekly_kpi_report(workspace_root)
    results["weekly_kpi"] = kpi
    return results


def faz60_directive() -> str:
    return (
        "[OTOMASYON — Faz 60]\n"
        "Build kilidi · haftalık KPI JSON · CI parity full (haftada 1).\n"
        "Kapat: RUZGAR_FAZ60=0 · Zorla full: RUZGAR_FAZ60_FORCE_FULL_PARITY=1\n"
    )
