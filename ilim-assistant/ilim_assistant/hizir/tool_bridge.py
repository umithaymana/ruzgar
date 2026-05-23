from __future__ import annotations

import json
import os
import re
from typing import Any

from ilim_assistant.hizir.bellek import (
    append_genel_onbellek_girdi,
    find_fresh_genel_girdi,
    find_hizir_firsat_summary_lines,
)
from ilim_assistant.hizir import pazar_context as pazar_ctx
from ilim_assistant.hizir.universal_scraper import UniversalScraper


def _maybe_append_margin_tool(uni: dict[str, Any], parts: list[str]) -> None:
    """İlk stoklu Trendyol / Amazon TR satırlarıyla hizir_analyze_opportunity çağrısı."""
    try:
        from ilim_assistant.hizir.tools import run_hizir_tool

        data = uni.get("data")
        if not isinstance(data, dict):
            return
        res = data.get("result")
        if not isinstance(res, dict):
            return
        loops = res.get("loops") if isinstance(res.get("loops"), dict) else {}
        yerel = loops.get("yerel_tr") if isinstance(loops.get("yerel_tr"), dict) else {}
        ty = yerel.get("trendyol") if isinstance(yerel.get("trendyol"), list) else res.get("trendyol") or []
        am = yerel.get("amazon_tr") if isinstance(yerel.get("amazon_tr"), list) else res.get("amazon") or []
        src = next((float(x["price"]) for x in ty if isinstance(x, dict) and x.get("in_stock")), None)
        tgt = next((float(x["price"]) for x in am if isinstance(x, dict) and x.get("in_stock")), None)
        if src is None or tgt is None:
            return
        comm = float(os.environ.get("HIZIR_DEFAULT_SALE_COMMISSION", "0.15"))
        out = run_hizir_tool(
            "hizir_analyze_opportunity",
            {
                "source_price": src,
                "target_price": tgt,
                "commission_rate": comm,
            },
        )
        parts.append(
            "=== Araç: hizir_analyze_opportunity (kaynak=ilk Trendyol, hedef=ilk Amazon TR) ===\n"
            + json.dumps(out, ensure_ascii=False, default=str)[:4000]
        )
    except Exception:
        return


def _komuta_pazar_tara(message: str) -> bool:
    low = (message or "").lower()
    if any(
        x in low
        for x in (
            "pazar yerini tara",
            "pazar yerlerini tara",
            "pazarı tara",
            "pazari tara",
            "pazar tara",
            "pazarları tara",
            "pazarlari tara",
        )
    ):
        return True
    return bool(_urun_tara_intent(message))


def _urun_tara_intent(message: str) -> bool:
    """«gereken ürünleri tara», «şu ürünleri tara» vb. — pazar adı şart değil."""
    raw = (message or "").strip()
    if len(raw) < 6:
        return False
    low = raw.lower()
    if re.search(r"ürün\w*\s+.{0,50}\s*tara", low):
        return True
    if re.search(r"tara\w*\s+.{0,40}\s*ürün", low):
        return True
    if re.search(r"\b(?:tara|tarayın|tarayalim|tarayalım|taramanı)\b", low) and any(
        x in low
        for x in (
            "ürün",
            "urun",
            "pazar",
            "fiyat",
            "stok",
            "trendyol",
            "amazon",
            "hepsiburada",
            "arbitraj",
            "dropship",
        )
    ):
        return True
    return False


def _norm_cache_key(message: str, kanallar: list[str] | None = None) -> str:
    t = re.sub(r"\s+", " ", (message or "").strip().lower())[:400]
    if kanallar:
        suf = "|ch:" + ",".join(sorted({str(x).strip().lower() for x in kanallar if str(x).strip()}))
        return (t + suf)[:480]
    return t


def _commercial_intent(message: str) -> bool:
    if _urun_tara_intent(message):
        return True
    low = (message or "").lower()
    if "trendyol" in low or "amazon" in low or "ebay" in low or "aliexpress" in low or "pazaryeri" in low or "pazar yeri" in low:
        return any(
            x in low
            for x in (
                "ucuz",
                "fiyat",
                "tl",
                "lira",
                "ne kadar",
                "ürün",
                "urun",
                "kulaklık",
                "kulaklik",
            )
        )
    if "en ucuz" in low and len((message or "").strip()) > 10:
        return True
    return False


def _flight_intent(message: str) -> bool:
    low = (message or "").lower()
    return any(
        x in low
        for x in (
            "uçuş",
            "ucus",
            "uçak bileti",
            "ucak bileti",
            "thy ",
            "pegasus",
            "flight ",
        )
    )


def build_dynamic_operasyon_context(
    message: str,
    *,
    weather_q: bool = False,
    has_live_weather_block: bool = False,
    mode_norm: str = "genel",
    pazar_kanallari: list[str] | None = None,
) -> str:
    """
    Merkezi bellek (önce) + gerekirse UniversalScraper / HIZIR tool çıktısı.
    Ana motor `user_payload` içine ekler.
    """
    if os.environ.get("RUZGAR_MERKEZI_BELLEK_TOOLS", "1").strip().lower() in (
        "0",
        "false",
        "no",
    ):
        return ""
    if mode_norm in frozenset({"ses", "okuma", "tercume", "uretim", "hizli"}):
        return ""

    msg = (message or "").strip()
    if not msg or len(msg) < 4:
        return ""

    parts: list[str] = []

    mem_lines = find_hizir_firsat_summary_lines(msg)
    if mem_lines:
        parts.append(
            "=== Merkezi bellek — kategori: hizir_ticaret.firsatlar (özet eşleşme) ===\n"
            + "\n".join(mem_lines)
        )

    ttl = float(os.environ.get("HIZIR_ONBELLEK_TTL_SEC", "300"))
    cache_key = _norm_cache_key(msg, pazar_kanallari)

    skip_weather = bool(weather_q and has_live_weather_block)

    hizir_mod = mode_norm == "hizir"
    scan_intent = (
        _commercial_intent(msg)
        or _komuta_pazar_tara(msg)
        or (hizir_mod and _urun_tara_intent(msg))
    )
    if scan_intent:
        cached = find_fresh_genel_girdi(
            tip="pazar_keşif", anahtar=cache_key, max_age_sec=ttl
        )
        if cached and isinstance(cached.get("veri"), dict):
            parts.append(
                "=== Önbellek (genel_onbellek.girdiler — güncel) ===\n"
                + json.dumps(cached["veri"], ensure_ascii=False)[:12000]
            )
        else:
            scraper = UniversalScraper()
            tok = pazar_ctx.set_pazar_kanallari(pazar_ctx.normalize_kanal_listesi(pazar_kanallari))
            try:
                uni = scraper.fetch(msg, skip_weather=skip_weather)
            finally:
                pazar_ctx.reset_pazar_kanallari(tok)
            if uni:
                parts.append(
                    "=== Canlı keşif — UniversalScraper + HIZIR araçları ===\n"
                    + json.dumps(uni, ensure_ascii=False, default=str)[:12000]
                )
                append_genel_onbellek_girdi(
                    {
                        "tip": "pazar_keşif",
                        "anahtar": cache_key,
                        "veri": uni,
                    }
                )
                _maybe_append_margin_tool(uni, parts)
        try:
            from ilim_assistant.hizir.ticaret_avci import reconcile_ticaret_avci_firsatlar

            reconcile_ticaret_avci_firsatlar()
        except Exception:
            pass
    elif _flight_intent(msg):
        cached = find_fresh_genel_girdi(
            tip="ucus_stub", anahtar=cache_key, max_age_sec=ttl
        )
        if cached and cached.get("veri"):
            parts.append(
                "=== Önbellek — uçuş (stub) ===\n"
                + json.dumps(cached["veri"], ensure_ascii=False)[:6000]
            )
        else:
            scraper = UniversalScraper()
            uni = scraper.fetch(msg, skip_weather=skip_weather)
            if uni:
                parts.append(
                    "=== UniversalScraper ===\n"
                    + json.dumps(uni, ensure_ascii=False, default=str)[:8000]
                )
                append_genel_onbellek_girdi(
                    {"tip": "ucus_stub", "anahtar": cache_key, "veri": uni}
                )
    elif not weather_q:
        low = msg.lower()
        if any(x in low for x in ("internette ara", "duckduckgo", "web başlık", "haber başlıkları")):
            scraper = UniversalScraper()
            uni = scraper.fetch(msg, skip_weather=True)
            if uni:
                parts.append(
                    "=== UniversalScraper (web) ===\n"
                    + json.dumps(uni, ensure_ascii=False, default=str)[:10000]
                )

    if not parts:
        return ""

    tail = (
        "\n\n[TALİMAT — OPERASYON MERKEZİ]\n"
        "Bu blok **Rüzgar araçları** ile üretildi (Merkezi Bellek + HIZIR global pazar motoru). "
        "Canlı fiyat/stok için satıcı sayfasında teyit iste; API kotası veya ağ hatalarında satır sayısı düşebilir. "
        "Ticari karar için sözleşme ve resmi kanalları hatırlat.\n"
    )
    return "\n\n".join(parts) + tail
