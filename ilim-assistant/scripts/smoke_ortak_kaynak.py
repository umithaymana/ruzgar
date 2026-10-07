# -*- coding: utf-8 -*-
"""Ortak kaynak altyapısı duman testi."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ilim_assistant.ana_motor_kaynak import (  # noqa: E402
    citation_directive_for_turn,
    format_context_blocks,
)
from ilim_assistant.ruzgar_ortak_kaynak import (  # noqa: E402
    DOGRULANAMADI,
    atif_yoksa_uyari,
    format_atif,
    load_alanlar,
    load_sema,
    lookup_kaynak,
    ortak_kaynak_status,
)


def main() -> int:
    failed = 0

    def _ok(msg: str) -> None:
        print(f"[OK] {msg}")

    def _fail(msg: str, detail: str = "") -> None:
        nonlocal failed
        failed += 1
        print(f"[FAIL] {msg} {detail}".rstrip())

    sema = load_sema()
    if not sema.get("version"):
        _fail("sema", "yuklenemedi")
    else:
        _ok(f"sema={sema.get('version')}")

    alanlar = load_alanlar()
    if len(alanlar) < 9:
        _fail("alanlar", f"sayi={len(alanlar)}")
    else:
        _ok(f"alan_sayisi={len(alanlar)}")

    st = ortak_kaynak_status()
    if not st.get("ok") or st.get("kayit_sayisi", 0) < 9:
        _fail("status", str(st))
    else:
        _ok(f"kayit={st.get('kayit_sayisi')} placeholder={st.get('placeholder_sayisi')}")

    hit = lookup_kaynak("gazali_ihya")
    if not hit or hit.get("kaynak_adi") != "İhyâü Ulûmi'd-Dîn":
        _fail("lookup_id", str(hit))
    else:
        _ok("lookup kaynak_id")

    hit2 = lookup_kaynak(
        "knowledge/ilim/din/09_ahlak_tasavvuf/eserler/gazali_ihya/incremental/x.md"
    )
    if not hit2 or hit2.get("kaynak_id") != "gazali_ihya":
        _fail("lookup_path", str(hit2))
    else:
        _ok("lookup dosya_yolu")

    atif = format_atif(hit)
    if "sayfa" in atif.lower() or "cilt" in atif.lower() or "bölüm" in atif.lower():
        _fail("atif_uydurma", atif)
    elif "Gazâlî" not in atif and "Gazali" not in atif:
        _fail("atif_icerik", atif)
    else:
        _ok(f"atif={atif[:80]}")

    uyari = atif_yoksa_uyari()
    if DOGRULANAMADI not in uyari and "doğrulanamadı" not in uyari.lower():
        _fail("uyari", uyari)
    else:
        _ok("dogrulanamadi metni")

    blocks = format_context_blocks(
        [("kalp hastaliklari", "knowledge/ilim/din/09_ahlak_tasavvuf/eserler/gazali_ihya/x.md", 0.7)]
    )
    if not blocks or "İhyâ" not in blocks[0][0] and "Ihya" not in blocks[0][0]:
        # Türkçe İhyâü beklenir
        if blocks and ("Gazâlî" in blocks[0][0] or "gazali" in blocks[0][0].lower()):
            _ok("format_context_blocks enrich")
        else:
            _fail("format_blocks", blocks[0][0][:120] if blocks else "bos")
    else:
        _ok("format_context_blocks enrich")

    cit = citation_directive_for_turn(source_count=1, archive_primary=False, web_present=False)
    if "uydurma" not in cit.lower() and "doğrulanamadı" not in cit:
        _fail("citation_directive", cit[:100])
    else:
        _ok("citation_directive uydurma yasagi")

    print(f"result: {8 - failed}/8 pass" if failed <= 8 else f"result: failed={failed}")
    # count actual checks dynamically
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
