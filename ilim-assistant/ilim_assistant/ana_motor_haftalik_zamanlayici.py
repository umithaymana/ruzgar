# Created by Ümit & Gökçenur
"""Ana Motor Faz R3 — haftalık özet otomatik zamanlayıcı (poll/tick)."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

_PKG_ROOT = Path(__file__).resolve().parent.parent
_STATE_PATH = _PKG_ROOT / ".ruzgar" / "ana_motor_weekly_schedule_state.json"


def weekly_schedule_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_WEEKLY_SCHEDULE", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _poll_sec() -> int:
    try:
        from ilim_assistant.ana_motor_schedule_tercih import effective_schedule_poll_sec

        return effective_schedule_poll_sec()
    except Exception:
        try:
            return max(300, int(os.environ.get("RUZGAR_ANA_WEEKLY_SCHEDULE_POLL_SEC", "3600")))
        except ValueError:
            return 3600


def _load_state() -> dict[str, Any]:
    if not _STATE_PATH.is_file():
        return {}
    try:
        data = json.loads(_STATE_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_state(state: dict[str, Any]) -> None:
    _STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def get_weekly_schedule_status() -> dict[str, Any]:
    if not weekly_schedule_enabled():
        return {"ok": True, "enabled": False, "disabled": True}
    state = _load_state()
    poll = _poll_sec()
    last_poll = float(state.get("last_poll_at") or 0)
    last_notify = float(state.get("last_notify_at") or 0)
    now = time.time()
    try:
        from ilim_assistant.ana_motor_haftalik_bildirim import _cooldown_active, _cooldown_sec

        cooldown = _cooldown_active()
        cooldown_sec = _cooldown_sec()
    except Exception:
        cooldown = False
        cooldown_sec = 604800
    next_poll = max(0.0, poll - (now - last_poll)) if last_poll > 0 else 0.0
    return {
        "ok": True,
        "enabled": True,
        "poll_sec": poll,
        "last_poll_at": last_poll or None,
        "last_notify_at": last_notify or None,
        "next_poll_in_sec": int(next_poll),
        "notify_cooldown_active": cooldown,
        "notify_cooldown_sec": cooldown_sec,
    }


def tick_weekly_schedule(*, days: int | None = None) -> dict[str, Any]:
    """Poll tick — cooldown uygunsa haftalık özet bildirimi gönder."""
    if not weekly_schedule_enabled():
        return {"ok": True, "skipped": True, "reason": "schedule_disabled"}
    try:
        from ilim_assistant.ana_motor_schedule_tercih import (
            effective_schedule_period_days,
            load_schedule_prefs,
        )

        prefs = load_schedule_prefs().get("prefs") or {}
        if not prefs.get("schedule_enabled", True):
            return {"ok": True, "skipped": True, "reason": "schedule_prefs_disabled"}
    except Exception:
        prefs = {}
    period = int(days if days is not None else effective_schedule_period_days())
    state = _load_state()
    now = time.time()
    poll = _poll_sec()
    last_poll = float(state.get("last_poll_at") or 0)
    if last_poll > 0 and (now - last_poll) < poll:
        return {
            "ok": True,
            "skipped": True,
            "reason": "poll_wait",
            "next_poll_in_sec": int(poll - (now - last_poll)),
        }
    state["last_poll_at"] = now
    _save_state(state)

    try:
        from ilim_assistant.ana_motor_haftalik_bildirim import (
            _cooldown_active,
            attach_weekly_notifications,
            weekly_notify_enabled,
        )
        from ilim_assistant.ana_motor_haftalik_ozet import build_weekly_timeline_summary

        if not weekly_notify_enabled():
            return {"ok": True, "skipped": True, "reason": "weekly_notify_disabled"}
        if _cooldown_active():
            return {"ok": True, "skipped": True, "reason": "notify_cooldown"}

        summary = build_weekly_timeline_summary(days=max(1, min(period, 30)))
        result = attach_weekly_notifications(summary, send_desktop=True, send_email=False)
        try:
            from ilim_assistant.ana_motor_compare_email import maybe_send_compare_email

            result["compare_email_status"] = maybe_send_compare_email(period_days=period)
        except Exception:
            pass
        try:
            from ilim_assistant.ana_motor_super_ozet_email import maybe_send_super_ozet_email

            result["super_ozet_email_status"] = maybe_send_super_ozet_email(period_days=period)
        except Exception:
            pass
        if result.get("desktop_notifications"):
            state = _load_state()
            state["last_notify_at"] = now
            _save_state(state)
        result["skipped"] = False
        result["schedule_tick"] = True
        return result
    except Exception as exc:
        return {"ok": False, "skipped": True, "error": str(exc)[:200]}
