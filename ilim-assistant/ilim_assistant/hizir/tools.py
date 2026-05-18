from __future__ import annotations

import json
from typing import Any, Callable

from ilim_assistant.hizir.avci import HizirAvci


def _listings_dict(
    query: str, *, fiyat_dedektifi: bool = False, channels: list[str] | None = None
) -> dict[str, Any]:
    from ilim_assistant.hizir.global_market_engine import build_global_market_listings

    q = (query or "").strip() or "ürün"
    scan_mode = "fiyat_dedektifi" if fiyat_dedektifi else "otomatik_arbitraj"
    payload = build_global_market_listings(q, limit=8, scan_mode=scan_mode, channels=channels)
    errors = dict(payload.get("errors") or {})
    return {
        "ok": bool(payload.get("ok", True)),
        "query": payload.get("query", q),
        "scan_mode": payload.get("scan_mode", scan_mode),
        "live": bool(payload.get("live")),
        "mock_marketplace": bool(payload.get("mock_marketplace")),
        "canli_pazar": bool(payload.get("canli_pazar")),
        "data_mode": payload.get("data_mode", "live"),
        "errors": errors,
        "loops": payload.get("loops") or {},
        "trendyol": payload.get("trendyol") or [],
        "amazon": payload.get("amazon") or [],
        "search_compare": payload.get("search_compare") or {},
        "static_live_fill": payload.get("static_live_fill") or [],
        "aktif_kanallar": payload.get("aktif_kanallar") or [],
        "kanal_secimi": payload.get("kanal_secimi") or [],
    }


def tool_hizir_market_listings(
    query: str = "", fiyat_dedektifi: bool = False, channels: list[str] | None = None
) -> dict[str, Any]:
    """Scraper: pazar yerlerinde ürün satırları; `fiyat_dedektifi` ile Search & Compare vitrin."""
    q = (query or "").strip() or "ürün"
    return _listings_dict(q, fiyat_dedektifi=bool(fiyat_dedektifi), channels=channels)


def tool_hizir_analyze_opportunity(
    source_price: float,
    target_price: float,
    commission_rate: float,
) -> dict[str, Any]:
    """Avci: sigortalı maliyet motoru ile marj / AVLA-BEKLE."""
    return HizirAvci().analyze_opportunity(
        float(source_price),
        float(target_price),
        float(commission_rate),
    )


_TOOL_REGISTRY: dict[str, Callable[..., dict[str, Any]]] = {
    "hizir_market_listings": lambda **kw: tool_hizir_market_listings(
        kw.get("query", ""),
        fiyat_dedektifi=bool(kw.get("fiyat_dedektifi")),
        channels=kw.get("channels"),
    ),
    "hizir_analyze_opportunity": lambda **kw: tool_hizir_analyze_opportunity(
        float(kw.get("source_price", 0)),
        float(kw.get("target_price", 0)),
        float(kw.get("commission_rate", 0.15)),
    ),
}


# Rüzgar / harici orkestrasyon için makine-okur tanımlar (ileride LLM tool-calling).
HIZIR_TOOL_SPECS: list[dict[str, Any]] = [
    {
        "name": "hizir_market_listings",
        "description": "Global pazar motoru: TR (Trendyol+Amazon TR) ve US/UK/DE (Amazon+eBay+US AliExpress). Varsayılan canlı; HIZIR_MOCK_MARKETPLACE=1 yalnızca geliştirici.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "fiyat_dedektifi": {
                    "type": "boolean",
                    "description": "True: ürün odaklı fiyat karşılaştırma (Fiyat Dedektifi). False: genel arbitraj taraması.",
                },
                "channels": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "İsteğe bağlı: trendyol, amazon_tr, hepsiburada, amazon_us, amazon_gb, amazon_de, ebay, aliexpress",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "hizir_analyze_opportunity",
        "description": "Alış/satış fiyatı ve satış komisyonu ile sigortalı net kâr ve AVLA/Bekle kararı.",
        "parameters": {
            "type": "object",
            "properties": {
                "source_price": {"type": "number"},
                "target_price": {"type": "number"},
                "commission_rate": {"type": "number", "description": "0.15 = %15"},
            },
            "required": ["source_price", "target_price", "commission_rate"],
        },
    },
]


def run_hizir_tool(name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    """Ana motor ve servislerin doğrudan çağıracağı tek giriş noktası."""
    fn = _TOOL_REGISTRY.get((name or "").strip())
    if fn is None:
        return {"ok": False, "error": "unknown_tool", "name": name}
    args = dict(arguments or {})
    try:
        out = fn(**args)
        return {"ok": True, "tool": name, "result": out}
    except Exception as exc:
        return {"ok": False, "tool": name, "error": str(exc)}


def run_hizir_tool_json(name: str, arguments_json: str) -> dict[str, Any]:
    try:
        payload = json.loads(arguments_json or "{}")
        if not isinstance(payload, dict):
            payload = {}
    except json.JSONDecodeError:
        payload = {}
    return run_hizir_tool(name, payload)
