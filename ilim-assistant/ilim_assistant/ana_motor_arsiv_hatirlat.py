# Created by Ümit & Gökçenur
"""Ana Motor Faz K3 — upload/arşiv TTL hatırlatıcıları."""

from __future__ import annotations

import os
import time
from typing import Any


def archive_ttl_remind_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_ARCHIVE_TTL_REMIND", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _upload_remind_sec() -> int:
    try:
        return max(300, int(os.environ.get("RUZGAR_ANA_UPLOAD_REMIND_SEC", "3600")))
    except ValueError:
        return 3600


def _archive_age_remind_days() -> int:
    try:
        return max(1, int(os.environ.get("RUZGAR_ANA_ARCHIVE_REMIND_DAYS", "30")))
    except ValueError:
        return 30


def collect_archive_ttl_reminders(*, limit: int = 20) -> dict[str, Any]:
    """Yakında süresi dolacak uploadlar ve eski arşiv oturumları."""
    if not archive_ttl_remind_enabled():
        return {"ok": True, "reminders": [], "count": 0, "disabled": True}

    from ilim_assistant.ana_motor_dosya_ingest import (
        _TTL_SEC,
        _lock,
        _load_disk_records,
        _purge_expired,
        _store,
        list_archived_sessions,
    )

    now = time.time()
    remind_before = _upload_remind_sec()
    age_days_limit = _archive_age_remind_days()
    reminders: list[dict[str, Any]] = []

    with _lock:
        _purge_expired()
        if not _store:
            _load_disk_records()
        for uid, rec in list(_store.items()):
            exp_raw = rec.get("expires_at")
            if exp_raw is not None:
                try:
                    exp = float(exp_raw)
                except (TypeError, ValueError):
                    exp = now + _TTL_SEC
            else:
                try:
                    created = float(rec.get("created_at", 0))
                except (TypeError, ValueError):
                    created = now
                exp = created + _TTL_SEC
            remaining = exp - now
            if 0 < remaining <= remind_before:
                fname = str(rec.get("filename") or uid[:8])
                reminders.append(
                    {
                        "kind": "upload_expiry",
                        "upload_id": uid,
                        "filename": fname,
                        "expires_in_sec": int(remaining),
                        "severity": "warn",
                        "hint": (
                            f"«{fname}» geçici bağlamı "
                            f"{int(remaining // 60)} dk içinde süresi dolacak — "
                            "Tek paket uygula veya arşivle."
                        ),
                    }
                )

    for row in list_archived_sessions(limit=50):
        archived_at = float(row.get("archived_at") or now)
        age_days = int((now - archived_at) / 86400)
        if age_days >= age_days_limit:
            sid = str(row.get("session_id") or "")
            topic = (row.get("topic") or "—").strip()[:80]
            reminders.append(
                {
                    "kind": "archive_age",
                    "session_id": sid,
                    "topic": topic,
                    "age_days": age_days,
                    "file_count": row.get("file_count"),
                    "severity": "info",
                    "hint": (
                        f"Arşiv {sid[:8]} — {age_days} gün önce paketlendi "
                        f"({row.get('file_count') or '?'} dosya). "
                        "Gerekirse geri yükle veya Nebula'ya ekle."
                    ),
                }
            )

    reminders.sort(
        key=lambda r: (
            0 if r.get("severity") == "warn" else 1,
            -int(r.get("expires_in_sec") or r.get("age_days") or 0),
        )
    )
    trimmed = reminders[: max(1, limit)]
    return {
        "ok": True,
        "reminders": trimmed,
        "count": len(trimmed),
        "upload_remind_sec": remind_before,
        "archive_age_days": age_days_limit,
    }
