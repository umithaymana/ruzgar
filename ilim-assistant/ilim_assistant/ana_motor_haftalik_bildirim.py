# Created by Ümit & Gökçenur
"""Ana Motor Faz Q1 — haftalık özet masaüstü/e-posta bildirimi."""

from __future__ import annotations

import json
import os
import smtplib
import time
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

_PKG_ROOT = Path(__file__).resolve().parent.parent
_STATE_PATH = _PKG_ROOT / ".ruzgar" / "ana_motor_weekly_notify_state.json"


def weekly_notify_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_WEEKLY_NOTIFY", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _cooldown_sec() -> int:
    try:
        return max(3600, int(os.environ.get("RUZGAR_ANA_WEEKLY_NOTIFY_COOLDOWN_SEC", "604800")))
    except ValueError:
        return 604800


def _load_state() -> dict[str, Any]:
    if not _STATE_PATH.is_file():
        return {}
    try:
        data = json.loads(_STATE_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_state(state: dict[str, Any]) -> None:
    _STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _cooldown_active() -> bool:
    last = float(_load_state().get("last_sent_at") or 0)
    return (time.time() - last) < _cooldown_sec()


def build_weekly_desktop_notifications(summary: dict[str, Any]) -> list[dict[str, Any]]:
    if not weekly_notify_enabled():
        return []
    try:
        from ilim_assistant.ana_motor_bildirim_tercih import effective_desktop_notify

        if not effective_desktop_notify():
            return []
    except Exception:
        from ilim_assistant.ana_motor_hatirlat_bildirim import desktop_notify_enabled

        if not desktop_notify_enabled():
            return []
    card = summary.get("summary_card") if isinstance(summary.get("summary_card"), dict) else {}
    body = str(card.get("body") or "").strip()
    if not body:
        return []
    return [
        {
            "title": str(card.get("title") or "Rüzgar — Haftalık özet"),
            "body": body[:220],
            "severity": "info",
            "kind": "weekly_summary",
        }
    ]


def maybe_send_weekly_email(summary: dict[str, Any], *, force: bool = False) -> dict[str, Any]:
    if not weekly_notify_enabled():
        return {"ok": True, "sent": False, "reason": "weekly_notify_disabled"}
    try:
        from ilim_assistant.ana_motor_bildirim_tercih import effective_email_notify

        if not effective_email_notify():
            return {"ok": True, "sent": False, "reason": "email_prefs_disabled"}
    except Exception:
        from ilim_assistant.ana_motor_hatirlat_bildirim import email_notify_enabled

        if not email_notify_enabled():
            return {"ok": True, "sent": False, "reason": "email_disabled"}
    if not force and _cooldown_active():
        return {"ok": True, "sent": False, "reason": "cooldown"}

    card = summary.get("summary_card") if isinstance(summary.get("summary_card"), dict) else {}
    body = str(card.get("body") or "").strip()
    if not body:
        return {"ok": True, "sent": False, "reason": "empty_summary"}

    host = os.environ.get("RUZGAR_SMTP_HOST", "").strip()
    port = int(os.environ.get("RUZGAR_SMTP_PORT", "587") or "587")
    user = os.environ.get("RUZGAR_SMTP_USER", "").strip()
    password = os.environ.get("RUZGAR_SMTP_PASS", "").strip()
    to_addr = os.environ.get("RUZGAR_REMIND_EMAIL_TO", "").strip()
    from_addr = os.environ.get("RUZGAR_REMIND_EMAIL_FROM", user or "ruzgar@local").strip()
    if not host or not to_addr:
        return {"ok": False, "sent": False, "error": "SMTP veya alıcı yapılandırılmamış."}

    title = str(card.get("title") or "Haftalık özet")
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = f"Rüzgar — {title}"
    msg["From"] = from_addr
    msg["To"] = to_addr
    try:
        with smtplib.SMTP(host, port, timeout=20) as srv:
            if os.environ.get("RUZGAR_SMTP_TLS", "1").strip().lower() not in ("0", "false", "no"):
                srv.starttls()
            if user and password:
                srv.login(user, password)
            srv.sendmail(from_addr, [to_addr], msg.as_string())
        state = _load_state()
        state["last_sent_at"] = time.time()
        state["last_channel"] = "email"
        _save_state(state)
        result = {"ok": True, "sent": True, "to": to_addr, "channel": "email"}
        try:
            from ilim_assistant.ana_motor_bildirim_gecmis import append_notify_history

            append_notify_history(
                channel="email",
                title=title,
                body=body[:300],
                severity="info",
                extra={"kind": "weekly_summary"},
            )
        except Exception:
            pass
        return result
    except Exception as exc:
        return {"ok": False, "sent": False, "error": str(exc)[:200]}


def attach_weekly_notifications(
    summary: dict[str, Any],
    *,
    send_desktop: bool = True,
    send_email: bool = False,
    force: bool = False,
) -> dict[str, Any]:
    """Haftalık özet yanıtına bildirim alanları ekle (cooldown'a saygılı)."""
    if not weekly_notify_enabled():
        summary["weekly_notify_disabled"] = True
        return summary
    payload = dict(summary)
    on_cooldown = _cooldown_active() and not force
    payload["weekly_notify_cooldown"] = on_cooldown

    desktop: list[dict[str, Any]] = []
    if send_desktop and not on_cooldown:
        desktop = build_weekly_desktop_notifications(summary)
        if desktop:
            try:
                from ilim_assistant.ana_motor_bildirim_gecmis import log_desktop_notifications

                log_desktop_notifications(desktop)
            except Exception:
                pass
            state = _load_state()
            state["last_sent_at"] = time.time()
            state["last_channel"] = "desktop"
            _save_state(state)
    payload["desktop_notifications"] = desktop

    email_status: dict[str, Any] = {"sent": False, "reason": "not_requested"}
    if send_email:
        email_status = maybe_send_weekly_email(summary, force=force)
    payload["email_status"] = email_status
    return payload
