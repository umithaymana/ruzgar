"""
Trendyol discovery istekleri — tarayıcı benzeri başlıklar, isteğe bağlı vekil, yeniden deneme.

Ortam (özet):
  HIZIR_HTTP_PROXY veya HIZIR_TRENDYOL_PROXY — http(s)://host:port (ücretsiz/ücretli vekil kendi sorumluluğunuzdadır).
  HIZIR_TRENDYOL_RETRIES — taban başına deneme (varsayılan 3).
  HIZIR_TRENDYOL_RETRY_SLEEP — denemeler arası saniye (varsayılan 0.6).
  HIZIR_TRENDYOL_USER_AGENTS — virgül veya satır sonu ile birden fazla User-Agent (dönüşümlü).
"""

from __future__ import annotations

import hashlib
import os
import time
from typing import Any

_DEFAULT_UAS = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
)


def _user_agents() -> list[str]:
    raw = (os.environ.get("HIZIR_TRENDYOL_USER_AGENTS") or "").strip()
    if not raw:
        return list(_DEFAULT_UAS)
    parts = [p.strip() for p in raw.replace("\n", ",").split(",") if p.strip()]
    return parts if parts else list(_DEFAULT_UAS)


def pick_user_agent(seed: str, attempt: int) -> str:
    uas = _user_agents()
    h = int(hashlib.md5(f"{seed}:{attempt}".encode()).hexdigest(), 16)
    return uas[h % len(uas)]


def trendyol_browser_headers(*, seed: str, attempt: int) -> dict[str, str]:
    ua = pick_user_agent(seed, attempt)
    return {
        "User-Agent": ua,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": (os.environ.get("HIZIR_TRENDYOL_ACCEPT_LANGUAGE") or "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7").strip(),
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Referer": (os.environ.get("HIZIR_TRENDYOL_REFERER") or "https://www.trendyol.com/").strip(),
        "Origin": (os.environ.get("HIZIR_TRENDYOL_ORIGIN") or "https://www.trendyol.com").strip(),
        "Sec-Fetch-Site": "same-site",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Sec-Ch-Ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }


def trendyol_requests_proxies() -> dict[str, str] | None:
    proxy = (os.environ.get("HIZIR_TRENDYOL_PROXY") or os.environ.get("HIZIR_HTTP_PROXY") or "").strip()
    if not proxy:
        return None
    return {"http": proxy, "https": proxy}


def trendyol_retry_config() -> tuple[int, float]:
    try:
        n = max(1, min(int(os.environ.get("HIZIR_TRENDYOL_RETRIES", "3")), 8))
    except ValueError:
        n = 3
    try:
        sleep_s = max(0.0, float(os.environ.get("HIZIR_TRENDYOL_RETRY_SLEEP", "0.6")))
    except ValueError:
        sleep_s = 0.6
    return n, sleep_s


TRENDYOL_LIVE_ENV_KEYS: tuple[str, ...] = (
    "HIZIR_HTTP_PROXY",
    "HIZIR_TRENDYOL_PROXY",
    "HIZIR_TRENDYOL_RETRIES",
    "HIZIR_TRENDYOL_RETRY_SLEEP",
    "HIZIR_TRENDYOL_USER_AGENTS",
    "HIZIR_TRENDYOL_REFERER",
    "HIZIR_TRENDYOL_ORIGIN",
    "HIZIR_TRENDYOL_ACCEPT_LANGUAGE",
    "HIZIR_TRENDYOL_SEARCH_BASE",
    "HIZIR_TRENDYOL_SEARCH_BASE_FALLBACKS",
    "HIZIR_TRENDYOL_CULTURE",
    "HIZIR_HTTP_TIMEOUT",
)
