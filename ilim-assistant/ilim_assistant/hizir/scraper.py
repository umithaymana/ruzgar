from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from ilim_assistant.hizir.market_live import (
    DEMO_PRODUCT_IMAGE_TR_AMAZON,
    DEMO_PRODUCT_IMAGE_TR_TRENDYOL,
    use_mock_marketplace,
)
from ilim_assistant.hizir.trendyol_resilience import TRENDYOL_LIVE_ENV_KEYS as _TRENDYOL_LIVE_ENV_KEYS

# Trendyol discovery: başlık / vekil / yeniden deneme `trendyol_resilience` içinde;
# HTTP çağrısı `market_live.fetch_trendyol_live` üzerinden yapılır.


def trendyol_live_env_keys() -> tuple[str, ...]:
    """Trendyol canlı isteklerinde kullanılan HIZIR_* ortam anahtarları (market_live ile ortak)."""
    return _TRENDYOL_LIVE_ENV_KEYS


@dataclass(frozen=True)
class ProductListing:
    """Pazar yerinden gelen tek ürün satırı (gerçek entegrasyonda API/HTML eşlemesi)."""

    marketplace: str
    product_name: str
    price: float
    in_stock: bool
    external_id: str = ""
    currency: str = "TRY"
    extra: dict[str, object] = field(default_factory=dict)


def _dict_rows_to_listings(rows: list[dict[str, Any]], marketplace: str) -> list[ProductListing]:
    out: list[ProductListing] = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        name = str(r.get("name") or "").strip() or "Ürün"
        try:
            price = float(r.get("price") or 0)
        except (TypeError, ValueError):
            continue
        if price <= 0:
            continue
        cur = str(r.get("currency") or "TRY").strip()[:8] or "TRY"
        out.append(
            ProductListing(
                marketplace=marketplace,
                product_name=name[:240],
                price=price,
                in_stock=bool(r.get("in_stock", True)),
                external_id=str(r.get("id") or "")[:80],
                currency=cur,
                extra=dict(r.get("extra") or {}),
            )
        )
    return out


class MarketplaceScraper(ABC):
    """Trendyol / Amazon vb. için ortak arayüz; fetch aşaması alt sınıfta."""

    marketplace_code: str = ""

    @abstractmethod
    def fetch_listings(self, query: str, *, limit: int = 10) -> list[ProductListing]:
        """Gerçek uygulamada HTTP istemcisi veya resmi API burada çalışır."""

    def _not_implemented_http_hint(self) -> str:
        return (
            f"{self.marketplace_code}: canlı çekim henüz bağlı değil; "
            "HTTP oturumu, hız sınırı ve robots.txt uyumu burada uygulanacak."
        )


class TrendyolScraperScaffold(MarketplaceScraper):
    """Trendyol TR: discovery JSON (canlı). Dayanıklılık: `trendyol_live_env_keys()` ile listelenen HIZIR_* değişkenleri + `market_live`."""

    marketplace_code = "trendyol"
    last_live_error: str | None = None

    def _mock_listings(self, query: str, *, limit: int) -> list[ProductListing]:
        q = (query or "").strip() or "örnek ürün"
        mock = [
            ProductListing(
                marketplace=self.marketplace_code,
                product_name=f"{q} (Trendyol mock)",
                price=100.0,
                in_stock=True,
                external_id="TY-MOCK-001",
                extra={"note": "simulated", "image": DEMO_PRODUCT_IMAGE_TR_TRENDYOL},
            ),
            ProductListing(
                marketplace=self.marketplace_code,
                product_name=f"{q} — ekonomik seçenek",
                price=95.5,
                in_stock=True,
                external_id="TY-MOCK-002",
                extra={"image": DEMO_PRODUCT_IMAGE_TR_TRENDYOL},
            ),
        ]
        return mock[: max(1, min(limit, len(mock)))]

    def fetch_listings(self, query: str, *, limit: int = 10) -> list[ProductListing]:
        type(self).last_live_error = None
        if use_mock_marketplace():
            return self._mock_listings(query, limit=limit)
        from ilim_assistant.hizir import market_live as ml

        rows, err = ml.fetch_trendyol_live(query, limit=limit)
        type(self).last_live_error = err
        if rows:
            return _dict_rows_to_listings(rows, self.marketplace_code)
        return []


class AmazonScraperScaffold(MarketplaceScraper):
    """Amazon TR: PA-API 5 (canlı) veya yalnızca HIZIR_MOCK_MARKETPLACE=1 ile yerel iskele."""

    marketplace_code = "amazon"
    last_live_error: str | None = None

    def _mock_listings(self, query: str, *, limit: int) -> list[ProductListing]:
        q = (query or "").strip() or "örnek ürün"
        mock = [
            ProductListing(
                marketplace=self.marketplace_code,
                product_name=f"{q} (Amazon mock)",
                price=210.0,
                in_stock=True,
                external_id="AZ-MOCK-100",
                extra={"note": "simulated", "image": DEMO_PRODUCT_IMAGE_TR_AMAZON},
            ),
            ProductListing(
                marketplace=self.marketplace_code,
                product_name=f"{q} — satıcı B",
                price=175.0,
                in_stock=False,
                external_id="AZ-MOCK-101",
                extra={"image": DEMO_PRODUCT_IMAGE_TR_AMAZON},
            ),
        ]
        return mock[: max(1, min(limit, len(mock)))]

    def fetch_listings(self, query: str, *, limit: int = 10) -> list[ProductListing]:
        type(self).last_live_error = None
        if use_mock_marketplace():
            return self._mock_listings(query, limit=limit)
        from ilim_assistant.hizir import market_live as ml

        rows, err = ml.fetch_amazon_live(query, limit=limit)
        type(self).last_live_error = err
        if rows:
            return _dict_rows_to_listings(rows, self.marketplace_code)
        return []
