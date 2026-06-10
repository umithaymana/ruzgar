# Created by Ümit & Gökçenur
"""Ana Motor Faz P3 — timeline olaylarından haftalık özet kartı."""

from __future__ import annotations

import os
import time
from collections import Counter
from typing import Any


def weekly_summary_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_WEEKLY_SUMMARY", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _default_days() -> int:
    try:
        return max(1, min(30, int(os.environ.get("RUZGAR_ANA_WEEKLY_SUMMARY_DAYS", "7"))))
    except ValueError:
        return 7


def build_weekly_timeline_summary(*, days: int | None = None, limit: int = 80) -> dict[str, Any]:
    """Son N gün timeline olaylarından özet kart üret."""
    if not weekly_summary_enabled():
        return {"ok": True, "summary_card": None, "disabled": True}
    period = int(days if days is not None else _default_days())
    from ilim_assistant.ana_motor_timeline_filtre import build_filtered_session_timeline

    tl = build_filtered_session_timeline(limit=limit, since_days=period)
    events = list(tl.get("events") or [])
    if not events:
        return {
            "ok": True,
            "period_days": period,
            "event_count": 0,
            "summary_card": {
                "title": f"Haftalık özet — son {period} gün",
                "body": "Bu dönemde kayıtlı timeline olayı yok.",
                "event_count": 0,
            },
        }

    by_type = Counter(str(e.get("type") or "—") for e in events)
    file_total = 0
    for e in events:
        try:
            file_total += int(e.get("file_count") or 0)
        except (TypeError, ValueError):
            pass
    sessions = {str(e.get("session_id") or "").strip() for e in events if e.get("session_id")}

    highlights: list[str] = []
    for ev in events[:5]:
        highlights.append(
            f"{ev.get('ts_label') or '?'} — {ev.get('label') or ev.get('type') or 'olay'}"
        )

    type_bits = " · ".join(f"{k}:{v}" for k, v in by_type.most_common(6))
    body = (
        f"{len(events)} olay · {len(sessions)} oturum · {file_total} dosya\n"
        f"{type_bits}\n"
        + ("\n".join(highlights) if highlights else "")
    )

    return {
        "ok": True,
        "period_days": period,
        "event_count": len(events),
        "unique_sessions": len(sessions),
        "file_total": file_total,
        "by_type": dict(by_type),
        "highlights": highlights,
        "generated_at": time.time(),
        "summary_card": {
            "title": f"Haftalık özet — son {period} gün",
            "body": body.strip(),
            "event_count": len(events),
            "unique_sessions": len(sessions),
            "file_total": file_total,
            "by_type": dict(by_type),
        },
    }
