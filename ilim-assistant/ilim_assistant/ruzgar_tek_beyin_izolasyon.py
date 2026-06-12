# Created by Ümit & Gökçenur
"""Tek beyin Faz I — soru/cevap eşleşmesi ve bilgi yolu bağlam izolasyonu."""

from __future__ import annotations

import os
import re
from typing import Any

TEK_BEYIN_IZOLASYON_VERSION = "tek-beyin-izolasyon-v1-2026-06-12-faz-i"

_KIM_SORUSU = re.compile(
    r"\b(kimdir|kimdi|kim\b|kimi|kimler|kimesne)\b",
    re.I,
)


def tek_beyin_izolasyon_enabled() -> bool:
    if os.environ.get("RUZGAR_TEK_BEYIN", "1").strip().lower() in ("0", "false", "no"):
        return False
    return os.environ.get("RUZGAR_TEK_BEYIN_IZOLASYON", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def sanitize_paired_messages(messages: list | None) -> list[dict[str, str]]:
    """Yalnızca geçerli user→assistant çiftlerini tut; yetim ve çift rol mesajlarını at."""
    try:
        from ilim_assistant.chat_core import ensure_messages

        msgs = ensure_messages(messages or [])
    except Exception:
        msgs = list(messages or [])
    out: list[dict[str, str]] = []
    pending_user = ""
    for item in msgs:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or "").strip().lower()
        content = str(item.get("content") or "").strip()
        if not content:
            continue
        if role == "user":
            pending_user = content
        elif role == "assistant":
            if pending_user:
                out.append({"role": "user", "content": pending_user})
                out.append({"role": "assistant", "content": content})
                pending_user = ""
    return out


def looks_like_bilgi_isolation_turn(
    message: str,
    question_plan: Any | None = None,
) -> bool:
    """Ansiklopedik / bilgi sorusu — önceki sohbet kirliliğini sınırla."""
    if not tek_beyin_izolasyon_enabled():
        return False
    primary = ""
    if question_plan is not None:
        primary = str(getattr(question_plan, "primary", "") or "").strip().lower()
    if primary in ("bilgi", "bilim", "dilbilgisi"):
        return True
    raw = (message or "").strip()
    if _KIM_SORUSU.search(raw):
        return True
    try:
        from ilim_assistant.ana_motor_plan import looks_like_encyclopedic_fact_question

        if looks_like_encyclopedic_fact_question(raw):
            return True
    except Exception:
        pass
    return False


def _bilgi_prior_cap() -> int:
    try:
        return max(0, min(int(os.environ.get("RUZGAR_TEK_BEYIN_BILGI_PRIOR", "4")), 8))
    except ValueError:
        return 4


def prior_messages_for_turn_isolated(
    history: list | None,
    mode: str,
    *,
    message: str = "",
    question_plan: Any | None = None,
) -> list[dict[str, str]]:
    """Temizlenmiş geçmiş; bilgi sorularında kısa öncül."""
    cleaned = sanitize_paired_messages(history)
    try:
        from ilim_assistant.chat_core import (
            _history_char_cap,
            _history_msg_cap,
            trim_chat_tail,
        )

        base = trim_chat_tail(
            cleaned,
            max_messages=_history_msg_cap(mode),
            max_total_chars=_history_char_cap(mode),
        )
    except Exception:
        base = cleaned
    if not looks_like_bilgi_isolation_turn(message, question_plan):
        return base
    cap = _bilgi_prior_cap()
    if cap <= 0:
        return []
    try:
        from ilim_assistant.chat_core import trim_chat_tail

        return trim_chat_tail(base, max_messages=cap, max_total_chars=2400)
    except Exception:
        return base[-cap:] if cap else []


def merge_turn_rows_client_first(
    client_rows: list[dict[str, str]],
    disk_rows: list[dict[str, str]],
    *,
    limit: int,
    session_id: str | None = None,
    min_client_turns: int = 2,
) -> list[dict[str, str]]:
    """
    İstemci geçmişi yeterliyse yalnızca onu kullan.
    Disk tamamlayıcısı yalnızca istemci boş/çok kısa iken; session_id ile süzülür.
    """
    client = [r for r in client_rows if (r.get("user") or "").strip()]
    if len(client) >= min_client_turns:
        return client[-limit:]

    filtered = list(disk_rows)
    sid = (session_id or "").strip()
    if sid:
        by_sid = [
            r
            for r in disk_rows
            if str(r.get("session_id") or "").strip() == sid
        ]
        if by_sid:
            filtered = by_sid

    if not client:
        return filtered[-limit:]

    anchor = (client[0].get("user") or "").strip()
    tail: list[dict[str, str]] = []
    passed = not anchor
    for row in filtered:
        u = str(row.get("user") or "").strip()
        if not passed:
            if u == anchor:
                passed = True
            continue
        tail.append({"user": u, "assistant": str(row.get("assistant") or "").strip()})

    seen = {f"{r.get('user')}\0{r.get('assistant')}" for r in tail}
    for row in client:
        key = f"{row.get('user')}\0{row.get('assistant')}"
        if key in seen:
            continue
        seen.add(key)
        tail.append(row)
    return tail[-limit:]


def bilgi_isolation_user_addon(message: str) -> str:
    """Bilgi turuna eklenecek kısa talimat."""
    q = (message or "").strip()
    if not q:
        return ""
    return (
        "\n\n[TALİMAT — BİLGİ TURU İZOLASYONU]\n"
        f"Yanıt yalnızca şu soruya: «{q[:240]}».\n"
        "Önceki sohbet konularını bu cevaba karıştırma; farklı kişi/konu uydurma.\n"
        "[/TALİMAT]\n"
    )


def tek_beyin_izolasyon_status() -> dict[str, Any]:
    return {
        "enabled": tek_beyin_izolasyon_enabled(),
        "version": TEK_BEYIN_IZOLASYON_VERSION,
        "bilgi_prior_cap": _bilgi_prior_cap(),
    }
