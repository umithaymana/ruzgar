from __future__ import annotations

from ilim_assistant.hizir.maliyet_motoru import MaliyetGirdileri, hesapla_sigortali_net_kar


class HizirAvci:
    """
    Sigortalı net kâr: alış + KDV + alış tarafı pazar komisyonu + kargo + %2 hata payı;
    satıştan pazar komisyonu düşülür. Eşik altı BEKLE; stop-loss için `risk_stop` modülü.
    """

    def __init__(
        self,
        *,
        profit_threshold_percent: float = 20.0,
        vat_rate: float | None = None,
        tax_multiplier: float | None = None,
        shipping_cost: float = 0.0,
        error_margin_rate: float = 0.02,
        buy_commission_rate: float = 0.0,
    ) -> None:
        self.profit_threshold_percent = profit_threshold_percent
        self.shipping_cost = shipping_cost
        self.error_margin_rate = error_margin_rate
        self.buy_commission_rate = buy_commission_rate
        if tax_multiplier is not None:
            self.vat_rate = max(0.0, float(tax_multiplier) - 1.0)
        elif vat_rate is not None:
            self.vat_rate = float(vat_rate)
        else:
            self.vat_rate = 0.20

    def analyze_opportunity(
        self,
        source_price: float,
        target_price: float,
        commission_rate: float,
        *,
        shipping_cost: float | None = None,
    ) -> dict:
        """
        commission_rate: satış fiyatı üzerinden pazar komisyonu (örn. 0.15 = %15).
        """
        threshold = self.profit_threshold_percent
        ship = self.shipping_cost if shipping_cost is None else float(shipping_cost)

        raw = hesapla_sigortali_net_kar(
            MaliyetGirdileri(
                alis_fiyat=float(source_price),
                satis_fiyat=float(target_price),
                satis_komisyon_oran=float(commission_rate),
                kdv_oran=self.vat_rate,
                kargo=ship,
                hata_payi_oran=self.error_margin_rate,
                alis_tarafi_komisyon_oran=self.buy_commission_rate,
            )
        )
        if isinstance(raw, dict) and raw.get("cost_basis") == 0.0:
            return {
                "status": "BEKLE",
                "net_profit": 0.0,
                "profit_margin_percent": 0.0,
                "profit_threshold_percent": threshold,
                "rejection_reason": "invalid_cost_basis",
                "rejection_detail": "Alış fiyatı pozitif değil.",
                "breakdown": {},
            }

        cost_basis = float(raw["cost_basis"])
        net_profit = float(raw["net_profit"])
        profit_margin_percent = float(raw["profit_margin_percent"])

        breakdown = {
            "purchase": raw["purchase"],
            "vat_amount": raw["vat_amount"],
            "buy_commission_amount": raw["buy_commission_amount"],
            "shipping": raw["shipping"],
            "error_margin_amount": raw["error_margin_amount"],
            "sale_commission_amount": raw["sale_commission_amount"],
            "cost_basis": raw["cost_basis"],
            "net_sale": raw["net_sale"],
        }

        base = {
            "net_profit": round(net_profit, 2),
            "profit_margin_percent": round(profit_margin_percent, 4),
            "profit_threshold_percent": threshold,
            "breakdown": breakdown,
        }

        if profit_margin_percent >= threshold:
            return {"status": "AVLA", **base}

        return {
            "status": "BEKLE",
            **base,
            "rejection_reason": "profit_margin_below_threshold",
            "rejection_detail": (
                f"Kâr marjı %{profit_margin_percent:.2f}; "
                f"asgari eşik %{threshold:.2f}."
            ),
        }
