"""
S3 — Sayı/güncel hard-gate + geniş scrub.

Kaynak yok/zayıfken LLM'e sayı üretme yolu kapanır; cevapta kaynaksız rakam scrub edilir.
"""
from __future__ import annotations

import os
import re
from typing import Any

S3_VERSION = "sohbet-sayi-hard-gate-s3-v1-2026-10-23"

_MISS = (
    "Ümit abi, bu sorunun net rakamını güvenilir kaynaktan çıkaramadım; "
    "sayı uydurmam. Resmi istatistik veya güncel kaynağa bakmak daha doğru."
)

_KAYNAK_OK = re.compile(
    r"(?i)(?:https?://|meb\.gov|tuik\.gov|tüik\.gov|y[oö]k\.gov|tcmb\.gov|"
    r"resmi\s+istatistik|open-meteo|openweathermap|bloomberg|reuters|"
    r"investing\.com|coindesk|binance|wikipedia\.org|wikidata)"
)

# Geniş scrub — okul/üni text_encoding'de; burada fx / skor / nüfus / genel istatistik
_FX_SAYISI = re.compile(
    r"(?i)(?:dolar|usd|euro|eur|bitcoin|btc).{0,24}"
    r"(?:\d{1,3}(?:[.,]\d{2,4})?|\d{2,6})"
    r"|"
    r"(?:\d{1,3}(?:[.,]\d{2,4})?|\d{2,6}).{0,12}"
    r"(?:tl|₺).{0,16}(?:dolar|usd|euro|eur|bitcoin|btc)"
)
_SKOR = re.compile(
    r"(?i)(?:\d{1,2}\s*[-–:]\s*\d{1,2}).{0,40}(?:maç|skor|bitti|galibiyet)|"
    r"(?:maç|skor).{0,40}(?:\d{1,2}\s*[-–:]\s*\d{1,2})"
)
_NUFUS_SAYISI = re.compile(
    r"(?i)n[uü]fus[^\n.]{0,40}(?:\d{1,3}(?:[.\s]\d{3})+|\d{5,}|\d{1,3}\s*milyon)|"
    r"(?:\d{1,3}(?:[.\s]\d{3})+|\d{5,}|\d{1,3}\s*milyon)[^\n.]{0,30}n[uü]fus"
)
_ILCE_SAYISI = re.compile(
    r"(?i)(?:\d{1,3})\s*(?:adet\s+)?il[cç]e|"
    r"il[cç]e[^\n.]{0,20}(?:\d{1,3})"
)
_PADISAH = re.compile(
    r"(?i)(?:\d{2,3})\s*(?:tane\s+)?padi[sş]ah|"
    r"padi[sş]ah[^\n.]{0,24}(?:\d{2,3})"
)
_OZEL_OKUL_GEN = re.compile(
    r"(?i)(?:\d{1,3}(?:[.\s]\d{3})+|\d{4,}|\d{1,3}\s*bin).{0,20}"
    r"(?:özel|ozel)\s+okul"
)


def hard_gate_enabled() -> bool:
    return os.environ.get("RUZGAR_SAYI_HARD_GATE", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def sayi_hard_miss_reply() -> str:
    return _MISS


def sayi_hard_miss_directive() -> str:
    return (
        "\n\n[TALİMAT — SAYI/GÜNCEL HARD-GATE S3]\n"
        "Bu soru sayı veya güncel bilgi istiyor; bu turda güvenilir web/raf özeti YOK veya yetersiz. "
        "Kesin rakam, skor, kur, nüfus veya resmi istatistik UYDURMA. "
        "Kısa dürüst cevap ver: kaynağa ulaşılamadı, sayı uydurulmaz. "
        f"Örnek ton: «{_MISS}»\n"
    )


def _web_grounded(web_extra: str) -> bool:
    w = (web_extra or "").strip()
    if len(w) < 64:
        return False
    if _KAYNAK_OK.search(w):
        return True
    # PRO / uzun özet
    return len(w) >= 280


def _local_grounded(blocks: str | list | None, hits: list | None) -> bool:
    if isinstance(blocks, str) and len(blocks.strip()) >= 80:
        return True
    if isinstance(blocks, (list, tuple)) and blocks:
        joined = " ".join(str(b) for b in blocks[:6])
        if len(joined) >= 80:
            return True
    if hits:
        try:
            for h in hits[:5]:
                if isinstance(h, (list, tuple)) and len(h) >= 3:
                    if float(h[2]) >= 0.55 and len(str(h[1] if len(h) > 1 else "")) > 40:
                        return True
                elif isinstance(h, dict):
                    sc = float(h.get("score") or h.get("similarity") or 0)
                    txt = str(h.get("text") or h.get("content") or "")
                    if sc >= 0.55 and len(txt) > 40:
                        return True
        except (TypeError, ValueError):
            pass
    return False


def should_force_sayi_miss(
    message: str,
    *,
    web_extra: str = "",
    blocks: Any = None,
    hits: list | None = None,
    live_weather_ctx: str = "",
) -> bool:
    """Kaynak yoksa sayı/güncel turda hard miss."""
    if not hard_gate_enabled():
        return False
    try:
        from ilim_assistant.sohbet_source_router import classify_source_intent

        d = classify_source_intent(message)
    except Exception:
        return False
    if not (d.needs_live or d.needs_number):
        return False
    if (live_weather_ctx or "").strip() and d.tip in ("guncel_hava", "guncel"):
        return False
    web_ok = _web_grounded(web_extra)
    local_ok = _local_grounded(blocks, hits)
    if d.needs_live and not d.library_ok:
        # Yalnız canlı kaynak kabul
        return not web_ok and not (live_weather_ctx or "").strip()
    if d.needs_live and d.library_ok:
        return not (web_ok or local_ok)
    # needs_number (tarih/bilim/coğrafya): raf veya web
    return not (web_ok or local_ok)


def scrub_ungrounded_live_numbers(text: str) -> str:
    """Cevapta kaynaksız kur/skor/nüfus/ilçe scrub — okul/üni text_encoding'de."""
    if not text or not hard_gate_enabled():
        return text
    if _KAYNAK_OK.search(text):
        return text
    t = text
    changed = False
    _SCRUB_RX = (_FX_SAYISI, _SKOR, _NUFUS_SAYISI, _ILCE_SAYISI, _PADISAH, _OZEL_OKUL_GEN)
    for rx in _SCRUB_RX:
        if rx.search(t):
            changed = True
            break
    if not changed:
        return t
    # Cümle bazlı temizle — sayı cümlesini miss ile değiştir
    parts = re.split(r"(?<=[.!?])\s+", t)
    out: list[str] = []
    miss_kondu = False
    for p in parts:
        if any(rx.search(p) for rx in _SCRUB_RX):
            if not miss_kondu:
                out.append(_MISS)
                miss_kondu = True
            continue
        if p.strip():
            out.append(p.strip())
    return " ".join(out).strip() or _MISS


def apply_sayi_hard_gate_scrub(
    reply: str,
    *,
    user_message: str = "",
    web_extra: str = "",
    blocks: Any = None,
    hits: list | None = None,
) -> str:
    """finalize sonrası: sayı/güncel + kaynaksız → scrub."""
    if not hard_gate_enabled() or not (reply or "").strip():
        return reply
    try:
        from ilim_assistant.sohbet_source_router import classify_source_intent

        d = classify_source_intent(user_message)
    except Exception:
        d = None
    if d is not None and not (d.needs_live or d.needs_number):
        # Yine de genel fx/skor scrub (yanlış turda sızmasın)
        return scrub_ungrounded_live_numbers(reply) if re.search(
            r"(?i)dolar|bitcoin|maç\s+skor|n[uü]fus", reply
        ) else reply
    if d is not None and not should_force_sayi_miss(
        user_message, web_extra=web_extra, blocks=blocks, hits=hits
    ):
        # Kaynak vardı — scrub gevşek (yalnız açık uydurma kalıpları)
        if _KAYNAK_OK.search(reply) or _web_grounded(web_extra):
            return reply
    return scrub_ungrounded_live_numbers(reply)
