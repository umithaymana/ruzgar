"""Geçmişteki «bulamadım / süre yetmedi» cevabı hafıza sayılmaz (aynı soru sonsuza dek kaçmasın)."""
from __future__ import annotations

from ilim_assistant import ruzgar_tek_beyin as tb
from ilim_assistant.ruzgar_umed_kurallari import MISS_PHRASE, TIMEOUT_PHRASE


def test_miss_ve_timeout_cevabi_taninir():
    assert tb._is_miss_or_timeout_reply(MISS_PHRASE)
    assert tb._is_miss_or_timeout_reply(TIMEOUT_PHRASE)
    assert tb._is_miss_or_timeout_reply("Ümit abi, bunu bulamadım, bana öğretir misin?")
    assert not tb._is_miss_or_timeout_reply("Abdesti bozan şeyler idrar, gaita, yellenme ve uykudur.")
    assert not tb._is_miss_or_timeout_reply("")


def test_sohbet_gecmisindeki_miss_hafiza_olmaz(monkeypatch):
    def fake_search(variant, limit=4):
        return {
            "items": [
                {"user": "Zekât kimlere verilir?", "assistant": MISS_PHRASE},
            ]
        }

    import ilim_assistant.ana_motor_sohbet_gecmis as sg

    monkeypatch.setattr(sg, "search_chat_history", fake_search)
    monkeypatch.setattr(tb, "_skip_hafiza_for_clarification_short", lambda m: False)
    monkeypatch.setattr(tb, "_idrak_blocks_personal_hafiza", lambda m, h: False)
    assert tb.lookup_chat_history_person_hint("Zekât kimlere verilir?") is None


def test_sohbet_gecmisindeki_gercek_cevap_hala_hafiza(monkeypatch):
    real = "Zekât fakirlere, miskinlere, zekât memurlarına ve diğer sekiz sınıfa verilir."

    def fake_search(variant, limit=4):
        return {"items": [{"user": "Zekât kimlere verilir?", "assistant": real}]}

    import ilim_assistant.ana_motor_sohbet_gecmis as sg

    monkeypatch.setattr(sg, "search_chat_history", fake_search)
    monkeypatch.setattr(tb, "_skip_hafiza_for_clarification_short", lambda m: False)
    monkeypatch.setattr(tb, "_idrak_blocks_personal_hafiza", lambda m, h: False)
    hint = tb.lookup_chat_history_person_hint("Zekât kimlere verilir?")
    assert hint and hint["eslesme"] == "chat_history"
