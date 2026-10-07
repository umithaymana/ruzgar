# -*- coding: utf-8 -*-
"""Anlık kütüphane / arşiv kapısı — lookup hızlı kalsın, sohbet LLM'e gitsin.

Kapat (eski davranış): RUZGAR_ANLIK_NIYET_GATE=0
"""
from __future__ import annotations

import os
import re
import unicodedata
from typing import Callable, Optional

_SYNTH_RE = re.compile(
    r"(?:"
    r"\banlat(?:ır\s*mısın|irmisin|sana)?\b|"
    r"\baçıkla(?:r\s*mısın|rmisin)?\b|\bacikla(?:r\s*misin|rmisin)?\b|"
    r"daha\s+açık|daha\s+acik|daha\s+uzun|detayl[ıi]|"
    r"kendi\s+cümle|kendi\s+cumle|"
    r"\bsohbet\b|\bkonuş(?:alım|alim)?\b|\bkonus(?:alim)?\b|"
    r"devam\s+et|anlamad[ıi]m|örnekle|ornekle|"
    r"doğal\s+konuş|dogal\s+konus|arkada[sş]\s+gibi|"
    r"panelde\s+aç|panelde\s+ac"
    r")",
    re.I,
)

_STRICT_LOOKUP_RE = re.compile(
    r"(?:"
    r"\b(?:buhari|buhârî|muslim|müslim|tirmizi|ebu\s*davud|nesai|ibn\s*mace)\b"
    r".{0,20}\b\d{1,5}\b|"
    r"\b(?:hadis|ayet)\s*(?:no|numara|#)?\s*\d{1,5}\b|"
    r"^\s*[\w'’çğıöşüâîû\.\-]{2,40}\s+(?:nedir|ne\s+demek)\s*[?.!]?\s*$"
    r")",
    re.I,
)

_LIBRARY_TRYERS: tuple[tuple[str, str, str], ...] = (
    ("ilim_assistant.ruzgar_siyer_kutuphane", "try_siyer_reply", "Siyer"),
    ("ilim_assistant.ruzgar_usul_fikh_kutuphane", "try_usul_fikh_reply", "Usûl"),
    ("ilim_assistant.ruzgar_fikh_kutuphane", "try_fikh_reply", "Fıkıh"),
    ("ilim_assistant.ruzgar_hadis_kutuphane", "try_hadis_reply", "Hadis"),
    ("ilim_assistant.ruzgar_akaid_kutuphane", "try_akaid_reply", "Akaid"),
    ("ilim_assistant.ruzgar_felsefe_kutuphane", "try_felsefe_reply", "Felsefe"),
    ("ilim_assistant.ruzgar_psikoloji_kutuphane", "try_psikoloji_reply", "Psikoloji"),
    ("ilim_assistant.ruzgar_edebiyat_kutuphane", "try_edebiyat_reply", "Edebiyat"),
    ("ilim_assistant.ruzgar_bilim_kutuphane", "try_bilim_reply", "Bilim"),
    ("ilim_assistant.ruzgar_cografya_kutuphane", "try_cografya_reply", "Coğrafya"),
    ("ilim_assistant.ruzgar_teknoloji_kutuphane", "try_teknoloji_reply", "Teknoloji"),
)


def anlik_niyet_gate_enabled() -> bool:
    return os.environ.get("RUZGAR_ANLIK_NIYET_GATE", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _fold(s: str) -> str:
    t = unicodedata.normalize("NFKD", s or "")
    t = "".join(c for c in t if not unicodedata.combining(c))
    return t.lower().strip()


def is_strict_library_lookup(message: str) -> bool:
    raw = (message or "").strip()
    if not raw or len(raw) > 120:
        return False
    return bool(_STRICT_LOOKUP_RE.search(raw))


def should_defer_library_instant(message: str) -> bool:
    if not anlik_niyet_gate_enabled():
        return False
    raw = (message or "").strip()
    if not raw:
        return False
    if is_strict_library_lookup(raw):
        return False
    if _SYNTH_RE.search(raw) or _SYNTH_RE.search(_fold(raw)):
        return True
    return False


def should_defer_archive_fast(message: str) -> bool:
    return should_defer_library_instant(message)


def _call_try(mod_path: str, fn_name: str, message: str) -> Optional[str]:
    try:
        import importlib

        mod = importlib.import_module(mod_path)
        fn: Callable[[str], Optional[str]] = getattr(mod, fn_name)
        out = fn(message)
        return (out or "").strip() or None
    except Exception:
        return None


def library_instant_would_match(message: str) -> bool:
    raw = (message or "").strip()
    if not raw:
        return False
    for mod_path, fn_name, _label in _LIBRARY_TRYERS:
        if _call_try(mod_path, fn_name, raw):
            return True
    return False


def collect_library_llm_context(message: str, *, max_chars: int = 2800) -> str:
    """Kütüphane eşleşmesini LLM ipucu olarak derle (kullanıcıya aynen basma)."""
    raw = (message or "").strip()
    if not raw:
        return ""
    if is_strict_library_lookup(raw) and not should_defer_library_instant(raw):
        return ""
    parts: list[str] = []
    used = 0
    for mod_path, fn_name, label in _LIBRARY_TRYERS:
        hit = _call_try(mod_path, fn_name, raw)
        if not hit:
            continue
        chunk = hit[:1200].strip()
        if not chunk:
            continue
        block = f"### {label}\n{chunk}"
        if used + len(block) > max_chars:
            break
        parts.append(block)
        used += len(block)
        if len(parts) >= 2:
            break
    if not parts:
        return ""
    return (
        "[KÜTÜPHANE İPUCU — dahili; kullanıcıya aynen okuma]\n"
        "Aşağıdaki kavram notunu kendi cümlelerinle, akıcı Türkçe ile anlat. "
        "Madde madde robot okuması yapma; kaynak dosya yolu veya «hafızamda» deme.\n\n"
        + "\n\n".join(parts)
        + "\n[/KÜTÜPHANE İPUCU]"
    )


def soft_library_synth_fallback(message: str) -> Optional[str]:
    """LLM yokken sohbet/anlat niyetinde kısa doğal köprü + kavram notu."""
    if not should_defer_library_instant(message):
        return None
    raw = (message or "").strip()
    hit = None
    for mod_path, fn_name, _label in _LIBRARY_TRYERS:
        hit = _call_try(mod_path, fn_name, raw)
        if hit:
            break
    if not hit:
        return None
    body = re.sub(r"\*+", "", hit).strip()
    if len(body) > 1600:
        body = body[:1600].rsplit(maxsplit=1)[0] + "…"
    return (
        "Ümit abi, kısaca şöyle özetleyeyim:\n\n"
        f"{body}\n\n"
        "İstersen bir yönünü daha açalım veya sohbete devam edelim."
    )
