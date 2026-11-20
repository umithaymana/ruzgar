# -*- coding: utf-8 -*-
"""Faz 1 — anlık kapı orkestrası: registry, covers, hadis tek politika."""
from __future__ import annotations


def test_forces_rag_niyet_karsilastir_anlat():
    from ilim_assistant.ruzgar_library_instant_registry import forces_library_rag

    assert forces_library_rag("Niyet hadisi nedir?") is True
    assert forces_library_rag("Tirmizî ile Buhârî karşılaştır") is True
    assert forces_library_rag("Hicret’i anlat") is True
    assert forces_library_rag("buhari 1") is False
    assert forces_library_rag("python nedir") is False  # strict tek-terim lookup


def test_instant_covers_no_single_token_auto_true():
    from ilim_assistant.ruzgar_kutuphane_gorev import instant_covers_query

    # Tek token «hicret» + alakasız kart → False (eski True gevşekliği yok)
    assert instant_covers_query("Hicret’i anlat", "Tasavvuf nedir kısa kart") is False
    # Karşılaştır her zaman False
    assert (
        instant_covers_query(
            "Tirmizî ile Buhârî karşılaştır",
            "Buhârî ve Tirmizî hakkında uzun kart metni",
        )
        is False
    )


def test_registry_defers_deep_hadis():
    from ilim_assistant.ruzgar_library_instant_registry import (
        try_library_instant_from_registry,
    )

    assert try_library_instant_from_registry("Niyet hadisi nedir?") is None
    assert try_library_instant_from_registry("Tirmizî ile Buhârî karşılaştır") is None
    assert try_library_instant_from_registry("Hicret’i anlat") is None


def test_hadis_dual_gate_same_policy():
    from ilim_assistant.ruzgar_hadis_anlik import try_hadis_instant_reply
    from ilim_assistant.ruzgar_hadis_kutuphane import try_hadis_reply

    for q in (
        "Niyet hadisi nedir?",
        "niyet hadisini Tirmizî ile karşılaştır",
        "niyet hadisi anlat",
    ):
        assert try_hadis_instant_reply(q) is None
        assert try_hadis_reply(q) is None


def test_registry_entries_include_tasavvuf_and_genel():
    from ilim_assistant.ruzgar_library_instant_registry import LIBRARY_INSTANT_ENTRIES

    keys = {e[2] for e in LIBRARY_INSTANT_ENTRIES}
    assert "tasavvuf_anlik" in keys
    assert "hadis_anlik" in keys
    assert "kutuphane_raf_hit" in keys
    assert "kutuphane_hit" in keys
