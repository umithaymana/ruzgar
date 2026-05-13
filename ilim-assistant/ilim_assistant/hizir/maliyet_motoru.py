from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MaliyetGirdileri:
    """Sigortalı net kâr: alış + KDV + (alış tarafı pazar komisyonu) + kargo + hata payı."""

    alis_fiyat: float
    satis_fiyat: float
    satis_komisyon_oran: float
    kdv_oran: float = 0.20
    kargo: float = 0.0
    hata_payi_oran: float = 0.02
    alis_tarafi_komisyon_oran: float = 0.0


def hesapla_sigortali_net_kar(g: MaliyetGirdileri) -> dict[str, float]:
    """
    Maliyet tabanı = alış + alış*KDV + alış*alis_tarafi_komisyon + kargo + alış*hata_payi.
    Net satış = satis - satis*satis_komisyon.
    """
    a = float(g.alis_fiyat)
    if a <= 0:
        return {
            "cost_basis": 0.0,
            "net_sale": 0.0,
            "net_profit": 0.0,
            "profit_margin_percent": 0.0,
            "purchase": a,
            "vat_amount": 0.0,
            "buy_commission_amount": 0.0,
            "shipping": 0.0,
            "error_margin_amount": 0.0,
            "sale_commission_amount": 0.0,
        }

    vat_amt = a * float(g.kdv_oran)
    buy_comm_amt = a * float(g.alis_tarafi_komisyon_oran)
    err_amt = a * float(g.hata_payi_oran)
    ship = float(g.kargo)
    cost = a + vat_amt + buy_comm_amt + ship + err_amt

    s = float(g.satis_fiyat)
    sale_comm_amt = s * float(g.satis_komisyon_oran)
    net_sale = s - sale_comm_amt
    net_profit = net_sale - cost
    margin_pct = (net_profit / cost) * 100.0 if cost > 0 else 0.0

    return {
        "cost_basis": round(cost, 4),
        "net_sale": round(net_sale, 4),
        "net_profit": round(net_profit, 4),
        "profit_margin_percent": round(margin_pct, 4),
        "purchase": a,
        "vat_amount": round(vat_amt, 4),
        "buy_commission_amount": round(buy_comm_amt, 4),
        "shipping": ship,
        "error_margin_amount": round(err_amt, 4),
        "sale_commission_amount": round(sale_comm_amt, 4),
    }
