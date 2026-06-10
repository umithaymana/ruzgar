# Created by Ümit & Gökçenur
"""Ana Motor Faz N1 — CSV'den toplu arşiv geri yükleme."""

from __future__ import annotations

import csv
import io
import os
from typing import Any


def csv_bulk_restore_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_CSV_BULK_RESTORE", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _max_bulk_sessions() -> int:
    try:
        return max(1, min(20, int(os.environ.get("RUZGAR_ANA_CSV_BULK_MAX", "8"))))
    except ValueError:
        return 8


def parse_session_ids_from_csv(csv_text: str) -> list[str]:
    """Paket geçmişi CSV'sinden benzersiz session_id listesi çıkar."""
    text = (csv_text or "").lstrip("\ufeff").strip()
    if not text:
        return []
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        return []
    sid_key = None
    for name in reader.fieldnames:
        low = (name or "").strip().lower()
        if low in ("session_id", "oturum_id", "session"):
            sid_key = name
            break
    if not sid_key:
        return []
    seen: set[str] = set()
    out: list[str] = []
    for row in reader:
        sid = str(row.get(sid_key) or "").strip()
        if not sid or sid in seen:
            continue
        seen.add(sid)
        out.append(sid)
    return out


def bulk_restore_from_csv(
    csv_text: str,
    *,
    max_sessions: int | None = None,
) -> dict[str, Any]:
    """CSV satırlarındaki oturumları sırayla arşivden geri yükle."""
    if not csv_bulk_restore_enabled():
        return {"ok": False, "error": "CSV toplu geri yükleme kapalı."}
    ids = parse_session_ids_from_csv(csv_text)
    if not ids:
        return {"ok": False, "error": "CSV'de session_id bulunamadı."}
    cap = int(max_sessions if max_sessions is not None else _max_bulk_sessions())
    ids = ids[:cap]

    from ilim_assistant.ana_motor_dosya_ingest import restore_archive_session

    restored: list[dict[str, Any]] = []
    errors: list[str] = []
    for sid in ids:
        rr = restore_archive_session(sid)
        if rr.get("ok"):
            restored.append(
                {
                    "session_id": sid,
                    "file_count": rr.get("file_count"),
                    "upload_ids": rr.get("upload_ids"),
                }
            )
        else:
            errors.append(f"{sid[:8]}: {rr.get('error') or 'hata'}")

    if not restored:
        return {
            "ok": False,
            "error": "; ".join(errors) or "Hiçbir oturum geri yüklenemedi.",
            "attempted": len(ids),
        }
    all_upload_ids: list[str] = []
    for r in restored:
        all_upload_ids.extend(list(r.get("upload_ids") or []))
    return {
        "ok": True,
        "restored_count": len(restored),
        "attempted": len(ids),
        "sessions": restored,
        "upload_ids": all_upload_ids,
        "errors": errors,
        "hint": (
            f"CSV'den {len(restored)}/{len(ids)} oturum geri yüklendi "
            f"({len(all_upload_ids)} dosya)."
        ),
    }
