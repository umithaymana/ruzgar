# Created by Ümit & Gökçenur
"""Faz D / 10 — Genel moddan programlamaya otonom debug + çok dosya patch köprüsü."""

from __future__ import annotations

import os
import re
import unicodedata


def _fold(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def otonom_debug_bridge_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_MOTOR_OTONOM_DEBUG", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


_TRACE_RE = re.compile(r"traceback\s*\(most recent call last\)", re.I)
_ERROR_LINE_RE = re.compile(
    r"(AssertionError|ModuleNotFoundError|ImportError|SyntaxError|TypeError|"
    r"ValueError|AttributeError|KeyError|FileNotFoundError)",
    re.I,
)


_EXTRA_DEBUG_CUES = (
    "pytest fail",
    "pytest failed",
    "test fail",
    "tests failed",
    "testler basarisiz",
    "testler başarısız",
    "kirmizi",
    "kırmızı",
    "cok dosya",
    "çok dosya",
    "birden fazla dosya",
    "multi file",
    "multi-file",
    "patch yaz",
    "otomatik patch",
    "pytest kirmizi",
    "pytest kırmızı",
    "hata verdi duzelt",
    "hata verdi düzelt",
    "sunucu log",
    "stack trace",
)


_DELEGATE_DEBUG_CUES = (
    "otomatik debug",
    "debug dongusu",
    "debug döngüsü",
    "pytest dongusu",
    "pytest döngüsü",
    "traceback",
    "pytest",
    "patch",
    "@@write",
    "@@read",
    "hata ayikla",
    "hata ayıkla",
    "kodu duzelt",
    "kodu düzelt",
    "testi gecir",
    "testi geçir",
)


def detect_otonom_debug_intent(message: str) -> bool:
    """Otonom pytest/patch döngüsü gerektiren kod hata turu."""
    if not otonom_debug_bridge_enabled():
        return False
    try:
        from ilim_assistant.motorlar.programlama_motoru import wants_autonomous_code_debug

        if wants_autonomous_code_debug(message):
            return True
    except Exception:
        pass
    raw = message or ""
    low = _fold(raw)
    if any(c in low for c in _EXTRA_DEBUG_CUES):
        return True
    if _TRACE_RE.search(raw) or _ERROR_LINE_RE.search(raw):
        return True
    if 'file "' in low and "line " in low:
        return True
    return False


def should_enable_code_debug_loop(
    message: str,
    mode_norm: str,
    *,
    coding_mode: bool = False,
) -> bool:
    """Programlama turunda Faz 10.4 pytest döngüsünü aç."""
    if mode_norm != "programlama" and not coding_mode:
        return False
    return detect_otonom_debug_intent(message)


def should_delegate_genel_debug(message: str, mode_norm: str) -> bool:
    """Genel moddan programlamaya delege — debug/patch niyeti."""
    if not otonom_debug_bridge_enabled():
        return False
    if mode_norm not in ("genel", "gelisim", "uretim", ""):
        return False
    low = _fold(message)
    if any(c in low for c in _DELEGATE_DEBUG_CUES):
        return True
    return detect_otonom_debug_intent(message)


def build_otonom_debug_directive(message: str) -> str:
    return (
        "[Faz D — Otonom debug köprüsü — Ümit & Gökçenur]\n"
        "Bu tur **otonom hata ayıklama**: kısa plan → `@@read` / harita → "
        "gerekirse **çok dosya** `@@write` patch → `patch onayla` veya otomatik yazım → "
        "pytest/npm doğrulama döngüsü.\n"
        "Traceback varsa kök nedeni bul; yalnızca semptom yamama.\n"
        f"[Kullanıcı isteği özeti]\n{(message or '').strip()[:1200]}\n"
    )
