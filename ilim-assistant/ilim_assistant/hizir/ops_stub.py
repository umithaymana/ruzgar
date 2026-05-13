from __future__ import annotations

from typing import Any


def autonomous_listing_stub(
    marketplace: str,
    product_snapshot: dict[str, Any],
) -> dict[str, Any]:
    """Fırsat yakalandığında hedef mağazada ürün açma — API bağlantısı sonrası doldurulacak."""
    return {
        "ok": False,
        "action": "create_or_update_listing",
        "marketplace": marketplace,
        "product_snapshot": product_snapshot,
        "detail": "Otonom listeleme: Satıcı API + ürün şeması doğrulaması gerekir.",
    }


def stop_target_sale_on_source_stockout_stub(
    marketplace: str,
    listing_id: str,
    *,
    source_in_stock: bool,
) -> dict[str, Any]:
    """Kaynak stok bittiğinde hedef satışı durdur (milisaniye hedefi için anlık kuyruk/API)."""
    if source_in_stock:
        return {"ok": True, "action": "noop", "detail": "Kaynak hâlâ stoklu."}
    return {
        "ok": False,
        "action": "pause_or_end_listing",
        "marketplace": marketplace,
        "listing_id": listing_id,
        "detail": "Stok kesintisi — canlı API ile anında durdurma henüz bağlı değil (stub).",
    }
