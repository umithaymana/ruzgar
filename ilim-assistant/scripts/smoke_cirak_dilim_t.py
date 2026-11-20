# -*- coding: utf-8 -*-
"""Çırak Dilim T — tavan dersi + onaysız yükseltme red (ağ yok)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _ok(cond: bool, label: str) -> int:
    print(("OK" if cond else "FAIL"), "-", label, flush=True)
    return 0 if cond else 1


def main() -> int:
    failed = 0
    from ilim_assistant.ruzgar_cirak_ders import (
        TAVAN_USTU_YASAK,
        try_cirak_dilim_t_tavan,
        try_cirak_tavan_yukselt,
    )

    ders_hit = try_cirak_dilim_t_tavan(
        "görev: projects/cirak-atolyesi cirak tavan_ders — Dilim T tavan ders · tam ajan",
        REPO,
    )
    failed += _ok(bool(ders_hit and ders_hit.get("ok")), "tavan ders ok")

    t_md = REPO / "projects" / "cirak-atolyesi" / "TAVAN_DERS.md"
    text = t_md.read_text(encoding="utf-8") if t_md.is_file() else ""
    failed += _ok(t_md.is_file() and "Tavan şimdi" in text, "TAVAN_DERS dosya")
    failed += _ok("genel_saha" in text and "boot_yuz_hub" in text, "üst yasaklar yazılı")

    red = try_cirak_dilim_t_tavan(
        "görev: projects/cirak-atolyesi cirak tavan_ders — Dilim T "
        "tavanı kaldır deneme genel saha aç · tam ajan",
        REPO,
    )
    failed += _ok(
        bool(
            red
            and red.get("ok")
            and red.get("writes_blocked")
            and red.get("rejected") == "tavan_ustu"
            and red.get("writes_ok") == 0
        ),
        "kaldır deneme red",
    )

    ty = try_cirak_tavan_yukselt(
        "görev: projects/cirak-atolyesi cirak tavan_yukselt — izinsiz · tam ajan",
        REPO,
    )
    failed += _ok(
        bool(ty and ty.get("writes_blocked") and ty.get("rejected") == "tavan_ustu"),
        "yukselt onaysız red",
    )

    failed += _ok("genel_saha" in TAVAN_USTU_YASAK, "TAVAN_USTU genel_saha")
    failed += _ok("boot_yuz_hub" in TAVAN_USTU_YASAK, "TAVAN_USTU boot_yuz_hub")

    ana = REPO / "ilim-assistant" / "ilim_assistant" / "TAVAN_DERS.md"
    failed += _ok(not ana.is_file(), "ana paket yok")

    total = 8
    print(f"result: {total - failed}/{total} pass", flush=True)
    if failed:
        print("Dilim T: KIRMIZI", flush=True)
        return 1
    print("Dilim T: YEŞİL — tavan ders + yükseltme red", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
