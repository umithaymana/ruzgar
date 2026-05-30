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
    if "faz" not in str(rep.get("version") or ""):
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

    from ilim_assistant.motorlar.tercume_context_rag import (
        TERCUME_RAG_VERSION,
        archive_context_snippets,
    )
    from ilim_assistant.motorlar.tercume_glossary import active_glossary_sets, glossary_term_pairs
    from ilim_assistant.motorlar.tercume_translate_memory import (
        clear_session,
        consistency_block,
        record_translation,
        seed_pairs_from_glossary,
    )

    pairs = glossary_term_pairs("imam rabbani mektubat halvet", source_file="mektubat.pdf", tgt_lang="tr")
    if not pairs:
        print("FAIL glossary pairs", pairs)
        return 1
    if "rabbani_mektubat" not in active_glossary_sets("mektubat rabbani", "x.pdf"):
        print("FAIL active sets")
        return 1
    seed_pairs_from_glossary("mektubat.pdf", "Mecdüddîn halvet", tgt_lang="tr")
    block = consistency_block("mektubat.pdf", tgt_lang="tr")
    if "Mecdüddîn" not in block and "TERİM" not in block:
        print("FAIL memory block", block[:120])
        return 1
    record_translation("mektubat.pdf", source_text="a", translated="b", tgt_lang="tr")
    rag, hits = archive_context_snippets("mektubat tasavvuf ihlas", source_file="mektubat.pdf")
    if "faz4" not in TERCUME_RAG_VERSION:
        print("FAIL rag version")
        return 1
    clear_session("mektubat.pdf")

    paths_f4 = {getattr(r, "path", "") for r in app.routes}
    if "/api/tercume/memory-clear" not in paths_f4:
        print("FAIL memory-clear route")
        return 1

    print("OK tercume faz4 — glossary memory rag")

    from ilim_assistant.motorlar.tercume_analyst import prepare_import_from_search
    from ilim_assistant.motorlar.tercume_analyst_jobs import (
        ANALYST_JOB_VERSION,
        get_analyst_job,
        resolve_tercume_job,
        start_analyst_job,
    )

    plan = prepare_import_from_search(
        query="mektubat rabbani",
        download_url="https://archive.org/download/example/mektubat.pdf",
    )
    if plan.get("mode") != "download" or not plan.get("download_url"):
        print("FAIL import plan", plan)
        return 1
    local_plan = prepare_import_from_search(query="mektubat rabbani", download_url="")
    if local_plan.get("mode") not in ("local", "download"):
        print("FAIL local/download plan", local_plan)
        return 1

    started = start_analyst_job(
        query="smoke",
        download=False,
        download_url="",
    )
    if not started.get("job_id"):
        print("FAIL start job", started)
        return 1
    jid = str(started["job_id"])
    st = get_analyst_job(jid)
    if not st.get("ok"):
        print("FAIL get job", st)
        return 1
    resolved = resolve_tercume_job(jid)
    if resolved.get("job_type") != "analyst_pipeline":
        print("FAIL resolve job", resolved)
        return 1
    if "faz5" not in ANALYST_JOB_VERSION:
        print("FAIL analyst job version")
        return 1

    paths_f5 = {getattr(r, "path", "") for r in app.routes}
    for need in (
        "/api/tercume/import-from-search",
        "/api/tercume/pipeline-start",
        "/api/tercume/jobs/{job_id}",
        "/api/tercume/pipeline-cancel",
    ):
        if need not in paths_f5:
            print("FAIL route", need)
            return 1

    print("OK tercume faz5 — import queue jobs")

    from ilim_assistant.motorlar.tercume_hafiza_bridge import (
        TERCUME_BRIDGE_VERSION,
        build_bridge_preview,
        save_bridge_entry,
        tercume_bridge_enabled,
    )

    if not tercume_bridge_enabled():
        print("FAIL bridge disabled")
        return 1
    prev = build_bridge_preview(
        "Bu parça tasavvuf ve ihlas hakkındadır.",
        "This passage is about tasawwuf and sincerity in worship.",
        source_file="mektubat.pdf",
        page_index=2,
        tgt_lang="en",
    )
    if not prev.get("ok") or not prev.get("soru"):
        print("FAIL bridge preview", prev)
        return 1
    dry = save_bridge_entry(
        "Bu parça tasavvuf ve ihlas hakkındadır.",
        "This passage is about tasawwuf and sincerity in worship.",
        source_file="smoke_test.pdf",
        approved=True,
        dry_run=True,
    )
    if not dry.get("ok") or not dry.get("dry_run"):
        print("FAIL bridge dry save", dry)
        return 1
    if "faz6" not in TERCUME_BRIDGE_VERSION:
        print("FAIL bridge version")
        return 1

    paths_f6 = {getattr(r, "path", "") for r in app.routes}
    for need in (
        "/api/tercume/bridge-preview",
        "/api/tercume/bridge-save",
        "/api/tercume/bridge-log",
    ):
        if need not in paths_f6:
            print("FAIL route", need)
            return 1

    print("OK tercume faz6 — hafiza bridge")

    from ilim_assistant.motorlar.tercume_analyst_report import (
        ANALYST_REPORT_VERSION,
        build_report_markdown,
        generate_analyst_report,
        report_enabled,
        save_report_file,
    )

    if not report_enabled():
        print("FAIL report disabled")
        return 1
    rep = generate_analyst_report("imam rabbani mektubat", read_pages=2)
    if not rep.get("ok") or not rep.get("markdown"):
        print("FAIL report generate", rep)
        return 1
    md = build_report_markdown(rep.get("analysis") or {})
    if "# Tercüme analist raporu" not in md:
        print("FAIL report markdown")
        return 1
    dry_save = save_report_file({**rep, "markdown": md})
    if not dry_save.get("report_rel"):
        print("FAIL report save", dry_save)
        return 1
    if "faz7" not in ANALYST_REPORT_VERSION:
        print("FAIL report version")
        return 1

    paths_f7 = {getattr(r, "path", "") for r in app.routes}
    for need in ("/api/tercume/report", "/api/tercume/report-start"):
        if need not in paths_f7:
            print("FAIL route", need)
            return 1

    print("OK tercume faz7 — analyst report")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
