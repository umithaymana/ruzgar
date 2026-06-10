# Created by Ümit & Gökçenur
"""Ana Motor Faz M2 — hatırlatıcı masaüstü/e-posta bildirimi."""

from __future__ import annotations

import os
import smtplib
import time
from email.mime.text import MIMEText
from typing import Any

_last_email_sent: float = 0.0


def desktop_notify_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_REMIND_DESKTOP", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def email_notify_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_REMIND_EMAIL", "0").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def _email_cooldown_sec() -> int:
    try:
        return max(300, int(os.environ.get("RUZGAR_ANA_REMIND_EMAIL_COOLDOWN_SEC", "3600")))
    except ValueError:
        return 3600


def build_desktop_notifications(reminders: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Renderer Notification API için kısa bildirim listesi."""
    try:
        from ilim_assistant.ana_motor_bildirim_tercih import (
            effective_desktop_notify,
            filter_reminders_by_prefs,
        )

        if not effective_desktop_notify():
            return []
        reminders = filter_reminders_by_prefs(reminders)
    except Exception:
        if not desktop_notify_enabled():
            return []
    out: list[dict[str, Any]] = []
    for row in reminders:
        hint = str(row.get("hint") or "").strip()
        if not hint:
            continue
        out.append(
            {
                "title": "Rüzgar — Ana Motor hatırlatıcı",
                "body": hint[:220],
                "severity": row.get("severity") or "info",
                "kind": row.get("kind"),
                "session_id": row.get("session_id"),
                "upload_id": row.get("upload_id"),
            }
        )
    try:
        from ilim_assistant.ana_motor_bildirim_gecmis import log_desktop_notifications

        if out:
            log_desktop_notifications(out)
    except Exception:
        pass
    return out


def maybe_send_email_reminders(reminders: list[dict[str, Any]]) -> dict[str, Any]:
    """İsteğe bağlı SMTP e-posta (env ile)."""
    global _last_email_sent
    try:
        from ilim_assistant.ana_motor_bildirim_tercih import (
            effective_email_notify,
            filter_reminders_by_prefs,
        )

        if not effective_email_notify():
            return {"ok": True, "sent": False, "reason": "email_prefs_disabled"}
        reminders = filter_reminders_by_prefs(reminders)
    except Exception:
        if not email_notify_enabled():
            return {"ok": True, "sent": False, "reason": "email_disabled_or_empty"}
    if not reminders:
        return {"ok": True, "sent": False, "reason": "email_disabled_or_empty"}
    now = time.time()
    if now - _last_email_sent < _email_cooldown_sec():
        return {"ok": True, "sent": False, "reason": "cooldown"}

    host = os.environ.get("RUZGAR_SMTP_HOST", "").strip()
    port = int(os.environ.get("RUZGAR_SMTP_PORT", "587") or "587")
    user = os.environ.get("RUZGAR_SMTP_USER", "").strip()
    password = os.environ.get("RUZGAR_SMTP_PASS", "").strip()
    to_addr = os.environ.get("RUZGAR_REMIND_EMAIL_TO", "").strip()
    from_addr = os.environ.get("RUZGAR_REMIND_EMAIL_FROM", user or "ruzgar@local").strip()
    if not host or not to_addr:
        return {"ok": False, "sent": False, "error": "SMTP veya alıcı yapılandırılmamış."}

    lines = [str(r.get("hint") or "") for r in reminders[:8] if r.get("hint")]
    if not lines:
        return {"ok": True, "sent": False, "reason": "no_hints"}
    body = "Rüzgar Ana Motor hatırlatıcıları:\n\n" + "\n".join(f"• {x}" for x in lines)
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = f"Rüzgar — {len(lines)} Ana Motor hatırlatıcısı"
    msg["From"] = from_addr
    msg["To"] = to_addr
    try:
        with smtplib.SMTP(host, port, timeout=20) as srv:
            if os.environ.get("RUZGAR_SMTP_TLS", "1").strip().lower() not in ("0", "false", "no"):
                srv.starttls()
            if user and password:
                srv.login(user, password)
            srv.sendmail(from_addr, [to_addr], msg.as_string())
        _last_email_sent = now
        result = {"ok": True, "sent": True, "to": to_addr, "count": len(lines)}
        try:
            from ilim_assistant.ana_motor_bildirim_gecmis import log_email_notification

            log_email_notification(result, reminders)
        except Exception:
            pass
        return result
    except Exception as exc:
        return {"ok": False, "sent": False, "error": str(exc)[:200]}
