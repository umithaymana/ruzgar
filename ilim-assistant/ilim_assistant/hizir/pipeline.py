from __future__ import annotations

from pathlib import Path
from typing import Any

from ilim_assistant.hizir.avci import HizirAvci
from ilim_assistant.hizir.bellek import persist_if_avla
from ilim_assistant.hizir.scraper import (
    AmazonScraperScaffold,
    ProductListing,
    TrendyolScraperScaffold,
)


def evaluate_mock_cross_market(
    query: str,
    *,
    commission_rate: float = 0.15,
    hunter: HizirAvci | None = None,
    bellek_path: Path | None = None,
    kullanici_id: str | None = None,
) -> dict[str, Any]:
    """
    İki iskelet scraper'dan ilk stoklu satırları alır, kaynak=Trendyol hedef=Amazon varsayar.
    Dönüş: analiz sözlüğü + kaynak/hedef özet; AVLA ise merkezi_bellek.json güncellenir.
    """
    src_scraper = TrendyolScraperScaffold()
    dst_scraper = AmazonScraperScaffold()
    hunter = hunter or HizirAvci()

    src_list = [x for x in src_scraper.fetch_listings(query, limit=5) if x.in_stock]
    dst_list = [x for x in dst_scraper.fetch_listings(query, limit=5) if x.in_stock]
    if not src_list or not dst_list:
        return {
            "ok": False,
            "reason": "no_in_stock_mock_rows",
            "analysis": None,
        }

    source: ProductListing = src_list[0]
    target: ProductListing = dst_list[0]
    product_label = f"{source.product_name} -> {target.product_name}"

    analysis = hunter.analyze_opportunity(
        source.price,
        target.price,
        commission_rate,
    )
    persisted = persist_if_avla(
        analysis,
        product_name=product_label,
        source_price=source.price,
        target_price=target.price,
        path=bellek_path,
        kullanici_id=kullanici_id,
    )
    return {
        "ok": True,
        "product_name": product_label,
        "source_price": source.price,
        "target_price": target.price,
        "analysis": analysis,
        "persisted_to_merkezi_bellek": persisted,
    }
