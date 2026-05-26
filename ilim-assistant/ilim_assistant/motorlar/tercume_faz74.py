# Created by Ümit & Gökçenur
"""
Tercüme motoru — Faz 74: ROK pilot (U5) — konuşarak yap.

Dil çifti ayrıştırma · atölye yönlendirme · altyazı/SRT ipucu.
Çeviri metni sohbette LLM ile (anlık meta komutlar hariç).
"""

from __future__ import annotations

import os
import re
import unicodedata
from typing import Any

from ilim_assistant.ruzgar_motor_kernel import (
    INTENT_CHAT,
    INTENT_COMMAND,
    INTENT_DO,
    register_classifier,
)

FAZ74_VERSION = "tercume-faz74-v1-2026-05-26"

_LANG_ALIASES: dict[str, str] = {
    "turkce": "tr",
    "türkçe": "tr",
    "turk": "tr",
    "ingilizce": "en",
    "english": "en",
    "ing": "en",
    "arapca": "ar",
    "arapça": "ar",
    "arabic": "ar",
    "almanca": "de",
    "german": "de",
    "fransizca": "fr",
    "fransızca": "fr",
    "french": "fr",
    "farsca": "fa",
    "farsça": "fa",
    "farsi": "fa",
    "rusca": "ru",
    "rusça": "ru",
    "russian": "ru",
    "otomatik": "auto",
    "auto": "auto",
}

_LANG_LABEL: dict[str, str] = {
    "auto": "Otomatik",
    "tr": "Türkçe",
    "en": "İngilizce",
    "ar": "Arapça",
    "de": "Almanca",
    "fr": "Fransızca",
    "fa": "Farsça",
    "ru": "Rusça",
}

_QUESTION_RE = re.compile(
    r"(?:\b(?:nedir|nasıl|nasil|ne\s+demek)\b|^(?:açıkla|acikla|anlat)\b)",
    re.I,
)
_LANG_LIST_RE = re.compile(
    r"(?:dil\s+listesi|tercüme\s+durum|tercume\s+durum|hangi\s+diller|"
    r"desteklenen\s+diller)",
    re.I,
)
_SUBTITLE_RE = re.compile(
    r"(?:altyazı|altyazi|srt\b|vtt\b|\.srt|\.vtt|subtitle)",
    re.I,
)
_TRANSLATE_RE = re.compile(
    r"(?:çevir|cevir|tercüme|tercume|translate|tercüme\s+et|tercume\s+et)",
    re.I,
)
_TO_LANG_RE = re.compile(
    r"(?:(\w+(?:ç|Ç|ğ|Ğ|ı|İ|ö|Ö|ş|Ş|ü|Ü)+|\w+)\s*(?:'ye|ye|e|a|ya)\s*)?çevir",
    re.I,
)
_CEIVIR_PREFIX_RE = re.compile(
    r"(?:çevir|cevir|tercüme|tercume)\s*[:：]\s*(.+)$",
    re.I | re.DOTALL,
)
_QUOTED_RE = re.compile(r"[«\"'](.+?)[»\"']", re.DOTALL)

_REGISTERED = False


def _enabled() -> bool:
    return os.environ.get("RUZGAR_TERCUME_FAZ74", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz74_enabled() -> bool:
    return _enabled()


def _ascii_fold(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def ensure_kernel_registered() -> None:
    global _REGISTERED
    if _REGISTERED:
        return
    register_classifier("tercume", classify_tercume_intent)
    _REGISTERED = True


def lang_label(code: str) -> str:
    return _LANG_LABEL.get((code or "").strip().lower(), code or "?")


def resolve_lang_token(token: str) -> str | None:
    t = _ascii_fold((token or "").strip())
    if not t:
        return None
    if t in _LANG_LABEL:
        return t
    return _LANG_ALIASES.get(t)


def parse_language_pair(message: str) -> tuple[str, str]:
    """(kaynak, hedef) kodları — varsayılan auto→en veya tr↔en tahmini."""
    raw = (message or "").strip()
    low = _ascii_fold(raw)
    src, tgt = "auto", "en"

    for code, label in _LANG_LABEL.items():
        if code == "auto":
            continue
        lab = _ascii_fold(label)
        if f"{lab}den" in low or f"{lab}dan" in low:
            src = code
        if f"{lab}ye" in low or f"{lab}e " in low or f"to {code}" in low:
            tgt = code

    m = re.search(
        r"(\w+)\s*(?:->|→|den|dan)\s*(\w+)",
        low,
    )
    if m:
        a = resolve_lang_token(m.group(1))
        b = resolve_lang_token(m.group(2))
        if a:
            src = a
        if b:
            tgt = b

    if "turkce" in low or "türkçe" in raw.lower():
        if "ingilizce" in low or "english" in low:
            if re.search(r"ingilizce\s*(?:ye|e)", low):
                src, tgt = "tr", "en"
            else:
                src, tgt = "en", "tr"
        elif tgt == "tr" and src == "auto":
            src = "en"

    if src == tgt and src != "auto":
        tgt = "en" if src == "tr" else "tr"

    return src, tgt


def extract_translate_text(message: str) -> str:
    raw = (message or "").strip()
    m = _CEIVIR_PREFIX_RE.search(raw)
    if m:
        return m.group(1).strip()
    q = _QUOTED_RE.search(raw)
    if q:
        return q.group(1).strip()
    if _TRANSLATE_RE.search(raw):
        for sep in ("—", "–", ":", "："):
            if sep in raw:
                tail = raw.split(sep, 1)[-1].strip()
                if len(tail) > 6 and not _TRANSLATE_RE.search(tail[:20]):
                    return tail
    return ""


def script_hint(text: str) -> str:
    body = text or ""
    if re.search(r"[\u0600-\u06FF]", body):
        return "Arapça/Farsça hat (RTL)"
    if re.search(r"[\u0400-\u04FF]", body):
        return "Kiril hat"
    if re.search(r"[a-zA-Z]", body) and not re.search(r"[çğıöşüÇĞİÖŞÜ]", body):
        return "Latince hat (TR dışı olabilir)"
    if re.search(r"[çğıöşüÇĞİÖŞÜ]", body, re.I):
        return "Türkçe hat"
    return "Belirsiz"


def classify_tercume_intent(
    message: str,
    *,
    mode_norm: str = "tercume",
    **kwargs: Any,
) -> dict[str, Any]:
    _ = kwargs
    if mode_norm != "tercume":
        return {"intent": INTENT_CHAT, "reason": "wrong_mode"}
    raw = (message or "").strip()
    if not raw:
        return {"intent": INTENT_CHAT, "reason": "empty"}
    low = _ascii_fold(raw)

    if _LANG_LIST_RE.search(low):
        return {"intent": INTENT_COMMAND, "reason": "lang_list"}
    if _SUBTITLE_RE.search(low) and not _TRANSLATE_RE.search(low):
        return {"intent": INTENT_COMMAND, "reason": "subtitle_help"}

    body = extract_translate_text(raw)
    if _TRANSLATE_RE.search(raw) or body:
        src, tgt = parse_language_pair(raw)
        if body or len(raw) > 40:
            return {
                "intent": INTENT_DO,
                "reason": "translate_text",
                "text": body or raw,
                "src": src,
                "tgt": tgt,
                "defer_llm": True,
            }
        return {
            "intent": INTENT_DO,
            "reason": "translate_no_text",
            "src": src,
            "tgt": tgt,
        }

    if _QUESTION_RE.search(raw):
        return {"intent": INTENT_CHAT, "reason": "question"}

    return {"intent": INTENT_CHAT, "reason": "conversation"}


def format_lang_list() -> str:
    lines = [
        "Ümit abi, **tercüme motoru dilleri:**",
        "",
        "Kaynak (otomatik dahil): " + ", ".join(f"**{v}** (`{k}`)" for k, v in _LANG_LABEL.items()),
        "",
        "Doğal örnekler:",
        "· `şunu ingilizceye çevir: …`",
        "· `arapçadan türkçeye çevir: …`",
        "· Sağ panel **Çevir** (uzun metin)",
        "",
        "Altyazı: Video motoru → SRT/VTT → buraya veya `altyazı çevir`",
        f"({FAZ74_VERSION})",
    ]
    return "\n".join(lines)


def format_subtitle_help() -> str:
    return (
        "Ümit abi, **altyazı / SRT** hattı:\n\n"
        "1. Video motorunda videoyu indirin veya dosya seçin.\n"
        "2. Altyazı dosyasını (SRT/VTT) videoya gömün veya metni çıkarın.\n"
        "3. Metni tercüme atölyesine yapıştırıp **Çevir** veya sohbette "
        "`altyazıyı türkçeye çevir:` + metin yazın.\n\n"
        f"({FAZ74_VERSION})"
    )


def format_translate_hint(src: str, tgt: str) -> str:
    return (
        f"Ümit abi, hedef dil **{lang_label(tgt)}** — kaynak **{lang_label(src)}**.\n"
        "Çevrilecek metni yazın veya yapıştırın.\n"
        "Örnek: `ingilizceye çevir: Merhaba dünya`\n"
        f"({FAZ74_VERSION})"
    )


def format_atolye_guidance(text: str, src: str, tgt: str) -> str:
    body = (text or "").strip()
    n = len(body)
    if n > 3500:
        return (
            f"Ümit abi, metin **{n}** karakter — sohbet zaman aşımına girebilir.\n"
            "Sağ panelde kaynak kutusuna yapıştırıp **Çevir** düğmesini kullanın.\n"
            f"Dil çifti: {lang_label(src)} → {lang_label(tgt)}\n"
            f"({FAZ74_VERSION})"
        )
    return (
        f"Ümit abi, çeviri **{lang_label(src)} → {lang_label(tgt)}** için metin hazır "
        f"({n} karakter, hat: {script_hint(body)}).\n\n"
        "Tam çeviri bu turda LLM ile üretilir; kısa metin doğrudan, uzun metin panelden.\n"
        f"({FAZ74_VERSION})"
    )


def build_translate_context_note(message: str) -> str:
    """build_motor_context için dil çifti notu."""
    src, tgt = parse_language_pair(message)
    body = extract_translate_text(message)
    extra = f"[TERCUME ROK] Dil: {lang_label(src)} → {lang_label(tgt)}."
    if body:
        extra += f" Metin ({len(body)} kr)."
    return extra


def maybe_instant_faz74(message: str) -> str | None:
    if not _enabled():
        return None
    ensure_kernel_registered()
    raw = (message or "").strip()
    if not raw:
        return None

    intent = classify_tercume_intent(raw, mode_norm="tercume")
    reason = intent.get("reason") or ""

    if intent.get("intent") == INTENT_COMMAND:
        if reason == "lang_list":
            return format_lang_list()
        if reason == "subtitle_help":
            return format_subtitle_help()

    if intent.get("intent") == INTENT_DO:
        if reason == "translate_no_text":
            return format_translate_hint(
                str(intent.get("src") or "auto"),
                str(intent.get("tgt") or "en"),
            )
        if reason == "translate_text" and intent.get("defer_llm"):
            body = str(intent.get("text") or "")
            if len(body) > 3500:
                return format_atolye_guidance(
                    body,
                    str(intent.get("src") or "auto"),
                    str(intent.get("tgt") or "en"),
                )
            return None

    return None


def augment_tercume_context(base: str, message: str = "") -> str:
    if not _enabled():
        return base
    ensure_kernel_registered()
    note = build_translate_context_note(message) if message else ""
    extra = (
        f"\n[TERCÜME ROK — Faz 74]\n"
        f"{note}\n"
        "Konuşarak: «ingilizceye çevir: …» · «dil listesi» · «altyazı çevir»\n"
        "Kapat: RUZGAR_TERCUME_FAZ74=0\n"
    )
    return (base or "").rstrip() + extra


def enrich_health_build(build: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(build or {})
    out["tercume_faz74"] = faz74_enabled()
    return out


def faz74_directive() -> str:
    return (
        "[TERCÜME — Konuşarak yap Faz 74]\n"
        "Örnek: `fransızcadan türkçeye çevir: …` · `dil listesi`\n"
        "Kapat: RUZGAR_TERCUME_FAZ74=0\n"
    )


ensure_kernel_registered()
