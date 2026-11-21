# -*- coding: utf-8 -*-
# Created by Ümit & Gökçenur
"""S3 smoke — BUSENAZ + kuran klon yolu · Edge yedek."""
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
    from ilim_assistant.motorlar.ses_klon_motoru import (
        clone_status_snapshot,
        coz_referans_yolu,
        coz_tilavet_referans_yolu,
        should_use_clone,
    )
    from ilim_assistant.ses_s3_klon_yolu import (
        S3_VERSION,
        run_s3_card,
        write_s3_docs,
    )
    from ilim_assistant.tts_service import read_ses_ayarlari

    failed = 0
    total = 0

    def check(cond: bool, label: str) -> None:
        nonlocal failed, total
        total += 1
        failed += _ok(cond, label)

    check("s3-klon-yolu" in S3_VERSION, f"ver {S3_VERSION}")

    ay = read_ses_ayarlari()
    muh = coz_referans_yolu("muhabbet", ayar=ay)
    til = coz_tilavet_referans_yolu("kuran", ayar=ay)
    check(muh is not None and muh.is_file(), f"muhabbet ref={muh}")
    check(
        muh is not None
        and ("BUSENAZ" in muh.name.upper() or muh.name.lower() == "muhabbet.wav"),
        f"BUSENAZ/muhabbet name={muh.name if muh else None}",
    )
    check(til is not None and til.name.lower() == "kuran.wav", f"kuran={til}")

    til_kar = coz_referans_yolu("tilavet", ayar=ay)
    check(
        til_kar is not None and "kuran" in til_kar.name.lower(),
        f"tilavet→kuran {til_kar}",
    )

    check(bool(ay.get("klon_onay") or ay.get("prefer_clone")), "klon_onay ayar")

    # backend=clone her zaman True (sonra API Edge'e düşer)
    check(
        should_use_clone(backend="clone", karakter="muhabbet", ayar=ay) is True,
        "should_clone=True",
    )
    check(
        should_use_clone(backend="edge", karakter="muhabbet", ayar=ay) is False,
        "should_edge=False",
    )

    st = clone_status_snapshot()
    check(isinstance(st.get("s3"), dict), "status.s3 block")
    check(bool((st.get("s3") or {}).get("edge_yedek")), "status edge_yedek")

    bus = ROOT / "arsiv" / "klon-sesler-umit-ozel" / "BUSENAZ ses.wav"
    check(bus.is_file() and bus.stat().st_size > 4096, "BUSENAZ ses.wav ozel")

    ds = (ROOT / "desktop_server.py").read_text(encoding="utf-8")
    check("RUZGAR_TTS_CLONE_STRICT" in ds, "API STRICT")
    check("edge_yedek_meta" in ds, "API edge yedek")
    check("clone_fallback" in ds, "API clone_fallback")

    card = run_s3_card()
    check(bool(card.get("s3_yesil")), f"s3_yesil={card.get('s3_yesil')}")
    check(bool((card.get("referans") or {}).get("busenaz_ok")), "card busenaz_ok")
    check(
        bool((card.get("referans") or {}).get("tilavet_kuran_ok")),
        "card tilavet_kuran_ok",
    )
    check(bool((card.get("edge_yedek") or {}).get("ok")), "edge sozlesme")

    paths = write_s3_docs(card)
    md = Path(paths["md"])
    check(md.is_file() and "BUSENAZ" in md.read_text(encoding="utf-8"), "doc")

    # S1/S2 regresyon hafif
    from ilim_assistant.ses_s1_tavan_profil import coz_tavan_profil
    from ilim_assistant.ses_s2_prosodi_tavan import s2_enabled

    check(coz_tavan_profil("asistan") == "muhabbet", "S1 duruyor")
    check(s2_enabled(), "S2 duruyor")

    print(f"result: {total - failed}/{total} pass")
    print(
        f"xtts={card.get('xtts_runtime')} klon_canli={card.get('klon_canli')} "
        f"→ {card.get('not', '')[:80]}"
    )
    print(f"wrote {md.name}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
