# Created by Ümit & Gökçenur
"""Ana Motor Faz O3 — timeline filtre (olay türü / oturum / tarih aralığı)."""

from __future__ import annotations

import os
import time
from typing import Any


def timeline_filter_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_TIMELINE_FILTER", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def apply_timeline_filters(
    events: list[dict[str, Any]],
    *,
    event_type: str | None = None,
    session_id: str | None = None,
    since_days: int | None = None,
    until_days: int | None = None,
) -> list[dict[str, Any]]:
    """Zaman çizelgesi olaylarını filtrele."""
    if not timeline_filter_enabled():
        return list(events or [])
    rows = list(events or [])
    et = (event_type or "").strip().lower()
    if et:
        rows = [e for e in rows if str(e.get("type") or "").lower() == et]
    sid = (session_id or "").strip().lower()
    if sid:
        rows = [
            e
            for e in rows
            if sid in str(e.get("session_id") or "").lower()
        ]
    now = time.time()
    day_sec = 86400.0
    if since_days is not None:
        try:
            sd = max(0, int(since_days))
            cutoff = now - sd * day_sec
            rows = [e for e in rows if float(e.get("ts") or 0) >= cutoff]
        except (TypeError, ValueError):
            pass
    if until_days is not None:
        try:
            ud = max(0, int(until_days))
            if ud > 0:
                older_than = now - ud * day_sec
                rows = [e for e in rows if float(e.get("ts") or 0) <= older_than]
        except (TypeError, ValueError):
            pass
    return rows


def build_filtered_session_timeline(
    *,
    limit: int = 24,
    event_type: str | None = None,
    session_id: str | None = None,
    since_days: int | None = None,
    until_days: int | None = None,
) -> dict[str, Any]:
    """Filtreli oturum zaman çizelgesi."""
    from ilim_assistant.ana_motor_oturum_timeline import build_session_timeline

    raw_limit = max(limit, limit * 3) if any(
        x is not None for x in (event_type, session_id, since_days, until_days)
    ) else limit
    base = build_session_timeline(limit=min(120, raw_limit))
    events = base.get("events") or []
    filtered = apply_timeline_filters(
        events,
        event_type=event_type,
        session_id=session_id,
        since_days=since_days,
        until_days=until_days,
    )
    trimmed = filtered[: max(1, limit)]
    payload = dict(base)
    payload["events"] = trimmed
    payload["count"] = len(trimmed)
    payload["filter"] = {
        "event_type": event_type,
        "session_id": session_id,
        "since_days": since_days,
        "until_days": until_days,
        "total_before_filter": len(events),
    }
    return payload
