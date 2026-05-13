from __future__ import annotations

import os
import random
import time
from dataclasses import dataclass


@dataclass
class SafeRequestConfig:
    """
    Resmi Satıcı API + insansı gecikme.
    Ortam değişkenleri: HIZIR_TRENDYOL_API_KEY, HIZIR_AMAZON_REFRESH_TOKEN vb. (ileride).
    """

    min_delay_sec: float = 0.8
    max_delay_sec: float = 2.8
    user_agent: str = "Ruzgar-Hizir/1.0 (seller-api; compliance)"

    @classmethod
    def from_env(cls) -> SafeRequestConfig:
        mn = float(os.environ.get("HIZIR_SAFE_DELAY_MIN", "0.8"))
        mx = float(os.environ.get("HIZIR_SAFE_DELAY_MAX", "2.8"))
        if mx < mn:
            mn, mx = mx, mn
        return cls(min_delay_sec=mn, max_delay_sec=mx)


def sleep_human_interval(cfg: SafeRequestConfig | None = None, *, execute: bool | None = None) -> float:
    """
    İstek öncesi rastgele insansı bekleme süresi (saniye).
    Varsayılan: uyku yok (test/sunucu). HIZIR_SAFE_REQUEST_SLEEP=1 ile gerçek bekleme.
    """
    c = cfg or SafeRequestConfig.from_env()
    delay = random.uniform(c.min_delay_sec, c.max_delay_sec)
    if execute is None:
        execute = os.environ.get("HIZIR_SAFE_REQUEST_SLEEP", "").strip().lower() in ("1", "true", "yes", "on")
    if execute:
        time.sleep(delay)
    return delay


def credentials_configured(marketplace: str) -> bool:
    """Resmi API için ortamda tanımlı anahtar var mı (içerik okunmaz)."""
    mp = (marketplace or "").strip().lower()
    env_map = {
        "amazon": os.environ.get("HIZIR_AMAZON_REFRESH_TOKEN")
        or os.environ.get("HIZIR_AMAZON_LWA_CLIENT_ID"),
        "trendyol": os.environ.get("HIZIR_TRENDYOL_API_KEY")
        or os.environ.get("HIZIR_TRENDYOL_SUPPLIER_KEY"),
    }
    v = env_map.get(mp)
    return bool(v and str(v).strip())


def safe_request_placeholder(
    marketplace: str,
    path: str,
    *,
    method: str = "GET",
    cfg: SafeRequestConfig | None = None,
) -> dict[str, object]:
    """
    Gerçek HTTP yerine sözleşme: önce gecikme, sonra anahtar varlığı kontrolü.
    Üretimde: imzalı istek, nonce, idempotency ve hız sınırı burada uygulanır.
    """
    _ = cfg
    waited = sleep_human_interval(SafeRequestConfig.from_env())
    has_cred = credentials_configured(marketplace)
    return {
        "ok": False,
        "marketplace": marketplace,
        "method": method,
        "path": path,
        "waited_sec": round(waited, 3),
        "credentials_configured": has_cred,
        "note": "Gerçek çağrı yok; yalnızca güvenli istek akışı iskeleti.",
    }
