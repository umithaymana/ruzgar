# Created by Ümit & Gökçenur
"""Tek beyin Faz C — kişisel hafıza cevabı doğrulama ve çelişki koruması."""

from __future__ import annotations

import os
import re
import unicodedata
from typing import Any

TEK_BEYIN_GUARD_VERSION = "tek-beyin-guard-v1-2026-06-12"

_CONTRADICTION_CUES = (
    "şair",
    "sair",
    "haymana ali",
    "yazar",
    "roman",
    "şiir",
    "siir",
    "biyografi",
    "ansiklopedi",
    "wikipedia",
    "uydur",
)
_STOP = frozenset(
    {
        "mit",
        "gökçenur",
        "gokcenur",
        "ümit",
        "umit",
        "kimdir",
        "kimdi",
        "olan",
        "için",
        "icin",
        "bir",
        "ile",
        "ve",
        "the",
    }
)


def tek_beyin_guard_enabled() -> bool:
    if os.environ.get("RUZGAR_TEK_BEYIN", "1").strip().lower() in ("0", "false", "no"):
        return False
    return os.environ.get("RUZGAR_TEK_BEYIN_GUARD", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _norm(text: str) -> str:
    t = unicodedata.normalize("NFKC", (text or "").strip().lower())
    return re.sub(r"\s+", " ", t)


def _key_tokens(text: str) -> set[str]:
    out: set[str] = set()
    for w in re.split(r"[^\wçğıöşüÇĞİÖŞÜ]+", (text or ""), flags=re.UNICODE):
        w = w.strip().lower()
        if len(w) >= 4 and w not in _STOP:
            out.add(w)
        if len(w) >= 6:
            out.add(w[:5])
    return out


def _min_overlap() -> float:
    try:
        return max(0.12, min(float(os.environ.get("RUZGAR_TEK_BEYIN_GUARD_MIN_OVERLAP", "0.22")), 0.6))
    except ValueError:
        return 0.22


def assess_hafiza_reply_fidelity(
    hint: dict[str, Any],
    reply: str,
    *,
    message: str = "",
) -> tuple[bool, float, str]:
    """
    Yanıt hafıza kaydıyla uyumlu mu?
    Dönüş: (ok, overlap_skoru, neden)
    """
    ham = str(hint.get("cevap") or "").strip()
    out = (reply or "").strip()
    if not ham or not out:
        return True, 1.0, ""
    ham_t = _key_tokens(ham)
    if not ham_t:
        return True, 1.0, ""
    rep_t = _key_tokens(out)
    overlap = len(ham_t & rep_t) / max(1, len(ham_t))
    rep_low = _norm(out)
    ham_low = _norm(ham)
    skor = float(hint.get("skor") or 0.0)

    for bad in _CONTRADICTION_CUES:
        if bad in rep_low and bad not in ham_low:
            if skor >= 0.75:
                return False, overlap, f"contradiction:{bad}"

    if overlap >= _min_overlap():
        return True, overlap, ""

    if skor >= 0.9 and overlap < _min_overlap():
        return False, overlap, "low_overlap_strong_hint"

    if skor >= 0.75 and overlap < _min_overlap() * 0.6:
        return False, overlap, "low_overlap"

    return True, overlap, ""


def natural_fallback_from_hint(message: str, hint: dict[str, Any]) -> str:
    """LLM uydurduysa — kayıtlı metni sıcak ama doğrudan anlat."""
    ham = str(hint.get("cevap") or "").strip()
    if not ham:
        return ""
    if ham.lower().startswith(("ümit abi", "umit abi", "evet", "hayır", "hayir")):
        return ham
    first = ham[0].lower() + ham[1:] if len(ham) > 1 else ham
    return f"Ümit abi, {first}"


def apply_personal_hafiza_guard(
    message: str,
    reply: str,
    hint: dict[str, Any] | None,
) -> str:
    """Kişisel hafıza turunda yanıtı doğrula; gerekirse kayıtlı cevaba dön."""
    if not tek_beyin_guard_enabled() or not hint:
        return (reply or "").strip()
    body = (reply or "").strip()
    if not body:
        return natural_fallback_from_hint(message, hint)
    ok, _ov, reason = assess_hafiza_reply_fidelity(hint, body, message=message)
    if ok:
        return body
    fb = natural_fallback_from_hint(message, hint)
    if fb:
        return fb
    return body


def guard_or_lookup_reply(
    message: str,
    reply: str,
    *,
    client_history: list | None = None,
) -> str:
    """Tam boru hattı sonunda — kişisel kayıt varsa yanıtı denetle."""
    if not tek_beyin_guard_enabled():
        return (reply or "").strip()
    try:
        from ilim_assistant.ruzgar_tek_beyin import (
            lookup_personal_hafiza_hint,
            resolve_memory_query_message,
        )

        target = resolve_memory_query_message(message, client_history)
        hint = lookup_personal_hafiza_hint(target)
    except Exception:
        hint = None
    if not hint:
        return (reply or "").strip()
    return apply_personal_hafiza_guard(target, reply, hint)


def should_skip_bilgi_for_weak_hafiza(message: str, hint: dict[str, Any] | None) -> bool:
    """Ansiklopedik soruda zayıf fuzzy eşleşmeyle hafızaya düşme."""
    if not hint:
        return False
    try:
        from ilim_assistant.ana_motor_plan import looks_like_encyclopedic_fact_question

        if not looks_like_encyclopedic_fact_question(message):
            return False
    except Exception:
        return False
    skor = float(hint.get("skor") or 0.0)
    eslesme = str(hint.get("eslesme") or "")
    return skor < 0.98 and eslesme != "tam"
