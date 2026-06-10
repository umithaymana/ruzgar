# Created by Ümit & Gökçenur
"""Ana Motor Faz N3 — paket geçmişi grafik özeti."""

from __future__ import annotations

import os
import time
from collections import Counter
from typing import Any


def paket_grafik_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_PAKET_GRAFIK", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _parse_ts(row: dict[str, Any]) -> float:
    raw = row.get("zaman") or row.get("archived_at") or row.get("ts") or ""
    if isinstance(raw, (int, float)):
        return float(raw)
    text = str(raw).strip()
    if not text:
        return 0.0
    try:
        return float(text)
    except ValueError:
        pass
    try:
        from datetime import datetime

        for fmt in ("%Y-%m-%d %H:%M UTC", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(text, fmt).timestamp()
            except ValueError:
                continue
    except Exception:
        pass
    return 0.0


def build_paket_history_summary(*, limit: int = 200) -> dict[str, Any]:
    """Paket geçmişinden özet sayılar ve 7 günlük çubuk verisi."""
    if not paket_grafik_enabled():
        return {"ok": True, "summary": {}, "disabled": True}

    from ilim_assistant.ana_motor_paket_csv import build_paket_history_rows

    rows = build_paket_history_rows(limit=limit)
    if not rows:
        return {"ok": True, "summary": {"total": 0}, "bars": [], "count": 0}

    by_olay = Counter(str(r.get("olay") or "—") for r in rows)
    by_kaynak = Counter(str(r.get("kaynak") or "—") for r in rows)
    file_total = 0
    for r in rows:
        try:
            file_total += int(r.get("dosya_sayisi") or 0)
        except (TypeError, ValueError):
            pass

    now = time.time()
    day_sec = 86400
    buckets = [0] * 7
    labels: list[str] = []
    for i in range(6, -1, -1):
        labels.append(f"-{i}g")
    for r in rows:
        ts = _parse_ts(r)
        if ts <= 0:
            continue
        age_days = int((now - ts) / day_sec)
        if 0 <= age_days < 7:
            buckets[6 - age_days] += 1

    peak = max(buckets) or 1
    bars = [
        {
            "label": labels[i],
            "count": buckets[i],
            "pct": round(100.0 * buckets[i] / peak, 1),
        }
        for i in range(7)
    ]

    return {
        "ok": True,
        "summary": {
            "total": len(rows),
            "file_total": file_total,
            "by_olay": dict(by_olay),
            "by_kaynak": dict(by_kaynak),
            "unique_sessions": len(
                {str(r.get("session_id") or "").strip() for r in rows if r.get("session_id")}
            ),
        },
        "bars": bars,
        "count": len(rows),
    }
