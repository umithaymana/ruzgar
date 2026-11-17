# Created by Ümit & Gökçenur
"""Smoke — Dilim 3 Mimar tek yüz; ilim kaçmasın."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from ilim_assistant.ana_motor_faz_mimar_tek_yuz import (
        enrich_orchestra_faz_mimar,
        parse_mimar_gorev_intent,
    )
    from ilim_assistant.motorlar.ana_motor_hub_faz76 import resolve_hub_target
    from ilim_assistant.ruzgar_orkestrasyon_faz_c import build_genel_orchestra_preview

    fails = 0

    hit = parse_mimar_gorev_intent("mimarda: mavi logo taslağı")
    ok = bool(hit) and hit.get("motor") == "mimar" and "logo" in str(hit.get("text") or "")
    print(f"  {'OK' if ok else 'FAIL'} mimarda: doldur")
    if not ok:
        fails += 1

    hit2 = parse_mimar_gorev_intent("fotoğraf paneli aç")
    ok2 = bool(hit2) and hit2.get("action") == "panel_ac"
    print(f"  {'OK' if ok2 else 'FAIL'} panel aç")
    if not ok2:
        fails += 1

    for msg in (
        "fotosentez nedir",
        "Karadeniz nerede",
        "ilim nedir",
        "nasılsın",
        "hafızada: not",
        "seste: merhaba",
    ):
        neg = parse_mimar_gorev_intent(msg)
        okn = neg is None
        print(f"  {'OK' if okn else 'FAIL'} negatif {msg[:36]!r}")
        if not okn:
            fails += 1

    # Hub: ilim genel'de
    tgt, _ = resolve_hub_target("fotosentez nedir")
    if tgt != "genel":
        print("FAIL hub ilim", tgt)
        fails += 1
    else:
        print("  OK hub ilim→genel")

    orch = enrich_orchestra_faz_mimar({}, "mimar paneline: kapak afişi")
    ua = orch.get("ui_action") or {}
    if ua.get("motor") != "mimar" or not orch.get("quiet"):
        print("FAIL enrich", ua)
        fails += 1
    else:
        print("  OK enrich")

    orch2, patch = build_genel_orchestra_preview("mimarda: poster")
    if (orch2.get("ui_action") or {}).get("motor") != "mimar" or not patch.get("faz_mimar"):
        print("FAIL preview", orch2.get("ui_action"), patch.get("faz_mimar"))
        fails += 1
    else:
        print("  OK preview faz_mimar")

    # ilim preview'da mimar handoff olmasın
    orch3, _ = build_genel_orchestra_preview("fotosentez nedir")
    ua3 = orch3.get("ui_action") or {}
    if ua3.get("motor") == "mimar":
        print("FAIL ilim mimara kaçtı", ua3)
        fails += 1
    else:
        print("  OK ilim mimara kaçmaz")

    if fails:
        print(f"FAIL ana_motor_faz_mimar_smoke fails={fails}")
        return 1
    print("PASS ana_motor_faz_mimar_smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
