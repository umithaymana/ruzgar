# -*- coding: utf-8 -*-
# Created by Ümit & Gökçenur
"""S1 smoke — muhabbet / âlim / tilavet Edge profil seçici."""
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
    from ilim_assistant.motorlar.ses_motoru import (
        SesKarakteri,
        normalize_ses_karakteri,
        varsayilan_karakter_icerige,
        IcerikYolu,
    )
    from ilim_assistant.ses_s1_tavan_profil import (
        S1_VERSION,
        TAVAN_PROFILLER,
        coz_tavan_profil,
        run_s1_card,
        set_tavan_profil,
        sohbet_profil_dogru_mu,
        write_s1_docs,
    )

    failed = 0
    total = 0

    def check(cond: bool, label: str) -> None:
        nonlocal failed, total
        total += 1
        failed += _ok(cond, label)

    check("s1-tavan-profil" in S1_VERSION, f"ver {S1_VERSION}")
    check(
        TAVAN_PROFILLER == ("muhabbet", "alim", "tilavet"),
        f"tavan={TAVAN_PROFILLER}",
    )

    # Alias / normalize
    check(
        normalize_ses_karakteri("asistan") == SesKarakteri.muhabbet,
        "asistan→muhabbet",
    )
    check(normalize_ses_karakteri("tilavet") == SesKarakteri.tilavet, "tilavet enum")
    check(normalize_ses_karakteri("kuran") == SesKarakteri.tilavet, "kuran→tilavet")
    check(coz_tavan_profil("asistan") == "muhabbet", "coz asistan")
    check(
        varsayilan_karakter_icerige(IcerikYolu.kuran) == SesKarakteri.tilavet,
        "icerik kuran→tilavet",
    )
    check(
        varsayilan_karakter_icerige(IcerikYolu.genel) == SesKarakteri.muhabbet,
        "icerik genel→muhabbet",
    )

    # Üç profil set + sohbet doğruluğu (ayar geri alınır)
    from ilim_assistant.tts_service import read_ses_ayarlari, write_ses_ayarlari

    onceki = str(read_ses_ayarlari().get("karakter") or "muhabbet")
    try:
        for p in TAVAN_PROFILLER:
            r = set_tavan_profil(p)
            check(r.get("ok") is True, f"set {p}")
            check(
                sohbet_profil_dogru_mu(p, read_ses_ayarlari()),
                f"sohbet profil doğru {p}",
            )
            snap = r.get("snapshot") or {}
            check(bool(snap.get("voice")), f"voice {p}={snap.get('voice')}")
            check(bool(snap.get("rate")), f"rate {p}={snap.get('rate')}")
    finally:
        write_ses_ayarlari({"karakter": normalize_ses_karakteri(onceki).value})

    card = run_s1_card()
    check(bool(card.get("alias_ok")), "alias_ok")
    check(bool(card.get("distinct_ok")), "distinct rate/pitch")
    check(bool(card.get("s1_yesil")), f"s1_yesil={card.get('s1_yesil')}")

    paths = write_s1_docs(card)
    md = Path(paths["md"])
    check(md.is_file() and "muhabbet" in md.read_text(encoding="utf-8"), "doc")

    # Desktop JS alias
    app_js = ROOT.parent / "ruzgar-desktop" / "app.js"
    txt = app_js.read_text(encoding="utf-8") if app_js.is_file() else ""
    check('return "muhabbet"' in txt, "app.js muhabbet default")
    check("tilavet" in txt and "normalizeKarakterForTts" in txt, "app.js tilavet")

    # BUSENAZ ref varlık (klon S3; S1 bozmaz)
    busenaz = ROOT / "arsiv" / "klon-sesler-umit-ozel" / "BUSENAZ ses.wav"
    check(busenaz.is_file() and busenaz.stat().st_size > 4096, "BUSENAZ ses.wav")

    print(f"result: {total - failed}/{total} pass")
    print(f"wrote {md.name}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
