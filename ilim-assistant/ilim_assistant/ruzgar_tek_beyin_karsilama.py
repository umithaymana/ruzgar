# Created by Ümit & Gökçenur
"""Tek beyin — oturum karşılama: dünkü konuşmayı hatırla, LLM beklemeden."""

from __future__ import annotations

import os
import re
import time
import unicodedata
from datetime import datetime, timezone
from typing import Any

TEK_BEYIN_KARSILAMA_VERSION = "tek-beyin-karsilama-v2-2026-06-13-aktif-motor"

_GREETING = re.compile(
    r"^(?:"
    r"günaydın|gunaydin|iyi\s+günler|iyi\s+gunler|"
    r"merhaba|selam(?:ün\s+aleyküm|un\s+aleykum|ın\s+aleyküm|in\s+aleykum)?|"
    r"hey|sa|naber|n'aber|"
    r"tekrar\s+merhaba|yeniden\s+merhaba|"
    r"ben\s+geldim|geldim"
    r")\s*[\!.?…]*$",
    re.I,
)
_GREETING_COMPLAINT = re.compile(
    r"(?:"
    r"günaydın\s+diyorum|gunaydin\s+diyorum|"
    r"selam\s+dedim|merhaba\s+dedim|"
    r"sohbetten\s+bahsed|sohbet\s+etmekten\s+bahsed|"
    r"karşılama\s+bekl|karsilama\s+bekl|"
    r"dün\s+ne\s+yapt|dun\s+ne\s+yapt|nerede\s+kald"
    r")",
    re.I,
)
_RESUME_CUE = re.compile(
    r"(?:"
    r"dün\s+ne|dun\s+ne|"
    r"dün\s+nerede|dun\s+nerede|"
    r"kald[ıi]g[ıi]m[ıi]z|kaldigimiz|"
    r"devam\s+edelim|"
    r"nerede\s+kald[ıi]k|nerede\s+kaldik|"
    r"son\s+konu|"
    r"önceki\s+oturum|onceki\s+oturum"
    r")",
    re.I,
)


def tek_beyin_karsilama_enabled() -> bool:
    if os.environ.get("RUZGAR_TEK_BEYIN", "1").strip().lower() in ("0", "false", "no"):
        return False
    return os.environ.get("RUZGAR_TEK_BEYIN_KARSILAMA", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _norm(text: str) -> str:
    t = unicodedata.normalize("NFKC", (text or "").strip().lower())
    return re.sub(r"\s+", " ", t)


def looks_like_greeting_complaint(message: str) -> bool:
    raw = (message or "").strip()
    if len(raw) < 12:
        return False
    return bool(_GREETING_COMPLAINT.search(_norm(raw)))


def looks_like_session_greeting(message: str) -> bool:
    raw = (message or "").strip()
    if not raw or len(raw) > 80:
        return False
    if _RESUME_CUE.search(_norm(raw)):
        return True
    return bool(_GREETING.match(raw))


def _clip(text: str, limit: int = 120) -> str:
    t = " ".join((text or "").split())
    return t if len(t) <= limit else t[: max(0, limit - 1)].rstrip() + "…"


def _load_recent_turns(*, limit: int = 40) -> list[dict[str, Any]]:
    try:
        from ilim_assistant.ana_motor_sohbet_gecmis import recent_chat_history

        data = recent_chat_history(limit=limit)
        return list(data.get("items") or [])
    except Exception:
        return []


def _topic_lines(items: list[dict[str, Any]], *, max_topics: int = 6) -> list[str]:
    seen: set[str] = set()
    topics: list[str] = []
    skip_greet = frozenset(
        {"günaydın", "gunaydin", "merhaba", "selam", "naber", "hey", "sa"}
    )
    for row in items:
        u = str(row.get("user") or "").strip()
        if not u or len(u) < 4:
            continue
        key = _norm(u)
        if key in seen:
            continue
        if key in skip_greet:
            continue
        if u.startswith("http"):
            continue
        seen.add(key)
        topics.append(_clip(u, 88))
        if len(topics) >= max_topics:
            break
    return topics


def _last_meaningful_turn(items: list[dict[str, Any]]) -> tuple[str, str]:
    for row in items:
        u = str(row.get("user") or "").strip()
        a = str(row.get("assistant") or "").strip()
        if not u or not a:
            continue
        if _norm(u) in ("günaydın", "gunaydin", "merhaba", "selam"):
            continue
        if a.startswith("[") or "kotası" in a.lower() or "quota" in a.lower():
            continue
        return u, a
    return "", ""


def _session_age_hours(items: list[dict[str, Any]]) -> float | None:
    if not items:
        return None
    try:
        ts = float(items[0].get("ts") or 0.0)
        if ts <= 0:
            return None
        return max(0.0, (time.time() - ts) / 3600.0)
    except (TypeError, ValueError):
        return None


def _parse_active_motor_line(conversation_context: str | None) -> str:
    ctx = (conversation_context or "").strip()
    if not ctx:
        return ""
    for pat in (
        r"(?im)aktif\s+motor\s*[:\-]\s*(?P<a>.+)$",
        r"(?im)motor\s*[:\-]\s*(?P<a>.+)$",
        r"(?im)chatMode\s*[:\-]\s*(?P<a>.+)$",
    ):
        m = re.search(pat, ctx)
        if m:
            return _clip(str(m.group("a") or "").strip(), 80)
    low = ctx.casefold()
    for label, key in (
        ("video", "Video motoru"),
        ("tercüme", "Tercüme motoru"),
        ("tercume", "Tercüme motoru"),
        ("programlama", "Programlama motoru"),
        ("sinema", "Sinema motoru"),
        ("hizir", "HIZIR"),
        ("nebula", "Nebula / kaynak"),
    ):
        if key.lower() in low or label in low:
            return key
    return ""


def build_session_resume_greeting(
    message: str,
    *,
    client_history: list | None = None,
    conversation_context: str | None = None,
    apology: bool = False,
) -> str | None:
    """Ümit abi geldiğinde — dün/son oturum özeti, LLM yok."""
    if not tek_beyin_karsilama_enabled():
        return None
    if not looks_like_session_greeting(message) and not (
        apology and looks_like_greeting_complaint(message)
    ):
        return None

    items = _load_recent_turns(limit=48)
    if client_history:
        try:
            from ilim_assistant.ana_motor_sohbet_gecmis import _merge_history_items

            items = _merge_history_items(
                disk_items=items,
                client_history=client_history,
                limit=48,
            )
        except Exception:
            pass

    blob = _norm(message)
    greet = "Merhaba Ümit abi"
    if "günaydın" in blob or "gunaydin" in blob:
        greet = "Günaydın Ümit abi"
    elif "selam" in blob:
        greet = "Selam Ümit abi"

    if not items:
        return (
            f"{greet}! Seni yine burada görmek güzel. "
            "Henüz kayıtlı önceki oturum bulamadım — bugün neye odaklanalım?"
        )

    topics = _topic_lines(items)
    last_u, last_a = _last_meaningful_turn(items)
    age_h = _session_age_hours(items)

    lines = []
    if apology:
        lines.append(
            "Haklısın Ümit abi — selamına tam karşılık veremedim; düzeltiyorum."
        )
        lines.append("")
    lines.append(f"{greet}! Seni tanıyorum — kaldığımız yerden devam edelim.")
    aktif = _parse_active_motor_line(conversation_context)
    if aktif:
        lines.append(f"**Aktif motor:** {aktif}")
    lines.append("")

    if age_h is not None:
        if age_h >= 18:
            when = "dün" if age_h < 36 else "önceki günlerde"
            lines.append(f"**{when.capitalize()}** konuştuğumuz başlıklardan bazıları:")
        else:
            lines.append("**Bugünkü oturumda** konuştuğumuz başlıklardan bazıları:")
    else:
        lines.append("**Son konuşmalarımızdan** hatırladıklarım:")

    if topics:
        for i, t in enumerate(topics[:5], 1):
            lines.append(f"{i}. {t}")
    else:
        lines.append("· Henüz net bir konu başlığı yok.")

    if last_u and last_a:
        lines.append("")
        lines.append(f"**En son:** «{_clip(last_u, 72)}»")
        lines.append(f"→ {_clip(last_a, 200)}")

    lines.append("")
    lines.append("Nereden devam edelim — söylemen yeterli.")
    return "\n".join(lines).strip()


def try_session_resume_greeting(
    message: str,
    *,
    client_history: list | None = None,
    conversation_context: str | None = None,
) -> str | None:
    if looks_like_greeting_complaint(message):
        return build_session_resume_greeting(
            message,
            client_history=client_history,
            conversation_context=conversation_context,
            apology=True,
        )
    return build_session_resume_greeting(
        message,
        client_history=client_history,
        conversation_context=conversation_context,
    )


def tek_beyin_karsilama_status() -> dict[str, Any]:
    return {
        "enabled": tek_beyin_karsilama_enabled(),
        "version": TEK_BEYIN_KARSILAMA_VERSION,
    }
