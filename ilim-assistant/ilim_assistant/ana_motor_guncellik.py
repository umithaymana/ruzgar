# Created by Ümit & Gökçenur
"""Ana Motor Faz C / 9.4 — web güncellik damgası."""

from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


def freshness_stamp_enabled() -> bool:
    return os.environ.get("RUZGAR_WEB_FRESHNESS_STAMP", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def reply_freshness_stamp_enabled() -> bool:
    return os.environ.get("RUZGAR_REPLY_FRESHNESS_STAMP", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _display_tz() -> ZoneInfo:
    name = (os.environ.get("RUZGAR_DISPLAY_TZ") or "Europe/Istanbul").strip()
    try:
        return ZoneInfo(name)
    except Exception:
        return ZoneInfo("UTC")


def web_scan_stamp_line() -> str:
    """Web bağlamı başlığı — UTC + yerel saat."""
    if not freshness_stamp_enabled():
        return ""
    utc = datetime.now(timezone.utc)
    local = utc.astimezone(_display_tz())
    return (
        f"**Güncellik:** Web taraması {utc.strftime('%Y-%m-%d %H:%M')} UTC "
        f"({local.strftime('%d.%m.%Y %H:%M')} yerel) — snippet'ler anlık olmayabilir.\n"
    )


def prepend_freshness_to_web_context(web_context: str) -> str:
    body = (web_context or "").strip()
    if not body or not freshness_stamp_enabled():
        return web_context
    stamp = web_scan_stamp_line().strip()
    if not stamp or stamp in body:
        return web_context
    return stamp + "\n" + body


def _has_freshness_line(text: str) -> bool:
    return bool(re.search(r"\*\*Güncellik:\*\*", text or "", re.I))


def append_reply_freshness_stamp(
    reply: str,
    *,
    web_was_used: bool,
    user_message: str = "",
) -> str:
    """Cevap sonuna güncellik notu (web kullanıldıysa)."""
    if not reply_freshness_stamp_enabled() or not web_was_used:
        return reply
    body = (reply or "").strip()
    if not body or _has_freshness_line(body):
        return reply
    utc = datetime.now(timezone.utc)
    local = utc.astimezone(_display_tz())
    low = (user_message or "").casefold()
    guncel_hint = any(
        x in low for x in ("güncel", "guncel", "bugün", "bugun", "haber", "son dakika")
    )
    extra = (
        f"\n\n**Güncellik:** Yanıtta web taraması kullanıldı "
        f"({local.strftime('%d.%m.%Y %H:%M')})."
    )
    if guncel_hint:
        extra += " Haber ve «bugün» sorularında kaynak tarihini kontrol et."
    return body + extra
