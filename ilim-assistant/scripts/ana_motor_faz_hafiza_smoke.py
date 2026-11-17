# Created by Ümit & Gökçenur
"""Smoke — Dilim 2 Hafıza tek yüz: panel handoff; hatırla çalmaz."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from ilim_assistant.ana_motor_faz_hafiza_tek_yuz import (
        enrich_orchestra_faz_hafiza,
        parse_hafiza_gorev_intent,
    )
    from ilim_assistant.ruzgar_orkestrasyon_faz_c import build_genel_orchestra_preview

    fails = 0

    hit = parse_hafiza_gorev_intent("hafızada: Çırak notu — dilim2 deneme")
    ok = bool(hit) and hit.get("motor") == "hafiza" and "Çırak" in str(hit.get("text") or "")
    print(f"  {'OK' if ok else 'FAIL'} hafızada: doldur")
    if not ok:
        fails += 1

    hit2 = parse_hafiza_gorev_intent("hafıza paneli aç")
    ok2 = bool(hit2) and hit2.get("action") == "panel_ac"
    print(f"  {'OK' if ok2 else 'FAIL'} panel aç")
    if not ok2:
        fails += 1

    for msg in (
        "nasılsın",
        "fotosentez nedir",
        "hatırla: anahtar = değer",
        "bunu hatırla: test",
        "hafıza durumu",
        "seste: merhaba",
    ):
        neg = parse_hafiza_gorev_intent(msg)
        okn = neg is None
        print(f"  {'OK' if okn else 'FAIL'} negatif {msg[:40]!r}")
        if not okn:
            fails += 1

    orch = enrich_orchestra_faz_hafiza({}, "hafıza paneline: not satırı")
    ua = orch.get("ui_action") or {}
    if not orch.get("quiet") or ua.get("motor") != "hafiza" or ua.get("kind") != "hafiza_gorev":
        print("FAIL enrich", ua)
        fails += 1
    else:
        print("  OK enrich_orchestra_faz_hafiza")

    orch_skip = enrich_orchestra_faz_hafiza(
        {"ui_action": {"type": "surface_handoff", "motor": "ses"}},
        "hafızada: x",
    )
    if orch_skip.get("ui_action", {}).get("motor") != "ses":
        print("FAIL skip when ui_action set")
        fails += 1
    else:
        print("  OK mevcut ui_action korunur")

    orch2, patch = build_genel_orchestra_preview("hafızada: plan dersi")
    ua2 = orch2.get("ui_action") or {}
    if ua2.get("motor") != "hafiza" or not patch.get("faz_hafiza"):
        print("FAIL preview", ua2, patch.get("faz_hafiza"))
        fails += 1
    else:
        print("  OK preview faz_hafiza")

    if fails:
        print(f"FAIL ana_motor_faz_hafiza_smoke fails={fails}")
        return 1
    print("PASS ana_motor_faz_hafiza_smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
