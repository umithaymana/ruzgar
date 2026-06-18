# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 91: E1 KPI (temiz istatistik + bakım pili).

Parity/agent kirliliğini filtreler; birleşik E1 pilini çalıştırır.
Komut: «e1 bakım» · «e1 kpi»
"""

from __future__ import annotations

import os
import re
import time
from pathlib import Path
from typing import Any

FAZ91_VERSION = "programlama-faz91-v1-2026-05-27"
_MAINT_RE = re.compile(
    r"(?:e1\s+bakim|e1\s+bakım|e1\s+kpi|e1\s+maintenance)",
    re.I,
)
_PARITY_POLLUTION_SCOPE = re.compile(r"smoke-cursor-ref", re.I)
_SMOKE_GOAL_RE = re.compile(
    r"\b(smoke|bench|parity|upgrade\s*runner|e1\s*bakim|e1\s*bakım|root\s*cause\s*learn)\b",
    re.I,
)
_BENCH_SOURCES = frozenset({"smoke", "bench", "parity", "upgrade_runner", "ci"})


def _is_legacy_verify_ok_but_failed(row: dict[str, Any]) -> bool:
    """Eski ajan: detayda doğrulama OK ama success=false (yazım/scope uyumsuzluğu)."""
    if row.get("success"):
        return False
    if str(row.get("source") or "") != "code_agent":
        return False
    detail = str(row.get("detail") or "").lower()
    return "doğrulama: ok" in detail or "dogrulama: ok" in detail


def _is_synthetic_smoke_failure(row: dict[str, Any]) -> bool:
    """Smoke scriptlerinin KPI'ya yazdığı sahte başarısızlıklar."""
    if row.get("success"):
        return False
    if int(row.get("turns_used") or 0) != 0:
        return False
    if float(row.get("elapsed_sec") or 0) != 0:
        return False
    goal = str(row.get("goal") or "").lower()
    detail = str(row.get("detail") or "").lower()
    if "smoke" in goal:
        return True
    return "pytest assert failed in test_health" in detail


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ91", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz91_enabled() -> bool:
    return _enabled()


def wants_e1_maintenance(message: str) -> bool:
    return _enabled() and bool(_MAINT_RE.search((message or "").strip()))


def e1_window_days() -> int:
    try:
        return max(1, min(90, int(os.environ.get("RUZGAR_E1_WINDOW_DAYS", "7"))))
    except ValueError:
        return 7


def _e1_target_rate() -> float:
    try:
        from ilim_assistant.motorlar.programlama_faz102_e1_live import e1_target_rate

        return e1_target_rate()
    except Exception:
        return 0.90


def is_kpi_eligible_outcome(row: dict[str, Any]) -> bool:
    """E1 ölçümünde sayılmaması gereken parity/agent/smoke kirliliği."""
    if not isinstance(row, dict):
        return False
    src = str(row.get("source") or "").strip().lower()
    if src in _BENCH_SOURCES:
        return False
    goal = str(row.get("goal") or "")
    if _SMOKE_GOAL_RE.search(goal):
        return False
    if _is_synthetic_smoke_failure(row):
        return False
    if _is_legacy_verify_ok_but_failed(row):
        return False
    detail = str(row.get("detail") or "").lower()
    if "dosya içeriği" in detail or "dosya icerigi" in detail:
        return False
    scope = str(row.get("scope_rel") or "")
    if _PARITY_POLLUTION_SCOPE.search(scope):
        if not row.get("success") and int(row.get("writes_ok") or 0) == 0:
            return False
    src = str(row.get("source") or "")
    if src == "code_agent" and not row.get("success"):
        if float(row.get("elapsed_sec") or 0) > 600 and int(row.get("writes_ok") or 0) == 0:
            if "smoke-cursor" in scope.lower() or "parity" in scope.lower():
                return False
    return True


def compute_e1_stats(
    workspace_root: str | Path | None,
    *,
    window_days: int | None = None,
) -> dict[str, Any]:
    """Filtrelenmiş canlı görev KPI (E1)."""
    days = window_days if window_days is not None else e1_window_days()
    try:
        from ilim_assistant.motorlar.programlama_faz55 import (
            _load_store,
            _outcomes_path,
        )
    except Exception:
        return {"ok": False, "error": "faz55"}
    target_fn = _e1_target_rate
    path = _outcomes_path(workspace_root)
    if path is None or not path.is_file():
        return {
            "ok": True,
            "total": 0,
            "success_count": 0,
            "success_rate": 0.0,
            "target_rate": target_fn(),
            "meets_target": False,
            "window_days": days,
            "filtered_out": 0,
        }
    store = _load_store(path)
    cutoff = time.time() - days * 86400
    raw = [
        o
        for o in (store.get("outcomes") or [])
        if isinstance(o, dict) and float(o.get("ts") or 0) >= cutoff
    ]
    rows = [o for o in raw if is_kpi_eligible_outcome(o)]
    filtered_out = len(raw) - len(rows)
    if not rows:
        return {
            "ok": True,
            "total": 0,
            "success_count": 0,
            "success_rate": 0.0,
            "target_rate": target_fn(),
            "meets_target": False,
            "window_days": days,
            "filtered_out": filtered_out,
        }
    ok_n = sum(1 for r in rows if r.get("success"))
    total = len(rows)
    rate = ok_n / total if total else 0.0
    target = target_fn()
    return {
        "ok": True,
        "total": total,
        "success_count": ok_n,
        "success_rate": round(rate, 3),
        "target_rate": target,
        "meets_target": rate >= target,
        "window_days": days,
        "filtered_out": filtered_out,
        "recent": rows[-8:],
    }


def run_e1_maintenance(
    workspace_root: str | Path | None,
    *,
    live_llm: bool = False,
) -> dict[str, Any]:
    """Birleşik E1 pili + zayıflık raporu yenile."""
    if not _enabled():
        return {"ok": False, "error": "faz91 kapalı"}
    t0 = time.perf_counter()
    before = compute_e1_stats(workspace_root)
    combined: dict[str, Any] = {}
    try:
        from ilim_assistant.motorlar.programlama_faz88 import run_combined_e1_battery

        combined = run_combined_e1_battery(workspace_root, live_llm=live_llm)
    except Exception as exc:
        combined = {"ok": False, "error": str(exc)[:120]}
    after = compute_e1_stats(workspace_root)
    weakness: dict[str, Any] = {}
    try:
        from ilim_assistant.motorlar.programlama_faz82 import build_weakness_report

        weakness = build_weakness_report(workspace_root)
    except Exception:
        pass
    return {
        "ok": True,
        "version": FAZ91_VERSION,
        "elapsed_sec": round(time.perf_counter() - t0, 2),
        "before": before,
        "after": after,
        "combined_battery": combined,
        "weakness": weakness,
        "improved": float(after.get("success_rate") or 0) > float(
            before.get("success_rate") or 0
        ),
    }


def format_e1_maintenance_report(report: dict[str, Any]) -> str:
    if not report.get("ok"):
        return f"E1 bakım çalışmadı: {report.get('error', '?')}"
    aft = report.get("after") or {}
    bef = report.get("before") or {}
    pct = int(float(aft.get("success_rate") or 0) * 100)
    bpct = int(float(bef.get("success_rate") or 0) * 100)
    tgt = int(float(aft.get("target_rate") or _e1_target_rate()) * 100)
    lines = [
        "**E1 bakım (Faz 91)**",
        "",
        f"KPI: **{aft.get('success_count', 0)}/{aft.get('total', 0)}** ({pct}%) "
        f"— önce {bpct}%",
        f"Pencere: {aft.get('window_days', 7)} gün · filtrelenen: {aft.get('filtered_out', 0)}",
    ]
    if aft.get("meets_target"):
        lines.append(f"Hedef ≥%{tgt} (Blok C): **evet**")
    else:
        lines.append(f"Hedef ≥%{tgt} (Blok C): **hayır**")
    comb = report.get("combined_battery") or {}
    if comb.get("ok"):
        cpct = int(float(comb.get("combined_success_rate") or 0) * 100)
        lines.append(f"Birleşik pil: **{cpct}%**")
    wr = report.get("weakness") or {}
    e1_items = [it for it in wr.get("items") or [] if it.get("id") == "E1"]
    if not e1_items:
        lines.append("E1 zayıflık: **temiz**")
    else:
        lines.append(f"E1: {e1_items[0].get('msg', '?')}")
    lines.append(f"\n({FAZ91_VERSION})")
    return "\n".join(lines)


def maybe_instant_faz91(
    message: str,
    workspace_root: str | Path | None = None,
) -> str | None:
    if not wants_e1_maintenance(message):
        return None
    report = run_e1_maintenance(workspace_root)
    return format_e1_maintenance_report(report)


def enrich_health_build(build: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(build or {})
    out["programlama_faz91"] = faz91_enabled()
    try:
        from ilim_assistant.motorlar.programlama_motoru import repo_root

        root = repo_root(None)
        stats = compute_e1_stats(root)
    except Exception:
        stats = {}
    out["e1_success_rate"] = stats.get("success_rate")
    out["e1_meets_target"] = stats.get("meets_target")
    out["e1_target_rate"] = stats.get("target_rate")
    return out


def faz91_directive() -> str:
    return (
        "[Faz 91 — E1 KPI bakım]\n"
        "Komut: `e1 bakım` — birleşik pil + temiz KPI\n"
        f"Kapat: RUZGAR_FAZ91=0 · {FAZ91_VERSION}\n"
    )
