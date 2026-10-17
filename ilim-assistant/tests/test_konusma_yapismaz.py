# Created by Ümit & Gökçenur
"""Hava yeni konuya yapışmasın. İç not silinsin. Öğrenilen raf okunsun."""

from ilim_assistant.chat_core import _weather_follow_up
from ilim_assistant.text_encoding import scrub_leaked_instructions
from ilim_assistant import ruzgar_egitim as eg


_HAVA_GECMIS = [
    {"role": "user", "content": "hava nasıl"},
    {"role": "assistant", "content": "İstanbul hafif yağmur, 13 derece."},
]


def test_ogrenilen_hava_olmaz():
    assert (
        _weather_follow_up(
            "çok iyi neler öğrendin mesala bana biraz örnek verirmisin",
            _HAVA_GECMIS,
        )
        is False
    )


def test_web_sitesi_hava_olmaz():
    assert (
        _weather_follow_up(
            "benim için bir web sitesi yapa bilir misin",
            _HAVA_GECMIS,
        )
        is False
    )


def test_hava_devami_durur():
    assert (
        _weather_follow_up("benim için sen bakıp bilgi ver", _HAVA_GECMIS) is True
    )


def test_bilgi_turu_satiri_silinir():
    ham = (
        "Buradayım Ümit abi.\n"
        "Bilgi Turu İzolasyonu: Soru doğrudan sana yönelik.\n"
        "Niyet: sohbet"
    )
    temiz = scrub_leaked_instructions(ham)
    assert "Bilgi Turu" not in temiz
    assert "Niyet:" not in temiz
    assert "Buradayım" in temiz


class _Raf:
    def __init__(self, rows):
        self._kayitlar = rows


def test_ogrenilen_rafi_bosken_uydurmaz(monkeypatch):
    monkeypatch.setattr(
        "ilim_assistant.hafiza_i_ruzgar.get_hafiza_motor",
        lambda: _Raf([]),
    )
    yanit = eg.reply_saklanan_dogrular("neler öğrendin")
    assert yanit
    assert "kaydetmedim" in yanit


def test_ogrenilen_rafi_duzeltmeyi_soyler(monkeypatch):
    monkeypatch.setattr(
        "ilim_assistant.hafiza_i_ruzgar.get_hafiza_motor",
        lambda: _Raf(
            [
                {
                    "motor_tipi": "EgitimDuzeltme",
                    "soru": "dünyamız hangi galakside",
                    "cevap": "Samanyolu'nda yüz milyarlarca yıldız vardır",
                }
            ]
        ),
    )
    yanit = eg.reply_saklanan_dogrular("neler öğrendin mesela")
    assert yanit
    assert "yüz milyarlarca" in yanit
    assert "kaydetmedim" not in yanit
