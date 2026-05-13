from __future__ import annotations

import json
from typing import Any, Callable

from ilim_assistant.hizir.avci import HizirAvci


def _listings_dict(query: str) -> dict[str, Any]:
    from ilim_assistant.hizir import market_live as ml
    from ilim_assistant.hizir.scraper import AmazonScraperScaffold, TrendyolScraperScaffold

    q = (query or "").strip() or "ürün"
    ty = TrendyolScraperScaffold()
    am = AmazonScraperScaffold()
    ty_rows = ty.fetch_listings(q, limit=6)
    am_rows = am.fetch_listings(q, limit=6)
    live = not ml.use_mock_marketplace()
    errors: dict[str, str] = {}
    if live:
        if TrendyolScraperScaffold.last_live_error:
            errors["trendyol"] = TrendyolScraperScaffold.last_live_error
        if AmazonScraperScaffold.last_live_error:
            errors["amazon"] = AmazonScraperScaffold.last_live_error
    return {
        "ok": True,
        "query": q,
        "live": live,
        "errors": errors,
        "trendyol": [
            {"name": x.product_name, "price": x.price, "in_stock": x.in_stock, "id": x.external_id}
            for x in ty_rows
        ],
        "amazon": [
            {"name": x.product_name, "price": x.price, "in_stock": x.in_stock, "id": x.external_id}
            for x in am_rows
        ],
    }


def tool_hizir_market_listings(query: str) -> dict[str, Any]:
    """Scraper: pazar yerlerinde (iskelet) ürün satırları."""
    q = (query or "").strip() or "ürün"
    return _listings_dict(q)


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
    "hizir_market_listings": lambda **kw: tool_hizir_market_listings(kw.get("query", "")),
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
        "description": "Trendyol ve Amazon için ürün adı, fiyat, stok listesi (canlı: varsayılan; HIZIR_MOCK_MARKETPLACE=1 ile sahte).",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
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
