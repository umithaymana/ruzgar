# Created by Ümit & Gökçenur
"""Ana Motor Faz S3 — zamanlayıcı tercih paneli (poll aralığı)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

_PKG_ROOT = Path(__file__).resolve().parent.parent
_PREFS_PATH = _PKG_ROOT / ".ruzgar" / "ana_motor_schedule_prefs.json"

_DEFAULTS: dict[str, Any] = {
    "schedule_enabled": True,
    "poll_sec": 3600,
    "period_days": 7,
    "compare_email_enabled": False,
    "super_ozet_email_enabled": False,
    "birlesik_email_enabled": False,
}


def schedule_prefs_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_SCHEDULE_PREFS", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _clamp_poll(sec: int) -> int:
    return max(300, min(86400, int(sec)))


def _clamp_days(days: int) -> int:
    return max(1, min(30, int(days)))


def load_schedule_prefs() -> dict[str, Any]:
    if not schedule_prefs_enabled():
        return {"ok": True, "prefs": dict(_DEFAULTS), "disabled": True}
    if not _PREFS_PATH.is_file():
        return {"ok": True, "prefs": dict(_DEFAULTS), "source": "default"}
    try:
        data = json.loads(_PREFS_PATH.read_text(encoding="utf-8"))
        merged = dict(_DEFAULTS)
        if isinstance(data, dict):
            merged.update({k: data[k] for k in _DEFAULTS if k in data})
        merged["poll_sec"] = _clamp_poll(int(merged.get("poll_sec") or 3600))
        merged["period_days"] = _clamp_days(int(merged.get("period_days") or 7))
        merged["schedule_enabled"] = bool(merged.get("schedule_enabled", True))
        merged["compare_email_enabled"] = bool(merged.get("compare_email_enabled", False))
        merged["super_ozet_email_enabled"] = bool(merged.get("super_ozet_email_enabled", False))
        merged["birlesik_email_enabled"] = bool(merged.get("birlesik_email_enabled", False))
        return {"ok": True, "prefs": merged, "source": "file"}
    except Exception as exc:
        return {"ok": True, "prefs": dict(_DEFAULTS), "source": "default", "warn": str(exc)}


def save_schedule_prefs(prefs: dict[str, Any]) -> dict[str, Any]:
    if not schedule_prefs_enabled():
        return {"ok": False, "error": "Zamanlayıcı tercih paneli kapalı."}
    clean = dict(_DEFAULTS)
    if isinstance(prefs, dict):
        if "schedule_enabled" in prefs:
            clean["schedule_enabled"] = bool(prefs["schedule_enabled"])
        if "poll_sec" in prefs:
            clean["poll_sec"] = _clamp_poll(int(prefs["poll_sec"]))
        if "period_days" in prefs:
            clean["period_days"] = _clamp_days(int(prefs["period_days"]))
        if "compare_email_enabled" in prefs:
            clean["compare_email_enabled"] = bool(prefs["compare_email_enabled"])
        if "super_ozet_email_enabled" in prefs:
            clean["super_ozet_email_enabled"] = bool(prefs["super_ozet_email_enabled"])
        if "birlesik_email_enabled" in prefs:
            clean["birlesik_email_enabled"] = bool(prefs["birlesik_email_enabled"])
    _PREFS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _PREFS_PATH.write_text(json.dumps(clean, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True, "prefs": clean, "hint": "Zamanlayıcı tercihleri kaydedildi."}


def effective_schedule_poll_sec() -> int:
    prefs = load_schedule_prefs().get("prefs") if schedule_prefs_enabled() else _DEFAULTS
    if not isinstance(prefs, dict) or not prefs.get("schedule_enabled", True):
        try:
            return max(300, int(os.environ.get("RUZGAR_ANA_WEEKLY_SCHEDULE_POLL_SEC", "3600")))
        except ValueError:
            return 3600
    return _clamp_poll(int(prefs.get("poll_sec") or 3600))


def effective_schedule_period_days() -> int:
    prefs = load_schedule_prefs().get("prefs") if schedule_prefs_enabled() else _DEFAULTS
    if isinstance(prefs, dict):
        return _clamp_days(int(prefs.get("period_days") or 7))
    return 7
