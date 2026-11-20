# -*- coding: utf-8 -*-
"""Dilim M3 — Masa→Ana Motor mühür kartı (ağ yok; alt smoke import, subprocess yok)."""
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
    from ilim_assistant.ruzgar_masa_soz import coz, masa_sohbet_paket
    from ilim_assistant.ruzgar_sohbet_onay_kapisi import clear_pending, try_handle_sohbet_onay

    clear_pending()

    failed += _ok(coz("belgeye mühür yaz")["eylem"] == "belge.yaz", "belge yaz")
    failed += _ok(coz("tabloda C3 e 1 yaz")["hucre"] == "C3", "tablo hücre")
    failed += _ok(coz("çizime kutu çiz")["eylem"] == "cizim.kutu", "çizim")
    failed += _ok(coz("sunuma bir slayt ekle: M3 | mühür")["baslik"] == "M3", "sunum")
    failed += _ok(coz("belgeyi oku")["eylem"] == "belge.oku", "oku serbest kalıp")
    failed += _ok(coz("A1 hücresine 9 yaz")["deger"] == "9", "hücresine")
    failed += _ok(coz("belgeye a yaz lütfen")["metin"] == "a", "nezaket")
    z = coz("belgeye a yaz ardından tabloda A1 e 2 yaz")
    failed += _ok(isinstance(z, dict) and len(z.get("liste") or []) == 2, "zincir 2")

    p = masa_sohbet_paket("belgeye mühür yaz")
    hit = try_handle_sohbet_onay("belgeye mühür yaz", masa_paket=p)
    failed += _ok(bool(hit and hit.get("masa") is None), "yazma pending")
    applied = try_handle_sohbet_onay("yap", masa_paket=None)
    failed += _ok(
        bool(applied and (applied.get("masa") or {}).get("eylem") == "belge.yaz"),
        "yap uygula",
    )
    clear_pending()

    zincir = masa_sohbet_paket("belgeye x yaz ardından tabloda B1 e 3 yaz")
    z_hit = try_handle_sohbet_onay(
        "belgeye x yaz ardından tabloda B1 e 3 yaz", masa_paket=zincir
    )
    failed += _ok(bool(z_hit and z_hit.get("masa") is None), "zincir pending")
    z_ok = try_handle_sohbet_onay("yap", masa_paket=None)
    failed += _ok(
        bool(z_ok and isinstance((z_ok.get("masa") or {}).get("liste"), list)),
        "zincir yap→liste",
    )
    clear_pending()

    oku = masa_sohbet_paket("belgede ne var")
    failed += _ok(
        try_handle_sohbet_onay("belgede ne var", masa_paket=oku) is None
        and (oku or {}).get("masa", {}).get("eylem") == "belge.oku",
        "okuma serbest",
    )

    ds = (ROOT / "desktop_server.py").read_text(encoding="utf-8")
    app = (REPO / "ruzgar-desktop" / "app.js").read_text(encoding="utf-8")
    masa_js = (REPO / "ruzgar-desktop" / "ruzgar-masa.js").read_text(encoding="utf-8")
    failed += _ok('"masa": done_event.get("masa")' in ds, "full masa alanı")
    failed += _ok("masa: j.masa || null" in app, "client full masa")
    failed += _ok("ruzgarMasaSunucuUygula" in masa_js, "istemci uygula")
    failed += _ok("masaListeUygula" in masa_js, "liste uygula")

    doc = ROOT / "docs" / "M3_MASA_ANA_MOTOR_MUHUR_2026-11-21.md"
    failed += _ok(doc.is_file() and "YEŞİL" in doc.read_text(encoding="utf-8"), "mühür doc")

    # Alt batarya — aynı süreçte (Windows nested pytest/subprocess kilit riski yok)
    scripts = str(ROOT / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    import smoke_masa_ana_motor_bag as bag
    import smoke_sohbet_onay_s1 as onay

    failed += _ok(bag.main() == 0, "alt smoke bag")
    failed += _ok(onay.main() == 0, "alt smoke onay")

    total = 20
    passed = total - failed
    print(f"result: {passed}/{total} pass", flush=True)
    if failed:
        print("MÜHÜR: KIRMIZI", flush=True)
        return 1
    print("MÜHÜR: YEŞİL — Masa→Ana Motor M3", flush=True)
    print("Sonraki: Çırak Dilim A (RUZGAR_CIRAK_GELISIM_PLAN_2026-11-18.md)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
