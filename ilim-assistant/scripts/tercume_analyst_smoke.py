#!/usr/bin/env python3
"""Faz 1–2 — tercüme analist smoke (skor, alias genişletme, arama v2)."""
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

    from ilim_assistant.motorlar.tercume_eser_arama import (
        TERCUME_ESER_ARAMA_VERSION,
        expand_search_query,
    )

    expanded, notes = expand_search_query("imam rabbani mektubat")
    if "mektubat" not in expanded.lower():
        print("FAIL expand_search_query", expanded, notes)
        return 1
    if "v2" not in TERCUME_ESER_ARAMA_VERSION:
        print("FAIL arama version", TERCUME_ESER_ARAMA_VERSION)
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
            "url": "https://archive.org/details/mektubat/example",
            "download_url": "https://archive.org/download/mektubat/example.pdf",
            "source": "Internet Archive (API)",
        },
        "imam-ı rabbani mektubat",
    )
    if float(row.get("score") or 0) < 40:
        print("FAIL score rabbani", row)
        return 1
    if row.get("confidence") not in ("high", "medium", "low"):
        print("FAIL confidence", row)
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

    rep = analyze_tercume_query("imam rabbani mektubat pdf", max_results=8)
    if not rep.get("ok"):
        print("FAIL analyze", rep)
        return 1
    if "faz2" not in str(rep.get("version") or ""):
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
        "/api/tercume/read-start",
        "/api/tercume/read-status",
    ):
        if need not in paths:
            print("FAIL route", need)
            return 1

    print("OK tercume analyst faz2 — alias expand + score + routes")

    from ilim_assistant.motorlar.tercume_read_pipeline import (
        READ_PIPELINE_VERSION,
        assess_page_quality,
        enrich_pages,
        summarize_page_quality_meta,
    )

    empty = assess_page_quality("   ")
    if empty.get("quality") != "empty":
        print("FAIL empty quality", empty)
        return 1
    ok = assess_page_quality("Bu sayfada yeterince uzun bir metin paragrafı var. " * 5)
    if ok.get("quality") not in ("ok", "low"):
        print("FAIL ok quality", ok)
        return 1
    pages = enrich_pages([{"index": 0, "text": "kısa", "label": "S1"}], source_kind="pdf")
    if not pages[0].get("quality"):
        print("FAIL enrich_pages", pages)
        return 1
    meta = summarize_page_quality_meta(pages)
    if "quality_summary" not in meta:
        print("FAIL summarize", meta)
        return 1
    if "faz3" not in READ_PIPELINE_VERSION:
        print("FAIL read pipeline version", READ_PIPELINE_VERSION)
        return 1

    print("OK tercume faz3 — read pipeline quality + routes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
