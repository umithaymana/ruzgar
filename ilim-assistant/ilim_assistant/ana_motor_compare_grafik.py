# Created by Ümit & Gökçenur
"""Ana Motor Faz R1 — karşılaştırma çift çubuk grafiği."""

from __future__ import annotations

import os
from typing import Any


def compare_chart_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_COMPARE_CHART", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def build_compare_dual_chart(*, period_days: int = 7, limit: int = 120) -> dict[str, Any]:
    """Bu dönem vs önceki dönem — çift çubuk verisi (olay/oturum/dosya)."""
    if not compare_chart_enabled():
        return {"ok": True, "groups": [], "disabled": True}

    from ilim_assistant.ana_motor_paket_karsilastir import build_paket_history_compare

    cmp = build_paket_history_compare(period_days=period_days, limit=limit)
    if not cmp.get("ok"):
        return {"ok": False, "error": "Karşılaştırma verisi alınamadı."}

    cur = cmp.get("current") if isinstance(cmp.get("current"), dict) else {}
    prev = cmp.get("previous") if isinstance(cmp.get("previous"), dict) else {}
    metrics = [
        ("Olay", int(cur.get("event_count") or 0), int(prev.get("event_count") or 0)),
        ("Oturum", int(cur.get("unique_sessions") or 0), int(prev.get("unique_sessions") or 0)),
        ("Dosya", int(cur.get("file_total") or 0), int(prev.get("file_total") or 0)),
    ]
    peak = max((max(c, p) for _, c, p in metrics), default=0) or 1
    groups: list[dict[str, Any]] = []
    for label, c_val, p_val in metrics:
        groups.append(
            {
                "label": label,
                "current": c_val,
                "previous": p_val,
                "current_pct": round(100.0 * c_val / peak, 1),
                "previous_pct": round(100.0 * p_val / peak, 1),
            }
        )

    return {
        "ok": True,
        "period_days": cmp.get("period_days") or period_days,
        "groups": groups,
        "delta": cmp.get("delta"),
        "legend": {"current": "Bu dönem", "previous": "Önceki dönem"},
    }
