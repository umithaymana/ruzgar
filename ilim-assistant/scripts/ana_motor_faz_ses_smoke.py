# Created by Ümit & Gökçenur
"""Smoke — Dilim 1 Ses tek yüz: sohbet → Ses quiet handoff + negatifler."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from ilim_assistant.ana_motor_faz_ses_tek_yuz import (
        enrich_orchestra_faz_ses,
        parse_ses_gorev_intent,
    )
    from ilim_assistant.ruzgar_orkestrasyon_faz_c import build_genel_orchestra_preview

    fails = 0

    hit = parse_ses_gorev_intent("seste: Selam Ümit abi, bu bir deneme metni.")
    ok = bool(hit) and hit.get("motor") == "ses" and "Selam" in str(hit.get("text") or "")
    print(f"  {'OK' if ok else 'FAIL'} seste: doldur")
    if not ok:
        fails += 1

    hit2 = parse_ses_gorev_intent("ses paneli aç")
    ok2 = bool(hit2) and hit2.get("action") == "panel_ac"
    print(f"  {'OK' if ok2 else 'FAIL'} panel aç")
    if not ok2:
        fails += 1

    hit3 = parse_ses_gorev_intent("sesle oku: Bismillahirrahmanirrahim")
    ok3 = bool(hit3) and hit3.get("action") == "oku_doldur"
    print(f"  {'OK' if ok3 else 'FAIL'} sesle oku")
    if not ok3:
        fails += 1

    for msg in (
        "nasılsın bugün",
        "fotosentez nedir",
        "alim moduna geç",
        "stt durumu",
        "şu videoyu indir https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    ):
        neg = parse_ses_gorev_intent(msg)
        okn = neg is None
        print(f"  {'OK' if okn else 'FAIL'} negatif {msg[:36]!r}")
        if not okn:
            fails += 1

    # Canlı ders: «seste: Merhaba…» casual sayılmasın
    try:
        from ilim_assistant.ana_motor_plan import looks_like_casual_social_chat

        if looks_like_casual_social_chat("seste: Merhaba Ümit abi, dilim1 deneme"):
            print("FAIL seste: casual sayılmamalı")
            fails += 1
        else:
            print("  OK seste: casual değil")
    except Exception as exc:
        print("FAIL casual check", exc)
        fails += 1

    orch = enrich_orchestra_faz_ses({}, "ses atölyesinde: Merhaba Rüzgar")
    ua = orch.get("ui_action") or {}
    if not orch.get("quiet") or ua.get("motor") != "ses" or ua.get("kind") != "ses_gorev":
        print("FAIL enrich", ua)
        fails += 1
    else:
        print("  OK enrich_orchestra_faz_ses")

    # 6c/E önce gelirse ses ezmez
    orch_skip = enrich_orchestra_faz_ses(
        {"ui_action": {"type": "surface_handoff", "motor": "video"}},
        "seste: x",
    )
    if orch_skip.get("ui_action", {}).get("motor") != "video":
        print("FAIL skip when ui_action set")
        fails += 1
    else:
        print("  OK mevcut ui_action korunur")

    orch2, patch = build_genel_orchestra_preview("seste: Çırak ders metni")
    ua2 = orch2.get("ui_action") or {}
    if ua2.get("motor") != "ses" or not patch.get("faz_ses"):
        print("FAIL preview", ua2, patch.get("faz_ses"))
        fails += 1
    else:
        print("  OK build_genel_orchestra_preview faz_ses")

    if fails:
        print(f"FAIL ana_motor_faz_ses_smoke fails={fails}")
        return 1
    print("PASS ana_motor_faz_ses_smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
