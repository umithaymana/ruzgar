#!/usr/bin/env python3
"""Faz 1 — tercüme analist smoke (skor + route + pipeline iskelet)."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))


def main() -> int:
    from ilim_assistant.motorlar.tercume_atolye import split_translation_units, translation_leaked_source_language

    units = split_translation_units("Line one\nLine two")
    if len(units) != 2:
        print("FAIL split_translation_units", units)
        return 1
    if not translation_leaked_source_language("something went wrong", "tr"):
        print("FAIL leak detect")
        return 1

    from ilim_assistant.motorlar.tercume_glossary import glossary_directive
    from ilim_assistant.motorlar.tercume_ocr_clean import clean_ocr_text

    g = glossary_directive("imam rabbani mektubat", source_file="mektubat.pdf", tgt_lang="tr")
    if "Rabbani" not in g and "rabbani" not in g.lower():
        print("FAIL glossary", g[:80])
        return 1
    ocr = clean_ocr_text("kelime-\ndevam\n\n\nsatir")
    if "kelimedevam" not in ocr.replace(" ", ""):
        print("FAIL ocr clean", repr(ocr))
        return 1

    from ilim_assistant.motorlar.tercume_analyst import (
        TERCUME_ANALYST_VERSION,
        analyze_tercume_query,
        score_search_item,
    )

    row = score_search_item(
        {
            "title": "Mektubat-i Rabbani PDF archive.org",
            "snippet": "Imam Rabbani letters",
            "url": "https://archive.org/download/mektubat/example.pdf",
            "source": "Internet Archive",
        },
        "imam-ı rabbani mektubat",
    )
    if float(row.get("score") or 0) < 40:
        print("FAIL score rabbani", row)
        return 1
    if not row.get("downloadable_hint"):
        print("FAIL downloadable_hint", row)
        return 1

    noise = score_search_item(
        {
            "title": "12 Imam in Shia Islam",
            "snippet": "twelve imams",
            "url": "https://example.com/12-imam",
            "source": "Genel",
        },
        "imam-ı rabbani mektubat",
    )
    if float(noise.get("score") or 100) > float(row.get("score") or 0):
        print("FAIL noise should rank lower", noise.get("score"), row.get("score"))
        return 1

    # analyze may hit network — tolerate empty DDG in CI
    rep = analyze_tercume_query("imam rabbani mektubat pdf", max_results=8)
    if not rep.get("ok"):
        print("FAIL analyze", rep)
        return 1
    if rep.get("version") != TERCUME_ANALYST_VERSION:
        print("FAIL version", rep.get("version"))
        return 1
    if not rep.get("scholar_url"):
        print("FAIL scholar_url missing")
        return 1

    from desktop_server import app

    paths = {getattr(r, "path", "") for r in app.routes}
    for need in (
        "/api/tercume/analyze",
        "/api/tercume/pipeline",
    ):
        if need not in paths:
            print("FAIL route", need)
            return 1

    print("OK tercume analyst faz1 — score + routes + analyze")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
