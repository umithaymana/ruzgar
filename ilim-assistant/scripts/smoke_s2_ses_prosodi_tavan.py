# -*- coding: utf-8 -*-
# Created by Ümit & Gökçenur
"""S2 smoke — prosodi + tilavet/âlim parametre tavanı."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _ok(cond: bool, label: str) -> int:
    print(("OK" if cond else "FAIL"), "-", label)
    return 0 if cond else 1


def main() -> int:
    from ilim_assistant.ses_s2_prosodi_tavan import (
        S2_VERSION,
        TAVAN_PARAM,
        ayarla_durak_carpani,
        ayarla_hiz_huzur,
        ayarla_rate_string,
        coz_tts_tavan_paketi,
        run_s2_card,
        s2_enabled,
        write_s2_docs,
    )

    failed = 0
    total = 0

    def check(cond: bool, label: str) -> None:
        nonlocal failed, total
        total += 1
        failed += _ok(cond, label)

    check("s2-prosodi-tavan" in S2_VERSION, f"ver {S2_VERSION}")
    check(s2_enabled(), "S2 varsayılan açık")
    check(set(TAVAN_PARAM) == {"muhabbet", "alim", "tilavet"}, "üç tavan param")

    # Hız/huzur sıkıştırma
    h_m, z_m = ayarla_hiz_huzur("muhabbet", hiz=0.92, huzur=0.88)
    h_t, z_t = ayarla_hiz_huzur("tilavet", hiz=0.92, huzur=0.88)
    check(h_t < h_m and z_t < z_m, f"tilavet daha yavas h={h_t}/{h_m} z={z_t}/{z_m}")

    d_m = ayarla_durak_carpani("muhabbet", 1.0)
    d_a = ayarla_durak_carpani("alim", 1.0)
    d_t = ayarla_durak_carpani("tilavet", 1.0)
    check(d_t > d_a > d_m, f"durak {d_m}<{d_a}<{d_t}")

    r0 = ayarla_rate_string("-20%", "muhabbet")
    r1 = ayarla_rate_string("-20%", "tilavet")
    check(r0 == "-20%", f"muhabbet rate ekstra yok {r0}")
    check(r1 != r0 and float(r1.rstrip("%")) < -20, f"tilavet rate ekstra {r1}")

    paket = coz_tts_tavan_paketi("tilavet", ayar={"hiz": 0.92, "huzur": 0.88, "durak": 1.0})
    check(paket.get("tilavet_durak") is True, "tilavet_durak flag")
    check(paket.get("tavan") == "tilavet", "paket tavan")

    # API kanca
    ds = (ROOT / "desktop_server.py").read_text(encoding="utf-8")
    check("coz_tts_tavan_paketi" in ds, "api_tts S2 kanca")
    check("tilavet=tilavet_pause" in ds or "tilavet=tilavet_pause" in ds.replace(" ", ""), "api prosody tilavet")

    ts = (ROOT / "ilim_assistant" / "tts_service.py").read_text(encoding="utf-8")
    check("tilavet: bool = False" in ts, "prosody tilavet param")

    card = run_s2_card()
    check(bool(card.get("distinct_pause_ok")), "distinct pause")
    check(bool(card.get("distinct_rate_ok")), "distinct rate")
    check(bool(card.get("s2_yesil")), f"s2_yesil={card.get('s2_yesil')}")
    ayet = (card.get("tilavet_ornek") or {}).get("ayet_durak_ms") or 0
    check(int(ayet) >= 1500, f"ayet_durak_ms={ayet}")
    check(len(card.get("kulak_liste") or []) == 3, "kulak checklist 3")

    paths = write_s2_docs(card)
    md = Path(paths["md"])
    check(md.is_file() and "tilavet" in md.read_text(encoding="utf-8"), "doc")

    # S1 regresyon hafif
    from ilim_assistant.ses_s1_tavan_profil import coz_tavan_profil

    check(coz_tavan_profil("asistan") == "muhabbet", "S1 alias duruyor")

    print(f"result: {total - failed}/{total} pass")
    print(f"wrote {md.name}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
