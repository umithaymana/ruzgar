# Created by Ümit & Gökçenur
"""Ana Motor Faz V3 — tüm tercihler tek JSON tam yedek / geri yükle."""

from __future__ import annotations

import json
import os
import time
from typing import Any

_ARCHIVE_VERSION = 1


def tam_prefs_yedek_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_TAM_PREFS_YEDEK", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def export_tam_prefs_archive() -> dict[str, Any]:
    if not tam_prefs_yedek_enabled():
        return {"ok": False, "error": "Tam tercih yedekleme kapalı."}

    notify: dict[str, Any] = {}
    schedule: dict[str, Any] = {}
    unified: dict[str, Any] = {}

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
    try:
        from ilim_assistant.ana_motor_birlesik_tercih import load_unified_prefs

        unified = load_unified_prefs().get("prefs") or {}
    except Exception:
        pass

    payload = {
        "version": _ARCHIVE_VERSION,
        "generated_at": time.time(),
        "notify_prefs": notify,
        "schedule_prefs": schedule,
        "unified_prefs": unified,
    }
    return {
        "ok": True,
        "json": json.dumps(payload, ensure_ascii=False, indent=2),
        "filename": "ruzgar_ana_motor_tam_tercih_yedek.json",
        "section_count": sum(1 for k in ("notify_prefs", "schedule_prefs", "unified_prefs") if payload[k]),
    }


def import_tam_prefs_archive(json_text: str) -> dict[str, Any]:
    if not tam_prefs_yedek_enabled():
        return {"ok": False, "error": "Tam tercih geri yükleme kapalı."}

    text = (json_text or "").strip()
    if not text:
        return {"ok": False, "error": "JSON boş."}
    try:
        data = json.loads(text)
    except Exception as exc:
        return {"ok": False, "error": f"JSON parse: {exc}"}
    if not isinstance(data, dict):
        return {"ok": False, "error": "Geçersiz arşiv formatı."}

    restored: list[str] = []
    errors: list[str] = []

    notify = data.get("notify_prefs")
    if isinstance(notify, dict) and notify:
        try:
            from ilim_assistant.ana_motor_bildirim_tercih import save_notify_prefs

            nr = save_notify_prefs(notify)
            if nr.get("ok"):
                restored.append("notify_prefs")
            else:
                errors.append(str(nr.get("error") or "notify_prefs"))
        except Exception as exc:
            errors.append(f"notify_prefs: {exc}")

    schedule = data.get("schedule_prefs")
    if isinstance(schedule, dict) and schedule:
        try:
            from ilim_assistant.ana_motor_schedule_tercih import save_schedule_prefs

            sr = save_schedule_prefs(schedule)
            if sr.get("ok"):
                restored.append("schedule_prefs")
            else:
                errors.append(str(sr.get("error") or "schedule_prefs"))
        except Exception as exc:
            errors.append(f"schedule_prefs: {exc}")

    unified = data.get("unified_prefs")
    if isinstance(unified, dict) and unified and "notify_prefs" not in restored:
        try:
            from ilim_assistant.ana_motor_birlesik_tercih import save_unified_prefs

            ur = save_unified_prefs(unified)
            if ur.get("ok"):
                restored.append("unified_prefs")
            else:
                errors.append(str(ur.get("error") or "unified_prefs"))
        except Exception as exc:
            errors.append(f"unified_prefs: {exc}")

    if not restored:
        return {"ok": False, "error": errors[0] if errors else "Geri yüklenecek tercih bulunamadı."}

    try:
        from ilim_assistant.ana_motor_birlesik_tercih import load_unified_prefs

        merged = load_unified_prefs().get("prefs") or {}
    except Exception:
        merged = {}

    hint = f"Tam tercih yedeği geri yüklendi: {', '.join(restored)}."
    if errors:
        hint += f" Uyarı: {'; '.join(errors[:3])}"
    return {
        "ok": True,
        "restored": restored,
        "prefs": merged,
        "hint": hint,
        "warnings": errors,
    }
