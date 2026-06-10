# Created by Ümit & Gökçenur
"""Ana Motor Faz O1 — CSV'den toplu paket sihirbazı tetikleme."""

from __future__ import annotations

import csv
import io
import os
from typing import Any


def csv_bulk_paket_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_CSV_BULK_PAKET", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _max_bulk_paket() -> int:
    try:
        return max(1, min(12, int(os.environ.get("RUZGAR_ANA_CSV_BULK_PAKET_MAX", "5"))))
    except ValueError:
        return 5


def parse_paket_rows_from_csv(csv_text: str) -> list[dict[str, str]]:
    """Paket geçmişi CSV'sinden session_id + isteğe bağlı konu satırları."""
    from ilim_assistant.ana_motor_csv_restore import parse_session_ids_from_csv

    text = (csv_text or "").lstrip("\ufeff").strip()
    if not text:
        return []
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        return [{"session_id": sid, "topic": ""} for sid in parse_session_ids_from_csv(text)]
    sid_key = None
    topic_key = None
    for name in reader.fieldnames:
        low = (name or "").strip().lower()
        if low in ("session_id", "oturum_id", "session") and not sid_key:
            sid_key = name
        if low in ("konu", "topic", "baslik") and not topic_key:
            topic_key = name
    if not sid_key:
        return [{"session_id": sid, "topic": ""} for sid in parse_session_ids_from_csv(text)]
    seen: set[str] = set()
    out: list[dict[str, str]] = []
    for row in reader:
        sid = str(row.get(sid_key) or "").strip()
        if not sid or sid in seen:
            continue
        seen.add(sid)
        topic = str(row.get(topic_key) or "").strip()[:200] if topic_key else ""
        out.append({"session_id": sid, "topic": topic})
    return out


def bulk_paket_from_csv(
    csv_text: str,
    *,
    max_sessions: int | None = None,
    do_restore_first: bool = True,
) -> dict[str, Any]:
    """CSV satırlarındaki oturumlar için paket sihirbazını sırayla çalıştır."""
    if not csv_bulk_paket_enabled():
        return {"ok": False, "error": "CSV toplu paket sihirbazı kapalı."}
    rows = parse_paket_rows_from_csv(csv_text)
    if not rows:
        return {"ok": False, "error": "CSV'de session_id bulunamadı."}
    cap = int(max_sessions if max_sessions is not None else _max_bulk_paket())
    rows = rows[:cap]

    from ilim_assistant.ana_motor_dosya_ingest import resolve_upload_ids, restore_archive_session
    from ilim_assistant.ana_motor_paket_sihirbaz import run_paket_sihirbaz

    results: list[dict[str, Any]] = []
    errors: list[str] = []
    for row in rows:
        sid = row["session_id"]
        topic = row.get("topic") or f"CSV toplu paket — {sid[:8]}"
        upload_ids = resolve_upload_ids(None, sid)
        if not upload_ids and do_restore_first:
            rr = restore_archive_session(sid)
            if rr.get("ok"):
                upload_ids = list(rr.get("upload_ids") or [])
            else:
                errors.append(f"{sid[:8]}: {rr.get('error') or 'restore'}")
                results.append({"session_id": sid, "ok": False, "error": rr.get("error")})
                continue
        if not upload_ids:
            errors.append(f"{sid[:8]}: dosya yok")
            results.append({"session_id": sid, "ok": False, "error": "Dosya/oturum bulunamadı."})
            continue
        wiz = run_paket_sihirbaz(
            session_id=sid,
            upload_ids=upload_ids,
            topic=topic,
        )
        results.append({"session_id": sid, **wiz})
        if not wiz.get("ok"):
            errors.append(f"{sid[:8]}: {wiz.get('error') or 'paket'}")

    ok_count = sum(1 for r in results if r.get("ok"))
    if ok_count == 0:
        return {
            "ok": False,
            "error": "; ".join(errors) or "Hiçbir paket tamamlanamadı.",
            "attempted": len(rows),
            "results": results,
        }
    return {
        "ok": True,
        "paket_count": ok_count,
        "attempted": len(rows),
        "results": results,
        "errors": errors,
        "hint": f"CSV'den {ok_count}/{len(rows)} oturum paketlendi.",
    }
