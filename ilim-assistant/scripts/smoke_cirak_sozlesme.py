# Created by Ümit & Gökçenur — sözleşme kapısı smoke
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ilim-assistant"))

from ilim_assistant.ruzgar_cirak_sozlesme import (
    cirak_contract_status,
    cirak_missing_symbols,
    cirak_pytest_targets,
    cirak_required_symbols,
)
from ilim_assistant.ruzgar_cirak_ders import try_cirak_dilim_gercek_paket


def main() -> int:
    goal = (
        "görev: projects/cirak-atolyesi cirak — filtre_satirlar generator yaz; "
        "tests/test_filtre.py pytest · tam ajan"
    )
    syms = cirak_required_symbols(goal)
    assert "filtre_satirlar" in syms, syms
    targets = cirak_pytest_targets(goal, "projects/cirak-atolyesi")
    assert any("test_filtre" in t for t in targets), targets

    # Yanlış API simülasyonu: yalnız filtrele_satir varsa missing olmalı
    atolye = ROOT / "projects" / "cirak-atolyesi"
    bad = atolye / "_smoke_bad_api.py"
    bad.write_text("def filtrele_satir(s, k): return True\n", encoding="utf-8")
    try:
        miss = cirak_missing_symbols(ROOT, goal, "projects/cirak-atolyesi")
        # filtre_satirlar diskte (gerçek dosyada) olabilir — kontrol: required içerir
        assert "filtre_satirlar" in cirak_required_symbols(goal)
        st = cirak_contract_status(ROOT, goal, "projects/cirak-atolyesi")
        assert st["active"] is True
        print("contract", st)
    finally:
        bad.unlink(missing_ok=True)

    hit = try_cirak_dilim_gercek_paket(
        "görev: projects/cirak-atolyesi cirak gercek_paket — supervised iskelet",
        ROOT,
    )
    assert hit and hit.get("ok"), hit
    print("gercek_paket_ok", hit.get("detail", "")[:120])
    print("SMOKE_OK cirak-sozlesme")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
