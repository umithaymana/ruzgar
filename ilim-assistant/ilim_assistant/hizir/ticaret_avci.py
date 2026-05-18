"""Genel önbellekteki pazar keşif verisinden Ticari Fırsatlar + aynı bölge içi arbitraj üretimi."""

from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import Any
from urllib.parse import quote, quote_plus

from ilim_assistant.hizir.avci import HizirAvci
from ilim_assistant.hizir.bellek import (
    _genel_onbellek,
    _hizir_ticaret,
    load_merkezi_bellek,
    merkezi_bellek_path,
    save_merkezi_bellek,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm_name(s: str) -> str:
    t = (s or "").lower()
    for noise in (
        "trendyol mock",
        "amazon mock",
        "— ekonomik",
        "— satıcı",
    ):
        t = t.replace(noise, " ")
    t = re.sub(r"[^\w\s\u00c0-\u024f]", " ", t, flags=re.UNICODE)
    return re.sub(r"\s+", " ", t).strip()


def _similar(a: str, b: str) -> float:
    na, nb = _norm_name(a), _norm_name(b)
    if not na or not nb:
        return 0.0
    if na in nb or nb in na:
        return 0.72
    return float(SequenceMatcher(None, na, nb).ratio())


def _short_product_title(name_a: str, name_b: str) -> str:
    for raw in (name_a, name_b):
        t = re.sub(r"\s*\([^)]*(?:mock|Mock)[^)]*\)\s*", " ", raw or "", flags=re.I)
        t = re.sub(r"\s+", " ", t).strip()
        if t:
            return t[:140]
    return "Eşleşen ürün"


def _price(row: dict[str, Any]) -> float | None:
    try:
        p = float(row.get("price"))
        if p > 0:
            return p
    except (TypeError, ValueError):
        pass
    return None


def _currency(row: dict[str, Any], fallback: str) -> str:
    c = str(row.get("currency") or fallback or "TRY").strip().upper()[:8]
    return c or "TRY"


def _in_stock_row(row: dict[str, Any]) -> bool:
    return bool(row.get("in_stock", True))


def _avg(prices: list[float]) -> float:
    return sum(prices) / len(prices) if prices else 0.0


def _fmt_money(n: float, cur: str) -> str:
    cur = (cur or "TRY").upper()
    if cur == "TRY":
        if n >= 1000:
            return f"{n:,.0f}".replace(",", ".") + " TL"
        s = f"{n:.2f}".rstrip("0").rstrip(".")
        return f"{s} TL"
    s = f"{n:.2f}".rstrip("0").rstrip(".")
    return f"{s} {cur}"


def _row_image_url(row: dict[str, Any]) -> str | None:
    for k in ("image", "image_url", "thumbnail", "img"):
        v = row.get(k)
        if isinstance(v, str) and v.strip().lower().startswith(("http://", "https://")):
            return v.strip()[:900]
    ex = row.get("extra")
    if isinstance(ex, dict):
        for k in ("image", "image_url", "main_image", "thumbnail", "imageUrl"):
            v = ex.get(k)
            if isinstance(v, str) and v.strip().lower().startswith(("http://", "https://")):
                return v.strip()[:900]
    return None


def _placeholder_product_image(seed: str) -> str:
    """Dış görsel yoksa veya CSP dışı URL — data: SVG yer tutucu (picsum yerine)."""
    from urllib.parse import quote

    sym = abs(hash(seed)) % 900 + 100
    svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' width='120' height='120' viewBox='0 0 120 120'>"
        "<rect width='120' height='120' rx='12' fill='%23232a34'/>"
        "<rect x='30' y='34' width='60' height='44' rx='4' fill='none' stroke='%23788a9c' stroke-width='2'/>"
        "<circle cx='44' cy='50' r='4' fill='%23788a9c'/>"
        "<path d='M76 70 L50 50' stroke='%23788a9c' stroke-width='2'/>"
        f"<text x='60' y='104' text-anchor='middle' fill='%235c6b7c' font-size='11' font-family='system-ui,sans-serif'>{sym}</text>"
        "</svg>"
    )
    return "data:image/svg+xml;charset=utf-8," + quote(svg)


def _row_product_url(row: dict[str, Any], platform_label: str, bolge: str, short_title: str) -> str:
    """Satın alma / ürün sayfası URL'si; yoksa pazar arama fallback."""
    for k in ("url", "product_url", "link", "item_web_url"):
        v = row.get(k)
        if isinstance(v, str) and v.strip().lower().startswith(("http://", "https://")):
            return v.strip()[:900]
    ex = row.get("extra") if isinstance(row.get("extra"), dict) else {}
    pl = (platform_label or "").lower()
    bol = (bolge or "").lower()
    asin = str(ex.get("asin") or row.get("id") or "").strip()
    if "amazon" in pl and len(asin) == 10 and asin.upper().startswith("B"):
        host = "www.amazon.com"
        if "tr" in pl or "yerel" in bol:
            host = "www.amazon.com.tr"
        elif "uk" in bol or "global_gb" in bol or "gb" in bol:
            host = "www.amazon.co.uk"
        elif "de" in bol or "global_de" in bol:
            host = "www.amazon.de"
        return f"https://{host}/dp/{asin}"
    iid = str(row.get("id") or "").strip()
    if "ebay" in pl and iid and iid != "ebay-live":
        dom = "www.ebay.com"
        if "uk" in bol or "global_gb" in bol:
            dom = "www.ebay.co.uk"
        elif "de" in bol or "global_de" in bol:
            dom = "www.ebay.de"
        return f"https://{dom}/itm/{quote(iid, safe='')}"
    if "hepsiburada" in pl:
        u = str(row.get("url") or "").strip()
        if u.lower().startswith("http"):
            return u[:900]
        q = quote_plus((short_title or "ürün")[:120])
        return f"https://www.hepsiburada.com/ara?q={q}"
    if "trendyol" in pl:
        tid = str(row.get("id") or "").strip()
        if tid.isdigit():
            return f"https://www.trendyol.com/brand/isim-p-{tid}"
        q = quote_plus((short_title or "ürün")[:120])
        return f"https://www.trendyol.com/sr?q={q}"
    if "aliexpress" in pl:
        q = quote_plus((short_title or "product")[:120])
        return f"https://www.aliexpress.com/wholesale?SearchText={q}"
    q = quote_plus((short_title or "product")[:120])
    if "amazon" in pl:
        host = "www.amazon.com.tr" if "tr" in pl or "yerel" in bol else "www.amazon.com"
        return f"https://{host}/s?k={q}"
    if "ebay" in pl:
        dom = "www.ebay.com"
        if "uk" in bol or "global_gb" in bol:
            dom = "www.ebay.co.uk"
        return f"https://{dom}/sch/i.html?_nkw={q}"
    return f"https://www.google.com/search?q={q}"


def _vat_rate_for_currency(cur: str) -> float:
    c = (cur or "TRY").upper()
    if c in ("TRY", "TL"):
        try:
            return float(os.environ.get("HIZIR_TR_VAT_RATE", "0.20"))
        except ValueError:
            return 0.20
    try:
        return float(os.environ.get("HIZIR_GLOBAL_VAT_RATE", "0"))
    except ValueError:
        return 0.0


def _commission_rate() -> float:
    try:
        return float(os.environ.get("HIZIR_DEFAULT_SALE_COMMISSION", "0.15"))
    except ValueError:
        return 0.15


def _tool_result_from_veri(veri: dict[str, Any]) -> dict[str, Any] | None:
    data = veri.get("data")
    if not isinstance(data, dict):
        return None
    res = data.get("result")
    return res if isinstance(res, dict) else None


def _loops_bolge_label(loop_id: str) -> str:
    return {
        "yerel_tr": "Yerel (TR)",
        "global_us": "Global (US)",
        "global_gb": "Global (UK)",
        "global_de": "Global (DE)",
    }.get(loop_id, loop_id)


def _analyze_pair(lo: float, hi: float, currency: str) -> dict[str, Any]:
    vat = _vat_rate_for_currency(currency)
    hunter = HizirAvci(vat_rate=vat, shipping_cost=0.0)
    return hunter.analyze_opportunity(lo, hi, _commission_rate())


def _arbitraj_pairs(
    rows_a: list[dict[str, Any]],
    label_a: str,
    rows_b: list[dict[str, Any]],
    label_b: str,
    *,
    query: str,
    seen: set[str],
    bolge: str,
    default_currency: str,
    live: bool,
    sim_threshold: float = 0.36,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    a_p = [(r, p) for r in rows_a if _in_stock_row(r) and (p := _price(r)) is not None]
    b_p = [(r, p) for r in rows_b if _in_stock_row(r) and (p := _price(r)) is not None]

    for ra, p_a in a_p:
        for rb, p_b in b_p:
            cur_a = _currency(ra, default_currency)
            cur_b = _currency(rb, default_currency)
            if cur_a != cur_b:
                continue
            name_a = str(ra.get("name") or "")
            name_b = str(rb.get("name") or "")
            if _similar(name_a, name_b) < sim_threshold:
                continue
            hi = max(p_a, p_b)
            lo = min(p_a, p_b)
            if hi <= 0 or (hi - lo) / hi < 0.06:
                continue
            cheap_plat = label_a if p_a < p_b else label_b
            expensive_plat = label_b if p_a < p_b else label_a
            cheap_row = ra if p_a < p_b else rb
            exp_row = rb if p_a < p_b else ra
            analysis = _analyze_pair(lo, hi, cur_a)
            net_m = float(analysis.get("profit_margin_percent") or 0.0)
            net_k = float(analysis.get("net_profit") or 0.0)
            gap_pct = (hi - lo) / hi * 100.0
            short = _short_product_title(name_a, name_b)
            key = f"A|{bolge}|{_norm_name(short)}|{cur_a}|{round(lo, 2)}|{round(hi, 2)}"
            if key in seen:
                continue
            seen.add(key)

            teyit = "Canlı veri; satıcı sayfasında fiyat/stok teyidi önerilir." if live else "Geliştirici modu."
            line = (
                f"⚖️ ARBITRAJ | Bölge: {bolge} | {short} — {cheap_plat}: {_fmt_money(lo, cur_a)}, "
                f"{expensive_plat}: {_fmt_money(hi, cur_a)} | Brüt fark ~%{gap_pct:.0f} | "
                f"Tahmini net marj %{net_m:.1f} | Tahmini net kâr {_fmt_money(net_k, cur_a)} ({teyit})"
            )
            img_u = _row_image_url(cheap_row) or _row_image_url(exp_row) or _placeholder_product_image(short)
            kaynak_ad = str(cheap_row.get("name") or short)[:120]
            hedef_ad = str(exp_row.get("name") or short)[:120]
            satinal_url = _row_product_url(cheap_row, cheap_plat, bolge, short)
            out.append(
                {
                    "kart_id": key,
                    "tarih": _now_iso(),
                    "otomatik": True,
                    "tur": "ARBITRAJ",
                    "ozet_metin": line,
                    "urun_adi": short[:240],
                    "platform": f"{cheap_plat} ↔ {expensive_plat}",
                    "sorgu": query[:200],
                    "kaynak_fiyat": round(lo, 2),
                    "hedef_fiyat": round(hi, 2),
                    "potansiyel_kar": round(net_k, 2),
                    "brut_fiyat_farki": round(hi - lo, 2),
                    "ucuz_platform": cheap_plat,
                    "pahali_platform": expensive_plat,
                    "kaynak_urun_adi": kaynak_ad,
                    "hedef_urun_adi": hedef_ad,
                    "gorsel_url": img_u,
                    "satinal_url": satinal_url,
                    "stok": bool(ra.get("in_stock")) and bool(rb.get("in_stock")),
                    "bolge": bolge,
                    "para_birimi": cur_a,
                    "net_marj_yuzde": round(net_m, 2),
                    "avla_durumu": str(analysis.get("status") or ""),
                }
            )
    return out


def _fiyat_listesi_kartlari(
    res: dict[str, Any],
    *,
    query: str,
    seen: set[str],
) -> list[dict[str, Any]]:
    if str(res.get("scan_mode") or "") != "fiyat_dedektifi":
        return []
    sc = res.get("search_compare")
    if not isinstance(sc, dict) or sc.get("mode") != "fiyat_dedektifi":
        return []
    raw_flat = sc.get("flat")
    if not isinstance(raw_flat, list):
        return []
    prev_grup: str | None = None
    out: list[dict[str, Any]] = []
    for idx, row in enumerate(raw_flat):
        if not isinstance(row, dict):
            continue
        p = _price(row)
        if p is None:
            continue
        name = str(row.get("name") or "Ürün").strip() or "Ürün"
        py = str(row.get("pazar_yeri") or "Pazar").strip()
        bolge_l = str(row.get("bolge") or "").strip()
        cur = _currency(row, "TRY")
        rid = str(row.get("id") or idx)
        key = f"PFL|{py}|{_norm_name(name)}|{round(p, 4)}|{cur}|{rid}"
        if key in seen:
            continue
        seen.add(key)
        sat_url = _row_product_url(row, py, bolge_l, name)
        grup = str(row.get("grup_etiketi") or "").strip()
        yeni = bool(grup and grup != prev_grup)
        if grup:
            prev_grup = grup
        lider = bool(row.get("lider_fiyat"))
        kargo = str(row.get("kargo_notu") or "").strip()
        img_u = _row_image_url(row) or _placeholder_product_image(name[:80])
        line = f"🔎 Fiyat Dedektifi | {py} · {_fmt_money(p, cur)} — {kargo[:120]}"
        try:
            peur = float(row.get("price_sort_eur") or 0.0)
        except (TypeError, ValueError):
            peur = 0.0
        out.append(
            {
                "kart_id": key,
                "tarih": _now_iso(),
                "otomatik": True,
                "tur": "FIYAT_LISTESI",
                "ozet_metin": line[:400],
                "urun_adi": name[:240],
                "platform": py,
                "pazar_yeri": py,
                "sorgu": query[:200],
                "kaynak_fiyat": round(p, 2),
                "para_birimi": cur,
                "bolge": bolge_l,
                "gorsel_url": img_u,
                "satinal_url": sat_url,
                "kargo_notu": kargo[:300],
                "lider_fiyat": lider,
                "grup_etiketi": grup,
                "yeni_grup": yeni,
                "vitrin_sira": idx,
                "stok": bool(row.get("in_stock", True)),
                "potansiyel_kar": peur,
            }
        )
    return out


def _platform_firsatlari(
    rows: list[dict[str, Any]],
    platform_label: str,
    *,
    query: str,
    seen: set[str],
    bolge: str,
    default_currency: str,
    live: bool,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    priced = [(r, p) for r in rows if _in_stock_row(r) and (p := _price(r)) is not None]
    if len(priced) < 1:
        return out

    prices = [p for _, p in priced]
    avg = _avg(prices)
    min_p = min(prices)
    foot = "Canlı veri; mağaza teyidi." if live else "Geliştirici modu."

    for r, price in priced:
        name = str(r.get("name") or "Ürün").strip() or "Ürün"
        cur = _currency(r, default_currency)
        key = f"F|{bolge}|{platform_label}|{_norm_name(name)}|{round(price, 2)}"
        if key in seen:
            continue

        below_avg = avg > 0 and price < avg * 0.999
        discount_vs_avg = ((avg - price) / avg * 100.0) if avg > 0 else 0.0
        steep = discount_vs_avg >= 18.0
        is_best = price <= min_p * 1.001 and len(priced) > 1

        if not (below_avg or steep or is_best):
            continue

        seen.add(key)
        pct = max(discount_vs_avg, 0.0)
        img_u = _row_image_url(r) or _placeholder_product_image(name[:80])
        if steep:
            line = (
                f"🔥 FIRSAT | Bölge: {bolge} | {name} — {platform_label}: %{pct:.0f} civarı ortalama altı "
                f"({_fmt_money(price, cur)}; {foot})"
            )
        elif below_avg:
            line = (
                f"🔥 FIRSAT | Bölge: {bolge} | {name} — {platform_label}: ortalamanın altında "
                f"{_fmt_money(price, cur)} (ref. ort. {_fmt_money(avg, cur)}; {foot})"
            )
        else:
            line = (
                f"🔥 FIRSAT | Bölge: {bolge} | {name} — {platform_label}: en iyi fiyat bandı "
                f"{_fmt_money(price, cur)} ({foot})"
            )

        out.append(
            {
                "kart_id": key,
                "tarih": _now_iso(),
                "otomatik": True,
                "tur": "FIRSAT",
                "ozet_metin": line,
                "urun_adi": name[:240],
                "platform": platform_label,
                "sorgu": query[:200],
                "kaynak_fiyat": round(price, 2),
                "hedef_fiyat": round(avg, 2),
                "potansiyel_kar": round(max(avg - price, 0.0), 2),
                "indirim_ortalama_yuzde": round(pct, 1),
                "stok": bool(r.get("in_stock", True)),
                "bolge": bolge,
                "para_birimi": cur,
                "gorsel_url": img_u,
            }
        )
    return out


def _process_tool_result(
    res: dict[str, Any],
    *,
    seen: set[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    arbitraj: list[dict[str, Any]] = []
    firsat: list[dict[str, Any]] = []
    query = str(res.get("query") or "").strip()
    live = bool(res.get("live"))
    loops = res.get("loops")

    if isinstance(loops, dict) and loops:
        for loop_id, bucket in loops.items():
            if not isinstance(bucket, dict):
                continue
            bolge = _loops_bolge_label(loop_id)
            if loop_id == "yerel_tr":
                ty = [x for x in (bucket.get("trendyol") or []) if isinstance(x, dict)]
                am = [x for x in (bucket.get("amazon_tr") or []) if isinstance(x, dict)]
                hb = [x for x in (bucket.get("hepsiburada") or []) if isinstance(x, dict)]
                arbitraj.extend(
                    _arbitraj_pairs(ty, "Trendyol", am, "Amazon TR", query=query, seen=seen, bolge=bolge, default_currency="TRY", live=live)
                )
                if hb:
                    arbitraj.extend(
                        _arbitraj_pairs(ty, "Trendyol", hb, "Hepsiburada", query=query, seen=seen, bolge=bolge, default_currency="TRY", live=live, sim_threshold=0.30)
                    )
                    arbitraj.extend(
                        _arbitraj_pairs(am, "Amazon TR", hb, "Hepsiburada", query=query, seen=seen, bolge=bolge, default_currency="TRY", live=live, sim_threshold=0.30)
                    )
                firsat.extend(_platform_firsatlari(ty, "Trendyol", query=query, seen=seen, bolge=bolge, default_currency="TRY", live=live))
                firsat.extend(_platform_firsatlari(am, "Amazon TR", query=query, seen=seen, bolge=bolge, default_currency="TRY", live=live))
                if hb:
                    firsat.extend(_platform_firsatlari(hb, "Hepsiburada", query=query, seen=seen, bolge=bolge, default_currency="TRY", live=live))
            elif loop_id.startswith("global_"):
                cur_hint = {"global_us": "USD", "global_gb": "GBP", "global_de": "EUR"}.get(loop_id, "USD")
                amz = [x for x in (bucket.get("amazon") or []) if isinstance(x, dict)]
                eby = [x for x in (bucket.get("ebay") or []) if isinstance(x, dict)]
                aex = [x for x in (bucket.get("aliexpress") or []) if isinstance(x, dict)]
                arbitraj.extend(
                    _arbitraj_pairs(amz, "Amazon", eby, "eBay", query=query, seen=seen, bolge=bolge, default_currency=cur_hint, live=live, sim_threshold=0.32)
                )
                if aex:
                    arbitraj.extend(
                        _arbitraj_pairs(
                            amz,
                            "Amazon",
                            aex,
                            "AliExpress",
                            query=query,
                            seen=seen,
                            bolge=bolge,
                            default_currency=cur_hint,
                            live=live,
                            sim_threshold=0.28,
                        )
                    )
                    arbitraj.extend(
                        _arbitraj_pairs(
                            eby,
                            "eBay",
                            aex,
                            "AliExpress",
                            query=query,
                            seen=seen,
                            bolge=bolge,
                            default_currency=cur_hint,
                            live=live,
                            sim_threshold=0.28,
                        )
                    )
                firsat.extend(_platform_firsatlari(amz, "Amazon", query=query, seen=seen, bolge=bolge, default_currency=cur_hint, live=live))
                firsat.extend(_platform_firsatlari(eby, "eBay", query=query, seen=seen, bolge=bolge, default_currency=cur_hint, live=live))
                firsat.extend(_platform_firsatlari(aex, "AliExpress", query=query, seen=seen, bolge=bolge, default_currency=cur_hint, live=live))
        fiy = _fiyat_listesi_kartlari(res, query=query, seen=seen)
        return arbitraj, firsat, fiy

    # Geriye uyumluluk: yalnızca trendyol + amazon
    ty = [x for x in (res.get("trendyol") or []) if isinstance(x, dict)]
    am = [x for x in (res.get("amazon") or []) if isinstance(x, dict)]
    bolge = "Yerel (TR)"
    arbitraj.extend(_arbitraj_pairs(ty, "Trendyol", am, "Amazon TR", query=query, seen=seen, bolge=bolge, default_currency="TRY", live=live))
    firsat.extend(_platform_firsatlari(ty, "Trendyol", query=query, seen=seen, bolge=bolge, default_currency="TRY", live=live))
    firsat.extend(_platform_firsatlari(am, "Amazon TR", query=query, seen=seen, bolge=bolge, default_currency="TRY", live=live))
    fiy = _fiyat_listesi_kartlari(res, query=query, seen=seen)
    return arbitraj, firsat, fiy


def _build_auto_rows_from_girdiler(
    girdiler: list[dict[str, Any]],
    *,
    max_girdi: int = 8,
    skip_kart_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    pazar = [g for g in girdiler if isinstance(g, dict) and g.get("tip") == "pazar_keşif"]
    if not pazar:
        return []

    chunk = pazar[-max_girdi:]
    seen_set: set[str] = set()
    arbitraj: list[dict[str, Any]] = []
    firsat: list[dict[str, Any]] = []
    fiyat: list[dict[str, Any]] = []

    for g in reversed(chunk):
        veri = g.get("veri")
        if not isinstance(veri, dict):
            continue
        if not isinstance(veri.get("data"), dict):
            continue
        pid = veri.get("plugin_id")
        if pid and str(pid) != "marketplace_commercial":
            continue
        res = _tool_result_from_veri(veri)
        if not isinstance(res, dict):
            continue
        a, f, fy = _process_tool_result(res, seen=seen_set)
        arbitraj.extend(a)
        firsat.extend(f)
        fiyat.extend(fy)

    arbitraj.sort(key=lambda r: -float(r.get("potansiyel_kar") or 0.0))
    firsat.sort(key=lambda r: -float(r.get("indirim_ortalama_yuzde") or r.get("potansiyel_kar") or 0.0))
    out = fiyat + arbitraj + firsat
    sk = skip_kart_ids or set()
    if not sk:
        return out
    return [r for r in out if isinstance(r, dict) and str(r.get("kart_id") or "") not in sk]


def reconcile_ticaret_avci_firsatlar(path=None) -> dict[str, Any]:
    """
    `genel_onbellek` içindeki son pazar keşiflerinden otomatik fırsat satırları üretir;
    elle eklenmiş (otomatik olmayan) fırsatları korur.
    """
    p = path or merkezi_bellek_path()
    doc = load_merkezi_bellek(p)
    htc = _hizir_ticaret(doc)
    girdiler = _genel_onbellek(doc)["girdiler"]
    if not isinstance(girdiler, list):
        girdiler = []

    manual = [r for r in htc["firsatlar"] if isinstance(r, dict) and not r.get("otomatik")]
    meta = htc.setdefault("meta", {})
    if not isinstance(meta, dict):
        meta = {}
        htc["meta"] = meta
    raw_skip = meta.get("pas_gecildi")
    skip_ids = {str(x).strip() for x in (raw_skip if isinstance(raw_skip, list) else []) if str(x).strip()}
    auto = _build_auto_rows_from_girdiler(girdiler, skip_kart_ids=skip_ids)
    htc["firsatlar"] = auto + manual
    save_merkezi_bellek(doc, path=p)
    return doc
