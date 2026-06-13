# Created by Ümit & Gökçenur
"""Ana Motor — Faz AE1: kalıcı SLO raporlarından trend ve tekrarlayan zayıf turlar."""

from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path
from typing import Any

FAZ_AE_SLO_TREND_VERSION = "slo-trend-faz-ae-v1-2026-06-13"


def slo_trend_enabled() -> bool:
    return os.environ.get("RUZGAR_SLO_TREND", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _reports_dir() -> Path:
    from ilim_assistant.ana_motor_faz_ad_slo_gece import _SLO_REPORTS_DIR

    return _SLO_REPORTS_DIR


def _load_report_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def build_slo_trend_report(*, limit: int = 12) -> dict[str, Any]:
    """Son N kalıcı SLO raporundan skor eğilimi + tekrarlayan zayıf turlar."""
    if not slo_trend_enabled():
        return {
            "ok": False,
            "enabled": False,
            "version": FAZ_AE_SLO_TREND_VERSION,
            "summary_tr": "SLO trend kapalı (RUZGAR_SLO_TREND=0)",
        }

    reports_dir = _reports_dir()
    if not reports_dir.is_dir():
        return {
            "ok": True,
            "enabled": True,
            "version": FAZ_AE_SLO_TREND_VERSION,
            "count": 0,
            "points": [],
            "recurring_weak": [],
            "trend": "none",
            "summary_tr": "Henüz kalıcı SLO raporu yok",
        }

    try:
        lim = max(2, min(30, int(limit)))
    except ValueError:
        lim = 12

    paths = sorted(reports_dir.glob("slo_*.json"), reverse=True)[:lim]
    points: list[dict[str, Any]] = []
    weak_counter: Counter[str] = Counter()
    weak_labels: dict[str, str] = {}

    for path in paths:
        data = _load_report_json(path)
        rep = data.get("weak_point_report") if isinstance(data.get("weak_point_report"), dict) else {}
        score = rep.get("score_pct")
        if score is None and data.get("passed") is not None and data.get("total"):
            try:
                score = round(100.0 * float(data["passed"]) / float(data["total"]), 1)
            except (TypeError, ValueError, ZeroDivisionError):
                score = None
        points.append(
            {
                "file": path.name,
                "saved_at": data.get("saved_at"),
                "score_pct": score,
                "passed": data.get("passed"),
                "total": data.get("total"),
                "pack_ok": data.get("pack_ok"),
                "live": data.get("live"),
                "summary_tr": rep.get("summary_tr"),
            }
        )
        for w in rep.get("weak_turns") or []:
            if not isinstance(w, dict):
                continue
            wid = str(w.get("id") or "").strip()
            if not wid:
                continue
            weak_counter[wid] += 1
            weak_labels[wid] = str(w.get("label") or wid)

    trend = "none"
    if len(points) >= 2:
        newest = points[0].get("score_pct")
        oldest = points[-1].get("score_pct")
        if isinstance(newest, (int, float)) and isinstance(oldest, (int, float)):
            delta = float(newest) - float(oldest)
            if delta >= 5:
                trend = "up"
            elif delta <= -5:
                trend = "down"
            else:
                trend = "stable"

    recurring = [
        {
            "id": wid,
            "label": weak_labels.get(wid, wid),
            "count": cnt,
        }
        for wid, cnt in weak_counter.most_common(5)
        if cnt >= 2
    ]

    if not points:
        summary = "Henüz kalıcı SLO raporu yok"
    elif len(points) == 1:
        summary = f"Tek rapor · skor {points[0].get('score_pct', '—')}%"
    else:
        latest = points[0].get("score_pct", "—")
        trend_tr = {"up": "yükseliş", "down": "düşüş", "stable": "stabil", "none": "—"}.get(
            trend, trend
        )
        rec_part = ""
        if recurring:
            rec_part = f" · tekrar: {', '.join(r['id'] for r in recurring[:3])}"
        summary = f"Son {len(points)} koşu · skor {latest}% · {trend_tr}{rec_part}"

    return {
        "ok": True,
        "enabled": True,
        "version": FAZ_AE_SLO_TREND_VERSION,
        "count": len(points),
        "points": points,
        "recurring_weak": recurring,
        "trend": trend,
        "summary_tr": summary,
    }


def slo_trend_status() -> dict[str, Any]:
    rep = build_slo_trend_report(limit=8)
    return {
        "enabled": slo_trend_enabled(),
        "version": FAZ_AE_SLO_TREND_VERSION,
        "count": rep.get("count", 0),
        "trend": rep.get("trend"),
        "summary_tr": rep.get("summary_tr"),
        "recurring_weak": rep.get("recurring_weak") or [],
    }
