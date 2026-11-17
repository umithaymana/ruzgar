# Created by Ümit & Gökçenur
"""F2.3 — çok eser kaynaklı sentez (directive + extractive multi-K)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from ilim_assistant.ana_motor_kaynak import (
        citation_directive_for_turn,
        cok_eser_sentez_directive,
        distinct_source_count,
    )
    from ilim_assistant.ruzgar_kutuphane_gorev import format_kutuphane_extractive_reply

    hits = [
        ("Birinci pasaj: abdest su ile alınır, niyet şarttır.", "kitaplar/fikih/abdest_a.md", 0.9),
        ("İkinci pasaj: abdestin farzları baş, kollar, ayaklardır.", "kitaplar/fikih/abdest_b.md", 0.85),
        ("Üçüncü pasaj: abdest bozan haller sayılır.", "kitaplar/akaid/abdest_c.md", 0.8),
        ("Aynı eser tekrar chunk.", "kitaplar/fikih/abdest_a.md", 0.7),
        ("Dördüncü eser: taharet bahsi.", "kitaplar/usul/taharet.md", 0.65),
    ]
    n = distinct_source_count(hits)
    assert n >= 3, n

    d = cok_eser_sentez_directive(source_count=len(hits), distinct_sources=n)
    assert "F2.3" in d and "[K" in d and "Kaynak izi" in d, d[:200]

    soft = citation_directive_for_turn(
        source_count=len(hits),
        archive_primary=True,
        web_present=False,
        soft_natural=True,
        distinct_sources=n,
    )
    assert "F2.3" in soft and ("çok eser" in soft.lower() or "ÇOK ESER" in soft), soft[:300]

    hard = citation_directive_for_turn(
        source_count=len(hits),
        archive_primary=True,
        web_present=False,
        soft_natural=False,
        distinct_sources=n,
    )
    assert "F2.3" in hard

    reply = format_kutuphane_extractive_reply(
        "abdest nedir",
        hits,
        want_source=True,
        multi_source=True,
    )
    assert "Kaynak izi" in reply, reply
    assert reply.count("[K") >= 2, reply
    assert "abdest_a" in reply or "abdest_b" in reply

    # tek kaynak → çok eser bloğu yok
    one = cok_eser_sentez_directive(source_count=1, distinct_sources=1)
    assert one == ""

    print("smoke_f2_3_cok_eser OK", f"distinct={n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
