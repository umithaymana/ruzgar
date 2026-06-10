# Created by Ümit & Gökçenur
"""Ana Motor Faz T2 — bildirim + zamanlayıcı birleşik tercih kartı."""

from __future__ import annotations

import os
from typing import Any


def unified_prefs_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_UNIFIED_PREFS", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def load_unified_prefs() -> dict[str, Any]:
    if not unified_prefs_enabled():
        return {"ok": True, "prefs": {}, "disabled": True}
    notify: dict[str, Any] = {}
    schedule: dict[str, Any] = {}
    try:
        from ilim_assistant.ana_motor_bildirim_tercih import load_notify_prefs

        notify = load_notify_prefs().get("prefs") or {}
    except Exception:
        pass
    try:
        from ilim_assistant.ana_motor_schedule_tercih import load_schedule_prefs

        schedule = load_schedule_prefs().get("prefs") or {}
    except Exception:
        pass
    merged = {
        "desktop_enabled": bool(notify.get("desktop_enabled", True)),
        "email_enabled": bool(notify.get("email_enabled", False)),
        "warn_only": bool(notify.get("warn_only", True)),
        "remind_poll_sec": int(notify.get("poll_sec") or 120),
        "schedule_enabled": bool(schedule.get("schedule_enabled", True)),
        "schedule_poll_sec": int(schedule.get("poll_sec") or 3600),
        "period_days": int(schedule.get("period_days") or 7),
        "compare_email_enabled": bool(schedule.get("compare_email_enabled", False)),
    }
    return {"ok": True, "prefs": merged}


def save_unified_prefs(prefs: dict[str, Any]) -> dict[str, Any]:
    if not unified_prefs_enabled():
        return {"ok": False, "error": "Birleşik tercih kartı kapalı."}
    if not isinstance(prefs, dict):
        return {"ok": False, "error": "Geçersiz tercih verisi."}
    notify_payload: dict[str, Any] = {}
    if "desktop_enabled" in prefs:
        notify_payload["desktop_enabled"] = prefs["desktop_enabled"]
    if "email_enabled" in prefs:
        notify_payload["email_enabled"] = prefs["email_enabled"]
    if "warn_only" in prefs:
        notify_payload["warn_only"] = prefs["warn_only"]
    if "remind_poll_sec" in prefs:
        notify_payload["poll_sec"] = prefs["remind_poll_sec"]
    if notify_payload:
        try:
            from ilim_assistant.ana_motor_bildirim_tercih import save_notify_prefs

            nr = save_notify_prefs(notify_payload)
            if not nr.get("ok"):
                return nr
        except Exception as exc:
            return {"ok": False, "error": f"Bildirim tercihleri: {exc}"}
    schedule_payload: dict[str, Any] = {}
    if "schedule_enabled" in prefs:
        schedule_payload["schedule_enabled"] = prefs["schedule_enabled"]
    if "schedule_poll_sec" in prefs:
        schedule_payload["poll_sec"] = prefs["schedule_poll_sec"]
    if "period_days" in prefs:
        schedule_payload["period_days"] = prefs["period_days"]
    if "compare_email_enabled" in prefs:
        schedule_payload["compare_email_enabled"] = prefs["compare_email_enabled"]
    if schedule_payload:
        try:
            from ilim_assistant.ana_motor_schedule_tercih import save_schedule_prefs

            sr = save_schedule_prefs(schedule_payload)
            if not sr.get("ok"):
                return sr
        except Exception as exc:
            return {"ok": False, "error": f"Zamanlayıcı tercihleri: {exc}"}
    return {
        "ok": True,
        "prefs": load_unified_prefs().get("prefs"),
        "hint": "Birleşik tercihler kaydedildi (bildirim + zamanlayıcı).",
    }
