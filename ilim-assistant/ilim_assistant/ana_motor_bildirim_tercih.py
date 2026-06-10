# Created by Ümit & Gökçenur
"""Ana Motor Faz N2 — bildirim tercih paneli (kalıcı JSON)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

_PKG_ROOT = Path(__file__).resolve().parent.parent
_PREFS_PATH = _PKG_ROOT / ".ruzgar" / "ana_motor_notify_prefs.json"

_DEFAULTS: dict[str, Any] = {
    "desktop_enabled": True,
    "email_enabled": False,
    "warn_only": True,
    "poll_sec": 120,
}


def notify_prefs_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_NOTIFY_PREFS", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _clamp_poll(sec: int) -> int:
    return max(60, min(600, int(sec)))


def load_notify_prefs() -> dict[str, Any]:
    if not notify_prefs_enabled():
        return {"ok": True, "prefs": dict(_DEFAULTS), "disabled": True}
    if not _PREFS_PATH.is_file():
        return {"ok": True, "prefs": dict(_DEFAULTS), "source": "default"}
    try:
        data = json.loads(_PREFS_PATH.read_text(encoding="utf-8"))
        merged = dict(_DEFAULTS)
        if isinstance(data, dict):
            merged.update({k: data[k] for k in _DEFAULTS if k in data})
        merged["poll_sec"] = _clamp_poll(int(merged.get("poll_sec") or 120))
        merged["desktop_enabled"] = bool(merged.get("desktop_enabled"))
        merged["email_enabled"] = bool(merged.get("email_enabled"))
        merged["warn_only"] = bool(merged.get("warn_only"))
        return {"ok": True, "prefs": merged, "source": "file"}
    except Exception as exc:
        return {"ok": True, "prefs": dict(_DEFAULTS), "source": "default", "warn": str(exc)}


def save_notify_prefs(prefs: dict[str, Any]) -> dict[str, Any]:
    if not notify_prefs_enabled():
        return {"ok": False, "error": "Bildirim tercih paneli kapalı."}
    clean = dict(_DEFAULTS)
    if isinstance(prefs, dict):
        if "desktop_enabled" in prefs:
            clean["desktop_enabled"] = bool(prefs["desktop_enabled"])
        if "email_enabled" in prefs:
            clean["email_enabled"] = bool(prefs["email_enabled"])
        if "warn_only" in prefs:
            clean["warn_only"] = bool(prefs["warn_only"])
        if "poll_sec" in prefs:
            clean["poll_sec"] = _clamp_poll(int(prefs["poll_sec"]))
    _PREFS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _PREFS_PATH.write_text(json.dumps(clean, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True, "prefs": clean, "hint": "Bildirim tercihleri kaydedildi."}


def filter_reminders_by_prefs(reminders: list[dict[str, Any]]) -> list[dict[str, Any]]:
    loaded = load_notify_prefs()
    prefs = loaded.get("prefs") if isinstance(loaded.get("prefs"), dict) else _DEFAULTS
    rows = list(reminders or [])
    if prefs.get("warn_only"):
        rows = [r for r in rows if r.get("severity") == "warn"]
    return rows


def effective_desktop_notify() -> bool:
    from ilim_assistant.ana_motor_hatirlat_bildirim import desktop_notify_enabled

    if not desktop_notify_enabled():
        return False
    prefs = load_notify_prefs().get("prefs") or _DEFAULTS
    return bool(prefs.get("desktop_enabled", True))


def effective_email_notify() -> bool:
    from ilim_assistant.ana_motor_hatirlat_bildirim import email_notify_enabled

    if not email_notify_enabled():
        return False
    prefs = load_notify_prefs().get("prefs") or _DEFAULTS
    return bool(prefs.get("email_enabled", False))


def effective_poll_sec() -> int:
    prefs = load_notify_prefs().get("prefs") or _DEFAULTS
    return _clamp_poll(int(prefs.get("poll_sec") or 120))
