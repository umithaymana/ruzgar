# Created by Ümit & Gökçenur
"""Ana Motor Faz M3 — paket geçmişi CSV dışa aktarım."""

from __future__ import annotations

import csv
import io
import os
from typing import Any


def paket_csv_export_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_PAKET_CSV_EXPORT", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def build_paket_history_rows(*, limit: int = 200) -> list[dict[str, Any]]:
    """Timeline + arşiv + otomatik paket satırlarını birleştir."""
    from ilim_assistant.ana_motor_oturum_timeline import build_session_timeline
    from ilim_assistant.ana_motor_dosya_ingest import list_archived_sessions

    rows: list[dict[str, Any]] = []
    tl = build_session_timeline(limit=limit)
    for ev in tl.get("events") or []:
        rows.append(
            {
                "kaynak": "timeline",
                "olay": ev.get("type") or "",
                "session_id": ev.get("session_id") or "",
                "zaman": ev.get("ts_label") or "",
                "dosya_sayisi": ev.get("file_count") or "",
                "konu": (ev.get("topic") or ev.get("label") or "")[:200],
                "arsiv_yolu": ev.get("archive_path") or "",
            }
        )

    for ar in list_archived_sessions(limit=limit):
        rows.append(
            {
                "kaynak": "arsiv",
                "olay": "archived",
                "session_id": ar.get("session_id") or "",
                "zaman": str(ar.get("archived_at") or ""),
                "dosya_sayisi": ar.get("file_count") or "",
                "konu": (ar.get("topic") or "")[:200],
                "arsiv_yolu": ar.get("archive_path") or "",
            }
        )

    try:
        from ilim_assistant.ana_motor_paket_auto import get_paket_auto_job_status

        job = get_paket_auto_job_status()
        if float(job.get("finished_at") or 0) > 0:
            result = job.get("result") if isinstance(job.get("result"), dict) else {}
            rows.append(
                {
                    "kaynak": "auto_paket",
                    "olay": "auto_paket",
                    "session_id": job.get("session_id") or "",
                    "zaman": str(job.get("finished_at") or ""),
                    "dosya_sayisi": len(job.get("upload_ids") or []),
                    "konu": (result.get("topic") or result.get("hint") or "")[:200],
                    "arsiv_yolu": "",
                }
            )
    except Exception:
        pass

    return rows[:limit]


def export_paket_history_csv(*, limit: int = 200) -> dict[str, Any]:
    """UTF-8 CSV metni üret."""
    if not paket_csv_export_enabled():
        return {"ok": False, "error": "Paket CSV dışa aktarım kapalı."}
    rows = build_paket_history_rows(limit=limit)
    if not rows:
        return {"ok": False, "error": "Dışa aktarılacak paket geçmişi yok."}

    fieldnames = [
        "kaynak",
        "olay",
        "session_id",
        "zaman",
        "dosya_sayisi",
        "konu",
        "arsiv_yolu",
    ]
    buf = io.StringIO()
    buf.write("\ufeff")
    writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    csv_text = buf.getvalue()
    return {
        "ok": True,
        "csv": csv_text,
        "row_count": len(rows),
        "filename": "ruzgar_ana_motor_paket_gecmisi.csv",
    }
