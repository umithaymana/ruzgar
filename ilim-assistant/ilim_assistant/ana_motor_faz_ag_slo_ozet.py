# Created by Ümit & Gökçenur
"""Ana Motor — Faz AG2: SLO birleşik özet (trend + aksiyon + son rapor)."""

from __future__ import annotations

import os
from typing import Any

FAZ_AG_SLO_OZET_VERSION = "slo-ozet-faz-ag-v1-2026-06-13"


def slo_ozet_enabled() -> bool:
    return os.environ.get("RUZGAR_SLO_OZET", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def build_slo_ozet_panel() -> dict[str, Any]:
    """Tek bakışta SLO durumu — AE trend + AF aksiyon + AD son rapor."""
    if not slo_ozet_enabled():
        return {
            "ok": False,
            "enabled": False,
            "version": FAZ_AG_SLO_OZET_VERSION,
            "summary_tr": "SLO özet kapalı",
        }

    trend: dict[str, Any] = {}
    actions: dict[str, Any] = {}
    last_score = None
    last_summary = ""

    try:
        from ilim_assistant.ana_motor_faz_ae_slo_trend import build_slo_trend_report

        trend = build_slo_trend_report(limit=6)
    except Exception:
        pass
    try:
        from ilim_assistant.ana_motor_faz_af_slo_aksiyon import build_slo_action_plan

        actions = build_slo_action_plan(limit=6)
    except Exception:
        pass
    try:
        from ilim_assistant.ana_motor_faz_ad_slo_gece import load_last_slo_report

        last = load_last_slo_report()
        rep = last.get("weak_point_report") if isinstance(last, dict) else {}
        if isinstance(rep, dict):
            last_score = rep.get("score_pct")
            last_summary = str(rep.get("summary_tr") or "")
    except Exception:
        pass

    parts: list[str] = []
    if last_score is not None:
        parts.append(f"Son skor {last_score}%")
    if trend.get("summary_tr"):
        parts.append(str(trend.get("summary_tr")))
    if actions.get("summary_tr"):
        parts.append(f"Aksiyon: {actions.get('summary_tr')}")

    summary = " · ".join(p for p in parts if p) or "Henüz SLO özeti yok — Canlı SLO koşusu başlatın"

    return {
        "ok": True,
        "enabled": True,
        "version": FAZ_AG_SLO_OZET_VERSION,
        "summary_tr": summary[:320],
        "last_score_pct": last_score,
        "trend": trend.get("trend"),
        "action_count": len(actions.get("actions") or []),
        "trend_summary": trend.get("summary_tr"),
        "action_summary": actions.get("summary_tr"),
    }


def slo_ozet_status() -> dict[str, Any]:
    panel = build_slo_ozet_panel()
    return {
        "enabled": slo_ozet_enabled(),
        "version": FAZ_AG_SLO_OZET_VERSION,
        "summary_tr": panel.get("summary_tr"),
        "last_score_pct": panel.get("last_score_pct"),
    }
