# -*- coding: utf-8 -*-
"""Faz 4 — beyin sırası + umed bütçe / prefetch."""
from __future__ import annotations

import time


def test_ilim_cloud_first_default_off(monkeypatch):
    monkeypatch.delenv("RUZGAR_ILIM_RAG_CLOUD_FIRST", raising=False)
    monkeypatch.setenv("RUZGAR_GENEL_LOCAL_FIRST", "1")
    from ilim_assistant.ruzgar_genel_faz90 import (
        brain_order_decision_table,
        ilim_rag_cloud_first_enabled,
    )

    assert ilim_rag_cloud_first_enabled() is False
    table = brain_order_decision_table()
    assert table["ilim_rag_cloud_first"] is False


def test_ilim_cloud_first_explicit_on(monkeypatch):
    monkeypatch.setenv("RUZGAR_ILIM_RAG_CLOUD_FIRST", "1")
    from ilim_assistant.ruzgar_genel_faz90 import (
        build_ilim_rag_brain_chain_ids,
        ilim_rag_cloud_first_enabled,
    )

    assert ilim_rag_cloud_first_enabled() is True
    ids = build_ilim_rag_brain_chain_ids()
    assert ids[0] in ("gemini", "groq")


def test_budget_includes_prefetch_start():
    from ilim_assistant.ruzgar_umed_cevap_emri import (
        begin_turn_budget,
        get_turn_deadline,
        remaining_sec,
        set_turn_deadline,
        turn_budget_sec,
    )

    set_turn_deadline(None)
    msg = "selam"
    full = turn_budget_sec(msg, mode_norm="genel")
    t0 = time.monotonic() - 5.0  # 5 sn önce prefetch başladı
    begin_turn_budget(msg, mode_norm="genel", started_monotonic=t0)
    rem = remaining_sec()
    # Prefetch 5 sn sayıldı → kalan ≈ full - 5
    assert rem < full - 3.0
    assert rem > full - 7.0
    d = get_turn_deadline()
    assert d is not None
    assert abs(d - (t0 + full)) < 0.5
    set_turn_deadline(None)
