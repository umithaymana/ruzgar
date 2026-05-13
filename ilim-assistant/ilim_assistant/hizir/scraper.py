from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


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
    marketplace_code = "trendyol"

    def fetch_listings(self, query: str, *, limit: int = 10) -> list[ProductListing]:
        """Canlı modda: oturum, hız sınırı, robots.txt ve `_not_implemented_http_hint` politikası uygulanır."""
        q = (query or "").strip() or "örnek ürün"
        mock = [
            ProductListing(
                marketplace=self.marketplace_code,
                product_name=f"{q} (Trendyol mock)",
                price=100.0,
                in_stock=True,
                external_id="TY-MOCK-001",
                extra={"note": "simulated"},
            ),
            ProductListing(
                marketplace=self.marketplace_code,
                product_name=f"{q} — ekonomik seçenek",
                price=95.5,
                in_stock=True,
                external_id="TY-MOCK-002",
            ),
        ]
        return mock[: max(1, min(limit, len(mock)))]


class AmazonScraperScaffold(MarketplaceScraper):
    marketplace_code = "amazon"

    def fetch_listings(self, query: str, *, limit: int = 10) -> list[ProductListing]:
        """Canlı modda: oturum, hız sınırı, robots.txt ve `_not_implemented_http_hint` politikası uygulanır."""
        q = (query or "").strip() or "örnek ürün"
        mock = [
            ProductListing(
                marketplace=self.marketplace_code,
                product_name=f"{q} (Amazon mock)",
                price=210.0,
                in_stock=True,
                external_id="AZ-MOCK-100",
                extra={"note": "simulated"},
            ),
            ProductListing(
                marketplace=self.marketplace_code,
                product_name=f"{q} — satıcı B",
                price=175.0,
                in_stock=False,
                external_id="AZ-MOCK-101",
            ),
        ]
        return mock[: max(1, min(limit, len(mock)))]
