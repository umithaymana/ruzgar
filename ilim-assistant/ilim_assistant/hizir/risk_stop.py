from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def stop_loss_should_close(
    profit_margin_percent: float,
    *,
    profit_threshold_percent: float = 20.0,
) -> bool:
    """Kâr marjı eşiğin altına düştüyse ilanı kapat (operasyon katmanı tetikler)."""
    return profit_margin_percent < profit_threshold_percent


def build_stop_loss_event(
    *,
    marketplace: str,
    listing_id: str,
    reason: str,
    margin_percent: float,
    threshold_percent: float,
) -> dict[str, Any]:
    """merkezi_bellek.json içi `hizir_stop_loss_log` satırı."""
    return {
        "tarih": datetime.now(timezone.utc).isoformat(),
        "pazaryeri": marketplace,
        "listing_id": listing_id,
        "neden": reason,
        "marj_yuzde": margin_percent,
        "esik_yuzde": threshold_percent,
    }


def maybe_log_stop_loss(
    profit_margin_percent: float,
    *,
    profit_threshold_percent: float,
    marketplace: str,
    listing_id: str,
    path: Path | None = None,
) -> dict[str, Any] | None:
    """Eşik altı marjda merkezi belleğe stop-loss satırı yazar; ListingControlStub ile birleştirilebilir."""
    from ilim_assistant.hizir.bellek import append_stop_loss_event

    if not stop_loss_should_close(
        profit_margin_percent, profit_threshold_percent=profit_threshold_percent
    ):
        return None
    ev = build_stop_loss_event(
        marketplace=marketplace,
        listing_id=listing_id,
        reason="profit_margin_below_threshold",
        margin_percent=profit_margin_percent,
        threshold_percent=profit_threshold_percent,
    )
    append_stop_loss_event(ev, path=path)
    return ev


class ListingControlStub:
    """
    Gerçek Satıcı API bağlanana kadar yer tutucu.
    Hedef: eşik altı marjda ilanı saniyeler içinde kapatma komutunu API'ye iletmek.
    """

    def close_listing(self, marketplace: str, listing_id: str, *, reason: str = "") -> dict[str, Any]:
        return {
            "ok": False,
            "action": "close_listing",
            "marketplace": marketplace,
            "listing_id": listing_id,
            "reason": reason or "stop_loss_or_manual",
            "detail": "Canlı pazar yeri API anahtarı ve uç nokta bağlantısı henüz yok (stub).",
        }
