# Created by Ümit & Gökçenur
"""Ana Motor — Faz AD1: SLO gece koşusu raporu kalıcılığı ve zamanlama."""

from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

FAZ_AD_SLO_GECE_VERSION = "slo-gece-faz-ad-v1-2026-06-13"

_ILIM_ROOT = Path(__file__).resolve().parent.parent
_SLO_LAST_JSON = _ILIM_ROOT / ".ruzgar_slo_last_report.json"
_SLO_REPORTS_DIR = _ILIM_ROOT / ".ruzgar_slo_reports"

_gece_lock = threading.Lock()
_gece_started = False


def slo_gece_enabled() -> bool:
    return os.environ.get("RUZGAR_SLO_GECE_KOSUSU", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def slo_gece_interval_hours() -> float:
    try:
        return max(6.0, float(os.environ.get("RUZGAR_SLO_GECE_INTERVAL_HOURS", "24")))
    except ValueError:
        return 24.0


def persist_slo_report(
    pack_out: dict[str, Any],
    report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """SLO paket sonucunu JSON + Markdown olarak kaydet."""
    rep = report or pack_out.get("weak_point_report") or {}
    if not rep and not pack_out.get("results"):
        return {"ok": False, "error": "bos_rapor"}

    try:
        from ilim_assistant.ruzgar_canli_slo_faz_k import format_weak_point_report_markdown
    except Exception:
        format_weak_point_report_markdown = None  # type: ignore[assignment,misc]

    ts = datetime.now(timezone.utc)
    stamp = ts.strftime("%Y-%m-%dT%H%M%SZ")
    payload = {
        "version": FAZ_AD_SLO_GECE_VERSION,
        "saved_at": ts.isoformat(),
        "pack_ok": bool(pack_out.get("ok")),
        "passed": pack_out.get("passed"),
        "total": pack_out.get("total"),
        "live": pack_out.get("live"),
        "weak_point_report": rep,
        "results": pack_out.get("results") or [],
    }

    _SLO_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    md_path = _SLO_REPORTS_DIR / f"slo_{stamp}.md"
    json_path = _SLO_REPORTS_DIR / f"slo_{stamp}.json"

    if format_weak_point_report_markdown:
        md_text = format_weak_point_report_markdown(rep)
        md_path.write_text(md_text, encoding="utf-8")
    else:
        md_path.write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")

    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    _SLO_LAST_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "ok": True,
        "json_path": str(json_path.name),
        "markdown_path": str(md_path.name),
        "saved_at": payload["saved_at"],
    }


def load_last_slo_report() -> dict[str, Any]:
    if not _SLO_LAST_JSON.is_file():
        return {}
    try:
        data = json.loads(_SLO_LAST_JSON.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def list_slo_report_files(*, limit: int = 8) -> list[dict[str, str]]:
    if not _SLO_REPORTS_DIR.is_dir():
        return []
    rows: list[dict[str, str]] = []
    for p in sorted(_SLO_REPORTS_DIR.glob("slo_*.md"), reverse=True)[:limit]:
        rows.append({"name": p.name, "kind": "markdown"})
    for p in sorted(_SLO_REPORTS_DIR.glob("slo_*.json"), reverse=True)[:limit]:
        if not any(r["name"].replace(".json", "") == p.stem for r in rows):
            rows.append({"name": p.name, "kind": "json"})
    return rows[:limit]


def slo_gece_status() -> dict[str, Any]:
    last = load_last_slo_report()
    rep = last.get("weak_point_report") if isinstance(last, dict) else {}
    return {
        "version": FAZ_AD_SLO_GECE_VERSION,
        "gece_enabled": slo_gece_enabled(),
        "interval_hours": slo_gece_interval_hours(),
        "last_saved_at": last.get("saved_at"),
        "last_score_pct": (rep or {}).get("score_pct") if isinstance(rep, dict) else None,
        "last_summary_tr": (rep or {}).get("summary_tr") if isinstance(rep, dict) else None,
        "reports_dir": str(_SLO_REPORTS_DIR.name),
        "recent_files": list_slo_report_files(limit=5),
    }


def _hours_since_last_report() -> float | None:
    last = load_last_slo_report()
    raw = str(last.get("saved_at") or "").strip()
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - dt).total_seconds() / 3600.0
    except Exception:
        return None


def should_run_gece_slo() -> bool:
    if not slo_gece_enabled():
        return False
    try:
        from ilim_assistant.ruzgar_canli_slo_faz_k import get_slo_job_status, slo_pack_enabled

        if not slo_pack_enabled():
            return False
        if get_slo_job_status().get("running"):
            return False
    except Exception:
        pass
    hours = _hours_since_last_report()
    if hours is None:
        return True
    return hours >= slo_gece_interval_hours()


def maybe_schedule_gece_slo_on_startup() -> dict[str, Any]:
    """API açılışında — son rapor eskiyse arka planda canlı SLO."""
    global _gece_started
    if not should_run_gece_slo():
        return {
            "ok": True,
            "skipped": True,
            "reason": "gece_kosusu_gerekmiyor",
            "version": FAZ_AD_SLO_GECE_VERSION,
        }
    with _gece_lock:
        if _gece_started:
            return {"ok": True, "already_scheduled": True}
        _gece_started = True

    try:
        from ilim_assistant.ruzgar_canli_slo_faz_k import (
            resolve_live_slo_base,
            start_slo_pack_background,
        )

        base = resolve_live_slo_base()
        out = start_slo_pack_background(live_base=base, workspace_root=None)
        if out.get("started") or out.get("already_running"):
            print(
                f"[Rüzgar] SLO gece koşusu başlatıldı — {base}",
                flush=True,
            )
        return {**out, "gece": True, "version": FAZ_AD_SLO_GECE_VERSION}
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:200], "version": FAZ_AD_SLO_GECE_VERSION}


def read_slo_report_markdown(filename: str) -> str:
    name = Path(filename).name
    if not name.startswith("slo_") or ".." in name:
        return ""
    path = _SLO_REPORTS_DIR / name
    if not path.is_file() or path.suffix not in (".md", ".json"):
        return ""
    try:
        return path.read_text(encoding="utf-8")[:12000]
    except Exception:
        return ""
