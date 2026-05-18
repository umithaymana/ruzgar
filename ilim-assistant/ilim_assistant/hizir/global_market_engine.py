"""
Global pazar motoru — aynı bölge içi kıyaslama (lojistik koruma).

- Yerel döngü (TR): Trendyol + Amazon TR (aynı para: TRY).
- Global döngüler: US / GB / DE içinde Amazon + eBay (+ isteğe bağlı AliExpress), bölgeler arası
  gönderim maliyeti hesaba katılmaz; yalnızca aynı `loop_id` içindeki platformlar eşlenir.
"""

from __future__ import annotations

import os
import re
from collections import Counter
from difflib import SequenceMatcher
from typing import Any

from ilim_assistant.hizir import market_live as ml

_LOGITECH_MOUSE_Q = re.compile(r"logitech\s+mouse\b", re.I)

# Wikimedia Commons — vitrin / CSP (upload.wikimedia.org) ile uyumlu demo görselleri
_DEMO_IMG_LOGITECH_G502 = (
    "https://upload.wikimedia.org/wikipedia/commons/thumb/4/49/Logitech_G502_HERO.jpg/320px-Logitech_G502_HERO.jpg"
)
_DEMO_IMG_LOGITECH_G203 = (
    "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b8/Logitech-G203-PRODIGY.jpg/320px-Logitech-G203-PRODIGY.jpg"
)
_DEMO_IMG_USB_C_PLUG = (
    "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4c/USB-C.jpg/320px-USB-C.jpg"
)
_DEMO_IMG_USB_ADAPTER = (
    "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/HDMI-usb-c-adapter.jpg/320px-HDMI-usb-c-adapter.jpg"
)
_DEMO_IMG_ESPRESSO = (
    "https://upload.wikimedia.org/wikipedia/commons/thumb/1/16/Coffee_machine_espresso.jpg/320px-Coffee_machine_espresso.jpg"
)
_DEMO_IMG_COFFEE_BEANS = (
    "https://upload.wikimedia.org/wikipedia/commons/thumb/4/45/A_small_cup_of_coffee.JPG/320px-A_small_cup_of_coffee.JPG"
)


def _row_from_listing(x: Any) -> dict[str, Any]:
    """ProductListing → pazar satırı (mock yolunda görsel/url extra alanları korunur)."""
    row: dict[str, Any] = {
        "name": str(getattr(x, "product_name", "") or "")[:240],
        "price": float(getattr(x, "price", 0) or 0),
        "in_stock": bool(getattr(x, "in_stock", True)),
        "id": str(getattr(x, "external_id", "") or "")[:80],
        "currency": str(getattr(x, "currency", "TRY") or "TRY")[:8],
    }
    ex = getattr(x, "extra", None)
    if not isinstance(ex, dict):
        ex = {}
    for k in ("image", "image_url", "thumbnail", "url"):
        v = ex.get(k)
        if isinstance(v, str) and v.strip().lower().startswith(("http://", "https://")):
            if k == "image_url":
                row["image"] = v.strip()[:900]
            else:
                row[k] = v.strip()[:900]
    return row


def _static_logitech_us_demo_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Sabit piyasa bandı (USD) — yalnızca demo; gerçek API gelince devre dışı kalır."""
    title = "Logitech G502 LIGHTSPEED Wireless Gaming Mouse"
    amazon = [
        {
            "name": title,
            "price": 55.0,
            "in_stock": True,
            "id": "STATIC-LIVE-AZ-US-001",
            "currency": "USD",
            "image": _DEMO_IMG_LOGITECH_G502,
            "url": "https://www.amazon.com/s?k=logitech+g502+wireless+gaming+mouse",
            "extra": {"source": "static_live", "note": "Demo ~55 USD Amazon US bandı"},
        }
    ]
    ebay = [
        {
            "name": title,
            "price": 35.0,
            "in_stock": True,
            "id": "STATIC-LIVE-EB-US-001",
            "currency": "USD",
            "image": _DEMO_IMG_LOGITECH_G203,
            "url": "https://www.ebay.com/sch/i.html?_nkw=logitech+g502+lightspeed",
            "extra": {"source": "static_live", "note": "Demo ~35 USD eBay US bandı"},
        }
    ]
    return amazon, ebay


def _inject_static_logitech_us_if_needed(
    q: str,
    loops: dict[str, dict[str, list[dict[str, Any]]]],
    errors: dict[str, str],
    sel: frozenset[str] | None = None,
) -> list[str]:
    if os.environ.get("HIZIR_STATIC_LIVE_LOGITECH_MOUSE", "1").strip().lower() in (
        "0",
        "false",
        "no",
        "off",
    ):
        return []
    if not _LOGITECH_MOUSE_Q.search((q or "").strip()):
        return []
    if sel is not None and not ({"amazon_us", "ebay"} <= sel):
        return []
    us = loops.get("global_us") or {}
    am = us.get("amazon") or []
    eb = us.get("ebay") or []
    if am or eb:
        return []
    am2, eb2 = _static_logitech_us_demo_rows()
    loops.setdefault("global_us", {"amazon": [], "ebay": [], "aliexpress": []})
    loops["global_us"]["amazon"] = am2
    loops["global_us"]["ebay"] = eb2
    errors["static_live_demo_us_mouse"] = (
        "Statik canlı demo: Amazon 55 USD / eBay 35 USD (Logitech Mouse). "
        "PA-API ve eBay OAuth tanımlandığında ve listeler dolunca otomatik kapanır "
        "(HIZIR_STATIC_LIVE_LOGITECH_MOUSE=0 ile de kapatılabilir)."
    )
    return ["global_us:logitech_mouse_static_live"]


_USB_HUB_Q = re.compile(r"usb\s*c\s*hub", re.I)


def _static_usb_hub_us_demo_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    title = "Anker USB C Hub 7-in-1 4K HDMI Ethernet"
    amazon = [
        {
            "name": title,
            "price": 48.0,
            "in_stock": True,
            "id": "STATIC-USB-AZ-1",
            "currency": "USD",
            "image": _DEMO_IMG_USB_C_PLUG,
            "url": "https://www.amazon.com/s?k=anker+usb+c+hub+7+in+1",
            "extra": {"source": "static_live", "note": "Demo USB hub Amazon US"},
        }
    ]
    ebay = [
        {
            "name": title,
            "price": 29.0,
            "in_stock": True,
            "id": "STATIC-USB-EB-1",
            "currency": "USD",
            "image": _DEMO_IMG_USB_ADAPTER,
            "url": "https://www.ebay.com/sch/i.html?_nkw=anker+usb+c+hub",
            "extra": {"source": "static_live", "note": "Demo USB hub eBay US"},
        }
    ]
    return amazon, ebay


def _inject_static_usb_hub_us_if_needed(
    q: str,
    loops: dict[str, dict[str, list[dict[str, Any]]]],
    errors: dict[str, str],
    sel: frozenset[str] | None = None,
) -> list[str]:
    if os.environ.get("HIZIR_STATIC_LIVE_USB_HUB_US", "1").strip().lower() in (
        "0",
        "false",
        "no",
        "off",
    ):
        return []
    if not _USB_HUB_Q.search((q or "").strip()):
        return []
    if sel is not None and not ({"amazon_us", "ebay"} <= sel):
        return []
    us = loops.get("global_us") or {}
    if (us.get("amazon") or []) or (us.get("ebay") or []):
        return []
    am2, eb2 = _static_usb_hub_us_demo_rows()
    loops.setdefault("global_us", {"amazon": [], "ebay": [], "aliexpress": []})
    loops["global_us"]["amazon"] = am2
    loops["global_us"]["ebay"] = eb2
    errors["static_live_demo_us_usb_hub"] = (
        "Statik canlı demo: USB C Hub (Amazon/eBay US). "
        "HIZIR_STATIC_LIVE_USB_HUB_US=0 ile kapatılabilir."
    )
    return ["global_us:usb_hub_static_live"]


_KAHVE_Q = re.compile(r"kahve\s+makinesi", re.I)


def _static_kahve_tr_demo_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    base = "Philips 3200 Serisi Espresso ve Americano Makinesi"
    trendyol = [
        {
            "name": base,
            "price": 11800.0,
            "in_stock": True,
            "id": "STATIC-KAHVE-TY",
            "currency": "TRY",
            "image": _DEMO_IMG_ESPRESSO,
            "url": "https://www.trendyol.com/sr?q=philips+3200+kahve",
            "extra": {"source": "static_live"},
        }
    ]
    amazon_tr = [
        {
            "name": base + " EP3246",
            "price": 14200.0,
            "in_stock": True,
            "id": "STATIC-KAHVE-AM",
            "currency": "TRY",
            "image": _DEMO_IMG_COFFEE_BEANS,
            "url": "https://www.amazon.com.tr/s?k=philips+3200",
            "extra": {"source": "static_live"},
        }
    ]
    return trendyol, amazon_tr


def _inject_static_kahve_tr_if_needed(
    q: str,
    loops: dict[str, dict[str, list[dict[str, Any]]]],
    errors: dict[str, str],
    sel: frozenset[str] | None = None,
) -> list[str]:
    if os.environ.get("HIZIR_STATIC_LIVE_KAHVE_TR", "1").strip().lower() in (
        "0",
        "false",
        "no",
        "off",
    ):
        return []
    if not _KAHVE_Q.search((q or "").strip()):
        return []
    if sel is not None and not ({"trendyol", "amazon_tr"} <= sel):
        return []
    tr = loops.get("yerel_tr") or {}
    if (tr.get("trendyol") or []) or (tr.get("amazon_tr") or []):
        return []
    t2, a2 = _static_kahve_tr_demo_rows()
    loops.setdefault("yerel_tr", {"trendyol": [], "amazon_tr": [], "hepsiburada": []})
    loops["yerel_tr"]["trendyol"] = t2
    loops["yerel_tr"]["amazon_tr"] = a2
    errors["static_live_demo_tr_kahve"] = (
        "Statik TR demo: Kahve makinesi (Trendyol / Amazon TR). "
        "HIZIR_STATIC_LIVE_KAHVE_TR=0 ile kapatılabilir."
    )
    return ["yerel_tr:kahve_static_live"]


def _lim(n: int) -> int:
    return max(1, min(int(n), 10))


ALL_PAZAR_KANALLARI: tuple[str, ...] = (
    "trendyol",
    "amazon_tr",
    "hepsiburada",
    "amazon_us",
    "amazon_gb",
    "amazon_de",
    "ebay",
    "aliexpress",
)


def normalize_pazar_kanallari(channels: list[str] | None) -> frozenset[str]:
    if channels is None:
        return frozenset(ALL_PAZAR_KANALLARI)
    got = frozenset(str(c).strip().lower() for c in channels if str(c).strip())
    valid = frozenset(x for x in got if x in ALL_PAZAR_KANALLARI)
    return valid


def sorted_listings_price_asc(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def _k(r: dict[str, Any]) -> tuple[float, str]:
        try:
            p = float(r.get("price"))
        except (TypeError, ValueError):
            p = 1e15
        return (p, str(r.get("name") or ""))

    return sorted(rows, key=_k)


def aktif_kanallar_meta(sel: frozenset[str]) -> list[dict[str, str]]:
    labels: dict[str, str] = {
        "trendyol": "Trendyol",
        "amazon_tr": "Amazon TR",
        "hepsiburada": "Hepsiburada",
        "amazon_us": "Amazon US",
        "amazon_gb": "Amazon UK",
        "amazon_de": "Amazon DE",
        "ebay": "eBay",
        "aliexpress": "AliExpress",
    }
    return [{"id": k, "label": labels[k]} for k in ALL_PAZAR_KANALLARI if k in sel]


def _loop_bolge_label(loop_id: str) -> str:
    return {
        "yerel_tr": "Yerel (TR)",
        "global_us": "Global (US)",
        "global_gb": "Global (UK)",
        "global_de": "Global (DE)",
    }.get(loop_id, loop_id)


def _pazar_yeri_label(loop_id: str, channel: str) -> str:
    if loop_id == "yerel_tr":
        if channel == "trendyol":
            return "Trendyol"
        if channel == "amazon_tr":
            return "Amazon TR"
        if channel == "hepsiburada":
            return "Hepsiburada"
    if channel == "amazon":
        if loop_id == "global_us":
            return "Amazon US"
        if loop_id == "global_gb":
            return "Amazon UK"
        if loop_id == "global_de":
            return "Amazon DE"
    if channel == "ebay":
        if loop_id == "global_us":
            return "eBay US"
        if loop_id == "global_gb":
            return "eBay UK"
        if loop_id == "global_de":
            return "eBay DE"
    if channel == "aliexpress":
        return "AliExpress"
    return channel


def _sc_norm(s: str) -> str:
    t = re.sub(r"[^\w\s\u00c0-\u024f]", " ", (s or "").lower(), flags=re.UNICODE)
    return re.sub(r"\s+", " ", t).strip()


def _approx_sort_eur(price: float, currency: str) -> float:
    """Kaba sıralama birimi (yalnızca vitrin sırası için)."""
    c = (currency or "TRY").upper()
    if c in ("TRY", "TL"):
        return float(price) / 37.0
    if c == "USD":
        return float(price) * 0.92
    if c == "GBP":
        return float(price) * 1.17
    if c == "EUR":
        return float(price)
    return float(price)


def _shipping_hint(loop_id: str) -> str:
    if loop_id == "yerel_tr":
        return "İlan fiyatı; kargo satıcı / kampanyaya göre dahil veya ayrı olabilir."
    return "İlan fiyatı; kargo çoğu pazarda ayrı veya ücretsiz gösterilir — satıcı sayfasında doğrulayın."


def _flatten_market_rows(loops: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not isinstance(loops, dict):
        return out
    for loop_id, bucket in loops.items():
        lid = str(loop_id)
        if not isinstance(bucket, dict):
            continue
        bolge = _loop_bolge_label(lid)
        for ch in ("trendyol", "amazon_tr", "hepsiburada", "amazon", "ebay", "aliexpress"):
            rows = bucket.get(ch)
            if not isinstance(rows, list):
                continue
            label = _pazar_yeri_label(lid, ch)
            for r in rows:
                if not isinstance(r, dict):
                    continue
                row = dict(r)
                row["_loop_id"] = lid
                row["_channel"] = ch
                row["pazar_yeri"] = label
                row["bolge"] = bolge
                out.append(row)
    return out


def _build_search_compare(
    loops: dict[str, Any],
    query: str,
    *,
    scan_mode: str,
) -> dict[str, Any]:
    empty = {"mode": "otomatik_arbitraj", "flat": [], "groups": []}
    if scan_mode != "fiyat_dedektifi":
        return dict(empty)
    flat = _flatten_market_rows(loops)
    qn = _sc_norm(query)
    priced: list[dict[str, Any]] = []
    for row in flat:
        if not bool(row.get("in_stock", True)):
            continue
        try:
            p = float(row.get("price"))
        except (TypeError, ValueError):
            continue
        if p <= 0:
            continue
        cur = str(row.get("currency") or "TRY").strip().upper()[:8] or "TRY"
        row["price_sort_eur"] = round(_approx_sort_eur(p, cur), 6)
        row["kargo_notu"] = _shipping_hint(str(row.get("_loop_id") or ""))
        nm = _sc_norm(str(row.get("name") or ""))
        sim = float(SequenceMatcher(None, nm, qn).ratio()) if qn and nm else 0.0
        if sim >= 0.38:
            row["grup_etiketi"] = (query or "Sorgu").strip()[:56] or "Sorgu"
        else:
            parts = [x for x in nm.split() if len(x) > 2][:4]
            row["grup_etiketi"] = (" ".join(parts).title()[:56] if parts else "Benzer ürünler")
        priced.append(row)

    priced.sort(key=lambda x: (float(x.get("price_sort_eur") or 0.0), str(x.get("name") or "")))
    for i, row in enumerate(priced):
        row["lider_fiyat"] = bool(i == 0)

    groups: list[dict[str, Any]] = []
    if priced:
        cnt = Counter(str(x.get("grup_etiketi") or "") for x in priced)
        groups = [{"grup_etiketi": k, "adet": v} for k, v in cnt.most_common(16) if k]

    return {"mode": "fiyat_dedektifi", "flat": priced, "groups": groups, "sorgu": (query or "")[:200]}


def build_global_market_listings(
    query: str,
    *,
    limit: int = 8,
    scan_mode: str = "otomatik_arbitraj",
    channels: list[str] | None = None,
) -> dict[str, Any]:
    """
    `hizir_market_listings` ve UniversalScraper için tek JSON gövdesi.

    Dönüş şeması:
      - trendyol / amazon: TR aynası (geriye uyumluluk).
      - loops: yerel_tr (trendyol, amazon_tr, hepsiburada), global_us, global_gb, global_de.
      - aktif_kanallar: vitrin başlığı için seçili kanal meta listesi.
      - search_compare: Fiyat Dedektifi modunda seçilen kanallar, ucuzdan pahalıya sıralı.
      - scan_mode: otomatik_arbitraj | fiyat_dedektifi
    """
    q = (query or "").strip() or "ürün"
    sm = (scan_mode or "otomatik_arbitraj").strip()
    if sm not in ("otomatik_arbitraj", "fiyat_dedektifi"):
        sm = "otomatik_arbitraj"
    lim = _lim(limit)
    live = not ml.use_mock_marketplace()
    sel = normalize_pazar_kanallari(channels)
    errors: dict[str, str] = {}
    loops: dict[str, dict[str, list[dict[str, Any]]]] = {}

    ty_rows: list[dict[str, Any]] = []
    am_tr_rows: list[dict[str, Any]] = []
    hb_rows: list[dict[str, Any]] = []

    if live:
        if "trendyol" in sel:
            ty_rows, e1 = ml.fetch_trendyol_live(q, limit=lim)
            if e1:
                errors["trendyol_tr"] = e1
            ty_rows = sorted_listings_price_asc(ty_rows)
        if "amazon_tr" in sel:
            am_tr_rows, e2 = ml.fetch_amazon_live(q, limit=lim, country_code="TR")
            if e2:
                errors["amazon_tr"] = e2
            am_tr_rows = sorted_listings_price_asc(am_tr_rows)
        if "hepsiburada" in sel:
            hb_rows, ehb = ml.fetch_hepsiburada_live(q, limit=lim)
            if ehb:
                errors["hepsiburada_tr"] = ehb
            hb_rows = sorted_listings_price_asc(hb_rows)
    else:
        from ilim_assistant.hizir.scraper import AmazonScraperScaffold, TrendyolScraperScaffold

        ty_sc = TrendyolScraperScaffold()
        am_sc = AmazonScraperScaffold()
        if "trendyol" in sel:
            ty_rows = sorted_listings_price_asc(
                [_row_from_listing(x) for x in ty_sc.fetch_listings(q, limit=lim)]
            )
        if "amazon_tr" in sel:
            am_tr_rows = sorted_listings_price_asc(
                [_row_from_listing(x) for x in am_sc.fetch_listings(q, limit=lim)]
            )

    loops["yerel_tr"] = {"trendyol": ty_rows, "amazon_tr": am_tr_rows, "hepsiburada": hb_rows}

    ae_shared: list[dict[str, Any]] = []
    if live and "aliexpress" in sel:
        ae_shared, ae_err = ml.fetch_aliexpress_live(q, limit=min(lim, 8))
        if ae_err:
            errors["aliexpress"] = ae_err
        ae_shared = sorted_listings_price_asc(list(ae_shared))

    region_specs: list[tuple[str, str, str, str]] = [
        ("global_us", "US", "EBAY_US", "USD"),
        ("global_gb", "GB", "EBAY_GB", "GBP"),
        ("global_de", "DE", "EBAY_DE", "EUR"),
    ]
    loop_am_key = {"global_us": "amazon_us", "global_gb": "amazon_gb", "global_de": "amazon_de"}

    for loop_id, am_cc, ebay_mid, _cur_hint in region_specs:
        bucket: dict[str, list[dict[str, Any]]] = {"amazon": [], "ebay": [], "aliexpress": []}
        if live:
            need_am = loop_am_key.get(loop_id, "") in sel
            need_eb = "ebay" in sel
            need_ae = loop_id == "global_us" and "aliexpress" in sel

            if need_am:
                am_rows, am_err = ml.fetch_amazon_live(q, limit=lim, country_code=am_cc)
                if am_err:
                    errors[f"amazon_{am_cc.lower()}"] = am_err
                else:
                    bucket["amazon"] = sorted_listings_price_asc(am_rows)
            if need_eb:
                eb_rows, eb_err = ml.fetch_ebay_live(q, marketplace_id=ebay_mid, limit=lim)
                if eb_err:
                    errors[f"ebay_{ebay_mid.lower()}"] = eb_err
                else:
                    bucket["ebay"] = sorted_listings_price_asc(eb_rows)
            if need_ae:
                bucket["aliexpress"] = list(ae_shared)
        loops[loop_id] = bucket

    static_fill: list[str] = []
    if live:
        static_fill.extend(_inject_static_logitech_us_if_needed(q, loops, errors, sel))
        static_fill.extend(_inject_static_usb_hub_us_if_needed(q, loops, errors, sel))
        static_fill.extend(_inject_static_kahve_tr_if_needed(q, loops, errors, sel))

    return {
        "ok": True,
        "query": q,
        "scan_mode": sm,
        "live": live,
        "mock_marketplace": not live,
        "canli_pazar": live,
        "data_mode": "mock" if not live else "live",
        "errors": errors,
        "loops": loops,
        "trendyol": ty_rows,
        "amazon": am_tr_rows,
        "static_live_fill": static_fill,
        "search_compare": _build_search_compare(loops, q, scan_mode=sm),
        "aktif_kanallar": aktif_kanallar_meta(sel),
        "kanal_secimi": sorted(sel),
    }