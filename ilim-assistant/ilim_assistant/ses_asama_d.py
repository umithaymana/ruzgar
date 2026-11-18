# Created by Ümit & Gökçenur
"""
Aşama D — Edge TTS akıcılık: erken parça, az sessizlik, retry, TR doğal ses.

A/B barge + C text_ready→first_audio (<~886–1000 ms) korunur.
Yeni motor yok; yalnız TTS pipeline iyileştirmesi.
"""

from __future__ import annotations

import os
import re
from typing import Any

ASAMA_D_VERSION = "ses-asama-d-v1-2026-11-18"
# C ölçümü ~886 ms; D bunu korur veya iyileştirir
TTS_KEEP_MS = 886.0
TTS_TARGET_MS = 1000.0

# Erken seslendirme — cümle/noktalama sınırında; kelime ortası YASAK
_FIRST_SOFT = 96
_FIRST_HARD = 160
_MERGE_SOFT = 280
_MERGE_HARD = 420


def asama_d_enabled() -> bool:
    return os.environ.get("RUZGAR_TTS_ASAMA_D", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def lean_silence_factor() -> float:
    """Cümle arası ekstra sessizliği kısalt (prosody)."""
    raw = os.environ.get("RUZGAR_TTS_D_LEAN", "0.55").strip() or "0.55"
    try:
        return max(0.35, min(1.0, float(raw)))
    except ValueError:
        return 0.55


def default_voice() -> str:
    return (
        os.environ.get("RUZGAR_TTS_VOICE", "tr-TR-AhmetNeural").strip()
        or "tr-TR-AhmetNeural"
    )


def default_rate() -> str:
    """Minimal rate — ağır SSML yok; hafif hızlanma ilk sesi öne alır."""
    return os.environ.get("RUZGAR_TTS_V3_RATE", "+3%").strip() or "+3%"


def asama_d_contract() -> dict[str, Any]:
    return {
        "version": ASAMA_D_VERSION,
        "tts_keep_ms": TTS_KEEP_MS,
        "tts_target_ms": TTS_TARGET_MS,
        "voice": default_voice(),
        "rate": default_rate(),
        "lean_silence": lean_silence_factor(),
        "chunk": {
            "first_soft": _FIRST_SOFT,
            "first_hard": _FIRST_HARD,
            "merge_soft": _MERGE_SOFT,
            "merge_hard": _MERGE_HARD,
            "no_mid_word": True,
            "keep_punctuation": True,
        },
        "asama_a_b_c_kept": True,
        "barge_settle_ms": 40,
    }


_CUMLE_RE = re.compile(r"^([\s\S]+?)([.!?…؟])(\s+|$)")
_SAFE_BREAK = ("。", ". ", "! ", "? ", "… ", "; ", ": ", ", ", " — ", " - ")


def _safe_cut(text: str, limit: int, *, min_keep: int = 24) -> tuple[str, str]:
    """limit civarında kelime/noktalama sınırında kes; yarım kelime yok."""
    t = (text or "").strip()
    if not t:
        return "", ""
    if len(t) <= limit:
        return t, ""
    window = t[: limit + 1]
    best = -1
    best_sep_len = 1
    for sep in _SAFE_BREAK:
        i = window.rfind(sep)
        if i >= min_keep and i > best:
            best = i
            best_sep_len = len(sep)
    if best >= min_keep:
        head = t[: best + best_sep_len].strip()
        rest = t[best + best_sep_len :].strip()
        return head, rest
    sp = window.rfind(" ")
    if sp >= min_keep:
        return t[:sp].strip(), t[sp + 1 :].strip()
    # Son çare: soft limit'e kadar ama boşluk yoksa bütünü ver (kelimeyi kesme)
    return t, ""


def split_speak_chunks(
    text: str,
    *,
    first_soft: int | None = None,
    first_hard: int | None = None,
    merge_hard: int | None = None,
) -> list[str]:
    """
    Metni erken seslendirilebilir parçalara böl.
    İlk parça kısa (erken TTS); devam doğal cümle/noktalama sınırında.
    """
    t = re.sub(r"\s+", " ", (text or "").strip())
    if len(t) < 2:
        return []
    fs = first_soft if first_soft is not None else _FIRST_SOFT
    fh = first_hard if first_hard is not None else _FIRST_HARD
    mh = merge_hard if merge_hard is not None else _MERGE_HARD

    chunks: list[str] = []
    rest = t
    first = True
    while rest:
        if first:
            m = _CUMLE_RE.match(rest)
            if m and len(m.group(1) + m.group(2)) <= fh + 40:
                head = (m.group(1) + m.group(2)).strip()
                if len(head) >= 18:
                    chunks.append(head)
                    rest = rest[m.end() :].strip()
                    first = False
                    continue
            head, rest = _safe_cut(rest, fs if len(rest) > fs else fh, min_keep=18)
            if head:
                chunks.append(head)
            first = False
            continue
        if len(rest) <= mh:
            chunks.append(rest)
            break
        head, rest2 = _safe_cut(rest, mh, min_keep=40)
        if not head:
            chunks.append(rest)
            break
        chunks.append(head)
        rest = rest2
    return [c for c in chunks if len(c) >= 2]


def classify_edge_error(exc: BaseException | str | None) -> dict[str, Any]:
    raw = str(exc or "")
    name = type(exc).__name__ if isinstance(exc, BaseException) else ""
    blob = f"{name}:{raw}".lower()
    kind = "unknown"
    user = "Ses sentezi başarısız. Biraz sonra tekrar dene."
    retryable = True
    if "noaudio" in blob or "no_audio" in blob or "empty" in blob:
        kind = "no_audio"
        user = "Edge TTS ses döndürmedi (NoAudio). Yeniden denendi; hâlâ boşsa ağ/Edge kontrol et."
    elif "timeout" in blob or "timed out" in blob:
        kind = "timeout"
        user = "Edge TTS zaman aşımı. Ağ yavaş veya Edge meşgul — tekrar dene."
    elif "connect" in blob or "network" in blob or "dns" in blob or "ssl" in blob:
        kind = "network"
        user = "Edge TTS ağına ulaşılamadı. İnternet / DNS kontrol et."
    elif "403" in blob or "401" in blob or "429" in blob:
        kind = "rate_limit"
        user = "Edge TTS geçici olarak reddetti (limit). Kısa bekle, tekrar dene."
    elif "cancel" in blob or "abort" in blob:
        kind = "cancelled"
        user = "Ses isteği iptal edildi."
        retryable = False
    return {
        "kind": kind,
        "retryable": retryable,
        "user_message": user,
        "detail": raw[:180],
    }


def apply_lean_pause_ms(ms: int) -> int:
    if not asama_d_enabled() or ms <= 0:
        return ms
    return max(0, int(round(ms * lean_silence_factor())))
