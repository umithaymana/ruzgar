# Created by Ümit & Gökçenur
"""Tek beyin Faz H — oturum özeti + hatırla birleşik yanıt."""

from __future__ import annotations

import os
import re
import time
import unicodedata
from typing import Any

TEK_BEYIN_HATIRLA_VERSION = "tek-beyin-hatirla-v1-2026-06-12-faz-h"

_SESSION_REMEMBER = re.compile(
    r"(?:"
    r"(?:bugün(?:kü|ku)?|bu)\s+(?:sohbet|konu[şs]ma|oturum)|"
    r"sohbet(?:imizi|i)?|konu[şs](?:mam[ıi]z[ıi]|tu[ğg]umuzu)|oturum(?:u)?"
    r")\s+"
    r"(?:hat[ıi]rla|kaydet|haf[ıi]zaya\s+al|not\s+al)",
    re.I,
)
_SESSION_REMEMBER_ALT = re.compile(
    r"(?:"
    r"hat[ıi]rla\s+(?:bugün(?:kü|ku)?\s+)?(?:sohbet|konu[şs]ma|oturum)|"
    r"kaydet\s+(?:bugün(?:kü|ku)?\s+)?(?:sohbet|konu[şs]ma|oturum)"
    r")",
    re.I,
)


def tek_beyin_hatirla_enabled() -> bool:
    if os.environ.get("RUZGAR_TEK_BEYIN", "1").strip().lower() in ("0", "false", "no"):
        return False
    return os.environ.get("RUZGAR_TEK_BEYIN_HATIRLA", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", (text or "").strip().lower()))


def _clip(text: str, limit: int) -> str:
    t = " ".join((text or "").split())
    return t if len(t) <= limit else t[: max(0, limit - 1)].rstrip() + "…"


def looks_like_remember_session_query(message: str) -> bool:
    """«Bugünkü sohbeti hatırla» — kişisel not değil, oturum özeti."""
    raw = (message or "").strip()
    if not raw or len(raw) > 500:
        return False
    blob = _norm(raw)
    if _SESSION_REMEMBER.search(blob) or _SESSION_REMEMBER_ALT.search(blob):
        return True
    if re.search(
        r"(?:sohbet|oturum|konu[sş]ma).{0,20}(?:hat[ıi]rla|kaydet)|"
        r"(?:hat[ıi]rla|kaydet).{0,20}(?:sohbet|oturum|bugün|bugun)",
        blob,
    ):
        return True
    return False


def _build_hafiza_payload(summary: dict[str, Any]) -> tuple[str, str]:
    text = str(summary.get("summary_text") or "").strip()
    topics = summary.get("topics") or []
    mood = str(summary.get("mood") or "").strip()
    turn_count = int(summary.get("turn_count") or 0)
    stamp = time.strftime("%Y-%m-%d %H:%M")
    soru = f"Oturum özeti — Ümit abi ile sohbet ({stamp})"
    lines = [
        f"Ümit abi ile sohbet özeti ({stamp}, {turn_count} tur):",
        text,
    ]
    if topics:
        lines.append("Başlıklar: " + "; ".join(_clip(t, 48) for t in topics[-8:]))
    if mood:
        lines.append(f"Duygu tonu: {mood}")
    cevap = "\n".join(x for x in lines if x).strip()[:4000]
    return soru, cevap


def try_remember_session_command(
    message: str,
    *,
    history: list | None = None,
    session_id: str | None = None,
) -> str | None:
    """Oturum özetini kalıcı hafızaya yaz + doğal onay yanıtı."""
    if not tek_beyin_hatirla_enabled():
        return None
    if not looks_like_remember_session_query(message):
        return None

    summary: dict[str, Any] | None = None
    try:
        from ilim_assistant.ruzgar_tek_beyin_ozet import (
            get_cached_summary,
            rebuild_session_summary,
        )

        summary = rebuild_session_summary(history=history, session_id=session_id)
        if not summary:
            cached = get_cached_summary()
            if cached:
                summary = cached
    except Exception:
        summary = None

    if not summary or not str(summary.get("summary_text") or "").strip():
        return (
            "Ümit abi, henüz kaydedecek kadar uzun bir sohbet yok — "
            "birkaç tur daha konuşunca bugünkü oturumu hatırlaya bilirim."
        )

    soru, cevap = _build_hafiza_payload(summary)
    try:
        from ilim_assistant.hafiza_i_ruzgar import get_hafiza_motor

        get_hafiza_motor().ekle_bilgi(soru, cevap, motor_tipi="Hafıza")
    except Exception as exc:
        return f"Ümit abi, oturum özetini yazamadım: {exc}"

    topics = summary.get("topics") or []
    mood = str(summary.get("mood") or "").strip()
    lines = [
        "Tamam Ümit abi — bugünkü sohbetimizi hafızama yazdım.",
        "",
        str(summary.get("summary_text") or "").strip(),
    ]
    if topics:
        lines.append("")
        lines.append("Öne çıkan başlıklar: " + " · ".join(_clip(t, 40) for t in topics[-5:]))
    if mood:
        lines.append(f"(Duygu tonu: {mood})")
    lines.append("")
    lines.append(
        "İstediğin zaman «bugün ne konuştuk» veya «oturum özeti» diye sorabilirsin."
    )
    return "\n".join(lines).strip()


def tek_beyin_hatirla_status() -> dict[str, Any]:
    return {
        "enabled": tek_beyin_hatirla_enabled(),
        "version": TEK_BEYIN_HATIRLA_VERSION,
    }
