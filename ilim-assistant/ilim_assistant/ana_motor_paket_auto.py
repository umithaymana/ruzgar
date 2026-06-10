# Created by Ümit & Gökçenur
"""Ana Motor Faz J1 — sohbet bitişinde paket sihirbazını otomatik kuyruğa al."""

from __future__ import annotations

import os
import threading
import time
from typing import Any


_auto_lock = threading.Lock()
_auto_job: dict[str, Any] = {"running": False}


def paket_auto_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_PAKET_AUTO", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def get_paket_auto_job_status() -> dict[str, Any]:
    with _auto_lock:
        return dict(_auto_job)


def _auto_worker(
    *,
    session_id: str | None,
    upload_ids: list[str],
    topic: str,
    collection: str,
) -> None:
    global _auto_job
    with _auto_lock:
        _auto_job = {
            "running": True,
            "session_id": session_id,
            "upload_ids": upload_ids,
            "topic": topic,
            "started_at": time.time(),
        }
    try:
        from ilim_assistant.ana_motor_paket_sihirbaz import run_paket_sihirbaz

        result = run_paket_sihirbaz(
            session_id=session_id,
            upload_ids=upload_ids,
            topic=topic,
            collection=collection,
            do_archive=True,
            do_remember=True,
            do_nebula=True,
            do_ttl_extend=True,
        )
        with _auto_lock:
            _auto_job = {
                "running": False,
                "session_id": session_id,
                "upload_ids": upload_ids,
                "result": result,
                "finished_at": time.time(),
            }
    except Exception as exc:
        with _auto_lock:
            _auto_job = {
                "running": False,
                "session_id": session_id,
                "error": str(exc),
                "finished_at": time.time(),
            }


def maybe_queue_auto_paket(req: Any, done: dict[str, Any]) -> dict[str, Any]:
    """Tur bittiğinde dosya oturumu varsa arka planda paket sihirbazını başlat."""
    if not paket_auto_enabled():
        return done
    if done.get("instant_gundelik") or done.get("instant_clarify") or done.get("instant_memory"):
        return done
    if getattr(req, "coding_mode", False):
        return done
    try:
        from ilim_assistant.chat_core import normalize_mode

        if normalize_mode(getattr(req, "mode", None) or "genel") == "programlama":
            return done
    except Exception:
        pass

    upload_ids = [str(x).strip() for x in (getattr(req, "ana_motor_upload_ids", None) or []) if str(x).strip()]
    session_id = (getattr(req, "ana_motor_session_id", None) or "").strip() or None
    if not upload_ids and not session_id:
        return done

    from ilim_assistant.ana_motor_dosya_ingest import resolve_upload_ids
    from ilim_assistant.ana_motor_paket_sihirbaz import wizard_enabled

    if not wizard_enabled():
        return done
    ids = resolve_upload_ids(upload_ids or None, session_id)
    if not ids:
        return done

    topic = str(done.get("user_message") or getattr(req, "message", "") or "").strip()[:240]
    collection = "tarih_kaynak"
    try:
        noc = done.get("nebula_oneri_card")
        if isinstance(noc, dict) and noc.get("collection"):
            collection = str(noc["collection"])
    except Exception:
        pass

    with _auto_lock:
        if _auto_job.get("running"):
            out = dict(done)
            out["paket_auto"] = {
                "ok": False,
                "queued": False,
                "error": "Önceki otomatik paket hâlâ çalışıyor.",
            }
            return out

    threading.Thread(
        target=_auto_worker,
        kwargs={
            "session_id": session_id,
            "upload_ids": ids,
            "topic": topic,
            "collection": collection,
        },
        daemon=True,
        name="ruzgar-paket-auto",
    ).start()

    out = dict(done)
    out["paket_auto"] = {
        "ok": True,
        "queued": True,
        "session_id": session_id,
        "upload_ids": ids,
        "file_count": len(ids),
        "hint": "Dosya oturumu sohbet sonrası otomatik paketlendi (arka plan).",
    }
    return out
