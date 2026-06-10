# Created by Ümit & Gökçenur
"""Ana Motor Faz Q2 — paket geçmişi karşılaştırma (bu hafta vs geçen hafta)."""

from __future__ import annotations

import os
import time
from collections import Counter
from typing import Any


def paket_compare_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_PAKET_COMPARE", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _default_period_days() -> int:
    try:
        return max(1, min(30, int(os.environ.get("RUZGAR_ANA_PAKET_COMPARE_DAYS", "7"))))
    except ValueError:
        return 7


def _bucket_events(events: list[dict[str, Any]], start: float, end: float) -> list[dict[str, Any]]:
    return [
        e
        for e in events
        if start <= float(e.get("ts") or 0) < end
    ]


def _stats(events: list[dict[str, Any]]) -> dict[str, Any]:
    by_type = Counter(str(e.get("type") or "—") for e in events)
    file_total = 0
    for e in events:
        try:
            file_total += int(e.get("file_count") or 0)
        except (TypeError, ValueError):
            pass
    sessions = {str(e.get("session_id") or "").strip() for e in events if e.get("session_id")}
    return {
        "event_count": len(events),
        "unique_sessions": len(sessions),
        "file_total": file_total,
        "by_type": dict(by_type),
    }


def build_paket_history_compare(*, period_days: int | None = None, limit: int = 120) -> dict[str, Any]:
    """Bu dönem vs önceki dönem timeline karşılaştırması."""
    if not paket_compare_enabled():
        return {"ok": True, "compare_card": None, "disabled": True}

    period = int(period_days if period_days is not None else _default_period_days())
    from ilim_assistant.ana_motor_oturum_timeline import build_session_timeline

    tl = build_session_timeline(limit=min(120, limit))
    events = list(tl.get("events") or [])
    now = time.time()
    day_sec = 86400.0
    cur_start = now - period * day_sec
    prev_start = now - 2 * period * day_sec

    current = _bucket_events(events, cur_start, now)
    previous = _bucket_events(events, prev_start, cur_start)
    cur_stats = _stats(current)
    prev_stats = _stats(previous)

    delta_events = cur_stats["event_count"] - prev_stats["event_count"]
    delta_sessions = cur_stats["unique_sessions"] - prev_stats["unique_sessions"]
    delta_files = cur_stats["file_total"] - prev_stats["file_total"]
    sign = lambda n: f"+{n}" if n > 0 else str(n)

    body = (
        f"Bu {period} gün: {cur_stats['event_count']} olay · "
        f"{cur_stats['unique_sessions']} oturum · {cur_stats['file_total']} dosya\n"
        f"Önceki {period} gün: {prev_stats['event_count']} olay · "
        f"{prev_stats['unique_sessions']} oturum · {prev_stats['file_total']} dosya\n"
        f"Fark: {sign(delta_events)} olay · {sign(delta_sessions)} oturum · {sign(delta_files)} dosya"
    )

    return {
        "ok": True,
        "period_days": period,
        "current": cur_stats,
        "previous": prev_stats,
        "delta": {
            "events": delta_events,
            "sessions": delta_sessions,
            "files": delta_files,
        },
        "compare_card": {
            "title": f"Karşılaştırma — son {period} gün vs önceki {period} gün",
            "body": body,
            "delta_events": delta_events,
            "delta_sessions": delta_sessions,
            "delta_files": delta_files,
        },
    }
