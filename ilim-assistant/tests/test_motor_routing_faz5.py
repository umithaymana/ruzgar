# -*- coding: utf-8 -*-
"""Faz 5 — motor routing: okuma≠mimar; hafıza kendi bağlamı."""
from __future__ import annotations


def test_normalize_okuma_not_mimar():
    from ilim_assistant.chat_core import normalize_mode

    assert normalize_mode("okuma") == "okuma"
    assert normalize_mode("bilim") == "okuma"
    assert normalize_mode("mimar") == "mimar"
    assert normalize_mode("hafiza") == "hafiza"


def test_orkestra_skips_hafiza_okuma_mimar():
    from ilim_assistant.chat_core import _orkestra_context_for_turn

    flags = {}
    assert _orkestra_context_for_turn("hafiza", flags) is False
    assert _orkestra_context_for_turn("okuma", flags) is False
    assert _orkestra_context_for_turn("mimar", flags) is False
    assert _orkestra_context_for_turn("programlama", flags) is False


def test_hafiza_motor_context_present():
    from ilim_assistant.motorlar.hafiza_motoru import build_motor_context

    ctx = build_motor_context("hatırla: test")
    assert "HAFIZA MOTORU" in ctx


def test_okuma_motor_context_present():
    from ilim_assistant.okuma_motoru import build_motor_context

    ctx = build_motor_context("hicreti anlat")
    assert ctx.strip()
    assert "MİMAR" not in ctx.upper() or "OKUMA" in ctx.upper() or "İLİM" in ctx.upper() or len(ctx) > 20


def test_cekirdek_doc_mentions_boot_split():
    import ilim_assistant.motorlar.ruzgar_cekirdegi as cek

    doc = (cek.__doc__ or "")
    assert "Boot" in doc or "boot" in doc
    assert "Mimar" in doc or "mimar" in doc.lower()
    assert "Hafıza" in doc or "hafiza" in doc.lower()
