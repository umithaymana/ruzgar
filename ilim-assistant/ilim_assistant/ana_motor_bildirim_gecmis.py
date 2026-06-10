# Created by Ümit & Gökçenur
"""Ana Motor Faz O2 — bildirim geçmişi (son 20 masaüstü/e-posta)."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

_PKG_ROOT = Path(__file__).resolve().parent.parent
_HISTORY_PATH = _PKG_ROOT / ".ruzgar" / "ana_motor_notify_history.jsonl"
_MAX_STORE = 200


def notify_history_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_NOTIFY_HISTORY", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _history_limit() -> int:
    try:
        return max(5, min(50, int(os.environ.get("RUZGAR_ANA_NOTIFY_HISTORY_LIMIT", "20"))))
    except ValueError:
        return 20


def append_notify_history(
    *,
    channel: str,
    title: str = "",
    body: str = "",
    severity: str = "info",
    session_id: str | None = None,
    upload_id: str | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    if not notify_history_enabled():
        return
    entry: dict[str, Any] = {
        "ts": time.time(),
        "channel": (channel or "desktop").strip()[:32],
        "title": (title or "")[:120],
        "body": (body or "")[:300],
        "severity": (severity or "info")[:16],
    }
    if session_id:
        entry["session_id"] = str(session_id)[:64]
    if upload_id:
        entry["upload_id"] = str(upload_id)[:64]
    if extra:
        entry.update({k: extra[k] for k in list(extra.keys())[:6]})
    try:
        _HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _HISTORY_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        _trim_history_file()
    except Exception:
        pass


def _trim_history_file() -> None:
    if not _HISTORY_PATH.is_file():
        return
    try:
        lines = _HISTORY_PATH.read_text(encoding="utf-8").splitlines()
        if len(lines) <= _MAX_STORE:
            return
        kept = lines[-_MAX_STORE:]
        _HISTORY_PATH.write_text("\n".join(kept) + "\n", encoding="utf-8")
    except Exception:
        pass


def list_notify_history(*, limit: int | None = None) -> dict[str, Any]:
    if not notify_history_enabled():
        return {"ok": True, "items": [], "count": 0, "disabled": True}
    cap = int(limit if limit is not None else _history_limit())
    items: list[dict[str, Any]] = []
    if _HISTORY_PATH.is_file():
        try:
            lines = _HISTORY_PATH.read_text(encoding="utf-8").splitlines()
            for line in reversed(lines):
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except Exception:
                    continue
                if isinstance(row, dict):
                    items.append(row)
                if len(items) >= cap:
                    break
        except Exception:
            pass
    return {"ok": True, "items": items, "count": len(items)}


def log_desktop_notifications(notifications: list[dict[str, Any]]) -> None:
    for n in notifications or []:
        append_notify_history(
            channel="desktop",
            title=str(n.get("title") or ""),
            body=str(n.get("body") or ""),
            severity=str(n.get("severity") or "info"),
            session_id=n.get("session_id"),
            upload_id=n.get("upload_id"),
        )


def log_email_notification(status: dict[str, Any], reminders: list[dict[str, Any]]) -> None:
    if not status.get("sent"):
        return
    body = "; ".join(
        str(r.get("hint") or "")[:80] for r in (reminders or [])[:5] if r.get("hint")
    )
    append_notify_history(
        channel="email",
        title=f"E-posta — {status.get('count') or '?'} hatırlatıcı",
        body=body or str(status.get("to") or ""),
        severity="warn",
        extra={"to": status.get("to")},
    )
