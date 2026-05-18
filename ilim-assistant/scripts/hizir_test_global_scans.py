"""Tek seferlik: US (Logitech Mouse) + TR (Kahve Makinesi) tarama, merkezi bellek senkronu.

Vitrin görselleri: `global_market_engine` statik demo + `market_live.DEMO_PRODUCT_*` (Wikimedia HTTPS);
ruzgar-desktop CSP img-src içinde upload.wikimedia.org gerekir.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# ilim-assistant kökünden çalıştırın: python scripts/hizir_test_global_scans.py
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from ilim_assistant.hizir.bellek import (  # noqa: E402
    append_genel_onbellek_girdi,
    load_merkezi_bellek,
    merkezi_bellek_path,
)
from ilim_assistant.hizir.global_market_engine import build_global_market_listings  # noqa: E402
from ilim_assistant.hizir.ticaret_avci import reconcile_ticaret_avci_firsatlar  # noqa: E402


def _wrap(payload: dict) -> dict:
    return {
        "plugin_id": "marketplace_commercial",
        "data": {"ok": True, "tool": "hizir_market_listings", "result": payload},
    }


def _err_summary(payload: dict, label: str) -> dict:
    e = payload.get("errors") or {}
    lines = [f"  {k}: {(str(v) or '')[:220]}" for k, v in sorted(e.items())]
    loops = payload.get("loops") or {}
    gu = loops.get("global_us") or {}
    yt = loops.get("yerel_tr") or {}
    return {
        "label": label,
        "live": payload.get("live"),
        "data_mode": payload.get("data_mode"),
        "error_keys": sorted(e.keys()),
        "us_amazon_row_count": len(gu.get("amazon") or []),
        "us_ebay_row_count": len(gu.get("ebay") or []),
        "tr_trendyol_row_count": len(yt.get("trendyol") or []),
        "tr_amazon_tr_row_count": len(yt.get("amazon_tr") or []),
        "errors_detail": lines,
    }


def main() -> None:
    p1 = build_global_market_listings("Logitech Mouse", limit=8)
    append_genel_onbellek_girdi(
        {
            "tip": "pazar_keşif",
            "anahtar": "us_scan:logitech mouse",
            "veri": _wrap(p1),
        }
    )

    p2 = build_global_market_listings("Kahve Makinesi", limit=8)
    append_genel_onbellek_girdi(
        {
            "tip": "pazar_keşif",
            "anahtar": "tr_scan:kahve makinesi",
            "veri": _wrap(p2),
        }
    )

    p3 = build_global_market_listings("USB C Hub", limit=8)
    append_genel_onbellek_girdi(
        {
            "tip": "pazar_keşif",
            "anahtar": "us_scan:usb c hub",
            "veri": _wrap(p3),
        }
    )

    reconcile_ticaret_avci_firsatlar()

    path = merkezi_bellek_path()
    doc = load_merkezi_bellek(path)
    htc = doc["kategoriler"]["hizir_ticaret"]
    firsatlar = htc.get("firsatlar") or []
    arb = [x for x in firsatlar if isinstance(x, dict) and x.get("tur") == "ARBITRAJ"]
    first_arb = arb[0] if arb else None

    report = {
        "merkezi_bellek_path": str(path),
        "scan_summaries": [
            _err_summary(p1, "Logitech Mouse (global_us + tum donguler)"),
            _err_summary(p2, "Kahve Makinesi (yerel_tr + tum donguler)"),
            _err_summary(p3, "USB C Hub (global_us + tum donguler)"),
        ],
        "arbitraj_kart_sayisi": len(arb),
        "farkli_urun_arbitraj": len({str(x.get("urun_adi") or "").strip() for x in arb if isinstance(x, dict)}),
        "ilk_arbitraj_karti_panel_icin": first_arb,
        "ilk_5_firsat_ozet": [
            {
                "tur": x.get("tur"),
                "bolge": x.get("bolge"),
                "ozet_metin": (x.get("ozet_metin") or "")[:300],
                "net_marj_yuzde": x.get("net_marj_yuzde"),
                "potansiyel_kar": x.get("potansiyel_kar"),
            }
            for x in firsatlar[:5]
            if isinstance(x, dict)
        ],
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    dp = report["farkli_urun_arbitraj"]
    if dp < 3:
        print(
            f"\n[HIZIR smoke] UYARI: en az 3 farklı ürün beklenirdi; bu çalıştırmada {dp}. "
            "Önceki pazar_keşif girdileri birikmiş olabilir — merkezi_bellek temizliği deneyin.",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
