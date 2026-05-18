"""
PA-API / discovery JSON başarısız olduğunda tarayıcı benzeri GET ile HTML üzerinden ürün satırı.

`trendyol_resilience` başlıkları kullanılır (User-Agent rotasyonu, isteğe bağlı vekil).
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any
from urllib.parse import quote_plus

import requests

from ilim_assistant.hizir import trendyol_resilience as tr
from ilim_assistant.hizir.safe_request import SafeRequestConfig, sleep_human_interval

_LOG = logging.getLogger(__name__)

try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover
    BeautifulSoup = None  # type: ignore[misc, assignment]


def _timeout() -> float:
    try:
        return float(os.environ.get("HIZIR_HTTP_TIMEOUT", "25"))
    except ValueError:
        return 25.0


def _retail_headers(*, seed: str, referer: str, attempt: int = 1) -> dict[str, str]:
    h = dict(tr.trendyol_browser_headers(seed=seed, attempt=attempt))
    h["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
    h["Referer"] = referer
    h["Sec-Fetch-Site"] = "same-origin"
    h["Sec-Fetch-Mode"] = "navigate"
    h["Sec-Fetch-Dest"] = "document"
    h["Sec-Fetch-User"] = "?1"
    h["Upgrade-Insecure-Requests"] = "1"
    return h


def fetch_amazon_search_html(
    query: str,
    *,
    limit: int = 8,
    host: str = "www.amazon.com.tr",
    currency: str = "TRY",
) -> tuple[list[dict[str, Any]], str | None]:
    """Amazon arama sonuç sayfası — PA-API yokken veya boş dönüşte."""
    if BeautifulSoup is None:
        return [], "Amazon HTML: beautifulsoup4 kurulu değil (pip install beautifulsoup4)."
    q = (query or "").strip() or "ürün"
    sleep_human_interval(SafeRequestConfig.from_env())
    url = f"https://{host}/s?k={quote_plus(q)}"
    proxies = tr.trendyol_requests_proxies()
    try:
        r = requests.get(
            url,
            headers=_retail_headers(seed=q, referer=f"https://{host}/"),
            timeout=_timeout(),
            proxies=proxies,
        )
    except requests.RequestException as exc:
        return [], f"Amazon HTML ağ: {exc}"
    if r.status_code != 200:
        return [], f"Amazon HTML HTTP {r.status_code}"
    soup = BeautifulSoup(r.text, "html.parser")
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for card in soup.select('div[data-component-type="s-search-result"]'):
        if len(rows) >= limit:
            break
        asin = (card.get("data-asin") or "").strip()
        if not asin or asin == "B000000000":
            continue
        title_el = card.select_one("h2 a span, h2 .a-text-normal")
        title = title_el.get_text(strip=True) if title_el else ""
        if not title:
            continue
        whole = card.select_one("span.a-price-whole")
        frac = card.select_one("span.a-price-fraction")
        price: float | None = None
        if whole:
            ws = whole.get_text(strip=True).replace(".", "").replace(",", "")
            fs = frac.get_text(strip=True) if frac else "0"
            try:
                price = float(f"{ws}.{fs}".replace("..", "."))
            except ValueError:
                price = None
        if price is None or price <= 0:
            continue
        img_el = card.select_one("img.s-image")
        img_u = img_el.get("src") if img_el else None
        row: dict[str, Any] = {
            "name": title[:240],
            "price": price,
            "in_stock": True,
            "id": asin,
            "currency": currency[:8],
            "extra": {"source": "html_scrape", "asin": asin, "amazon_host": host},
        }
        if isinstance(img_u, str) and img_u.startswith("http"):
            row["image"] = img_u.strip()[:900]
        key = asin
        if key in seen:
            continue
        seen.add(key)
        rows.append(row)
    if not rows:
        return [], "Amazon HTML: arama kartı ayrıştırılamadı (sayfa yapısı değişmiş olabilir)."
    _LOG.info("Amazon HTML fallback: %s satır (%s)", len(rows), host)
    return rows[:limit], None


def fetch_trendyol_next_data_html(query: str, *, limit: int = 8) -> tuple[list[dict[str, Any]], str | None]:
    """Trendyol SR sayfası — __NEXT_DATA__ içinden ürün listesi."""
    q = (query or "").strip() or "ürün"
    sleep_human_interval(SafeRequestConfig.from_env())
    url = f"https://www.trendyol.com/sr?q={quote_plus(q)}"
    proxies = tr.trendyol_requests_proxies()
    try:
        r = requests.get(
            url,
            headers=_retail_headers(seed=q, referer="https://www.trendyol.com/"),
            timeout=_timeout(),
            proxies=proxies,
        )
    except requests.RequestException as exc:
        return [], f"Trendyol HTML ağ: {exc}"
    if r.status_code != 200:
        return [], f"Trendyol HTML HTTP {r.status_code}"
    m = re.search(
        r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>(?P<j>\{.*?\})</script>',
        r.text,
        re.DOTALL,
    )
    if not m:
        return [], "Trendyol HTML: __NEXT_DATA__ bulunamadı."
    try:
        data = json.loads(m.group("j"))
    except json.JSONDecodeError:
        return [], "Trendyol HTML: __NEXT_DATA__ JSON çözülemedi."
    products: list[Any] = []
    stack = [data]
    while stack:
        o = stack.pop()
        if isinstance(o, dict):
            if isinstance(o.get("products"), list) and o["products"]:
                products = o["products"]
                break
            for v in o.values():
                if isinstance(v, (dict, list)):
                    stack.append(v)
        elif isinstance(o, list):
            for v in o:
                if isinstance(v, (dict, list)):
                    stack.append(v)
    rows: list[dict[str, Any]] = []
    for it in products[: max(limit * 3, 20)]:
        if len(rows) >= limit:
            break
        if not isinstance(it, dict):
            continue
        name = str(it.get("name") or it.get("brand") or "").strip()
        if not name:
            continue
        price = None
        for pk in ("price", "discountedPrice", "sellingPrice"):
            pv = it.get(pk)
            if isinstance(pv, dict):
                pv = pv.get("value") or pv.get("text")
            try:
                if pv is not None:
                    price = float(pv)
                    break
            except (TypeError, ValueError):
                continue
        if price is None or price <= 0:
            continue
        pid = str(it.get("id") or it.get("contentId") or it.get("productId") or "")[:80]
        img_u: str | None = None
        im = it.get("image") or it.get("images")
        if isinstance(im, str) and im.startswith("http"):
            img_u = im
        elif isinstance(im, dict):
            u = im.get("url") or im.get("imageUrl")
            if isinstance(u, str) and u.startswith("http"):
                img_u = u
        row: dict[str, Any] = {
            "name": name[:240],
            "price": float(price),
            "in_stock": True,
            "id": pid or "ty-html",
            "currency": "TRY",
            "extra": {"source": "html_scrape"},
        }
        if img_u:
            row["image"] = img_u[:900]
        rows.append(row)
    if not rows:
        return [], "Trendyol HTML: ürün listesi çıkarılamadı."
    _LOG.info("Trendyol HTML fallback: %s satır", len(rows))
    return rows[:limit], None


def fetch_hepsiburada_search_html(query: str, *, limit: int = 8) -> tuple[list[dict[str, Any]], str | None]:
    """Hepsiburada arama — ürün kartı linkleri ve metinden kaba fiyat."""
    if BeautifulSoup is None:
        return [], "Hepsiburada HTML: beautifulsoup4 kurulu değil."
    q = (query or "").strip() or "ürün"
    sleep_human_interval(SafeRequestConfig.from_env())
    url = f"https://www.hepsiburada.com/ara?q={quote_plus(q)}"
    proxies = tr.trendyol_requests_proxies()
    try:
        r = requests.get(
            url,
            headers=_retail_headers(seed=q, referer="https://www.hepsiburada.com/"),
            timeout=_timeout(),
            proxies=proxies,
        )
    except requests.RequestException as exc:
        return [], f"Hepsiburada HTML ağ: {exc}"
    if r.status_code != 200:
        return [], f"Hepsiburada HTML HTTP {r.status_code}"
    soup = BeautifulSoup(r.text, "html.parser")
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for a in soup.select('a[href*="-p-"]'):
        if len(rows) >= limit:
            break
        href = (a.get("href") or "").strip()
        if not href or "-p-" not in href:
            continue
        if not href.startswith("http"):
            href = "https://www.hepsiburada.com" + href
        title = a.get_text(strip=True)[:240]
        if len(title) < 6:
            continue
        m = re.search(r"-p-(HBCV?\d+|[A-Z0-9]+)", href, re.I)
        pid = m.group(1) if m else href[-40:]
        if pid in seen:
            continue
        price = None
        parent = a.find_parent("li") or a.find_parent("div")
        if parent:
            t = parent.get_text(" ", strip=True)
            pm = re.search(r"([\d]{1,3}(?:\.\d{3})*(?:,\d{2})?)\s*TL", t)
            if pm:
                raw = pm.group(1).replace(".", "").replace(",", ".")
                try:
                    price = float(raw)
                except ValueError:
                    price = None
        if price is None or price <= 0:
            continue
        seen.add(pid)
        rows.append(
            {
                "name": title,
                "price": price,
                "in_stock": True,
                "id": pid[:80],
                "currency": "TRY",
                "url": href[:900],
                "extra": {"source": "html_scrape"},
            }
        )
    if not rows:
        return [], "Hepsiburada HTML: ürün satırı çıkarılamadı."
    _LOG.info("Hepsiburada HTML fallback: %s satır", len(rows))
    return rows[:limit], None
