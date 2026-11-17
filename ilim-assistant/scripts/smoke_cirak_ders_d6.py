# Created by Ümit & Gökçenur
"""Dilim 6 — Çırak ders sözleşmesi smoke."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from ilim_assistant.ruzgar_cirak_ders import (
        CIRAK_GOREV_TURLERI,
        USTA_KIRILGAN,
        cirak_gorev_metni,
        cirak_status,
        yesil_dilim_icin_ders_gerekli,
    )

    fails = 0

    from ilim_assistant.ruzgar_cirak_ders import wants_full_code_agent

    g = cirak_gorev_metni("smoke_yesil", "ana_motor_faz_ses_smoke geçsin")
    if (
        not g.startswith("görev:")
        or "cirak smoke_yesil" not in g
        or "[cirak:" in g
        or "tam ajan" not in g
    ):
        print("FAIL gorev metni", g)
        fails += 1
    else:
        print("  OK çırak görev satırı")
    if not wants_full_code_agent(g):
        print("FAIL wants_full_code_agent")
        fails += 1
    else:
        print("  OK wants_full_code_agent")

    from pathlib import Path

    from ilim_assistant.ruzgar_cirak_ders import try_cirak_supervised_write

    root = Path(__file__).resolve().parents[2]
    probe = (
        "görev: cirak smoke_yesil — projects/cirak-atolyesi/_smoke_probe.py "
        "print PASS cirak-d9 · tam ajan"
    )
    wr = try_cirak_supervised_write(probe, root)
    probe_path = root / "projects" / "cirak-atolyesi" / "_smoke_probe.py"
    okw = bool(wr and wr.get("ok") and probe_path.is_file())
    print(f"  {'OK' if okw else 'FAIL'} supervised write")
    if not okw:
        fails += 1
    else:
        try:
            probe_path.unlink()
        except OSError:
            pass

    bad = yesil_dilim_icin_ders_gerekli({})
    if bad.get("ok"):
        print("FAIL boş ders yeşil olmamalı")
        fails += 1
    else:
        print("  OK ders yoksa yeşil değil")

    good = yesil_dilim_icin_ders_gerekli(
        {
            "dilim": "1",
            "ders": "profil anlığı çalma",
            "smoke_veya_dosya": "ana_motor_faz_ses_smoke.py",
        }
    )
    if not good.get("ok"):
        print("FAIL dolu ders", good)
        fails += 1
    else:
        print("  OK ders ile yeşil")

    st = cirak_status()
    if "boot_sirasi" not in USTA_KIRILGAN or "tek_dosya_patch" not in CIRAK_GOREV_TURLERI:
        print("FAIL listeler")
        fails += 1
    else:
        print("  OK usta/çırak ayrımı", st.get("version"))

    if fails:
        print(f"FAIL smoke_cirak_ders_d6 fails={fails}")
        return 1
    print("PASS smoke_cirak_ders_d6")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
