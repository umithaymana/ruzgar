# Created by Ümit & Gökçenur
"""Tek beyin Faz F — oturum özeti ve bağlam enjeksiyonu (dost/hafıza erken yollar)."""

from __future__ import annotations

import os
import re
from typing import Any

TEK_BEYIN_BAGLAM_VERSION = "tek-beyin-baglam-v1-2026-06-12-faz-f"


def tek_beyin_baglam_enabled() -> bool:
    if os.environ.get("RUZGAR_TEK_BEYIN", "1").strip().lower() in ("0", "false", "no"):
        return False
    return os.environ.get("RUZGAR_TEK_BEYIN_BAGLAM", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _clip(text: str, limit: int) -> str:
    t = " ".join((text or "").split())
    return t if len(t) <= limit else t[: max(0, limit - 1)].rstrip() + "…"


def _brief_turn_limit() -> int:
    try:
        return max(3, min(int(os.environ.get("RUZGAR_TEK_BEYIN_BAGLAM_TURNS", "6")), 12))
    except ValueError:
        return 6


def _brief_char_cap() -> int:
    try:
        return max(400, min(int(os.environ.get("RUZGAR_TEK_BEYIN_BAGLAM_CHARS", "1100")), 3000))
    except ValueError:
        return 1100


def _turns_from_history(history: list | None, *, limit: int) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    if not history:
        return out
    pending_user = ""
    for item in history:
        if isinstance(item, dict):
            role = str(item.get("role") or "").strip().lower()
            content = str(item.get("content") or "").strip()
            if not content:
                continue
            if role == "user":
                pending_user = content
            elif role == "assistant" and pending_user:
                out.append({"user": pending_user, "assistant": content})
                pending_user = ""
            continue
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            user = str(item[0] or "").strip()
            assistant = str(item[1] or "").strip()
            if user and assistant:
                out.append({"user": user, "assistant": assistant})
    return out[-limit:]


def build_rolling_session_brief(history: list | None) -> str:
    """Son turlardan kısa özet — LLM çağrısı yok."""
    if not tek_beyin_baglam_enabled():
        return ""
    turns = _turns_from_history(history, limit=_brief_turn_limit())
    if not turns:
        return ""
    lines: list[str] = []
    for row in turns:
        user = _clip(row.get("user") or "", 72)
        assistant = _clip(row.get("assistant") or "", 96)
        if user:
            lines.append(f"· Ümit: {user}")
        if assistant:
            lines.append(f"  Rüzgar: {assistant}")
    if not lines:
        return ""
    body = "\n".join(lines)
    cap = _brief_char_cap()
    if len(body) > cap:
        body = body[-cap:]
        body = "…\n" + body.split("\n", 1)[-1] if "\n" in body else "…" + body
    return body


def _mood_hint_line(history: list | None) -> str:
    try:
        from ilim_assistant.ruzgar_tek_beyin_oturum import analyze_mood_thread

        mt = analyze_mood_thread(history)
        if mt.active:
            return f"Dost sohbet aktif ({mt.mood_label or 'sohbet'}, tur {mt.turn_count})."
        if mt.paused:
            return (
                f"Dost sohbet ara verdi — bilgi sorusu girdi "
                f"({mt.mood_label or 'sohbet'} hâlâ hatırlanır)."
            )
    except Exception:
        pass
    return ""


def build_tek_beyin_baglam_addon(
    message: str,
    history: list | None,
    *,
    conversation_context: str | None = None,
) -> str:
    """Dost/hafıza erken yollarına eklenecek bağlam bloğu."""
    if not tek_beyin_baglam_enabled():
        return ""
    sections: list[str] = []
    brief = build_rolling_session_brief(history)
    if brief:
        sections.append(
            "[OTURUM ÖZETİ — son turlar; kullanıcıya aynen okuma]\n"
            + brief
            + "\n[/OTURUM ÖZETİ]"
        )
    mood = _mood_hint_line(history)
    if mood:
        sections.append(f"[DUYGU DURUMU] {mood} [/DUYGU DURUMU]")
    ctx = (conversation_context or "").strip()
    if ctx:
        sections.append(
            "[İSTEMCİ SOHBET BAĞLAMI]\n"
            + _clip(ctx, 2200)
            + "\n[/İSTEMCİ SOHBET BAĞLAMI]"
        )
    raw = (message or "").strip()
    if raw and re.search(r"\b(?:az\s+önce|biraz\s+önce|o\s+konuda|devam)\b", raw, re.I):
        sections.append(
            "[TALİMAT] Kullanıcı önceki turlara atıf yapıyor; oturum özetinden bağlamı çöz. "
            "Robotik «anlamadım» deme.\n"
        )
    if not sections:
        return ""
    return "\n\n" + "\n\n".join(sections) + "\n"


def tek_beyin_baglam_status() -> dict[str, Any]:
    return {
        "enabled": tek_beyin_baglam_enabled(),
        "version": TEK_BEYIN_BAGLAM_VERSION,
        "brief_turns": _brief_turn_limit(),
        "brief_chars": _brief_char_cap(),
    }
