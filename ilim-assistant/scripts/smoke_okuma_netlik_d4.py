# Created by Ümit & Gökçenur
"""Dilim 4 — Okuma netliği: kısmi kasıtlı; yetim sanılmasın; ilim→genel."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from ilim_assistant.motorlar.ana_motor_hub_faz76 import resolve_hub_target
    from ilim_assistant.motorlar.ruzgar_cekirdegi import (
        HUB_MOTOR_IDS,
        SOHBET_ANA_MOTOR_ALIAS,
        cekirdek_envanter,
    )
    from ilim_assistant.ruzgar_oz_bilgi import MOTOR_KARTLARI, motor_kartlari
    from ilim_assistant.ruzgar_orkestrasyon_faz_c import build_genel_orchestra_preview

    fails = 0

    if "okuma" in HUB_MOTOR_IDS:
        print("FAIL okuma hub listesinde olmamalı")
        fails += 1
    else:
        print("  OK okuma hub dışı")

    if "okuma" not in SOHBET_ANA_MOTOR_ALIAS:
        print("FAIL okuma sohbet alias yok")
        fails += 1
    else:
        print("  OK okuma→Ana Motor alias")

    tgt, meta = resolve_hub_target("fotosentez nedir")
    if tgt != "genel":
        print("FAIL ilim", tgt, meta)
        fails += 1
    else:
        print("  OK ilim→genel")

    orch, _ = build_genel_orchestra_preview("Karadeniz nerede")
    ua = orch.get("ui_action") or {}
    if ua.get("motor") in ("mimar", "okuma"):
        print("FAIL coğrafya atölyeye kaçtı", ua)
        fails += 1
    else:
        print("  OK coğrafya atölyeye kaçmaz")

    kart = next(m for m in MOTOR_KARTLARI if m["id"] == "okuma")
    if kart.get("hub") is not False or kart.get("bag") != "kismi_kasten":
        print("FAIL kart", kart)
        fails += 1
    else:
        print("  OK kart bag=kismi_kasten hub=False")

    if "yetim" in str(kart.get("huner") or "").lower() and "değil" not in str(
        kart.get("huner") or ""
    ).lower():
        print("FAIL kart yetim gibi yazılmış")
        fails += 1
    else:
        print("  OK kart yetim sanılmaz")

    live = motor_kartlari()
    okuma_live = next(x for x in live if x["id"] == "okuma")
    env = cekirdek_envanter()
    if "okuma" in (env.get("hub_motors") or []):
        print("FAIL canlı envanter hub")
        fails += 1
    else:
        print("  OK canlı envanter", okuma_live.get("bag") or kart.get("bag"))

    if fails:
        print(f"FAIL smoke_okuma_netlik_d4 fails={fails}")
        return 1
    print("PASS smoke_okuma_netlik_d4")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
