# Created by Ümit & Gökçenur
"""Tek beyin — kişisel hafıza önceliği, soru tipi, doğal yanıt yönlendirme."""

from __future__ import annotations

import os
import re
import unicodedata
from typing import Any, Iterator, Optional

TEK_BEYIN_VERSION = "tek-beyin-v1-2026-06-12"

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
    return lookup_personal_hafiza_hint(target) is not None


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

        return iter_hafiza_dogal_reply(
            target,
            history or [],
            mode_norm=mode_norm,
            hint=hint,
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
    return {
        "primary": "hafiza",
        "use_ilim_rag": False,
        "prefer_web": False,
        "prefer_archive": False,
        "tek_beyin": True,
        "hafiza_hint": hint,
    }
