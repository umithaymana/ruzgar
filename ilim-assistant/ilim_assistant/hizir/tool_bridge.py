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
from ilim_assistant.hizir.universal_scraper import UniversalScraper


def _maybe_append_margin_tool(uni: dict[str, Any], parts: list[str]) -> None:
    """İlk stoklu Trendyol / Amazon mock fiyatlarıyla hizir_analyze_opportunity çağrısı."""
    try:
        from ilim_assistant.hizir.tools import run_hizir_tool

        data = uni.get("data")
        if not isinstance(data, dict):
            return
        res = data.get("result")
        if not isinstance(res, dict):
            return
        ty = res.get("trendyol") or []
        am = res.get("amazon") or []
        src = next((float(x["price"]) for x in ty if x.get("in_stock")), None)
        tgt = next((float(x["price"]) for x in am if x.get("in_stock")), None)
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
            "=== Araç: hizir_analyze_opportunity (kaynak=ilk Trendyol, hedef=ilk Amazon) ===\n"
            + json.dumps(out, ensure_ascii=False, default=str)[:4000]
        )
    except Exception:
        return


def _komuta_pazar_tara(message: str) -> bool:
    low = (message or "").lower()
    return any(
        x in low
        for x in (
            "pazar yerini tara",
            "pazar yerlerini tara",
            "pazarı tara",
            "pazari tara",
            "pazar tara",
        )
    )


def _norm_cache_key(message: str) -> str:
    t = re.sub(r"\s+", " ", (message or "").strip().lower())[:400]
    return t


def _commercial_intent(message: str) -> bool:
    low = (message or "").lower()
    if "trendyol" in low or "amazon" in low or "pazaryeri" in low or "pazar yeri" in low:
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
    cache_key = _norm_cache_key(msg)

    skip_weather = bool(weather_q and has_live_weather_block)

    if _commercial_intent(msg) or _komuta_pazar_tara(msg):
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
            uni = scraper.fetch(msg, skip_weather=skip_weather)
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
        "Bu blok **Rüzgar araçları** ile üretildi (Merkezi Bellek + HIZIR / UniversalScraper). "
        "Pazar satırları **canlı çekim** ise yine de fiyat/stok için mağaza sayfasında teyit iste; "
        "HIZIR_MOCK_MARKETPLACE=1 ile sahte veri kullanıldıysa bunu açıkça belirt. "
        "Ticari karar için sözleşme ve resmi kanalları hatırlat.\n"
    )
    return "\n\n".join(parts) + tail
