# Created by Ümit & Gökçenur
"""Canlı döviz kuru — DuckDuckGo snippet'ten anlık USD/EUR/altın okuma."""

from __future__ import annotations

import os
import re
from typing import Optional

from ilim_assistant.persona import OWNER_ADDRESS

_FX_WORDS = (
    "dolar",
    "euro",
    "sterlin",
    "altın",
    "altin",
    "usd",
    "eur",
    "gbp",
    "gram altın",
    "gram altin",
)

_RATE_RE = re.compile(
    r"(?P<num>\d{1,3}(?:[.,]\d{1,4})?)\s*(?:tl|₺|try|türk\s*liras[ıi])",
    re.I,
)
_USD_BODY_RE = re.compile(
    r"(?:1\s*)?(?:amerikan\s*)?dolar[ıi]?\s*(?:\(|USD\))?[^.]{0,40}?"
    r"(?P<num>\d{1,3}(?:[.,]\d{1,4})?)\s*(?:tl|₺)",
    re.I,
)
_EUR_BODY_RE = re.compile(
    r"(?:1\s*)?euro\s*(?:\(|EUR\))?[^.]{0,40}?"
    r"(?P<num>\d{1,3}(?:[.,]\d{1,4})?)\s*(?:tl|₺)",
    re.I,
)


def fx_live_enabled() -> bool:
    return os.environ.get("RUZGAR_FX_LIVE", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def looks_like_fx_rate_question(message: str) -> bool:
    low = (message or "").lower()
    if not any(w in low for w in _FX_WORDS):
        return False
    return bool(
        re.search(
            r"(?:kaç|kac|ne\s*kadar|fiyat|kur|tl|₺|bugün|bugun|güncel|guncel|şu\s*an|su\s*an)",
            low,
        )
    )


def _pick_pair(message: str) -> tuple[str, str, str]:
    """(etiket, arama, gövde_regex_adı)"""
    low = (message or "").lower()
    if "euro" in low or "eur" in low:
        return ("Euro (EUR)", "EUR TRY kur doviz.com", "eur")
    if "sterlin" in low or "gbp" in low:
        return ("Sterlin (GBP)", "GBP TRY kur", "gbp")
    if "altın" in low or "altin" in low:
        return ("Gram altın", "gram altın fiyatı TL", "gold")
    return ("Amerikan Doları (USD)", "USD TRY kur doviz.com", "usd")


def _parse_rate_from_rows(rows: list[dict], kind: str) -> Optional[tuple[str, str]]:
    """(rate_display, source_url)"""
    for r in rows or []:
        blob = f"{r.get('title') or ''} {r.get('body') or ''}"
        href = str(r.get("href") or "").strip()
        m = None
        if kind == "eur":
            m = _EUR_BODY_RE.search(blob) or _RATE_RE.search(blob)
        elif kind == "usd":
            m = _USD_BODY_RE.search(blob) or _RATE_RE.search(blob)
        else:
            m = _RATE_RE.search(blob)
        if not m:
            continue
        # TR formatını koru: 49,1263
        disp = m.group("num")
        try:
            val = float(disp.replace(",", "."))
        except ValueError:
            continue
        # Makul kur aralığı (eski 18,45 zehirini ele)
        if kind in ("usd", "eur", "gbp") and not (20.0 <= val <= 200.0):
            continue
        if kind == "gold" and not (500.0 <= val <= 20000.0):
            continue
        return disp, href
    return None


def try_live_fx_reply(message: str) -> Optional[str]:
    """DDG snippet'ten canlı kur — LLM beklemeden."""
    if not fx_live_enabled() or not looks_like_fx_rate_question(message):
        return None
    label, query, kind = _pick_pair(message)
    addr = OWNER_ADDRESS or "Ümit abi"
    honest = (
        f"{addr}, bugünkü {label} fiyatını güvenilir bir sayfadan okuyamadım. "
        "Yanlış bir rakam yazmayayım. Biraz sonra tekrar sorarsan yeniden bakarım."
    )
    if os.environ.get("ENABLE_WEB_SEARCH", "1").strip() in ("0", "false", "no"):
        return honest
    try:
        from ilim_assistant.web_tools import _ddgs_search

        rows = _ddgs_search(query, max_results=8)
        if not rows:
            rows = _ddgs_search(f"{label} TL", max_results=8)
    except Exception:
        return honest
    parsed = _parse_rate_from_rows(rows, kind)
    if not parsed:
        return honest
    rate, src = parsed
    src_note = ""
    if src:
        host = src.split("/")[2] if "://" in src else src
        src_note = f" Kaynak: {host}."
    return (
        f"{addr}, şu an 1 {label} yaklaşık {rate} TL."
        f"{src_note} Kur gün içinde oynayabilir."
    )


def try_price_source_followup(message: str) -> Optional[str]:
    """«Kaynağı nereden aldın» — önceki rakam sayfadan gelmediyse bunu söyle."""
    low = (message or "").lower()
    if not re.search(r"kaynak|nereden\s+ald", low):
        return None
    try:
        from ilim_assistant.ana_motor_sohbet_gecmis import recent_chat_history

        items = list(recent_chat_history(limit=4).get("items") or [])
    except Exception:
        return None
    prev = ""
    for row in items:
        text = str(row.get("assistant") or "").strip()
        if text:
            prev = text
            break
    if not prev:
        return None
    if re.search(r"kaynak\s*:", prev, re.I):
        host = ""
        m = re.search(r"Kaynak:\s*([^\s.]+)", prev, re.I)
        if m:
            host = m.group(1)
        if host:
            return f"Ümit abi, bir önceki rakamı {host} sayfasından okumuştum."
        return "Ümit abi, bir önceki rakamın yanında kaynak da vardı; o satıra bakabilirsin."
    if re.search(r"\d", prev) and re.search(r"tl|dolar|euro|altın|altin|sterlin", prev, re.I):
        return (
            "Ümit abi, o rakamı canlı bir sayfadan okuyamadım, kaynak da yok. "
            "Uydurma bir fiyat vermemeliydim. İstersen şimdi yeniden bakarım."
        )
    return None


def fx_live_context_line(message: str) -> str:
    """Web bağlamının tepesine eklenecek kısa kur özeti."""
    reply = try_live_fx_reply(message)
    if not reply:
        return ""
    # OWNER hitabını çıkar, ham özet bırak
    body = re.sub(r"^[^,]+,\s*", "", reply).strip()
    return f"=== CANLI KUR ÖZETİ (web snippet) ===\n{body}\n"
