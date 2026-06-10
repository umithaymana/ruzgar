# Created by Ümit & Gökçenur
"""Ana Motor Faz U1 — süper özet otomatik haftalık e-posta."""

from __future__ import annotations

import json
import os
import smtplib
import time
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

_PKG_ROOT = Path(__file__).resolve().parent.parent
_STATE_PATH = _PKG_ROOT / ".ruzgar" / "ana_motor_super_ozet_email_state.json"


def super_ozet_email_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_SUPER_OZET_EMAIL", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _cooldown_sec() -> int:
    try:
        return max(3600, int(os.environ.get("RUZGAR_ANA_SUPER_OZET_EMAIL_COOLDOWN_SEC", "604800")))
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


def effective_super_ozet_email() -> bool:
    if not super_ozet_email_enabled():
        return False
    try:
        from ilim_assistant.ana_motor_bildirim_tercih import effective_email_notify

        if not effective_email_notify():
            return False
    except Exception:
        from ilim_assistant.ana_motor_hatirlat_bildirim import email_notify_enabled

        if not email_notify_enabled():
            return False
    try:
        from ilim_assistant.ana_motor_schedule_tercih import load_schedule_prefs

        prefs = load_schedule_prefs().get("prefs") or {}
        return bool(prefs.get("super_ozet_email_enabled", False))
    except Exception:
        return False


def maybe_send_super_ozet_email(
    *,
    period_days: int = 7,
    force: bool = False,
) -> dict[str, Any]:
    if not super_ozet_email_enabled():
        return {"ok": True, "sent": False, "reason": "super_ozet_email_disabled"}
    if not effective_super_ozet_email() and not force:
        return {"ok": True, "sent": False, "reason": "super_ozet_email_prefs_off"}
    state = _load_state()
    now = time.time()
    if not force and (now - float(state.get("last_sent_at") or 0)) < _cooldown_sec():
        return {"ok": True, "sent": False, "reason": "cooldown"}

    from ilim_assistant.ana_motor_super_ozet_pdf import build_super_ozet_lines

    lines = build_super_ozet_lines(period_days=period_days)
    body = "\n".join(lines).strip()
    if not body:
        return {"ok": True, "sent": False, "reason": "empty_super_ozet"}

    host = os.environ.get("RUZGAR_SMTP_HOST", "").strip()
    port = int(os.environ.get("RUZGAR_SMTP_PORT", "587") or "587")
    user = os.environ.get("RUZGAR_SMTP_USER", "").strip()
    password = os.environ.get("RUZGAR_SMTP_PASS", "").strip()
    to_addr = os.environ.get("RUZGAR_REMIND_EMAIL_TO", "").strip()
    from_addr = os.environ.get("RUZGAR_REMIND_EMAIL_FROM", user or "ruzgar@local").strip()
    if not host or not to_addr:
        return {"ok": False, "sent": False, "error": "SMTP veya alıcı yapılandırılmamış."}

    period = max(1, min(int(period_days), 30))
    title = f"Rüzgar Ana Motor — Süper özet ({period} gün)"
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = title
    msg["From"] = from_addr
    msg["To"] = to_addr
    try:
        with smtplib.SMTP(host, port, timeout=20) as srv:
            if os.environ.get("RUZGAR_SMTP_TLS", "1").strip().lower() not in ("0", "false", "no"):
                srv.starttls()
            if user and password:
                srv.login(user, password)
            srv.sendmail(from_addr, [to_addr], msg.as_string())
        state["last_sent_at"] = now
        _save_state(state)
        result = {"ok": True, "sent": True, "to": to_addr, "channel": "super_ozet_email"}
        try:
            from ilim_assistant.ana_motor_bildirim_gecmis import append_notify_history

            append_notify_history(
                channel="email",
                title=title,
                body=body[:300],
                severity="info",
                extra={"kind": "super_ozet"},
            )
        except Exception:
            pass
        return result
    except Exception as exc:
        return {"ok": False, "sent": False, "error": str(exc)[:200]}
