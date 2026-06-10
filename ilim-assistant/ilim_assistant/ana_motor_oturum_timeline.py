# Created by Ümit & Gökçenur
"""Ana Motor Faz L3 — oturum geçmişi zaman çizelgesi."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

_PKG_ROOT = Path(__file__).resolve().parent.parent
_UPLOAD_ROOT = _PKG_ROOT / ".ruzgar" / "ana_motor_uploads"


def timeline_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_SESSION_TIMELINE", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _fmt_ts(ts: float) -> str:
    try:
        from datetime import datetime, timezone

        return datetime.fromtimestamp(float(ts), tz=timezone.utc).strftime(
            "%Y-%m-%d %H:%M UTC"
        )
    except Exception:
        return str(int(ts))


def build_session_timeline(*, limit: int = 24) -> dict[str, Any]:
    """Aktif oturum, arşiv, birleştirme ve otomatik paket olaylarını birleştir."""
    if not timeline_enabled():
        return {"ok": True, "events": [], "count": 0, "disabled": True}

    from ilim_assistant.ana_motor_dosya_ingest import list_archived_sessions

    events: list[dict[str, Any]] = []
    sessions_dir = _UPLOAD_ROOT / "sessions"
    if sessions_dir.is_dir():
        for p in sessions_dir.glob("*.json"):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                continue
            sid = str(data.get("session_id") or p.stem)
            ids = [str(x) for x in data.get("upload_ids") or [] if str(x).strip()]
            ts = float(
                data.get("updated_at")
                or data.get("restored_at")
                or data.get("created_at")
                or p.stat().st_mtime
            )
            events.append(
                {
                    "type": "active_session",
                    "session_id": sid,
                    "ts": ts,
                    "ts_label": _fmt_ts(ts),
                    "file_count": len(ids),
                    "label": f"Aktif oturum — {len(ids)} dosya",
                }
            )
            merged_from = data.get("merged_from")
            if isinstance(merged_from, list) and merged_from:
                mts = float(data.get("created_at") or ts)
                events.append(
                    {
                        "type": "merged",
                        "session_id": sid,
                        "ts": mts,
                        "ts_label": _fmt_ts(mts),
                        "merged_from": merged_from,
                        "file_count": len(ids),
                        "label": (
                            f"Birleştirildi — {len(merged_from)} oturum → "
                            f"{len(ids)} dosya"
                        ),
                    }
                )
            if data.get("restored_at"):
                rts = float(data["restored_at"])
                events.append(
                    {
                        "type": "restored",
                        "session_id": sid,
                        "ts": rts,
                        "ts_label": _fmt_ts(rts),
                        "file_count": len(ids),
                        "label": f"Arşivden geri yüklendi — {len(ids)} dosya",
                    }
                )
            if data.get("ttl_extended_at"):
                tts = float(data["ttl_extended_at"])
                events.append(
                    {
                        "type": "ttl_extended",
                        "session_id": sid,
                        "ts": tts,
                        "ts_label": _fmt_ts(tts),
                        "label": "TTL uzatıldı",
                    }
                )

    for row in list_archived_sessions(limit=40):
        ats = float(row.get("archived_at") or time.time())
        sid = str(row.get("session_id") or "")
        events.append(
            {
                "type": "archived",
                "session_id": sid,
                "ts": ats,
                "ts_label": _fmt_ts(ats),
                "topic": row.get("topic") or "",
                "file_count": row.get("file_count"),
                "archive_path": row.get("archive_path"),
                "label": (
                    f"Arşivlendi — {row.get('file_count') or '?'} dosya "
                    f"({(row.get('topic') or '—')[:40]})"
                ),
            }
        )

    try:
        from ilim_assistant.ana_motor_paket_auto import get_paket_auto_job_status

        job = get_paket_auto_job_status()
        finished = float(job.get("finished_at") or 0)
        if finished > 0:
            result = job.get("result") if isinstance(job.get("result"), dict) else {}
            events.append(
                {
                    "type": "auto_paket",
                    "session_id": job.get("session_id"),
                    "ts": finished,
                    "ts_label": _fmt_ts(finished),
                    "file_count": len(job.get("upload_ids") or []),
                    "ok": bool(result.get("ok")),
                    "label": (
                        "Otomatik paket tamam"
                        if result.get("ok")
                        else "Otomatik paket (kısmi/hata)"
                    ),
                }
            )
        started = float(job.get("started_at") or 0)
        if job.get("running") and started > 0:
            events.append(
                {
                    "type": "auto_paket_running",
                    "session_id": job.get("session_id"),
                    "ts": started,
                    "ts_label": _fmt_ts(started),
                    "label": "Otomatik paket çalışıyor…",
                }
            )
    except Exception:
        pass

    events.sort(key=lambda e: float(e.get("ts") or 0), reverse=True)
    trimmed = events[: max(1, limit)]
    try:
        from ilim_assistant.ana_motor_timeline_actions import attach_timeline_actions

        trimmed = attach_timeline_actions(trimmed)
    except Exception:
        pass
    return {"ok": True, "events": trimmed, "count": len(trimmed)}
