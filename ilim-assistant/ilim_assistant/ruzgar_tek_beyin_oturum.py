# Created by Ümit & Gökçenur
"""Tek beyin Faz D — oturum derinliği, mood devamı, sesli tur uyumu."""

from __future__ import annotations

import os
import re
import unicodedata
from dataclasses import dataclass
from typing import Any

TEK_BEYIN_OTURUM_VERSION = "tek-beyin-oturum-v1-2026-06-12-faz-d"

_TOPIC_BREAK = re.compile(
    r"\b(?:"
    r"nedir|kimdir|kimdi|ne zaman|kaç|kac|"
    r"hat[ıi]rla|kaydet|"
    r"osmanl[ıi]|padisah|padişah|"
    r"program|kod|python|javascript|pytest|"
    r"indir|youtube|http|www\.|"
    r"çevir|cevir|dublaj|ocr|pdf"
    r")\b",
    re.I,
)
_CONTINUATION = re.compile(
    r"(?:"
    r"^evet\b|^hay[ıi]r\b|^peki\b|^tamam\b|^hakl[ıi]\s*s[ıi]n\b|"
    r"^bilmiyorum\b|^anlad[ıi]m\b|^devam\b|"
    r"ne\s+öner|ne\s+oner|sen\s+ne\s+d[üu][şs]|"
    r"yorgun|iyi\s+de[ğg]il|fena\s+de[ğg]il|"
    r"dinle|anlat|konu[şs]|konus|"
    r"sen\s+de|bana\s+da|"
    r"öyle\s+mi|oyle\s+mi|"
    r"neden\b|niye\b|nas[ıi]l\s+ge[çc]"
    r")",
    re.I,
)


def tek_beyin_oturum_enabled() -> bool:
    if os.environ.get("RUZGAR_TEK_BEYIN", "1").strip().lower() in ("0", "false", "no"):
        return False
    return os.environ.get("RUZGAR_TEK_BEYIN_OTURUM", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", (text or "").strip().lower()))


def _clip(text: str, limit: int) -> str:
    t = (text or "").strip()
    return t if len(t) <= limit else t[: max(0, limit - 1)].rstrip() + "…"


@dataclass(frozen=True)
class MoodThread:
    active: bool
    mood_label: str
    opening_snippet: str
    turn_count: int
    anchor_index: int


def _turns_from_history(history: list | None, *, limit: int = 14) -> list[dict[str, str]]:
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


def _mood_label_for(text: str) -> str:
    blob = _norm(text)
    if any(x in blob for x in ("canım sıkıldı", "canim sikildi", "sıkıldım", "sikildim")):
        return "can_sikintisi"
    if any(x in blob for x in ("moralim bozuk", "keyfim yok", "üzgünüm", "uzgunum", "mutsuzum")):
        return "uzgun"
    if any(x in blob for x in ("yalnızım", "yalnizim", "yanımda ol", "yanimda ol")):
        return "yalnizlik"
    if any(x in blob for x in ("dertleş", "dertles", "dinler misin")):
        return "dertlesme"
    return "dost_sohbet"


def _breaks_mood_thread(message: str) -> bool:
    raw = (message or "").strip()
    if not raw:
        return True
    if _TOPIC_BREAK.search(_norm(raw)):
        return True
    try:
        from ilim_assistant.ruzgar_tek_beyin import (
            looks_like_personal_memory_query,
            personal_hafiza_blocks_bilgi_path,
        )

        if looks_like_personal_memory_query(raw):
            return True
        if personal_hafiza_blocks_bilgi_path(raw):
            return True
    except Exception:
        pass
    try:
        from ilim_assistant.ana_motor_plan import _explicit_research_intent

        if _explicit_research_intent(raw):
            return True
    except Exception:
        pass
    return False


def analyze_mood_thread(history: list | None, *, lookback: int = 12) -> MoodThread:
    turns = _turns_from_history(history, limit=lookback)
    if not turns:
        return MoodThread(False, "", "", 0, -1)

    anchor = -1
    opening = ""
    label = ""
    try:
        from ilim_assistant.ruzgar_tek_beyin import looks_like_friend_mood_chat
    except Exception:
        looks_like_friend_mood_chat = lambda _m: False  # type: ignore[assignment,misc]

    for i in range(len(turns) - 1, -1, -1):
        user = turns[i].get("user") or ""
        if looks_like_friend_mood_chat(user):
            anchor = i
            opening = user
            label = _mood_label_for(user)
            break

    if anchor < 0:
        return MoodThread(False, "", "", 0, -1)

    max_span = _int_env("RUZGAR_TEK_BEYIN_MOOD_MAX_TURNS", 14, lo=4, hi=24)
    if len(turns) - anchor > max_span:
        return MoodThread(False, "", "", 0, -1)

    for t in turns[anchor:]:
        if _breaks_mood_thread(t.get("user") or ""):
            return MoodThread(False, "", "", 0, -1)

    return MoodThread(
        active=True,
        mood_label=label,
        opening_snippet=_clip(opening, 120),
        turn_count=len(turns) - anchor,
        anchor_index=anchor,
    )


def is_mood_thread_active(history: list | None) -> bool:
    if not tek_beyin_oturum_enabled():
        return False
    return analyze_mood_thread(history).active


def looks_like_mood_continuation(message: str, history: list | None) -> bool:
    """Açık mood işareti olmadan dost sohbet devamı (Faz D)."""
    if not tek_beyin_oturum_enabled():
        return False
    raw = (message or "").strip()
    if not raw or len(raw) > 500:
        return False
    if not is_mood_thread_active(history):
        return False
    if _breaks_mood_thread(raw):
        return False
    try:
        from ilim_assistant.ruzgar_tek_beyin import looks_like_friend_mood_chat

        if looks_like_friend_mood_chat(raw):
            return True
    except Exception:
        pass
    blob = _norm(raw)
    if len(raw) < 220:
        return True
    if _CONTINUATION.search(blob):
        return True
    if "?" in raw and len(raw.split()) <= 18:
        return True
    return False


def build_mood_thread_system_addon(thread: MoodThread | None) -> str:
    if not thread or not thread.active:
        return ""
    labels = {
        "can_sikintisi": "can sıkıntısı / sıkılma",
        "uzgun": "moral bozuk / üzgün",
        "yalnizlik": "yalnızlık / yanında olma ihtiyacı",
        "dertlesme": "dertleşme",
        "dost_sohbet": "yakın dost sohbeti",
    }
    mood_tr = labels.get(thread.mood_label, "yakın sohbet")
    return (
        f"\n\n[DOST OTURUM — devam]\n"
        f"Bu, kesintisiz bir dost sohbeti ({mood_tr}). "
        f"İlk mesaj: «{thread.opening_snippet}». "
        f"Tur: {thread.turn_count}.\n"
        "Önceki duygusal tonu sürdür; konuyu ansiklopedi/RAG yoluna çekme. "
        "Kısa devam cümlelerini («evet», «yorgunum», «ne önerirsin») bağlamdan çöz.\n"
        "[/DOST OTURUM]\n"
    )


def dost_prior_depth(*, mood_active: bool, voice_turn: bool) -> int:
    try:
        base = int(os.environ.get("RUZGAR_DOGAL_PRIOR_MSGS", "14"))
    except ValueError:
        base = 14
    if mood_active:
        try:
            base = max(base, int(os.environ.get("RUZGAR_TEK_BEYIN_MOOD_PRIOR", "18")))
        except ValueError:
            base = max(base, 18)
    if voice_turn:
        try:
            base = max(base, int(os.environ.get("RUZGAR_TEK_BEYIN_VOICE_PRIOR", "10")))
        except ValueError:
            base = max(base, 10)
    return max(4, min(base, 28))


def dost_max_tokens(*, mood_active: bool, voice_turn: bool) -> int:
    try:
        base = int(os.environ.get("RUZGAR_DOGAL_MAX_TOKENS", "720"))
    except ValueError:
        base = 720
    if mood_active:
        try:
            base = max(base, int(os.environ.get("RUZGAR_TEK_BEYIN_MOOD_MAX_TOKENS", "880")))
        except ValueError:
            base = max(base, 880)
    if voice_turn:
        try:
            cap = int(os.environ.get("RUZGAR_TEK_BEYIN_VOICE_MAX_TOKENS", "320"))
        except ValueError:
            cap = 320
        base = min(base, cap)
    return max(120, min(base, 1200))


def build_voice_turn_addon() -> str:
    return (
        "\n\n[SESLİ TUR — TTS]\n"
        "Yanıt sesli okunacak: 2–4 kısa cümle, akıcı paragraf; madde listesi yok. "
        "Uzun açıklama veya kaynak listesi verme.\n"
        "[/SESLİ TUR]\n"
    )


def enrich_dost_history(history: list | None) -> list:
    """Mood oturumunda jsonl + istemci geçmişini kronolojik birleştir."""
    if not tek_beyin_oturum_enabled():
        return list(history or [])
    try:
        from ilim_assistant.chat_core import ensure_messages

        client = ensure_messages(history or [])
    except Exception:
        client = list(history or [])
    cap = dost_prior_depth(mood_active=True, voice_turn=False) * 2
    if len(client) >= cap:
        return client[-cap:]
    try:
        from ilim_assistant.ana_motor_sohbet_gecmis import recent_chat_history

        disk = recent_chat_history(limit=cap).get("items") or []
    except Exception:
        return client[-cap:] if client else []
    disk_msgs: list[dict[str, str]] = []
    for row in reversed(disk):
        user = str(row.get("user") or "").strip()
        assistant = str(row.get("assistant") or "").strip()
        if user:
            disk_msgs.append({"role": "user", "content": user})
        if assistant:
            disk_msgs.append({"role": "assistant", "content": assistant})
    if not disk_msgs:
        return client[-cap:] if client else []
    seen: set[str] = set()
    merged: list[dict[str, str]] = []
    for msg in disk_msgs + client:
        role = str(msg.get("role") or "")
        content = str(msg.get("content") or "").strip()
        if not content:
            continue
        key = f"{role}\0{content}"
        if key in seen:
            continue
        seen.add(key)
        merged.append({"role": role, "content": content})
    return merged[-cap:]


def _int_env(name: str, default: int, *, lo: int, hi: int) -> int:
    try:
        v = int(os.environ.get(name, str(default)).strip())
    except ValueError:
        v = default
    return max(lo, min(v, hi))


def tek_beyin_oturum_status() -> dict[str, Any]:
    return {
        "enabled": tek_beyin_oturum_enabled(),
        "version": TEK_BEYIN_OTURUM_VERSION,
        "mood_max_turns": _int_env("RUZGAR_TEK_BEYIN_MOOD_MAX_TURNS", 14, lo=4, hi=24),
        "mood_prior_msgs": _int_env("RUZGAR_TEK_BEYIN_MOOD_PRIOR", 18, lo=8, hi=28),
        "voice_max_tokens": _int_env("RUZGAR_TEK_BEYIN_VOICE_MAX_TOKENS", 320, lo=120, hi=600),
    }
