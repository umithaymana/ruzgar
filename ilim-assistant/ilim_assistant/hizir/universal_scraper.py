from __future__ import annotations

import re
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class UniversalPlugin(Protocol):
    """Genişleme yuvası: yeni veri kaynakları bu arayüzle eklenir."""

    def plugin_id(self) -> str: ...

    def priority(self) -> int: ...
    """Yüksek önce denenir."""

    def supports(self, message: str) -> bool: ...

    def fetch(self, message: str) -> dict[str, Any]: ...


def extract_product_query(message: str) -> str:
    t = (message or "").lower()
    for noise in (
        "trendyol'da",
        "trendyolda",
        "trendyol da",
        "trendyol",
        "amazon'da",
        "amazonda",
        "amazon da",
        "amazon",
        "tr'de",
        "tr de",
        "en ucuz",
        "ucuz",
        "hangi",
        "nedir",
        "fiyatı",
        "fiyati",
        "kaç",
        "kac",
        "tl",
        "lira",
    ):
        t = t.replace(noise, " ")
    t = re.sub(r"[^\w\s\u00c0-\u024f]", " ", t, flags=re.UNICODE)
    t = re.sub(r"\s+", " ", t).strip()
    return t[:160] or "ürün"


class CommercialMarketplacePlugin:
    """Pazar yeri satır üretimi — HIZIR `hizir_market_listings` aracını çağırır."""

    def plugin_id(self) -> str:
        return "marketplace_commercial"

    def priority(self) -> int:
        return 80

    def supports(self, message: str) -> bool:
        low = (message or "").lower()
        if any(
            x in low
            for x in (
                "pazar yerini tara",
                "pazar yerlerini tara",
                "pazarı tara",
                "pazari tara",
                "pazar tara",
            )
        ):
            return True
        if "trendyol" in low or "amazon" in low or "pazaryeri" in low or "pazar yeri" in low:
            return any(
                x in low
                for x in (
                    "ucuz",
                    "fiyat",
                    "tl",
                    "lira",
                    "ne kadar",
                    "satış",
                    "ürün",
                    "urun",
                )
            )
        if "en ucuz" in low and len((message or "").strip()) > 10:
            return True
        return False

    def fetch(self, message: str) -> dict[str, Any]:
        from ilim_assistant.hizir.tools import run_hizir_tool

        q = extract_product_query(message)
        return run_hizir_tool("hizir_market_listings", {"query": q})


class WeatherUniversalPlugin:
    """Hava: ana motorda ayrı kanal var; burada yalnızca yedek / tek blok özet."""

    def plugin_id(self) -> str:
        return "weather"

    def priority(self) -> int:
        return 40

    def supports(self, message: str) -> bool:
        low = (message or "").lower()
        return any(
            x in low
            for x in (
                "hava durumu",
                "hava nasıl",
                "meteoroloji",
                "yağmur",
                "kar ",
                "sıcaklık",
            )
        )

    def fetch(self, message: str) -> dict[str, Any]:
        try:
            from ilim_assistant.weather_live import compute_live_weather_outcome

            ctx, instant = compute_live_weather_outcome(message)
            return {"context": ctx or "", "instant_reply": instant or ""}
        except Exception as exc:
            return {"error": str(exc), "context": "", "instant_reply": ""}


class FlightStubPlugin:
    def plugin_id(self) -> str:
        return "flight_stub"

    def priority(self) -> int:
        return 60

    def supports(self, message: str) -> bool:
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
                "boarding",
            )
        )

    def fetch(self, message: str) -> dict[str, Any]:
        return {
            "status": "stub",
            "detail": "Uçuş fiyatı / koltuk API’si (Amadeus, taşıyıcı resmi API) burada bağlanacak.",
            "message_echo": (message or "")[:200],
        }


class WebHeadlinePlugin:
    """İstenirse kısa web başlıkları — ana motordaki DDG ile çakışmayı azaltmak için dar tetik."""

    def plugin_id(self) -> str:
        return "web_headline"

    def priority(self) -> int:
        return 20

    def supports(self, message: str) -> bool:
        low = (message or "").lower()
        return any(
            x in low
            for x in (
                "internette ara",
                "duckduckgo",
                "web başlık",
                "haber başlıkları",
            )
        )

    def fetch(self, message: str) -> dict[str, Any]:
        try:
            from ilim_assistant.web_tools import build_web_context, refined_search_query

            q = refined_search_query(message).strip()
            if not q:
                return {"ok": False, "reason": "empty_query"}
            ctx = build_web_context(q, max_results=5, fetch_first_n_urls=0)
            return {"ok": bool(ctx), "snippets": ctx[:8000] if ctx else ""}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}


def default_plugins() -> list[Any]:
    return [
        CommercialMarketplacePlugin(),
        FlightStubPlugin(),
        WeatherUniversalPlugin(),
        WebHeadlinePlugin(),
    ]


class UniversalScraper:
    """
    Evrensel dış veri yönlendiricisi. Yeni modül = `UniversalPlugin` uygula ve listeye ekle.
    """

    def __init__(self, plugins: list[Any] | None = None) -> None:
        self._plugins: list[Any] = list(plugins) if plugins is not None else default_plugins()

    def register(self, plugin: Any) -> None:
        self._plugins.append(plugin)

    def fetch(
        self,
        message: str,
        *,
        skip_weather: bool = False,
    ) -> dict[str, Any] | None:
        msg = (message or "").strip()
        if not msg:
            return None
        ordered = sorted(self._plugins, key=lambda p: p.priority(), reverse=True)
        for p in ordered:
            if skip_weather and p.plugin_id() == "weather":
                continue
            try:
                if p.supports(msg):
                    return {"plugin_id": p.plugin_id(), "data": p.fetch(msg)}
            except Exception as exc:
                return {"plugin_id": p.plugin_id(), "error": str(exc), "data": {}}
        return None
