"""
Canlı pazar listeleri — Trendyol (discovery JSON), Amazon (PA-API 5, çoklu ülke), eBay Browse API.

Ortam değişkenleri
------------------
HIZIR_MOCK_MARKETPLACE=1  → yalnızca geliştirici; üretimde kullanmayın (varsayılan kapalı).

Canlı (varsayılan, HIZIR_MOCK_MARKETPLACE kapalı veya 0):
  HIZIR_AMAZON_ACCESS_KEY, HIZIR_AMAZON_SECRET_KEY, HIZIR_AMAZON_PARTNER_TAG
    → python-amazon-paapi (PA-API 5) ile amazon.* alan adına göre ülke.
  Ülke: fetch çağrısında country_code veya HIZIR_AMAZON_COUNTRY (TR, US, DE, GB/UK).
  Trendyol: `trendyol_resilience` — HIZIR_TRENDYOL_PROXY / HIZIR_HTTP_PROXY, HIZIR_TRENDYOL_RETRIES,
    HIZIR_TRENDYOL_RETRY_SLEEP, HIZIR_TRENDYOL_USER_AGENTS, Referer/Origin (isteğe bağlı).
  Statik US demo (yalnızca «Logitech Mouse» sorgusu, PA-API+eBay boşken): HIZIR_STATIC_LIVE_LOGITECH_MOUSE=1 (varsayılan).

eBay Browse (US/GB/DE aynı bölge listeleri):
  HIZIR_EBAY_CLIENT_ID, HIZIR_EBAY_CLIENT_SECRET  → OAuth client_credentials.

AliExpress (isteğe bağlı — imzalı Open Platform):
  HIZIR_ALIEXPRESS_APP_KEY, HIZIR_ALIEXPRESS_APP_SECRET  → ds.text.search.

İstekler arasında insansı gecikme: HIZIR_SAFE_REQUEST_SLEEP=1 (safe_request.sleep_human_interval).
"""

from __future__ import annotations

import base64
import hashlib
import logging
import os
import time
from typing import Any

import requests

from ilim_assistant.hizir.safe_request import SafeRequestConfig, sleep_human_interval

_LOG = logging.getLogger(__name__)

_EBAY_TOKEN: dict[str, Any] = {"access_token": "", "expires_at": 0.0}

_DEFAULT_TY_BASE = (
    "https://apigw.trendyol.com/discovery-web-searchgw-service/v2/api/infinite-scroll/sr"
)
_BUILTIN_TY_FALLBACKS = (
    "https://public.trendyol.com/discovery-web-searchgw-service/v2/api/infinite-scroll/sr",
)


def _trendyol_http_get_json(
    base: str,
    params: dict[str, str],
    *,
    seed: str,
) -> tuple[dict[str, Any] | None, str | None]:
    from ilim_assistant.hizir import trendyol_resilience as tr

    n_ret, sleep_s = tr.trendyol_retry_config()
    proxies = tr.trendyol_requests_proxies()
    timeout = float(os.environ.get("HIZIR_HTTP_TIMEOUT", "25"))
    last_err: str | None = None
    for attempt in range(1, n_ret + 1):
        if attempt > 1:
            delay = sleep_s * (1.4 ** (attempt - 2))
            if delay > 0:
                time.sleep(delay)
        headers = tr.trendyol_browser_headers(seed=seed, attempt=attempt)
        try:
            r = requests.get(
                base,
                params=params,
                headers=headers,
                timeout=timeout,
                proxies=proxies,
            )
        except requests.RequestException as exc:
            last_err = f"ağ: {exc}"
            continue

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
            last_err = f"HTTP {r.status_code}: {msg}"
            continue

        try:
            data = r.json()
        except ValueError:
            last_err = "JSON çözülemedi"
            continue

        if not isinstance(data, dict):
            last_err = "Beklenmeyen yanıt biçimi"
            continue
        return data, None

    return None, last_err or "Trendyol: bilinmeyen ağ hatası"


def use_mock_marketplace() -> bool:
    """Üretimde daima 0 bırakın; canlı uçlar varsayılan olarak etkindir."""
    return os.environ.get("HIZIR_MOCK_MARKETPLACE", "0").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


# Mock / dokümantasyon — gerçek HTTPS örnekleri (ruzgar-desktop CSP: upload.wikimedia.org)
DEMO_PRODUCT_IMAGE_TR_TRENDYOL = (
    "https://upload.wikimedia.org/wikipedia/commons/thumb/1/16/Coffee_machine_espresso.jpg/320px-Coffee_machine_espresso.jpg"
)
DEMO_PRODUCT_IMAGE_TR_AMAZON = (
    "https://upload.wikimedia.org/wikipedia/commons/thumb/4/45/A_small_cup_of_coffee.JPG/320px-A_small_cup_of_coffee.JPG"
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
            img_u: str | None = None
            im = it.get("image")
            if isinstance(im, dict):
                u = im.get("url") or im.get("imageUrl")
                if isinstance(u, str) and u.startswith("http"):
                    img_u = u.strip()[:900]
            if img_u is None and isinstance(it.get("images"), list) and it["images"]:
                first = it["images"][0]
                if isinstance(first, dict):
                    u = first.get("url") or first.get("imageUrl")
                    if isinstance(u, str) and u.startswith("http"):
                        img_u = u.strip()[:900]
            row: dict[str, Any] = {
                "name": name,
                "price": float(price),
                "in_stock": in_stock,
                "id": pid or "ty-live",
                "currency": "TRY",
                "extra": {"source": "live"},
            }
            if img_u:
                row["image"] = img_u
            rows.append(row)

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
        data, err = _trendyol_http_get_json(base, params, seed=q)
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
    err_join = "Trendyol (tüm denemeler): " + " | ".join(errs[:4])[:900]
    if os.environ.get("HIZIR_TRENDYOL_HTML_FALLBACK", "1").strip().lower() in (
        "0",
        "false",
        "no",
        "off",
    ):
        return [], err_join
    try:
        from ilim_assistant.hizir.market_html_fallback import fetch_trendyol_next_data_html

        rows_html, herr = fetch_trendyol_next_data_html(q, limit=max(1, min(limit, 20)))
        if rows_html:
            return rows_html, None
        if herr:
            return [], f"{err_join} | HTML: {herr}"
    except Exception as exc:  # pragma: no cover
        _LOG.warning("Trendyol HTML fallback: %s", exc)
    return [], err_join


def fetch_hepsiburada_live(query: str, *, limit: int = 10) -> tuple[list[dict[str, Any]], str | None]:
    """Hepsiburada — yalnızca HTML keşif (PA-API yok)."""
    from ilim_assistant.hizir.market_html_fallback import fetch_hepsiburada_search_html

    return fetch_hepsiburada_search_html((query or "").strip() or "ürün", limit=max(1, min(int(limit), 20)))


def _amazon_country_enum(country_code: str) -> Any:
    """python-amazon-paapi Country üyesi (UK → GB eşlemesi)."""
    from amazon_paapi.models import Country

    cc = (country_code or "TR").strip().upper()
    cc = {"UK": "GB", "ENGLAND": "GB"}.get(cc, cc)
    try:
        return getattr(Country, cc)
    except AttributeError:
        return Country.TR


def fetch_amazon_live(
    query: str,
    *,
    limit: int = 10,
    country_code: str | None = None,
) -> tuple[list[dict[str, Any]], str | None]:
    """
    PA-API 5 ile canlı arama. `country_code`: TR, US, DE, GB (UK için GB kullanın).
    Belirtilmezse HIZIR_AMAZON_COUNTRY veya TR.
    """
    q = (query or "").strip() or "ürün"
    n = max(1, min(int(limit), 10))
    key = (os.environ.get("HIZIR_AMAZON_ACCESS_KEY") or "").strip()
    secret = (os.environ.get("HIZIR_AMAZON_SECRET_KEY") or "").strip()
    tag = (os.environ.get("HIZIR_AMAZON_PARTNER_TAG") or "").strip()
    cc0 = (country_code or os.environ.get("HIZIR_AMAZON_COUNTRY") or "TR").strip().upper()
    cc0 = {"UK": "GB", "ENGLAND": "GB"}.get(cc0, cc0)
    host_cur = {
        "TR": ("www.amazon.com.tr", "TRY"),
        "US": ("www.amazon.com", "USD"),
        "DE": ("www.amazon.de", "EUR"),
        "GB": ("www.amazon.co.uk", "GBP"),
    }.get(cc0, ("www.amazon.com.tr", "TRY"))

    def _html_amazon() -> tuple[list[dict[str, Any]], str | None]:
        if os.environ.get("HIZIR_AMAZON_HTML_FALLBACK", "1").strip().lower() in (
            "0",
            "false",
            "no",
            "off",
        ):
            return [], "Amazon HTML yedek kapalı (HIZIR_AMAZON_HTML_FALLBACK=0)."
        try:
            from ilim_assistant.hizir.market_html_fallback import fetch_amazon_search_html

            return fetch_amazon_search_html(
                q,
                limit=n,
                host=host_cur[0],
                currency=host_cur[1],
            )
        except Exception as exc:  # pragma: no cover
            return [], f"Amazon HTML: {exc}"

    if not (key and secret and tag):
        rows_h, err_h = _html_amazon()
        if rows_h:
            return rows_h, None
        return (
            [],
            (
                "Amazon PA-API anahtarları yok; HTML yedek de sonuç vermedi: "
                + (err_h or "bilinmeyen")
            )[:900],
        )

    try:
        from amazon_paapi import AmazonApi
    except ImportError:
        rows_h, err_h = _html_amazon()
        if rows_h:
            return rows_h, None
        return (
            [],
            "Amazon PA-API için paket eksik: pip install 'python-amazon-paapi>=5.2.0,<6'. "
            f"HTML yedek: {err_h or '—'}",
        )

    sleep_human_interval(SafeRequestConfig.from_env())
    cc = cc0
    country = _amazon_country_enum(cc)

    try:
        api = AmazonApi(key, secret, tag, country, throttling=float(os.environ.get("HIZIR_AMAZON_THROTTLE", "1")))
        result = api.search_items(keywords=q, item_count=n)
    except Exception as exc:
        _LOG.warning("Amazon PA-API hatası (%s): %s", cc, exc)
        rows_h, err_h = _html_amazon()
        if rows_h:
            return rows_h, None
        return [], f"Amazon PA-API ({cc}): {exc} | HTML: {err_h or '—'}"

    items = getattr(result, "items", None) or []
    out: list[dict[str, Any]] = []
    default_cur = {"TR": "TRY", "US": "USD", "DE": "EUR", "GB": "GBP"}.get(cc, "USD")
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
        currency = default_cur
        try:
            if it.offers and it.offers.listings:
                lst = it.offers.listings[0]
                pr = getattr(lst, "price", None)
                if pr is not None:
                    amt = getattr(pr, "amount", None)
                    if amt is not None:
                        price_val = float(amt)
                    cur = getattr(pr, "currency", None)
                    if cur:
                        currency = str(cur).upper()[:8]
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
        img_url: str | None = None
        try:
            if it.images and it.images.primary and it.images.primary.large:
                lu = getattr(it.images.primary.large, "url", None)
                if isinstance(lu, str) and lu.startswith("http"):
                    img_url = lu.strip()[:900]
        except Exception:
            img_url = None
        row: dict[str, Any] = {
            "name": title[:240],
            "price": price_val,
            "in_stock": in_stock,
            "id": asin,
            "currency": currency,
            "extra": {"source": "live", "asin": asin, "amazon_country": cc},
        }
        if img_url:
            row["image"] = img_url
        out.append(row)

    if not out:
        rows_h, err_h = _html_amazon()
        if rows_h:
            return rows_h, None
        return [], (
            f"Amazon ({cc}): PA-API sonuç yok; HTML: {err_h or '—'} "
            f"(PA-API kota/kısıt veya HTML ayrıştırma)."
        )[:900]

    return out, None


def _ebay_oauth_token() -> tuple[str | None, str | None]:
    cid = (os.environ.get("HIZIR_EBAY_CLIENT_ID") or "").strip()
    csec = (os.environ.get("HIZIR_EBAY_CLIENT_SECRET") or "").strip()
    if not cid or not csec:
        return None, (
            "eBay Browse API: HIZIR_EBAY_CLIENT_ID ve HIZIR_EBAY_CLIENT_SECRET "
            "(production uygulama kimlikleri) tanımlayın."
        )
    now = time.time()
    if (
        _EBAY_TOKEN.get("access_token")
        and float(_EBAY_TOKEN.get("expires_at", 0)) > now + 30.0
    ):
        return str(_EBAY_TOKEN["access_token"]), None

    basic = base64.b64encode(f"{cid}:{csec}".encode("utf-8")).decode("ascii")
    scope = (
        os.environ.get("HIZIR_EBAY_OAUTH_SCOPE")
        or "https://api.ebay.com/oauth/api_scope"
    ).strip()
    from urllib.parse import quote_plus

    try:
        r = requests.post(
            "https://api.ebay.com/identity/v1/oauth2/token",
            headers={
                "Authorization": f"Basic {basic}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data=f"grant_type=client_credentials&scope={quote_plus(scope)}",
            timeout=float(os.environ.get("HIZIR_HTTP_TIMEOUT", "25")),
        )
    except requests.RequestException as exc:
        return None, f"eBay OAuth ağ: {exc}"
    if r.status_code != 200:
        return None, f"eBay OAuth HTTP {r.status_code}: {r.text[:240]}"
    try:
        data = r.json()
    except ValueError:
        return None, "eBay OAuth: JSON yanıtı geçersiz"
    tok = str(data.get("access_token") or "")
    if not tok:
        return None, "eBay OAuth: access_token yok"
    exp = now + float(data.get("expires_in", 7200))
    _EBAY_TOKEN["access_token"] = tok
    _EBAY_TOKEN["expires_at"] = exp
    return tok, None


def fetch_ebay_live(
    query: str,
    *,
    marketplace_id: str = "EBAY_US",
    limit: int = 10,
) -> tuple[list[dict[str, Any]], str | None]:
    """
    eBay Browse API item_summary/search. marketplace_id: EBAY_US, EBAY_GB, EBAY_DE.
    """
    tok, err = _ebay_oauth_token()
    if err or not tok:
        return [], err or "eBay: token alınamadı"

    q = (query or "").strip() or "item"
    n = max(1, min(int(limit), 20))
    sleep_human_interval(SafeRequestConfig.from_env())
    url = "https://api.ebay.com/buy/browse/v1/item_summary/search"
    try:
        r = requests.get(
            url,
            params={"q": q, "limit": n},
            headers={
                "Authorization": f"Bearer {tok}",
                "X-EBAY-C-MARKETPLACE-ID": marketplace_id.strip() or "EBAY_US",
                "Accept": "application/json",
                "Accept-Language": "en-US,en;q=0.9",
            },
            timeout=float(os.environ.get("HIZIR_HTTP_TIMEOUT", "25")),
        )
    except requests.RequestException as exc:
        return [], f"eBay arama ağ: {exc}"
    if r.status_code != 200:
        return [], f"eBay HTTP {r.status_code}: {r.text[:240]}"
    try:
        payload = r.json()
    except ValueError:
        return [], "eBay: JSON çözülemedi"
    summaries = payload.get("itemSummaries") if isinstance(payload, dict) else None
    if not isinstance(summaries, list):
        return [], "eBay: itemSummaries yok"

    rows: list[dict[str, Any]] = []
    for it in summaries:
        if not isinstance(it, dict):
            continue
        title = str(it.get("title") or "Ürün").strip()[:240]
        price_obj = it.get("price") if isinstance(it.get("price"), dict) else {}
        try:
            price_val = float(price_obj.get("value"))
        except (TypeError, ValueError):
            continue
        if price_val <= 0:
            continue
        cur = str(price_obj.get("currency") or "USD").upper()[:8]
        iid = str(it.get("itemId") or it.get("legacyItemId") or "")[:64]
        img_u: str | None = None
        im = it.get("image")
        if isinstance(im, dict):
            iu = im.get("imageUrl") or im.get("url")
            if isinstance(iu, str) and iu.startswith("http"):
                img_u = iu.strip()[:900]
        row: dict[str, Any] = {
            "name": title,
            "price": price_val,
            "in_stock": True,
            "id": iid or "ebay-live",
            "currency": cur,
            "extra": {"source": "live", "ebay_marketplace": marketplace_id},
        }
        if img_u:
            row["image"] = img_u
        rows.append(row)
    if not rows:
        return [], f"eBay ({marketplace_id}): sonuç veya fiyat satırı yok."
    return rows, None


def _aliexpress_sign(params: dict[str, str], app_secret: str) -> str:
    keys = sorted(params.keys())
    concat = app_secret + "".join(f"{k}{params[k]}" for k in keys) + app_secret
    return hashlib.md5(concat.encode("utf-8")).hexdigest().upper()


def fetch_aliexpress_live(query: str, *, limit: int = 10) -> tuple[list[dict[str, Any]], str | None]:
    """
    AliExpress Dropshipping / sistem API — aliexpress.ds.text.search (imzalı REST).
    Oturum: HIZIR_ALIEXPRESS_ACCESS_TOKEN (çoğu DS yöntemi için gerekir).
    """
    app_key = (os.environ.get("HIZIR_ALIEXPRESS_APP_KEY") or "").strip()
    app_secret = (os.environ.get("HIZIR_ALIEXPRESS_APP_SECRET") or "").strip()
    session = (os.environ.get("HIZIR_ALIEXPRESS_ACCESS_TOKEN") or "").strip()
    if not app_key or not app_secret:
        return (
            [],
            "AliExpress: HIZIR_ALIEXPRESS_APP_KEY ve HIZIR_ALIEXPRESS_APP_SECRET tanımlayın "
            "(Open Platform uygulaması).",
        )
    if not session:
        return (
            [],
            "AliExpress DS araması için HIZIR_ALIEXPRESS_ACCESS_TOKEN (seller token) tanımlayın.",
        )

    q = (query or "").strip() or "phone"
    n = max(1, min(int(limit), 20))
    sleep_human_interval(SafeRequestConfig.from_env())

    base: dict[str, str] = {
        "method": "aliexpress.ds.text.search",
        "app_key": app_key,
        "timestamp": str(int(time.time() * 1000)),
        "sign_method": "md5",
        "session": session,
        "format": "json",
        "v": "2.0",
        "keywords_text": q[:200],
        "page_size": str(n),
        "target_currency": (os.environ.get("HIZIR_ALIEXPRESS_TARGET_CURRENCY") or "USD").strip(),
        "target_language": (os.environ.get("HIZIR_ALIEXPRESS_TARGET_LANGUAGE") or "EN").strip(),
    }
    base["sign"] = _aliexpress_sign(base, app_secret)
    gateway = (os.environ.get("HIZIR_ALIEXPRESS_GATEWAY") or "https://api-sg.aliexpress.com/sync").strip()

    try:
        r = requests.post(
            gateway,
            data=base,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=float(os.environ.get("HIZIR_HTTP_TIMEOUT", "30")),
        )
    except requests.RequestException as exc:
        return [], f"AliExpress ağ: {exc}"
    if r.status_code != 200:
        return [], f"AliExpress HTTP {r.status_code}: {r.text[:240]}"
    try:
        body = r.json()
    except ValueError:
        return [], "AliExpress: JSON çözülemedi"

    err = ""
    if isinstance(body, dict):
        err_obj = body.get("error_response")
        if isinstance(err_obj, dict):
            err = str(err_obj.get("msg") or err_obj.get("code") or "")

    rsp = None
    if isinstance(body, dict):
        rsp = body.get("aliexpress_ds_text_search_response")
    if not isinstance(rsp, dict):
        return [], f"AliExpress: beklenmeyen yanıt ({err or repr(body)[:200]})"

    data = rsp.get("data")
    if not isinstance(data, dict):
        return [], f"AliExpress: data yok ({err})"

    products = data.get("products")
    if not isinstance(products, list):
        return [], f"AliExpress: ürün listesi yok ({err})"

    rows: list[dict[str, Any]] = []
    for p in products:
        if not isinstance(p, dict):
            continue
        title = str(p.get("product_title") or p.get("title") or "Ürün").strip()[:240]
        try:
            price_val = float(p.get("target_sale_price") or p.get("sale_price") or 0)
        except (TypeError, ValueError):
            continue
        if price_val <= 0:
            continue
        cur = str(p.get("target_sale_price_currency") or p.get("currency_code") or "USD").upper()[:8]
        pid = str(p.get("product_id") or p.get("item_id") or "")[:32]
        rows.append(
            {
                "name": title,
                "price": price_val,
                "in_stock": True,
                "id": pid or "ae-live",
                "currency": cur,
                "extra": {"source": "live", "marketplace": "aliexpress"},
            }
        )
    if not rows:
        return [], f"AliExpress: eşleşen satır yok ({err})".strip()
    return rows, None
