# Created by Ümit & Gökçenur
"""Ana Motor Faz L1 — hatırlatıcıdan tek tık paket sihirbazı köprüsü."""

from __future__ import annotations

import os
from typing import Any


def reminder_wizard_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_REMINDER_WIZARD", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _find_session_for_upload(upload_id: str) -> str | None:
    from pathlib import Path
    import json

    uid = (upload_id or "").strip()
    if not uid:
        return None
    root = Path(__file__).resolve().parent.parent / ".ruzgar" / "ana_motor_uploads" / "sessions"
    if not root.is_dir():
        return None
    for p in root.glob("*.json"):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        ids = [str(x) for x in data.get("upload_ids") or []]
        if uid in ids:
            return str(data.get("session_id") or p.stem)
    return None


def enrich_reminder_actions(reminders: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Hatırlatıcılara tek tık paket sihirbazı aksiyonu ekle."""
    if not reminder_wizard_enabled():
        return reminders
    out: list[dict[str, Any]] = []
    for row in reminders:
        item = dict(row)
        kind = str(item.get("kind") or "")
        if kind == "upload_expiry":
            uid = str(item.get("upload_id") or "")
            sid = _find_session_for_upload(uid)
            item["action"] = {
                "type": "paket_sihirbaz",
                "session_id": sid,
                "upload_ids": [uid] if uid else None,
                "topic": f"TTL hatırlatıcı — {item.get('filename') or uid[:8]}",
            }
        elif kind == "archive_age":
            sid = str(item.get("session_id") or "")
            item["action"] = {
                "type": "paket_sihirbaz",
                "session_id": sid or None,
                "do_restore_first": True,
                "topic": (item.get("topic") or "Arşiv oturumu")[:200],
            }
        out.append(item)
    return out


def run_reminder_paket_sihirbaz(
    *,
    kind: str = "",
    session_id: str | None = None,
    upload_ids: list[str] | None = None,
    topic: str = "",
    do_restore_first: bool = False,
) -> dict[str, Any]:
    """Hatırlatıcıdan paket sihirbazını çalıştır (gerekirse önce arşiv restore)."""
    if not reminder_wizard_enabled():
        return {"ok": False, "error": "Hatırlatıcı paket köprüsü kapalı."}
    from ilim_assistant.ana_motor_paket_sihirbaz import run_paket_sihirbaz, wizard_enabled

    if not wizard_enabled():
        return {"ok": False, "error": "Paket sihirbazı kapalı."}

    sid = (session_id or "").strip() or None
    ids = [str(x).strip() for x in (upload_ids or []) if str(x).strip()]

    if do_restore_first and sid:
        from ilim_assistant.ana_motor_dosya_ingest import restore_archive_session

        rr = restore_archive_session(sid)
        if not rr.get("ok"):
            return rr
        ids = list(rr.get("upload_ids") or ids)

    if not ids and not sid:
        return {"ok": False, "error": "Hatırlatıcı için oturum/dosya bulunamadı."}

    topic_clean = (topic or "").strip()[:240] or f"Hatırlatıcı paket ({kind or 'genel'})"
    result = run_paket_sihirbaz(
        session_id=sid,
        upload_ids=ids or None,
        topic=topic_clean,
        do_archive=True,
        do_remember=True,
        do_nebula=True,
        do_ttl_extend=True,
    )
    if not result.get("ok"):
        return result

    try:
        from ilim_assistant.ana_motor_paket_ozet import build_paket_ozet_card

        card = build_paket_ozet_card(result, source="reminder")
        if card:
            result["summary_card"] = card
    except Exception:
        pass
    try:
        from ilim_assistant.ana_motor_nebula_oneri import build_session_nebula_card

        nb = build_session_nebula_card(
            session_id=result.get("session_id"),
            upload_ids=list(result.get("upload_ids") or []),
            topic=topic_clean,
        )
        if nb:
            result["nebula_card"] = nb
    except Exception:
        pass
    result["hint"] = result.get("hint") or "Hatırlatıcıdan paket sihirbazı tamamlandı."
    return result
