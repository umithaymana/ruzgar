"""Din soruları TDK tam-madde yoluna sapmaz (kütüphane/Şâmile'ye gider); sözlük soruları sapar."""
from __future__ import annotations

import pytest

from ilim_assistant import chat_core as c


@pytest.mark.parametrize(
    "soru",
    [
        "Zekât kimlere verilir?",
        "Namazın şartları nelerdir?",
        "Vitir namazı nedir?",
        "Hac kimlere farzdır?",
        "Abdesti bozan şeyler nelerdir?",
    ],
)
def test_din_sorusu_tdk_tam_madde_yoluna_girmez(soru, monkeypatch):
    monkeypatch.delenv("RUZGAR_TDK_EXACT_DIN", raising=False)
    lem = c._extract_lemma_for_tdk(soru)
    assert c._tdk_exact_path_allowed(soru, lem) is False


@pytest.mark.parametrize("soru", ["Elektroliz nedir?", "Sıfat nedir?"])
def test_sozluk_sorusu_tdk_yolunu_korur(soru, monkeypatch):
    monkeypatch.delenv("RUZGAR_TDK_EXACT_DIN", raising=False)
    lem = c._extract_lemma_for_tdk(soru)
    assert c._tdk_exact_path_allowed(soru, lem) is True


def test_bayrakla_eski_davranis(monkeypatch):
    monkeypatch.setenv("RUZGAR_TDK_EXACT_DIN", "1")
    soru = "Namazın şartları nelerdir?"
    assert c._tdk_exact_path_allowed(soru, c._extract_lemma_for_tdk(soru)) is True
