# Created by Ümit & Gökçenur
"""Dilim 9 / çırak dersi — tek yüz erken handoff (ses + hizir) smoke.

Usta notu: İlk çırak görev satırında [cirak:…] path_hint'i bozdu; dosyayı usta yazdı.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from ilim_assistant.ruzgar_orkestrasyon_faz_c import build_genel_orchestra_preview

    fails = 0
    cases = (
        ("seste: cirak deneme", "ses"),
        ("hizirda: cirak not", "hizir"),
    )
    for msg, motor in cases:
        orch, patch = build_genel_orchestra_preview(msg)
        ua = orch.get("ui_action") or {}
        ok = (
            ua.get("type") == "surface_handoff"
            and ua.get("motor") == motor
            and (
                patch.get("faz_ses")
                or patch.get("faz_hizir")
                or orch.get("faz_ses")
                or orch.get("faz_hizir")
            )
        )
        print(f"  {'OK' if ok else 'FAIL'} {msg!r} -> motor={ua.get('motor')!r}")
        if not ok:
            fails += 1

    if fails:
        print(f"FAIL smoke_tek_yuz_early_d9 fails={fails}")
        return 1
    print("PASS smoke_tek_yuz_early_d9")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
