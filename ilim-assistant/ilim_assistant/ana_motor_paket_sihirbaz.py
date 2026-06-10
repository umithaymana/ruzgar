# Created by Ümit & Gökçenur
"""Ana Motor Faz I1 — Nebula + hatırla + arşiv tek paket sihirbazı."""

from __future__ import annotations

import os
from typing import Any


def wizard_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_PAKET_SIHIRBAZ", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def run_paket_sihirbaz(
    *,
    session_id: str | None = None,
    upload_ids: list[str] | None = None,
    topic: str = "",
    collection: str = "tarih_kaynak",
    do_archive: bool = True,
    do_remember: bool = True,
    do_nebula: bool = True,
    do_ttl_extend: bool = True,
) -> dict[str, Any]:
    """
    Tek turda: arşiv → TTL uzat → hafıza → Nebula (arka plan indeks).
    """
    if not wizard_enabled():
        return {"ok": False, "error": "Paket sihirbazı kapalı."}

    from ilim_assistant.ana_motor_dosya_ingest import (
        archive_session_package,
        extend_session_ttl,
        resolve_upload_ids,
    )

    ids = resolve_upload_ids(upload_ids, session_id)
    if not ids:
        return {"ok": False, "error": "Sihirbaz için dosya/oturum gerekli."}

    sid = (session_id or "").strip() or None
    topic_clean = (topic or "").strip()[:240]
    coll = (collection or "tarih_kaynak").strip() or "tarih_kaynak"
    steps: list[dict[str, Any]] = []
    errors: list[str] = []

    if do_archive:
        ar = archive_session_package(sid, upload_ids=ids, topic=topic_clean)
        steps.append({"step": "archive", **ar})
        if not ar.get("ok"):
            errors.append(str(ar.get("error") or "arşiv"))
        elif not sid:
            sid = str(ar.get("session_id") or "")

    if do_ttl_extend:
        ttl = extend_session_ttl(sid, upload_ids=ids)
        steps.append({"step": "ttl_extend", **ttl})
        if not ttl.get("ok"):
            errors.append(str(ttl.get("error") or "ttl"))

    if do_remember:
        from ilim_assistant.ana_motor_session_hafiza import remember_upload_session

        mem = remember_upload_session(sid, upload_ids=ids, topic=topic_clean)
        steps.append({"step": "remember", **mem})
        if not mem.get("ok"):
            errors.append(str(mem.get("error") or "hafıza"))

    nebula_async = False
    if do_nebula:
        from ilim_assistant.ana_motor_nebula_apply import start_nebula_apply_background

        nb = start_nebula_apply_background(coll, topic_clean or "Oturum paketi", upload_ids=ids)
        steps.append({"step": "nebula", **nb})
        if not nb.get("ok"):
            errors.append(str(nb.get("error") or "nebula"))
        else:
            nebula_async = bool(nb.get("async"))

    ok_steps = sum(1 for s in steps if s.get("ok"))
    if ok_steps == 0:
        return {
            "ok": False,
            "error": "; ".join(errors) or "Hiçbir adım tamamlanamadı.",
            "steps": steps,
        }

    return {
        "ok": True,
        "session_id": sid,
        "upload_ids": ids,
        "topic": topic_clean,
        "collection": coll,
        "steps": steps,
        "nebula_async": nebula_async,
        "partial_errors": errors,
        "hint": (
            f"Paket sihirbazı: {ok_steps}/{len(steps)} adım tamam. "
            + ("Nebula indeksi arka planda sürüyor." if nebula_async else "")
        ),
    }
