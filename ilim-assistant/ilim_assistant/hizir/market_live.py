"""
Canlı pazar listeleri — Trendyol (discovery JSON) ve Amazon TR (Product Advertising API 5).

Ortam değişkenleri
------------------
HIZIR_MOCK_MARKETPLACE=1  → sahte satırlar (geliştirici).

Canlı (varsayılan, HIZIR_MOCK_MARKETPLACE kapalı veya 0):
  HIZIR_AMAZON_ACCESS_KEY, HIZIR_AMAZON_SECRET_KEY, HIZIR_AMAZON_PARTNER_TAG
    → python-amazon-paapi (PA-API 5) ile www.amazon.com.tr araması.
  Trendyol için ek anahtar gerekmez; isteğe bağlı:
    HIZIR_TRENDYOL_SEARCH_BASE — birincil arama JSON uç noktası.
    HIZIR_TRENDYOL_SEARCH_BASE_FALLBACKS — virgülle ek uç noktalar (apigw kapalıysa).

İstekler arasında insansı gecikme: HIZIR_SAFE_REQUEST_SLEEP=1 (safe_request.sleep_human_interval).
"""

from __future__ import annotations

import logging
import os
from typing import Any

import requests

from ilim_assistant.hizir.safe_request import SafeRequestConfig, sleep_human_interval

_LOG = logging.getLogger(__name__)

_DEFAULT_TY_BASE = (
    "https://apigw.trendyol.com/discovery-web-searchgw-service/v2/api/infinite-scroll/sr"
)
_BUILTIN_TY_FALLBACKS = (
    "https://public.trendyol.com/discovery-web-searchgw-service/v2/api/infinite-scroll/sr",
)

_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8",
}


def use_mock_marketplace() -> bool:
    return os.environ.get("HIZIR_MOCK_MARKETPLACE", "0").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def _price_from_obj(obj: Any) -> float | None:
    if obj is None:
        return None
    if isinstance(obj, (int, float)) and float(obj) > 0:
        return float(obj)
    if isinstance(obj, str):
        try:
            s = obj.replace("TL", "").replace("₺", "").replace(".", "").replace(",", ".").strip()
            v = float(s)
            return v if v > 0 else None
        except ValueError:
            return None
    if isinstance(obj, dict):
        for k in (
            "sellingPrice",
            "discountedPrice",
            "mOriginalPrice",
            "value",
            "text",
            "price",
            "current",
        ):
            if k in obj:
                p = _price_from_obj(obj[k])
                if p is not None:
                    return p
    return None


def _title_from_product(p: dict[str, Any]) -> str:
    for k in ("name", "title", "productName", "brand", "text"):
        v = p.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()[:220]
    return "Ürün"


def _parse_trendyol_products(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """API gövdesinden düz satır listesi: name, price, in_stock, id."""
    rows: list[dict[str, Any]] = []
    seen: set[tuple[float, str]] = set()

    def take_list(lst: list[Any]) -> None:
        for it in lst:
            if not isinstance(it, dict):
                continue
            price = _price_from_obj(it.get("price"))
            if price is None:
                continue
            pid = str(it.get("id") or it.get("contentId") or it.get("productId") or "")[:80]
            st = it.get("inStock")
            if st is None:
                st = it.get("hasStock")
            in_stock = bool(st) if st is not None else True
            name = _title_from_product(it)
            key = (round(float(price), 2), name[:80])
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                {
                    "name": name,
                    "price": float(price),
                    "in_stock": in_stock,
                    "id": pid or "ty-live",
                    "extra": {"source": "live"},
                }
            )

    res = payload.get("result") if isinstance(payload.get("result"), dict) else None
    if res and isinstance(res.get("products"), list):
        take_list(res["products"])
    elif isinstance(payload.get("products"), list):
        take_list(payload["products"])
    else:

        def walk(o: Any, depth: int = 0) -> None:
            if depth > 14 or isinstance(o, (str, int, float, bool)) or o is None:
                return
            if isinstance(o, dict):
                if "products" in o and isinstance(o["products"], list):
                    take_list(o["products"])
                for v in o.values():
                    walk(v, depth + 1)
            elif isinstance(o, list):
                for v in o:
                    walk(v, depth + 1)

        walk(payload)
    return rows


def _trendyol_search_url_candidates() -> list[str]:
    raw = (os.environ.get("HIZIR_TRENDYOL_SEARCH_BASE_FALLBACKS") or "").strip()
    extra = [u.strip() for u in raw.split(",") if u.strip()]
    primary = (os.environ.get("HIZIR_TRENDYOL_SEARCH_BASE") or "").strip() or _DEFAULT_TY_BASE
    out: list[str] = []
    for u in (primary, *extra, *_BUILTIN_TY_FALLBACKS):
        if u and u not in out:
            out.append(u)
    return out


def _trendyol_http_get_json(base: str, params: dict[str, str]) -> tuple[dict[str, Any] | None, str | None]:
    try:
        r = requests.get(
            base,
            params=params,
            headers=_BROWSER_HEADERS,
            timeout=float(os.environ.get("HIZIR_HTTP_TIMEOUT", "25")),
        )
    except requests.RequestException as exc:
        return None, f"ağ: {exc}"

    if r.status_code != 200:
        msg = r.text[:220]
        ct = (r.headers.get("content-type") or "").lower()
        if "json" in ct:
            try:
                j = r.json()
                if isinstance(j, dict) and j.get("message"):
                    msg = str(j["message"])[:220]
            except Exception:
                pass
        return None, f"HTTP {r.status_code}: {msg}"

    try:
        data = r.json()
    except ValueError:
        return None, "JSON çözülemedi"

    if not isinstance(data, dict):
        return None, "Beklenmeyen yanıt biçimi"
    return data, None


def fetch_trendyol_live(query: str, *, limit: int = 10) -> tuple[list[dict[str, Any]], str | None]:
    """Dönüş: ({name, price, in_stock, id, extra}, hata_metni)."""
    q = (query or "").strip() or "ürün"
    sleep_human_interval(SafeRequestConfig.from_env())
    params = {
        "q": q,
        "pi": "1",
        "culture": os.environ.get("HIZIR_TRENDYOL_CULTURE", "tr-TR").strip() or "tr-TR",
    }

    errs: list[str] = []
    for base in _trendyol_search_url_candidates():
        data, err = _trendyol_http_get_json(base, params)
        if err:
            errs.append(f"{base.split('//', 1)[-1][:48]} → {err}")
            _LOG.warning("Trendyol deneme %s: %s", base, err)
            continue
        if data is None:
            continue
        rows = _parse_trendyol_products(data)[: max(1, min(limit, 20))]
        if rows:
            return rows, None
        errs.append(f"{base.split('//', 1)[-1][:48]} → ürün yok / şema")

    if not errs:
        return [], "Trendyol: uç nokta listesi boş"
    return [], "Trendyol (tüm denemeler): " + " | ".join(errs[:4])[:900]


def fetch_amazon_live(query: str, *, limit: int = 10) -> tuple[list[dict[str, Any]], str | None]:
    key = (os.environ.get("HIZIR_AMAZON_ACCESS_KEY") or "").strip()
    secret = (os.environ.get("HIZIR_AMAZON_SECRET_KEY") or "").strip()
    tag = (os.environ.get("HIZIR_AMAZON_PARTNER_TAG") or "").strip()
    if not (key and secret and tag):
        return (
            [],
            "Amazon canlı arama için HIZIR_AMAZON_ACCESS_KEY, HIZIR_AMAZON_SECRET_KEY ve "
            "HIZIR_AMAZON_PARTNER_TAG (PA-API 5 ortaklık etiketi) tanımlayın.",
        )

    try:
        from amazon_paapi import AmazonApi
        from amazon_paapi.models import Country
    except ImportError:
        return (
            [],
            "Amazon PA-API için paket eksik: pip install 'python-amazon-paapi>=5.2.0,<6'",
        )

    sleep_human_interval(SafeRequestConfig.from_env())
    country_code = (os.environ.get("HIZIR_AMAZON_COUNTRY") or "TR").strip().upper()
    try:
        country = getattr(Country, country_code)
    except AttributeError:
        country = Country.TR

    q = (query or "").strip() or "ürün"
    n = max(1, min(int(limit), 10))

    try:
        api = AmazonApi(key, secret, tag, country, throttling=float(os.environ.get("HIZIR_AMAZON_THROTTLE", "1")))
        result = api.search_items(keywords=q, item_count=n)
    except Exception as exc:
        _LOG.warning("Amazon PA-API hatası: %s", exc)
        return [], f"Amazon PA-API: {exc}"

    items = getattr(result, "items", None) or []
    out: list[dict[str, Any]] = []
    for it in items:
        title = ""
        try:
            if it.item_info and it.item_info.title and it.item_info.title.display_value:
                title = str(it.item_info.title.display_value).strip()
        except Exception:
            title = ""
        if not title:
            title = "Ürün"
        price_val: float | None = None
        try:
            if it.offers and it.offers.listings:
                lst = it.offers.listings[0]
                pr = getattr(lst, "price", None)
                if pr is not None:
                    amt = getattr(pr, "amount", None)
                    if amt is not None:
                        price_val = float(amt)
        except Exception:
            price_val = None
        if price_val is None or price_val <= 0:
            continue
        asin = str(getattr(it, "asin", "") or "")[:20]
        in_stock = True
        try:
            if it.offers and it.offers.listings:
                av = getattr(it.offers.listings[0], "availability", None)
                if av and getattr(av, "type", None):
                    in_stock = "Now" in str(av.type) or "InStock" in str(av.type)
        except Exception:
            pass
        out.append(
            {
                "name": title[:240],
                "price": price_val,
                "in_stock": in_stock,
                "id": asin,
                "extra": {"source": "live", "asin": asin},
            }
        )

    if not out:
        return [], "Amazon: arama sonucu veya fiyat bilgisi dönmedi (PA-API kota/kısıt olabilir)."

    return out, None
