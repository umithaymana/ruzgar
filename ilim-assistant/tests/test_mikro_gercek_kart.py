# Created by Ümit & Gökçenur
"""Konum kartı başka soruyu yutmasın."""

from ilim_assistant.ruzgar_tek_beyin_analiz import (
    build_analiz_system_addon,
    try_simple_factual_reply,
)


def test_dunya_hangi_galakside_karti_durur():
    yanit = try_simple_factual_reply("dünyamız hangi galakside")
    assert yanit
    assert "Samanyolu" in yanit


def test_yildiz_sayisi_galaksi_kartini_okumaz():
    yanit = try_simple_factual_reply(
        "peki saman yolu galaksisinde kaç tane yıldız vardır"
    )
    assert yanit is None


def test_takvim_karti_durur():
    yanit = try_simple_factual_reply("bir yılda kaç ay var")
    assert yanit
    assert "12" in yanit


def test_bilgi_notu_kart_gibi_okunmaz():
    ek = build_analiz_system_addon("samanyolu galaksisinde kaç yıldız vardır")
    assert "notu okuma" in ek
