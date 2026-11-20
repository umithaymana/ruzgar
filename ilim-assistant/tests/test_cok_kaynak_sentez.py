# -*- coding: utf-8 -*-
"""Çok kaynaklı sentez — dar alan sıkışması kırılır."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("RUZGAR_COK_KAYNAK", "1")


def _hits():
    return [
        ("Buhârî'de ameller niyetlere göredir.", "knowledge/ilim/din/05_hadis/kutub_i_sitte/buhari/1.jsonl", 0.91),
        ("Müslim'de aynı mana farklı isnadla geçer.", "knowledge/ilim/din/05_hadis/kutub_i_sitte/muslim/1.jsonl", 0.88),
        ("Tirmizî bu babda benzer rivayet nakleder.", "knowledge/ilim/din/05_hadis/kutub_i_sitte/tirmizi/1.jsonl", 0.84),
        ("İbn Hişâm siyerinde hicret anlatılır.", "knowledge/ilim/din/08_siyer/eserler/ibn_hisham.md", 0.70),
        ("Doğum tarihi 570 civarıdır.", "knowledge/ilim/din/08_siyer/eserler/dogum_notu.md", 0.95),
    ]


def test_diversify_prefers_multiple_books():
    from ilim_assistant.ruzgar_cok_kaynak_sentez import (
        count_distinct_books,
        diversify_hits_by_book,
    )

    out = diversify_hits_by_book(_hits(), max_books=4, per_book=1, max_total=4)
    assert len(out) >= 3
    assert count_distinct_books(out) >= 3


def test_pack_mentions_multi_source_and_no_narrow_lock():
    from ilim_assistant.ruzgar_cok_kaynak_sentez import pack_multi_source_context

    packed = pack_multi_source_context(_hits(), max_books=4)
    assert "ÇOK KAYNAKLI" in packed
    assert "dar alan" in packed.lower() or "doğum" in packed.lower()
    assert "[K1]" in packed
    assert "[K2]" in packed


def test_comparison_offer_for_hadis():
    from ilim_assistant.ruzgar_cok_kaynak_sentez import comparison_offer_line

    line = comparison_offer_line("niyet hadisi nedir", _hits())
    assert "karşılaştır" in line.lower() or "karsilastir" in line.lower() or "rivayet" in line.lower()


def test_library_rag_top_k_boost():
    from ilim_assistant.ruzgar_cok_kaynak_sentez import library_rag_top_k_boost

    boosted = library_rag_top_k_boost(2, "Hz. Ebubekir kimdir? Kütüphaneden anlat.")
    assert boosted >= 4


def test_extractive_reply_uses_multiple_passages():
    from ilim_assistant.ruzgar_kutuphane_gorev import format_kutuphane_extractive_reply

    reply = format_kutuphane_extractive_reply("niyet hadisi nedir", _hits(), want_source=True)
    assert "[1]" in reply
    assert "[2]" in reply or "Kaynak izi" in reply
    assert "doğum" not in reply.lower() or "Buhârî" in reply or "Buhari" in reply.lower() or "niyet" in reply.lower()


def test_grounding_directive_blocks_narrow_field_lock():
    from ilim_assistant.ruzgar_kutuphane_gorev import grounding_directive

    text = grounding_directive(
        want_source=False,
        source_count=4,
        message="hicreti anlat",
        distinct_books=3,
    )
    assert "Dar alan" in text or "doğum" in text.lower()
    assert "3–5" in text or "3-5" in text or "ÇOK KAYNAK" in text


def test_hadis_instant_offers_comparison():
    from ilim_assistant.ruzgar_hadis_anlik import try_hadis_instant_reply

    out = try_hadis_instant_reply("niyet hadisi nedir")
    assert out is not None
    assert "Buhârî" in out or "Buhari" in out
    assert "karşılaştır" in out.lower() or "rivayet" in out.lower()


def test_hadis_compare_request_defers_to_rag():
    from ilim_assistant.ruzgar_hadis_anlik import try_hadis_instant_reply

    out = try_hadis_instant_reply("niyet hadisini Tirmizî ile karşılaştır")
    assert out is None


def test_should_force_library_synthesis():
    from ilim_assistant.ruzgar_cok_kaynak_sentez import should_force_library_synthesis

    assert should_force_library_synthesis(hits=_hits(), mode_norm="genel", message="hadis")


def test_should_synthesize_without_web_when_multi_local():
    from ilim_assistant.ana_motor_sentez import should_synthesize_turn

    class _P:
        primary = "bilgi"

    ok = should_synthesize_turn(
        question_plan=_P(),
        hits=_hits(),
        web_extra="",
        mode_norm="genel",
        user_message="niyet hadisi nedir",
    )
    assert ok is True


def test_isolation_marks_kutuphane_bilgi():
    from ilim_assistant.ruzgar_tek_beyin_izolasyon import looks_like_bilgi_isolation_turn

    assert looks_like_bilgi_isolation_turn("Fotosentez nedir? Kütüphaneden özetle.")
