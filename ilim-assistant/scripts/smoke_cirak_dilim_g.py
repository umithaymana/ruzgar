# -*- coding: utf-8 -*-
"""Çırak Dilim G — hibrit doğruluk: written + disk + smoke (ağ yok)."""
from __future__ import annotations

import subprocess
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
        claim_yesil_gecerli,
        try_cirak_dilim_g_hibrit,
    )

    hit = try_cirak_dilim_g_hibrit(
        "görev: projects/cirak-atolyesi cirak hibrit_g — Dilim G hibrit doğruluk · tam ajan",
        REPO,
    )
    failed += _ok(bool(hit and hit.get("ok")), "dilim g ok")
    failed += _ok(bool(hit and hit.get("disk_ok") and hit.get("smoke_ok")), "disk+smoke")

    atolye = REPO / "projects" / "cirak-atolyesi"
    mod = atolye / "hibrit_g_modul.py"
    sm = atolye / "smoke_hibrit_g.py"
    ders = atolye / "DERS_G_HIBRIT.md"
    failed += _ok(mod.is_file() and "PASS cirak-G" in mod.read_text(encoding="utf-8"), "modul PASS")
    failed += _ok(sm.is_file(), "smoke dosya")
    failed += _ok(
        ders.is_file() and "live-bat" in ders.read_text(encoding="utf-8"),
        "ders live-bat",
    )

    r = subprocess.run(
        [sys.executable, str(sm)],
        cwd=str(atolye),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=15,
    )
    failed += _ok(r.returncode == 0 and "PASS cirak-G" in (r.stdout or ""), "PASS cirak-G")

    bad = claim_yesil_gecerli(written="", disk_ok=True, smoke_ok=True)
    failed += _ok(not bad.get("ok"), "kansız iddia kırmızı")

    ana = REPO / "ilim-assistant" / "ilim_assistant" / "hibrit_g_modul.py"
    failed += _ok(not ana.is_file(), "ana paket yok")

    total = 8
    print(f"result: {total - failed}/{total} pass", flush=True)
    if failed:
        print("Dilim G: KIRMIZI", flush=True)
        return 1
    print("Dilim G: YEŞİL — written+disk+smoke", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
