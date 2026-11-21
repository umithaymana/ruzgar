# -*- coding: utf-8 -*-
# Created by Ümit & Gökçenur
"""S4 smoke — raftan kısa pasaj → sesle oku bağ (masa+mobil API)."""
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
    from ilim_assistant.ses_s4_okuma_bag import (
        S4_VERSION,
        parse_okuma_ses_komut,
        prepare_okuma_ses,
        run_s4_card,
        s4_enabled,
        write_s4_docs,
    )

    failed = 0
    total = 0

    def check(cond: bool, label: str) -> None:
        nonlocal failed, total
        total += 1
        failed += _ok(cond, label)

    check("s4-okuma-bag" in S4_VERSION, f"ver {S4_VERSION}")
    check(s4_enabled(), "S4 varsayılan açık")

    cmd = parse_okuma_ses_komut("raftan oku fotosentez")
    check(bool(cmd and cmd.get("query") == "fotosentez"), f"komut parse {cmd}")

    prep = prepare_okuma_ses("fotosentez", action="oku", session_id="_smoke_s4")
    check(bool(prep.get("ok")), f"pasaj ok={prep.get('ok')} err={prep.get('error')}")
    check(int(prep.get("chars") or 0) >= 40, f"chars={prep.get('chars')}")
    check(prep.get("karakter") in ("alim", "tilavet", "muhabbet"), f"kar={prep.get('karakter')}")
    check(bool(prep.get("yol")), f"yol={prep.get('yol')}")
    check(bool(prep.get("mobil_ayni_api")), "mobil_ayni_api")

    devam = prepare_okuma_ses("fotosentez", action="devam", session_id="_smoke_s4")
    check(bool(devam.get("ok")), f"devam ok={devam.get('ok')}")
    check(
        int(devam.get("offset") or 0) > 0 or devam.get("pasaj") != prep.get("pasaj"),
        f"devam offset={devam.get('offset')}",
    )

    tekrar = prepare_okuma_ses(action="tekrar", session_id="_smoke_s4")
    check(
        bool(tekrar.get("ok") and tekrar.get("pasaj") == devam.get("pasaj")),
        "tekrar ayni pasaj",
    )

    yavas = prepare_okuma_ses(action="yavas", session_id="_smoke_s4")
    check(bool(yavas.get("ok") and yavas.get("yavas")), "yavas bayrak")

    # API kancaları
    ds = (ROOT / "desktop_server.py").read_text(encoding="utf-8")
    check("/api/okuma/pasaj" in ds, "api pasaj")
    check("/api/okuma/sesle" in ds, "api sesle")
    check("prepare_okuma_ses" in ds, "api prepare")

    desk = ROOT.parent / "ruzgar-desktop" / "app.js"
    desk_txt = desk.read_text(encoding="utf-8") if desk.is_file() else ""
    check("speakRaftanPasaj" in desk_txt, "masa speakRaftanPasaj")
    check("btn-ses-raftan" in desk_txt or "btnSesRaftan" in desk_txt, "masa buton kanca")

    mob = ROOT / "static" / "mobil-pwa" / "app.js"
    mob_txt = mob.read_text(encoding="utf-8") if mob.is_file() else ""
    check("speakRaftanPasaj" in mob_txt, "mobil speakRaftanPasaj")
    check("parseRaftanChatCmd" in mob_txt, "mobil chat komut")
    check("/api/okuma/pasaj" in mob_txt, "mobil pasaj API")

    # S1–S3 regresyon hafif
    from ilim_assistant.ses_s1_tavan_profil import coz_tavan_profil
    from ilim_assistant.ses_s2_prosodi_tavan import s2_enabled
    from ilim_assistant.ses_s3_klon_yolu import S3_VERSION

    check(coz_tavan_profil("asistan") == "muhabbet", "S1 duruyor")
    check(s2_enabled(), "S2 duruyor")
    check("s3-klon" in S3_VERSION, "S3 modül duruyor")

    card = run_s4_card()
    check(bool(card.get("s4_yesil")), f"s4_yesil={card.get('s4_yesil')}")
    check(len(card.get("kulak_liste") or []) == 3, "kulak 3")

    paths = write_s4_docs(card)
    md = Path(paths["md"])
    check(md.is_file() and "pasaj" in md.read_text(encoding="utf-8").lower(), "doc")

    print(f"result: {total - failed}/{total} pass")
    print(
        f"demo={ (card.get('demo') or {}).get('eser_id') } "
        f"kar={ (card.get('demo') or {}).get('karakter') } "
        f"chars={ (card.get('demo') or {}).get('chars') }"
    )
    print(f"wrote {md.name}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
