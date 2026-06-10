# Created by Ümit & Gökçenur
"""Ana Motor Faz M1 — timeline olaylarından tek tık restore/merge/paket."""

from __future__ import annotations

import os
from typing import Any


def timeline_actions_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_TIMELINE_ACTIONS", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _active_session_id() -> str | None:
    from pathlib import Path
    import json

    root = Path(__file__).resolve().parent.parent / ".ruzgar" / "ana_motor_uploads" / "sessions"
    if not root.is_dir():
        return None
    best: tuple[float, str] | None = None
    for p in root.glob("*.json"):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        sid = str(data.get("session_id") or p.stem)
        ts = float(data.get("updated_at") or data.get("created_at") or p.stat().st_mtime)
        if best is None or ts > best[0]:
            best = (ts, sid)
    return best[1] if best else None


def attach_timeline_actions(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Timeline satırlarına UI aksiyonları ekle."""
    if not timeline_actions_enabled():
        return events
    active_sid = _active_session_id()
    out: list[dict[str, Any]] = []
    for ev in events:
        item = dict(ev)
        sid = str(item.get("session_id") or "").strip()
        etype = str(item.get("type") or "")
        actions: list[dict[str, str]] = []
        if sid:
            if etype in ("archived", "restored", "active_session"):
                actions.append({"id": "restore", "label": "Geri yükle"})
            if etype == "archived" and active_sid and active_sid != sid:
                actions.append(
                    {
                        "id": "merge_active",
                        "label": "Aktifle birleştir",
                        "merge_with_session_id": active_sid,
                    }
                )
            actions.append({"id": "paket", "label": "Tek paket"})
        item["actions"] = actions
        out.append(item)
    return out


def run_timeline_action(
    action: str,
    session_id: str,
    *,
    merge_with_session_id: str | None = None,
    topic: str = "",
) -> dict[str, Any]:
    """Timeline'dan restore, merge veya paket sihirbazı."""
    if not timeline_actions_enabled():
        return {"ok": False, "error": "Timeline aksiyonları kapalı."}
    sid = (session_id or "").strip()
    if not sid:
        return {"ok": False, "error": "session_id gerekli."}
    act = (action or "").strip().lower()
    topic_clean = (topic or "").strip()[:240]

    if act == "restore":
        from ilim_assistant.ana_motor_dosya_ingest import restore_archive_session

        return restore_archive_session(sid)

    if act == "merge_active":
        other = (merge_with_session_id or _active_session_id() or "").strip()
        if not other:
            return {"ok": False, "error": "Birleştirilecek aktif oturum yok."}
        if other == sid:
            return {"ok": False, "error": "Aynı oturum birleştirilemez."}
        from ilim_assistant.ana_motor_dosya_ingest import merge_upload_sessions

        return merge_upload_sessions([other, sid])

    if act == "paket":
        from ilim_assistant.ana_motor_dosya_ingest import list_session_upload_ids
        from ilim_assistant.ana_motor_reminder_wizard import run_reminder_paket_sihirbaz

        has_live = bool(list_session_upload_ids(sid))
        return run_reminder_paket_sihirbaz(
            kind="timeline",
            session_id=sid,
            topic=topic_clean or f"Timeline paket — {sid[:8]}",
            do_restore_first=not has_live,
        )

    return {"ok": False, "error": f"Bilinmeyen timeline aksiyonu: {action}"}
