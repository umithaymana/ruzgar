# -*- coding: utf-8 -*-
"""S3 smoke — sayı/güncel hard-gate + geniş scrub."""
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
    from ilim_assistant.sohbet_sayi_hard_gate import (
        S3_VERSION,
        apply_sayi_hard_gate_scrub,
        sayi_hard_miss_directive,
        sayi_hard_miss_reply,
        scrub_ungrounded_live_numbers,
        should_force_sayi_miss,
    )
    from ilim_assistant.sohbet_yalan_korpus import list_yalan_cases
    from ilim_assistant.text_encoding import cila_sohbet_metni, finalize_assistant_reply

    failed = 0
    failed += _ok("hard-gate-s3" in S3_VERSION, f"ver {S3_VERSION}")
    failed += _ok("uydurmam" in sayi_hard_miss_reply(), "miss phrase")
    failed += _ok("HARD-GATE" in sayi_hard_miss_directive(), "directive")

    # Kaynaksız → force
    failed += _ok(
        should_force_sayi_miss(
            "Türkiye'de kaç üniversite var webten bak",
            web_extra="",
            blocks="",
            hits=[],
        ),
        "web+kaç → force",
    )
    failed += _ok(
        should_force_sayi_miss("bugün dolar kaç TL", web_extra="", blocks=""),
        "dolar → force",
    )
    # Kaynaklı → force yok
    web_ok = "https://www.yok.gov.tr istatistik: 208 üniversite resmi liste"
    failed += _ok(
        not should_force_sayi_miss(
            "Türkiye'de kaç üniversite var webten bak",
            web_extra=web_ok * 2,
            blocks="",
        ),
        "yök web → no force",
    )
    # Kısa kavram force yok
    failed += _ok(
        not should_force_sayi_miss("os nedir", web_extra="", blocks=""),
        "os nedir → no force",
    )

    # Scrub
    scrubbed = scrub_ungrounded_live_numbers(
        "Bugün dolar 34.50 TL civarında. Başka bir şey?"
    )
    failed += _ok("uydurmam" in scrubbed and "34.50" not in scrubbed, "fx scrub")

    uni = cila_sohbet_metni("Türkiye'de 209 üniversite vardır diye biliyorum.")
    failed += _ok("209" not in uni or "uydurmam" in uni or "YÖK" in uni, "uni cila")

    # Korpus: needs_live|number → boş kaynakta force
    cases = list_yalan_cases()
    miss = []
    for c in cases:
        if not (c.get("needs_live") or c.get("needs_number")):
            continue
        if not should_force_sayi_miss(str(c["message"]), web_extra="", blocks="", hits=[]):
            # library_ok + needs_number might still force when empty — should force
            miss.append(c["id"])
    failed += _ok(not miss, f"korpus boş-kaynak force miss={miss[:6]}")

    # apply scrub with user context
    out = apply_sayi_hard_gate_scrub(
        "Galatasaray maçı 3-1 bitti.",
        user_message="bu hafta Galatasaray maçı kaç kaç bitti",
        web_extra="",
    )
    failed += _ok("uydurmam" in out or "3-1" not in out, "skor scrub")

    fin = finalize_assistant_reply("Bitcoin şu an 97000 dolar.")
    failed += _ok("97000" not in fin or "uydurmam" in fin, "finalize btc scrub")

    total = 12
    print(f"result: {total - failed}/{total} pass")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
