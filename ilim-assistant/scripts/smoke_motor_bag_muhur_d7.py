# Created by Ümit & Gökçenur
"""Dilim 7 — Motor bağ mühür: öz-bilgi kartları ↔ tek yüz gerçeği."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from ilim_assistant.ana_motor_faz_hafiza_tek_yuz import faz_hafiza_enabled
    from ilim_assistant.ana_motor_faz_hizir_tek_yuz import faz_hizir_enabled
    from ilim_assistant.ana_motor_faz_mimar_tek_yuz import faz_mimar_enabled
    from ilim_assistant.ana_motor_faz_ses_tek_yuz import faz_ses_enabled
    from ilim_assistant.ana_motor_faz6c_tek_yuz import faz6c_enabled
    from ilim_assistant.ana_motor_faz_e_tek_yuz import faz_e_enabled
    from ilim_assistant.ruzgar_cirak_ders import cirak_status
    from ilim_assistant.ruzgar_oz_bilgi import MOTOR_KARTLARI, kapasite_karti, motor_kartlari

    fails = 0

    expect_tek = {
        "ses": faz_ses_enabled(),
        "hafiza": faz_hafiza_enabled(),
        "mimar": faz_mimar_enabled(),
        "hizir": faz_hizir_enabled(),
        "programlama": faz6c_enabled(),
        "video": faz_e_enabled(),
        "tercume": faz_e_enabled(),
    }

    by_id = {m["id"]: m for m in MOTOR_KARTLARI}
    for mid, on in expect_tek.items():
        kart = by_id.get(mid) or {}
        flagged = bool(kart.get("tek_yuz"))
        if on and mid in ("ses", "hafiza", "mimar", "hizir", "programlama", "video", "tercume"):
            # kartta tek_yuz True beklenenler (programlama/video/tercume kartta bayrak yoksa hub+huner yeter)
            if mid in ("ses", "hafiza", "mimar", "hizir") and not flagged:
                print(f"FAIL {mid} kart tek_yuz yok")
                fails += 1
            else:
                print(f"  OK {mid} tek_yuz/faz açık")

    okuma = by_id["okuma"]
    if okuma.get("hub") is not False or okuma.get("bag") != "kismi_kasten":
        print("FAIL okuma dürüst değil", okuma)
        fails += 1
    else:
        print("  OK okuma kismi_kasten")

    kap = kapasite_karti()
    if "Programlama tavanı" not in " ".join(kap.get("zayif") or []) and "~%70" not in str(
        kap.get("tavan")
    ):
        # tavan dict
        if kap.get("tavan", {}).get("programlama") != "~%70":
            print("FAIL kapasite tavan", kap.get("tavan"))
            fails += 1
        else:
            print("  OK kapasite tavan")
    else:
        print("  OK kapasite dürüst")

    live = motor_kartlari()
    if len(live) < 8:
        print("FAIL motor_kartlari kısa", len(live))
        fails += 1
    else:
        print("  OK motor_kartlari", len(live))

    st = cirak_status()
    if not st.get("enabled"):
        print("FAIL cirak")
        fails += 1
    else:
        print("  OK cirak", st.get("version"))

    if fails:
        print(f"FAIL smoke_motor_bag_muhur_d7 fails={fails}")
        return 1
    print("PASS smoke_motor_bag_muhur_d7")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
