"""Madde 1.4 — «Kalıp ≠ bilgi»: öğretilmiş selam/davranış kalıpları sohbette ezber olarak dönmez;
gerçek bilgi («adım Ümit») şablon cümleyle sarılmadan korunur."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ilim_assistant import hafiza_i_ruzgar as h
from ilim_assistant import ruzgar_egitim as eg


@pytest.fixture()
def hafiza(tmp_path: Path, monkeypatch):
    dosya = tmp_path / "ruzgar_genel_hafiza.json"
    dosya.write_text(
        json.dumps(
            [
                {"motor_tipi": "Egitim", "soru": "selam", "cevap": "Aleykümselam Ümit abi, hoş geldin, nasılsın bugün?"},
                {"motor_tipi": "Egitim", "soru": "nasılsın", "cevap": "Ben iyiyim Ümit abi, sen nasılsın?"},
                {
                    "motor_tipi": "Egitim",
                    "soru": "selam dersem",
                    "cevap": "Selam dediğimde böyle cevap ver: kısa ve samimi ol, abi diye hitap et.",
                },
                {"motor_tipi": "Hafıza", "soru": "benim adım ne", "cevap": "Adın Ümit."},
                {"motor_tipi": "Egitim", "soru": "adım ne", "cevap": "Adın Ümit."},
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    m = h.HafizaIRuzgar(dosya_yolu=dosya)
    monkeypatch.setattr(h, "_hafiza_singleton", m)
    monkeypatch.delenv("RUZGAR_KAPSAM_HAFIZA", raising=False)
    return m


@pytest.mark.parametrize(
    "msg", ["selam", "Selam Rüzgar", "nasılsın", "günaydın", "teşekkürler", "selam dersem ne cevap verirsin"]
)
def test_sohbet_kalibi_ezber_donmez(hafiza, msg):
    assert eg.maybe_egitim_learned_reply(msg) is None
    assert eg.lookup_egitim_reply(msg) is None
    assert eg.lookup_greeting_egitim_reply(msg) is None


@pytest.mark.parametrize("msg", ["benim adım ne", "adım ne"])
def test_gercek_bilgi_sarilmadan_korunur(hafiza, msg):
    assert eg.maybe_egitim_learned_reply(msg) == "Adın Ümit."
    assert eg.lookup_egitim_reply(msg) == "Adın Ümit."


def test_davranis_talimati_kullaniciya_okunmaz(hafiza):
    talimat = "Selam dediğimde böyle cevap ver: kısa ve samimi ol, abi diye hitap et."
    assert eg.cevap_kullaniciya_okunmamali(talimat, user_msg="selam dersem") or eg.cevap_is_davranis_talimati(talimat)
