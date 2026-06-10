# Created by Ümit & Gökçenur
"""Ana Motor Faz S1 — karşılaştırma CSV/PDF raporu."""

from __future__ import annotations

import csv
import io
import json
import os
import time
from typing import Any


def compare_export_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_COMPARE_EXPORT", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _build_compare_report(*, period_days: int = 7) -> dict[str, Any]:
    from ilim_assistant.ana_motor_paket_karsilastir import build_paket_history_compare

    cmp = build_paket_history_compare(period_days=period_days)
    if not cmp.get("ok"):
        return {"ok": False, "error": "Karşılaştırma verisi alınamadı."}
    return {"ok": True, "compare": cmp, "period_days": period_days}


def export_compare_csv(*, period_days: int = 7) -> dict[str, Any]:
    if not compare_export_enabled():
        return {"ok": False, "error": "Karşılaştırma dışa aktarım kapalı."}
    base = _build_compare_report(period_days=period_days)
    if not base.get("ok"):
        return base
    cmp = base["compare"]
    cur = cmp.get("current") if isinstance(cmp.get("current"), dict) else {}
    prev = cmp.get("previous") if isinstance(cmp.get("previous"), dict) else {}
    delta = cmp.get("delta") if isinstance(cmp.get("delta"), dict) else {}
    rows = [
        {
            "metrik": "olay",
            "bu_donem": cur.get("event_count", 0),
            "onceki_donem": prev.get("event_count", 0),
            "fark": delta.get("events", 0),
        },
        {
            "metrik": "oturum",
            "bu_donem": cur.get("unique_sessions", 0),
            "onceki_donem": prev.get("unique_sessions", 0),
            "fark": delta.get("sessions", 0),
        },
        {
            "metrik": "dosya",
            "bu_donem": cur.get("file_total", 0),
            "onceki_donem": prev.get("file_total", 0),
            "fark": delta.get("files", 0),
        },
    ]
    buf = io.StringIO()
    buf.write("\ufeff")
    writer = csv.DictWriter(buf, fieldnames=["metrik", "bu_donem", "onceki_donem", "fark"])
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    period = int(cmp.get("period_days") or period_days)
    return {
        "ok": True,
        "csv": buf.getvalue(),
        "row_count": len(rows),
        "filename": f"ruzgar_ana_motor_karsilastirma_{period}g.csv",
    }


def export_compare_json(*, period_days: int = 7) -> dict[str, Any]:
    if not compare_export_enabled():
        return {"ok": False, "error": "Karşılaştırma dışa aktarım kapalı."}
    base = _build_compare_report(period_days=period_days)
    if not base.get("ok"):
        return base
    cmp = base["compare"]
    payload = {
        "generated_at": time.time(),
        "period_days": cmp.get("period_days") or period_days,
        "current": cmp.get("current"),
        "previous": cmp.get("previous"),
        "delta": cmp.get("delta"),
        "compare_card": cmp.get("compare_card"),
    }
    period = int(payload["period_days"])
    return {
        "ok": True,
        "json": json.dumps(payload, ensure_ascii=False, indent=2),
        "filename": f"ruzgar_ana_motor_karsilastirma_{period}g.json",
    }


def export_compare_pdf(*, period_days: int = 7) -> dict[str, Any]:
    if not compare_export_enabled():
        return {"ok": False, "error": "Karşılaştırma dışa aktarım kapalı."}
    base = _build_compare_report(period_days=period_days)
    if not base.get("ok"):
        return base
    cmp = base["compare"]
    card = cmp.get("compare_card") if isinstance(cmp.get("compare_card"), dict) else {}
    body = str(card.get("body") or "").strip()
    if not body:
        return {"ok": False, "error": "Karşılaştırma raporu boş."}
    from ilim_assistant.ana_motor_paket_export import build_minimal_pdf

    lines = body.split("\n")
    period = int(cmp.get("period_days") or period_days)
    pdf_bytes = build_minimal_pdf(
        lines,
        title=f"Ruzgar Karsilastirma {period}g",
    )
    return {
        "ok": True,
        "pdf": pdf_bytes,
        "filename": f"ruzgar_ana_motor_karsilastirma_{period}g.pdf",
    }
