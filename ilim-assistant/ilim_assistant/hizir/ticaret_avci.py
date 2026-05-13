"""Genel önbellekteki pazar keşif verisinden Ticari Fırsatlar + arbitraj üretimi (mock uyumlu)."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import Any

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
    for noise in ("(trendyol mock)", "(amazon mock)", "trendyol mock", "amazon mock", "— ekonomik", "— satıcı"):
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


def _short_product_title(name_ty: str, name_am: str) -> str:
    for raw in (name_ty, name_am):
        t = re.sub(r"\s*\([^)]*(?:mock|Mock)[^)]*\)\s*", " ", raw or "", flags=re.I)
        t = re.sub(r"\s+", " ", t).strip()
        if t:
            return t[:140]
    return "Eşleşen ürün"


def _extract_market_lists(
    veri: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str, bool]:
    """UniversalScraper çıktısından Trendyol / Amazon satırları ve canlı bayrak."""
    trendyol: list[dict[str, Any]] = []
    amazon: list[dict[str, Any]] = []
    query = ""
    live = False

    data = veri.get("data")
    if not isinstance(data, dict):
        return trendyol, amazon, query, live

    res = data.get("result")
    if not isinstance(res, dict):
        return trendyol, amazon, query, live

    ty = res.get("trendyol")
    am = res.get("amazon")
    if isinstance(ty, list):
        trendyol = [x for x in ty if isinstance(x, dict)]
    if isinstance(am, list):
        amazon = [x for x in am if isinstance(x, dict)]
    query = str(res.get("query") or "").strip()
    live = bool(res.get("live"))
    return trendyol, amazon, query, live


def _in_stock_row(row: dict[str, Any]) -> bool:
    return bool(row.get("in_stock", True))


def _price(row: dict[str, Any]) -> float | None:
    try:
        p = float(row.get("price"))
        if p > 0:
            return p
    except (TypeError, ValueError):
        pass
    return None


def _avg(prices: list[float]) -> float:
    return sum(prices) / len(prices) if prices else 0.0


def _fmt_tl(n: float) -> str:
    if n >= 1000:
        return f"{n:,.0f}".replace(",", ".") + " TL"
    s = f"{n:.2f}".rstrip("0").rstrip(".")
    return f"{s} TL"


def _platform_firsatlari(
    rows: list[dict[str, Any]],
    platform_label: str,
    *,
    query: str,
    seen: set[str],
    footnote: str = "",
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    priced = [(r, p) for r in rows if _in_stock_row(r) and (p := _price(r)) is not None]
    if len(priced) < 1:
        return out

    prices = [p for _, p in priced]
    avg = _avg(prices)
    min_p = min(prices)

    for r, price in priced:
        name = str(r.get("name") or "Ürün").strip() or "Ürün"
        key = f"F|{platform_label}|{_norm_name(name)}|{round(price, 2)}"
        if key in seen:
            continue

        below_avg = avg > 0 and price < avg * 0.999
        discount_vs_avg = ((avg - price) / avg * 100.0) if avg > 0 else 0.0
        steep = discount_vs_avg >= 20.0
        is_best = price <= min_p * 1.001 and len(priced) > 1

        if not (below_avg or steep or is_best):
            continue

        seen.add(key)
        pct = max(discount_vs_avg, 0.0)
        if steep:
            line = (
                f"🔥 FIRSAT: {name} — {platform_label}'da %{pct:.0f} civarı ortalama altı! "
                f"Fiyat: {_fmt_tl(price)}"
            )
        elif below_avg:
            line = (
                f"🔥 FIRSAT: {name} — {platform_label}'da ortalamanın altında. "
                f"Fiyat: {_fmt_tl(price)} (referans ort. {_fmt_tl(avg)})"
            )
        else:
            line = f"🔥 FIRSAT: {name} — {platform_label}'da en iyi fiyat bandında: {_fmt_tl(price)}"
        if footnote:
            line = f"{line} ({footnote})"

        out.append(
            {
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
            }
        )
    return out


def _arbitraj_satirlari(
    trendyol: list[dict[str, Any]],
    amazon: list[dict[str, Any]],
    *,
    query: str,
    seen: set[str],
    footnote: str = "",
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    ty_p = [(r, p) for r in trendyol if _in_stock_row(r) and (p := _price(r)) is not None]
    am_p = [(r, p) for r in amazon if _in_stock_row(r) and (p := _price(r)) is not None]

    for tr, p_ty in ty_p:
        name_ty = str(tr.get("name") or "")
        for ar, p_am in am_p:
            name_am = str(ar.get("name") or "")
            if _similar(name_ty, name_am) < 0.38:
                continue
            hi = max(p_ty, p_am)
            lo = min(p_ty, p_am)
            if hi <= 0 or (hi - lo) / hi < 0.08:
                continue

            cheap = "Trendyol" if p_ty < p_am else "Amazon"
            expensive = "Amazon" if p_ty < p_am else "Trendyol"
            gap_pct = (hi - lo) / hi * 100.0
            short = _short_product_title(name_ty, name_am)
            key = f"A|{_norm_name(short)}|{round(lo, 2)}|{round(hi, 2)}"
            if key in seen:
                continue
            seen.add(key)

            suffix = f"; {footnote}" if footnote else "; simülasyon verisi"
            line = (
                f"⚖️ ARBITRAJ: {short} — {cheap}'da {_fmt_tl(lo)}, {expensive}'da {_fmt_tl(hi)} "
                f"(~%{gap_pct:.0f} fiyat farkı{suffix})"
            )
            out.append(
                {
                    "tarih": _now_iso(),
                    "otomatik": True,
                    "tur": "ARBITRAJ",
                    "ozet_metin": line,
                    "urun_adi": short[:240],
                    "platform": f"{cheap} ↔ {expensive}",
                    "sorgu": query[:200],
                    "kaynak_fiyat": round(lo, 2),
                    "hedef_fiyat": round(hi, 2),
                    "potansiyel_kar": round(hi - lo, 2),
                    "ucuz_platform": cheap,
                    "pahali_platform": expensive,
                    "stok": bool(tr.get("in_stock")) and bool(ar.get("in_stock")),
                }
            )
    return out


def _build_auto_rows_from_girdiler(girdiler: list[dict[str, Any]], *, max_girdi: int = 8) -> list[dict[str, Any]]:
    pazar = [g for g in girdiler if isinstance(g, dict) and g.get("tip") == "pazar_keşif"]
    if not pazar:
        return []

    chunk = pazar[-max_girdi:]
    seen_set: set[str] = set()
    arbitraj: list[dict[str, Any]] = []
    firsat: list[dict[str, Any]] = []

    for g in reversed(chunk):
        veri = g.get("veri")
        if not isinstance(veri, dict):
            continue
        if not isinstance(veri.get("data"), dict):
            continue
        pid = veri.get("plugin_id")
        if pid and str(pid) != "marketplace_commercial":
            continue
        ty, am, q, live = _extract_market_lists(veri)
        if not ty and not am:
            continue
        fn = "canlı liste; satıcı sayfasında doğrulayın" if live else ""
        arbitraj.extend(_arbitraj_satirlari(ty, am, query=q, seen=seen_set, footnote=fn))
        firsat.extend(_platform_firsatlari(ty, "Trendyol", query=q, seen=seen_set, footnote=fn))
        firsat.extend(_platform_firsatlari(am, "Amazon", query=q, seen=seen_set, footnote=fn))

    arbitraj.sort(key=lambda r: -float(r.get("potansiyel_kar") or 0.0))
    firsat.sort(key=lambda r: -float(r.get("indirim_ortalama_yuzde") or r.get("potansiyel_kar") or 0.0))
    return arbitraj + firsat


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
    auto = _build_auto_rows_from_girdiler(girdiler)
    htc["firsatlar"] = auto + manual
    save_merkezi_bellek(doc, path=p)
    return doc
