# -*- coding: utf-8 -*-
"""Dilim M1 — Ana motor masa bağı: paket → onay → full/istemci izi (ağ yok)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _ok(cond: bool, label: str) -> int:
    print(("OK" if cond else "FAIL"), "-", label)
    return 0 if cond else 1


def main() -> int:
    failed = 0
    from ilim_assistant.ruzgar_masa_soz import coz, masa_sohbet_paket
    from ilim_assistant.ruzgar_sohbet_onay_kapisi import (
        clear_pending,
        try_handle_sohbet_onay,
    )

    clear_pending()

    # Dört masa — yazma paketi
    for msg, eylem in (
        ("belgeye selam yaz", "belge.yaz"),
        ("tabloda A1 e 10 yaz", "tablo.hucre"),
        ("çizime kutu çiz", "cizim.kutu"),
        ("sunuma Hoş geldin slaytı ekle: bugün", "sunum.ekle"),
    ):
        p = masa_sohbet_paket(msg)
        failed += _ok(
            bool(p and p.get("masa") and (p["masa"].get("eylem") == eylem or p["masa"].get("liste"))),
            f"paket {eylem}",
        )

    # Nezaket
    failed += _ok(
        coz("belgeye merhaba yaz lütfen") == {"eylem": "belge.yaz", "metin": "merhaba"},
        "nezaket lütfen",
    )

    # Yazma → onay ister; «yap» ile masa gelir
    p = masa_sohbet_paket("belgeye kalfa yolu yaz")
    hit = try_handle_sohbet_onay("belgeye kalfa yolu yaz", masa_paket=p)
    failed += _ok(
        bool(hit and hit.get("masa") is None and "yap" in (hit.get("reply") or "").lower()),
        "yazma onay bekler",
    )
    apply = try_handle_sohbet_onay("yap", masa_paket=None)
    failed += _ok(
        bool(apply and (apply.get("masa") or {}).get("eylem") == "belge.yaz"),
        "yap → masa eylem",
    )
    clear_pending()

    # Okuma serbest (onay yok)
    oku = masa_sohbet_paket("belgede ne yazıyor")
    free = try_handle_sohbet_onay("belgede ne yazıyor", masa_paket=oku)
    failed += _ok(free is None and (oku or {}).get("masa", {}).get("eylem") == "belge.oku", "okuma serbest")

    # Dilim M2 — doğal + zincir + onay
    failed += _ok(coz("A1 hücresine 7 yaz")["deger"] == "7", "M2 hücresine")
    failed += _ok(coz("belgeye yaz merhaba")["metin"] == "merhaba", "M2 yaz boşluksuz")
    zincir = masa_sohbet_paket("belgeye selam yaz ardından tabloda B2 e 5 yaz")
    failed += _ok(
        bool(zincir and isinstance((zincir.get("masa") or {}).get("liste"), list) and len(zincir["masa"]["liste"]) == 2),
        "M2 zincir paket",
    )
    clear_pending()
    z_hit = try_handle_sohbet_onay(
        "belgeye selam yaz ardından tabloda B2 e 5 yaz",
        masa_paket=zincir,
    )
    failed += _ok(bool(z_hit and z_hit.get("masa") is None), "M2 zincir onay bekler")
    z_ok = try_handle_sohbet_onay("yap", masa_paket=None)
    failed += _ok(
        bool(z_ok and isinstance((z_ok.get("masa") or {}).get("liste"), list)),
        "M2 zincir yap→liste",
    )
    clear_pending()

    # /api/chat/full masa alanı + istemci uygula
    ds = (ROOT / "desktop_server.py").read_text(encoding="utf-8")
    failed += _ok('"masa": done_event.get("masa")' in ds, "full JSON masa")
    failed += _ok("masa_sohbet_paket" in ds and "try_handle_sohbet_onay" in ds, "stream masa+onay")
    app = (REPO / "ruzgar-desktop" / "app.js").read_text(encoding="utf-8")
    failed += _ok("masa: j.masa || null" in app, "client full→done.masa")
    masa_js = (REPO / "ruzgar-desktop" / "ruzgar-masa.js").read_text(encoding="utf-8")
    failed += _ok("ruzgarMasaSunucuUygula" in masa_js and "masaUygula" in masa_js, "istemci uygula")

    total = 17
    print(f"result: {total - failed}/{total} pass")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
