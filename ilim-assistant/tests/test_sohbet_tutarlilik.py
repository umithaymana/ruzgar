# -*- coding: utf-8 -*-
"""Sohbet tutarlılığı — tek selam, tek zincir, tek üslup, hafıza paketi."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("RUZGAR_SOHBET_TEK_KAPI", "1")
os.environ.setdefault("RUZGAR_SOHBET_TARZ", "chatgpt")
os.environ.setdefault("RUZGAR_GENEL_LOCAL_FIRST", "1")


def test_canonical_selam_no_dun_konustuk():
    from ilim_assistant.ruzgar_sohbet_tek_kapi import canonical_selam_reply
    from ilim_assistant.chat_fast_lane import try_instant_reply
    from ilim_assistant.ruzgar_umed_kurallari import SELAM_STANDART

    a = canonical_selam_reply("selam", has_prior_session=False)
    b = try_instant_reply("selam", "genel")
    assert a == b == SELAM_STANDART
    assert "dün konuştuk" not in a.lower()
    assert "konuşmaya hazırım" in a


def test_selam_ruzgar_named():
    from ilim_assistant.ruzgar_sohbet_tek_kapi import canonical_selam_reply
    from ilim_assistant.ruzgar_umed_kurallari import SELAM_RUZGAR

    assert canonical_selam_reply("selam rüzgar", has_prior_session=False) == SELAM_RUZGAR


def test_selam_with_resume_only_when_prior():
    from ilim_assistant.ruzgar_sohbet_tek_kapi import canonical_selam_reply
    from ilim_assistant.ruzgar_umed_kurallari import SELAM_WITH_RESUME

    hist = [
        {"role": "user", "content": "merhaba"},
        {"role": "assistant", "content": "selam"},
    ]
    assert canonical_selam_reply("selam", history=hist) == SELAM_WITH_RESUME
    assert "dün" not in SELAM_WITH_RESUME.lower()


def test_faz91_does_not_skip_pure_greeting():
    from ilim_assistant.ruzgar_dogal_sohbet_faz91 import should_skip_instant_shortcuts

    assert should_skip_instant_shortcuts("selam", "genel") is False
    assert should_skip_instant_shortcuts("merhaba", "genel") is False


def test_chatgpt_tarz_does_not_force_gemini_first_when_ollama_on(monkeypatch):
    from ilim_assistant import ruzgar_genel_faz90 as f90

    monkeypatch.setenv("RUZGAR_SOHBET_TARZ", "chatgpt")
    monkeypatch.setenv("RUZGAR_GENEL_LOCAL_FIRST", "1")
    monkeypatch.setenv("RUZGAR_GENEL_BRAIN_CHAIN", "")
    monkeypatch.setattr(f90, "ollama_available", lambda: True)
    monkeypatch.setattr(f90, "_gemini_on_cooldown", lambda: False)
    ids = f90.build_genel_brain_chain_ids()
    assert ids[0] in ("denge", "hizli")
    assert "gemini" in ids


def test_unified_uslup_and_cok_kaynak_preserved():
    from ilim_assistant.prompts import pick_system

    metin = pick_system(False, "genel")
    assert "Sohbet düzeni" in metin
    assert "İlk cümle sorunun sonucu olsun." in metin
    assert "çok kaynaklı" in metin.lower() or "3–5" in metin or "3-5" in metin
    # Eski ayrı Bilge/Ollama yığını yok
    assert "Bilge sesi — RUZGAR_BILGE_VOICE" not in metin
    assert "Ollama-only — samimi ve doğru" not in metin
    assert metin.count("Sohbet düzeni") == 1


def test_persona_chain_mentions_ollama():
    from ilim_assistant.ruzgar_umed_kurallari import PERSONA_CONTEXT_BLOCK

    assert "Ollama" in PERSONA_CONTEXT_BLOCK
    assert "RUZGAR_SOHBET_TARZ" in PERSONA_CONTEXT_BLOCK


def test_turn_memory_pack_skips_greeting():
    from ilim_assistant.ruzgar_session_context import build_turn_memory_pack

    assert build_turn_memory_pack("selam", mode_norm="genel") == ""


def test_fast_lane_selam_respects_history():
    from ilim_assistant.chat_fast_lane import try_instant_reply
    from ilim_assistant.ruzgar_umed_kurallari import SELAM_STANDART, SELAM_WITH_RESUME

    assert try_instant_reply("selam", "genel", history=None) == SELAM_STANDART
    hist = [
        {"role": "user", "content": "merhaba"},
        {"role": "assistant", "content": "selam"},
    ]
    assert try_instant_reply("selam", "genel", history=hist) == SELAM_WITH_RESUME
    assert "dün konuştuk" not in SELAM_WITH_RESUME.lower()


def test_sohbet_once_still_allows_selam_resume(monkeypatch):
    from ilim_assistant.ana_motor_plan import maybe_gundelik_instant_reply
    from ilim_assistant.ruzgar_umed_kurallari import SELAM_STANDART, SELAM_WITH_RESUME

    monkeypatch.setenv("RUZGAR_SOHBET_ONCE", "1")
    empty = maybe_gundelik_instant_reply("selam", "genel", {}, history=None)
    assert empty == SELAM_STANDART
    assert "dün konuştuk" not in (empty or "").lower()

    hist = [
        {"role": "user", "content": "merhaba"},
        {"role": "assistant", "content": "selam"},
    ]
    resumed = maybe_gundelik_instant_reply("selam", "genel", {}, history=hist)
    assert resumed == SELAM_WITH_RESUME

    # Sohbet-once: nasılsın şablonu değil → None (LLM)
    assert maybe_gundelik_instant_reply("nasılsın", "genel", {}) is None


def test_allow_selam_resume_instant_helper():
    from ilim_assistant.ruzgar_sohbet_once import allow_selam_resume_instant

    assert allow_selam_resume_instant("selam") is True
    assert allow_selam_resume_instant("merhaba rüzgar") is True
    assert allow_selam_resume_instant("niyet hadisi nedir") is False
