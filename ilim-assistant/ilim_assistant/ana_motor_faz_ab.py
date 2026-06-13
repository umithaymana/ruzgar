# Created by Ümit & Gökçenur
"""Ana Motor Faz AB — oturum JSON dışa aktarma + Kaynak panel birleşik Nebula apply."""

from __future__ import annotations

import os
import time
from typing import Any

FAZ_AB_VERSION = "ana-motor-faz-ab-v1-2026-06-13"


def faz_ab_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_FAZ_AB", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def session_export_enabled() -> bool:
    if not faz_ab_enabled():
        return False
    return os.environ.get("RUZGAR_ANA_SESSION_EXPORT", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def birlesik_apply_enabled() -> bool:
    if not faz_ab_enabled():
        return False
    return os.environ.get("RUZGAR_ANA_KAYNAK_BIRLESIK_APPLY", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def export_session_json(
    *,
    limit: int | None = None,
    session_id: str | None = None,
    mode: str | None = None,
) -> dict[str, Any]:
    """Faz AB1 — jsonl sohbet geçmişini JSON olarak dışa aktar."""
    if not session_export_enabled():
        return {"ok": False, "error": "Oturum dışa aktarma kapalı.", "items": [], "count": 0}
    from ilim_assistant.ana_motor_sohbet_gecmis import export_session_chat_history

    out = export_session_chat_history(
        session_id=session_id,
        mode=mode,
        limit=limit,
    )
    out["version"] = FAZ_AB_VERSION
    out["feature"] = "session_export"
    return out


def resolve_birlesik_nebula_plan(
    *,
    nebula_card: dict[str, Any] | None = None,
    ozet_card: dict[str, Any] | None = None,
    upload_ids: list[str] | None = None,
    session_id: str | None = None,
    topic: str = "",
) -> dict[str, Any]:
    """Faz AB2 — öncelik: Nebula öneri → paket özeti → yükleme oturumu."""
    if not birlesik_apply_enabled():
        return {"ok": False, "error": "Birleşik Nebula apply kapalı."}

    card = nebula_card if nebula_card and nebula_card.get("ok") else None
    if card:
        coll = str(card.get("collection") or "").strip()
        top = str(card.get("topic") or topic or "").strip()
        if coll and top:
            return {
                "ok": True,
                "source": "nebula_oneri",
                "collection": coll,
                "topic": top[:240],
                "upload_ids": list(upload_ids or card.get("upload_ids") or []) or None,
                "session_id": (session_id or card.get("session_id") or "").strip() or None,
            }

    if ozet_card and ozet_card.get("ok"):
        from ilim_assistant.ana_motor_paket_ozet import build_ozet_nebula_apply_payload

        payload = build_ozet_nebula_apply_payload(ozet_card)
        if payload:
            return {
                "ok": True,
                "source": "paket_ozet",
                **payload,
            }

    ids = [str(x).strip() for x in (upload_ids or []) if str(x).strip()]
    sid = (session_id or "").strip() or None
    top = (topic or "").strip()[:240] or "Oturum paketi"
    if ids or sid:
        return {
            "ok": True,
            "source": "upload_session",
            "collection": "tarih_kaynak",
            "topic": top,
            "upload_ids": ids or None,
            "session_id": sid,
        }

    return {
        "ok": False,
        "error": "Uygulanacak Nebula kaynağı yok — önce araştırma veya dosya yükleyin.",
    }


def run_birlesik_nebula_apply(
    *,
    nebula_card: dict[str, Any] | None = None,
    ozet_card: dict[str, Any] | None = None,
    upload_ids: list[str] | None = None,
    session_id: str | None = None,
    topic: str = "",
) -> dict[str, Any]:
    plan = resolve_birlesik_nebula_plan(
        nebula_card=nebula_card,
        ozet_card=ozet_card,
        upload_ids=upload_ids,
        session_id=session_id,
        topic=topic,
    )
    if not plan.get("ok"):
        return {**plan, "version": FAZ_AB_VERSION}

    from ilim_assistant.ana_motor_dosya_ingest import resolve_upload_ids
    from ilim_assistant.ana_motor_nebula_apply import apply_nebula_oneri, nebula_apply_enabled

    if not nebula_apply_enabled():
        return {"ok": False, "error": "Nebula tek tık ekleme kapalı.", "version": FAZ_AB_VERSION}

    coll = str(plan.get("collection") or "").strip()
    top = str(plan.get("topic") or "").strip()
    uids = resolve_upload_ids(plan.get("upload_ids"), plan.get("session_id"))
    result = apply_nebula_oneri(coll, top, upload_ids=uids or None)
    result["birlesik_source"] = plan.get("source")
    result["version"] = FAZ_AB_VERSION
    result["planned_at"] = time.time()
    return result


def faz_ab_status() -> dict[str, Any]:
    return {
        "ok": True,
        "version": FAZ_AB_VERSION,
        "enabled": faz_ab_enabled(),
        "session_export": session_export_enabled(),
        "kaynak_birlesik_apply": birlesik_apply_enabled(),
    }
