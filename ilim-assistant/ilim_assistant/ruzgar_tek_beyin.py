# Created by Ümit & Gökçenur
"""Tek beyin — kişisel hafıza önceliği, soru tipi, doğal yanıt yönlendirme."""

from __future__ import annotations

import os
import re
import unicodedata
from typing import Any, Iterator, Optional

TEK_BEYIN_VERSION = "tek-beyin-v11-2026-06-12-faz-k"

_KIM_SORUSU = re.compile(
    r"\b(kimdir|kimdi|kim\b|kimi|kimler|kimesne)\b",
    re.I,
)
_MEMORY_RECHECK = re.compile(
    r"(?:emin\s+misin|dogru\s+mu|doğru\s+mu|bir\s+daha\s+bak|tekrar\s+bak|"
    r"haf[ıi]zana\s+bak|kay[ıi]tl[ıi]na\s+bak|yanl[ıi][şs]\s+m[ıi])",
    re.I,
)
_ENCYCLOPEDIC_MARKERS = (
    "osmanlı",
    "osmanli",
    "padişah",
    "padisah",
    "devlet",
    "imparator",
    "hanedan",
    "filozof",
    "yazar",
    "şair",
    "sair",
    "bilim insanı",
    "tarih",
    "uygarlık",
    "uygarlik",
    "cumhuriyet",
)


def tek_beyin_enabled() -> bool:
    return os.environ.get("RUZGAR_TEK_BEYIN", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _norm_blob(text: str) -> str:
    t = unicodedata.normalize("NFKC", (text or "").strip().lower())
    return re.sub(r"\s+", " ", t)


def looks_like_memory_recheck_query(message: str) -> bool:
    raw = (message or "").strip()
    if len(raw) < 8:
        return False
    return bool(_MEMORY_RECHECK.search(_norm_blob(raw)))


def looks_like_personal_memory_query(message: str) -> bool:
    """Kişisel hafıza / profil sorusu (ansiklopedi değil)."""
    raw = (message or "").strip()
    if len(raw) < 4:
        return False
    blob = _norm_blob(raw)
    if looks_like_memory_recheck_query(raw):
        return True
    if any(
        x in blob
        for x in (
            "hatırla",
            "hatirla",
            "hafızana",
            "hafizana",
            "kaydettik",
            "kaydetmiş",
            "profilim",
            "ailem",
            "çocuklarım",
            "cocuklarim",
            "eşim",
            "esim",
        )
    ):
        return True
    if _KIM_SORUSU.search(blob):
        if any(m in blob for m in _ENCYCLOPEDIC_MARKERS):
            return False
        if re.search(r"\b(?:ne zaman|kaç yıl|kuruldu|nedir)\b", blob):
            return False
        return True
    return False


def _history_user_messages(client_history: list | None) -> list[str]:
    out: list[str] = []
    if not client_history:
        return out
    for item in client_history:
        if isinstance(item, dict):
            if str(item.get("role") or "").strip().lower() == "user":
                u = str(item.get("content") or "").strip()
                if u:
                    out.append(u)
        elif isinstance(item, (list, tuple)) and len(item) >= 1:
            u = str(item[0] or "").strip()
            if u:
                out.append(u)
    return out


def resolve_memory_query_message(
    message: str,
    client_history: list | None = None,
) -> str:
    """«Emin misin hafızana bak» → bir önceki asıl soruya dön."""
    raw = (message or "").strip()
    if not looks_like_memory_recheck_query(raw):
        return raw
    for u in reversed(_history_user_messages(client_history)):
        if looks_like_memory_recheck_query(u):
            continue
        if len(u) >= 5:
            return u
    return raw


def lookup_personal_hafiza_hint(message: str) -> Optional[dict[str, Any]]:
    """Kişisel hafıza eşleşmesi; bilgi yolunu kesmek için daha düşük eşik."""
    if not tek_beyin_enabled():
        return None
    msg = (message or "").strip()
    if not msg or "=" in msg or len(msg) > 4000:
        return None
    try:
        from ilim_assistant.hafiza_dogal_sentez import (
            _is_miss_answer,
            dogal_konus_enabled,
            should_skip_hafiza_dogal,
        )
        from ilim_assistant.hafiza_i_ruzgar import genel_hafiza_lookup_detayli

        if not dogal_konus_enabled():
            return None
        if should_skip_hafiza_dogal(msg) and not looks_like_personal_memory_query(msg):
            return None
        detay = genel_hafiza_lookup_detayli(msg)
    except Exception:
        return None
    if not detay:
        return None
    cevap = str(detay.get("cevap") or "").strip()
    if _is_miss_answer(cevap):
        return None
    skor = float(detay.get("skor") or 0.0)
    try:
        base_min = float(os.environ.get("RUZGAR_TEK_BEYIN_MIN_SCORE", "0.58"))
    except ValueError:
        base_min = 0.58
    if looks_like_personal_memory_query(msg):
        base_min = min(base_min, 0.55)
    if skor < base_min:
        return None
    return {
        "cevap": cevap,
        "soru": str(detay.get("soru") or "").strip(),
        "eslesme": str(detay.get("eslesme") or "fuzzy"),
        "skor": skor,
    }


def personal_hafiza_blocks_bilgi_path(message: str) -> bool:
    """Bilgi/cloud/web hızlı yollarını kapat — kişisel kayıt var."""
    if not tek_beyin_enabled():
        return False
    target = resolve_memory_query_message(message)
    hint = lookup_personal_hafiza_hint(target)
    if not hint:
        return False
    try:
        from ilim_assistant.ruzgar_tek_beyin_dogrulama import should_skip_bilgi_for_weak_hafiza

        if should_skip_bilgi_for_weak_hafiza(message, hint):
            return False
    except Exception:
        pass
    return True


def should_use_personal_hafiza_first(
    message: str,
    client_history: list | None = None,
) -> bool:
    if not tek_beyin_enabled():
        return False
    target = resolve_memory_query_message(message, client_history)
    if lookup_personal_hafiza_hint(target):
        return True
    if looks_like_personal_memory_query(target):
        return lookup_personal_hafiza_hint(target) is not None
    return False


def iter_tek_beyin_hafiza_reply(
    message: str,
    history: list | None,
    *,
    mode_norm: str = "genel",
    conversation_context: str | None = None,
    session_id: str | None = None,
) -> Iterator[str] | None:
    """Kişisel hafıza → doğal sentez (LLM yalnızca anlatım; bilgi kaynaktan)."""
    if not tek_beyin_enabled():
        return None
    target = resolve_memory_query_message(message or "", history)
    hint = lookup_personal_hafiza_hint(target)
    if not hint:
        if not looks_like_personal_memory_query(target):
            return None
        return None
    try:
        from ilim_assistant.hafiza_dogal_sentez import iter_hafiza_dogal_reply
        from ilim_assistant.ruzgar_tek_beyin_baglam import build_tek_beyin_baglam_addon

        baglam = build_tek_beyin_baglam_addon(
            target,
            history,
            conversation_context=conversation_context,
            session_id=session_id,
        )
        try:
            from ilim_assistant.ruzgar_tek_beyin_tek_ses import build_tek_beyin_voice_system_addon

            voice = build_tek_beyin_voice_system_addon("hafiza")
        except Exception:
            voice = ""
        ctx = ((baglam or "") + (voice or "")).strip() or None

        return iter_hafiza_dogal_reply(
            target,
            history or [],
            mode_norm=mode_norm,
            hint=hint,
            context_addon=ctx,
        )
    except Exception:
        return None


def tek_beyin_plan_override(message: str) -> dict[str, Any] | None:
    """plan_question için hafıza önceliği meta."""
    if not tek_beyin_enabled():
        return None
    target = resolve_memory_query_message(message)
    hint = lookup_personal_hafiza_hint(target)
    if not hint and not looks_like_personal_memory_query(target):
        return None
    if not hint:
        return None
    try:
        from ilim_assistant.ruzgar_tek_beyin_dogrulama import should_skip_bilgi_for_weak_hafiza

        if should_skip_bilgi_for_weak_hafiza(message, hint):
            return None
    except Exception:
        pass
    return {
        "primary": "hafiza",
        "use_ilim_rag": False,
        "prefer_web": False,
        "prefer_archive": False,
        "tek_beyin": True,
        "hafiza_hint": hint,
    }


# --- Faz B: dost sohbet ---

_FRIEND_MOOD = re.compile(
    r"(?:can[ıi]m\s+s[ıi]k[ıi]ld[ıi]|s[ıi]k[ıi]ld[ıi]m|"
    r"moralim\s+bozuk|keyfim\s+yok|"
    r"üzgünüm|uzgunum|mutsuzum|"
    r"yaln[ıi]z[ıi]m|"
    r"dertle[şs]|"
    r"konu[şs]mak\s+istiyorum|"
    r"sohbet\s+etmek\s+istiyorum|"
    r"arkada[şs]\s+gibi|dost\s+gibi|"
    r"can\s+s[ıi]k[ıi]nt[ıi]s[ıi]|"
    r"s[ıi]k[ıi]c[ıi]\s+bir\s+gün)",
    re.I,
)


def dost_sohbet_enabled() -> bool:
    if not tek_beyin_enabled():
        return False
    return os.environ.get("RUZGAR_TEK_BEYIN_DOST", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def looks_like_friend_mood_chat(message: str) -> bool:
    """Can sıkıntısı, dertleşme, yakın muhabbet — bilgi/RAG değil."""
    raw = (message or "").strip()
    if not raw or len(raw) > 600:
        return False
    blob = _norm_blob(raw)
    if _FRIEND_MOOD.search(blob):
        return True
    cues = (
        "canım sıkıldı",
        "canim sikildi",
        "sıkıldım",
        "sikildim",
        "moralim bozuk",
        "keyfim yok",
        "dertleşelim",
        "dertleşmek",
        "konuşalım mı",
        "konusalim mi",
        "sohbet edelim mi",
        "yanımda ol",
        "yanimda ol",
        "dinler misin",
        "biraz konuş",
        "biraz konus",
        "seninle sohbet",
        "seninle konus",
    )
    return any(c in blob for c in cues)


def should_use_dost_sohbet_first(
    message: str,
    client_history: list | None = None,
    *,
    mode_norm: str = "genel",
) -> bool:
    """Kişisel hafıza değil — dost/sohbet modu (Faz B + D devam)."""
    if not dost_sohbet_enabled():
        return False
    if should_use_personal_hafiza_first(message, client_history):
        return False
    raw = (message or "").strip()
    if not raw:
        return False
    if mode_norm not in ("genel", "uretim", "gelisim"):
        return False
    if personal_hafiza_blocks_bilgi_path(raw):
        return False
    try:
        from ilim_assistant.ruzgar_tek_beyin_oturum import looks_like_mood_continuation

        if looks_like_mood_continuation(raw, client_history):
            return True
    except Exception:
        pass
    if looks_like_friend_mood_chat(raw):
        return True
    try:
        from ilim_assistant.ana_motor_plan import looks_like_casual_social_chat

        if looks_like_casual_social_chat(raw):
            return True
    except Exception:
        pass
    try:
        from ilim_assistant.ruzgar_dogal_sohbet_faz91 import (
            dogal_sohbet_enabled,
            is_natural_conversation_turn,
        )

        if dogal_sohbet_enabled():
            return is_natural_conversation_turn(
                raw,
                mode_norm,
                None,
                history=client_history,
            )
    except Exception:
        pass
    return False


def iter_tek_beyin_dost_reply(
    message: str,
    history: list | None,
    *,
    mode_norm: str = "genel",
    voice_turn: bool = False,
    conversation_context: str | None = None,
    session_id: str | None = None,
) -> Iterator[str] | None:
    """Dost sohbet — Groq/Ollama doğal yanıt (web/RAG yok)."""
    if not should_use_dost_sohbet_first(message, history, mode_norm=mode_norm):
        return None
    try:
        from ilim_assistant.ana_motor_casual import iter_casual_fast_reply
        from ilim_assistant.ruzgar_tek_beyin_baglam import build_tek_beyin_baglam_addon
        from ilim_assistant.ruzgar_tek_beyin_oturum import (
            analyze_mood_thread,
            build_mood_thread_system_addon,
            build_voice_turn_addon,
            dost_max_tokens,
            dost_prior_depth,
            enrich_dost_history,
            looks_like_mood_resume,
            tek_beyin_oturum_enabled,
        )

        hist = history or []
        mood_thread = None
        mood_active = False
        resuming = False
        if tek_beyin_oturum_enabled():
            hist = enrich_dost_history(hist, session_id=session_id)
            mood_thread = analyze_mood_thread(hist)
            resuming = looks_like_mood_resume(message or "", hist)
            mood_active = bool(mood_thread.active) or (
                resuming and bool(mood_thread.paused)
            )
        addon = build_mood_thread_system_addon(mood_thread, resuming=resuming)
        addon += build_tek_beyin_baglam_addon(
            message or "",
            hist,
            conversation_context=conversation_context,
            session_id=session_id,
        )
        if voice_turn:
            addon += build_voice_turn_addon()
        try:
            from ilim_assistant.ruzgar_tek_beyin_tek_ses import build_tek_beyin_voice_system_addon

            addon += build_tek_beyin_voice_system_addon("dost")
        except Exception:
            pass
        gen = iter_casual_fast_reply(
            message or "",
            hist,
            mode_norm=mode_norm,
            system_addon=addon or None,
            prior_depth_override=dost_prior_depth(
                mood_active=mood_active,
                voice_turn=voice_turn,
            ),
            max_tokens_override=dost_max_tokens(
                mood_active=mood_active,
                voice_turn=voice_turn,
            ),
        )
        return gen
    except Exception:
        return None


def classify_tek_beyin_turn(
    message: str,
    client_history: list | None = None,
    *,
    mode_norm: str = "genel",
) -> str:
    """dost | hafiza | default"""
    if should_use_personal_hafiza_first(message, client_history):
        return "hafiza"
    if should_use_dost_sohbet_first(message, client_history, mode_norm=mode_norm):
        return "dost"
    return "default"


def tek_beyin_dost_plan_override(message: str) -> dict[str, Any] | None:
    if not dost_sohbet_enabled():
        return None
    if not should_use_dost_sohbet_first(message, None, mode_norm="genel"):
        return None
    return {
        "primary": "gundelik",
        "use_ilim_rag": False,
        "prefer_web": False,
        "prefer_archive": False,
        "tek_beyin": True,
        "tek_beyin_dost": True,
    }
