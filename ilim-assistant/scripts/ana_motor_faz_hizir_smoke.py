# Created by Ümit & Gökçenur
"""Smoke — Dilim 8 Hızır tek yüz; pazar tara çalmaz."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from ilim_assistant.ana_motor_faz_hizir_tek_yuz import (
        enrich_orchestra_faz_hizir,
        faz_hizir_status,
        parse_hizir_gorev_intent,
    )
    from ilim_assistant.ruzgar_orkestrasyon_faz_c import build_genel_orchestra_preview

    fails = 0

    hit = parse_hizir_gorev_intent("hizirda: ikinci el telefon fırsatı notu")
    ok = bool(hit) and hit.get("motor") == "hizir" and "telefon" in str(hit.get("text") or "")
    print(f"  {'OK' if ok else 'FAIL'} hizirda: doldur")
    if not ok:
        fails += 1

    hit2 = parse_hizir_gorev_intent("hızır paneli aç")
    ok2 = bool(hit2) and hit2.get("action") == "panel_ac"
    print(f"  {'OK' if ok2 else 'FAIL'} panel aç")
    if not ok2:
        fails += 1

    for msg in (
        "pazar tara",
        "fotosentez nedir",
        "nasılsın",
        "seste: merhaba",
        "hizir durum",
    ):
        neg = parse_hizir_gorev_intent(msg)
        okn = neg is None
        print(f"  {'OK' if okn else 'FAIL'} negatif {msg!r}")
        if not okn:
            fails += 1

    st = faz_hizir_status()
    if st.get("pazar_api") is not False:
        print("FAIL pazar_api False olmalı")
        fails += 1
    else:
        print("  OK pazar_api=False")

    orch = enrich_orchestra_faz_hizir({}, "hizir paneline: tarama notu")
    ua = orch.get("ui_action") or {}
    if ua.get("motor") != "hizir" or not orch.get("quiet"):
        print("FAIL enrich", ua)
        fails += 1
    else:
        print("  OK enrich")

    orch2, patch = build_genel_orchestra_preview("hizirda: not")
    if (orch2.get("ui_action") or {}).get("motor") != "hizir" or not patch.get("faz_hizir"):
        print("FAIL preview", orch2.get("ui_action"), patch.get("faz_hizir"))
        fails += 1
    else:
        print("  OK preview faz_hizir")

    if fails:
        print(f"FAIL ana_motor_faz_hizir_smoke fails={fails}")
        return 1
    print("PASS ana_motor_faz_hizir_smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
