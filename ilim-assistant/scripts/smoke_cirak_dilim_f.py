# -*- coding: utf-8 -*-
"""Çırak Dilim F — mini mühür + gece raporu (ağ yok)."""
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
    from ilim_assistant.ruzgar_cirak_ders import try_cirak_dilim_f_muhur

    hit = try_cirak_dilim_f_muhur(
        "görev: projects/cirak-atolyesi cirak mini_muhur — Dilim F gece_rapor · tam ajan",
        REPO,
    )
    failed += _ok(bool(hit and hit.get("ok")), "dilim f ok")
    failed += _ok(int(hit.get("writes_ok") or 0) >= 2, "iki yazım")

    atolye = REPO / "projects" / "cirak-atolyesi"
    muhur = atolye / "MINI_MUHUR_DILIM_F.md"
    gece = atolye / "GECE_RAPORU_2026-11-18.md"
    failed += _ok(muhur.is_file(), "MINI_MUHUR dosya")
    failed += _ok(gece.is_file(), "GECE_RAPORU dosya")

    mt = muhur.read_text(encoding="utf-8") if muhur.is_file() else ""
    gt = gece.read_text(encoding="utf-8") if gece.is_file() else ""
    failed += _ok(
        "atölye çırağı hazır" in mt.lower() and "genel saha hayır" in mt.lower(),
        "mühür cümlesi",
    )
    failed += _ok(all(f"- {k}: yeşil" in mt for k in "ABCDE"), "A–E yeşil kart")
    failed += _ok("genel saha" in gt.lower() and "hayır" in gt.lower() or "açma" in gt.lower(), "gece saha kapalı")

    ana = REPO / "ilim-assistant" / "ilim_assistant" / "MINI_MUHUR_DILIM_F.md"
    failed += _ok(not ana.is_file(), "ana paket yok")

    total = 8
    print(f"result: {total - failed}/{total} pass", flush=True)
    if failed:
        print("Dilim F: KIRMIZI", flush=True)
        return 1
    print("Dilim F: YEŞİL — atölye çırağı hazır; genel saha hayır", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
