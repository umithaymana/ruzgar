# Created by Ümit & Gökçenur
"""Hava yeni konuya yapışmasın. İç not silinsin. Öğrenilen raf okunsun."""

from ilim_assistant.chat_core import _weather_follow_up
from ilim_assistant.ruzgar_kuran_anlik import (
    looks_like_kuran_question,
    try_kuran_instant_reply,
)
from ilim_assistant.tarih_intent import tarih_intent
from ilim_assistant.text_encoding import cila_sohbet_metni, finalize_assistant_reply, scrub_leaked_instructions
from ilim_assistant.weather_live import is_weather_query
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


def test_medeniyet_bilgi_ver_hava_olmaz():
    assert (
        _weather_follow_up(
            "ilk medeniyet nerede kurulmuştur bana biraz bilgi verir misin",
            _HAVA_GECMIS,
        )
        is False
    )
    assert (
        is_weather_query(
            "ben hava durumunu sormadım ilk medeniyet nerede kuruldu söyle bana dedim"
        )
        is False
    )


def test_medeniyet_kuran_karti_olmaz():
    soru = "ilk medeniyet nerede kurulmuştur bana biraz bilgi verir misin"
    assert looks_like_kuran_question(soru) is False
    assert try_kuran_instant_reply(soru) is None
    assert tarih_intent(soru) is True
    assert looks_like_kuran_question("bakara suresi medeni mi") is True


def test_istanbul_hava_durur():
    assert is_weather_query("istanbulda havalar nasıl olacak bugün ve yarın") is True


def test_okul_sayisi_hava_olmaz():
    assert (
        _weather_follow_up(
            "istanbulda kaç özel okul var web ten bakıp bana söyler misin",
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
    once = eg.reply_saklanan_dogrular("önceki günler neler öğrenmiştin")
    assert once
    assert "kaydetmedim" in once


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


def test_sohbet_cilasi_kart_tekrar_ve_uydurma_sayiyi_birakir():
    ham = (
        "[Edip] Edebiyat ve gazel okumasında durur.\n"
        "Erzurum'un ilçeleri vardır.\n\n"
        "Erzurum'un ilçeleri vardır.\n\n"
        "[TALİMAT — TEKRAR ETME] önceki cevabı kopyalama.\n"
        "Referans (kopyalama değil): eski paragraf.\n"
        "Türkiye'de 1500 özel okul vardır. Doğu Anadolu illeri ayrıdır."
    )
    temiz = cila_sohbet_metni(ham)
    assert "[Edip]" not in temiz
    assert "TEKRAR ETME" not in temiz
    assert "Referans" not in temiz
    assert temiz.count("Erzurum'un ilçeleri") == 1
    assert "1500" not in temiz
    assert "Sayı uydurmam" in temiz
    assert "Doğu Anadolu" in temiz
    kaynakli = cila_sohbet_metni(
        "MEB sayfası 1500 özel okul yazar. https://ornek.example/okul"
    )
    assert "1500" in kaynakli
    son = finalize_assistant_reply(
        "[Alim] İlmihal kartı.\nGüneş sisteminde bir yıldız vardır."
    )
    assert "[Alim]" not in son
    assert "bir yıldız" in son
