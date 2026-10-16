# Created by Ümit & Gökçenur
"""Adım 1 — kendini incele + kütüphane envanteri, model yok."""

from ilim_assistant.motorlar.programlama_faz10 import should_delegate_to_programlama
from ilim_assistant.motorlar.programlama_motoru import (
    is_programlama_reserved_command,
    maybe_programlama_instant_reply,
    wants_self_scan,
)
from ilim_assistant.motorlar.programlama_router import ProgRoute, classify_route
from ilim_assistant.ruzgar_bilgisayar_kutuphane import (
    format_bilgisayar_envanter,
    try_bilgisayar_reply,
    wants_bilgisayar_envanter,
)


def test_kendini_incele_oz_taramaya_baglanir():
    assert wants_self_scan("kendini incele")
    assert wants_self_scan("sistemini incele")
    assert wants_self_scan("kendini tara")
    assert not wants_self_scan("hava nasıl")
    assert is_programlama_reserved_command("kendini incele")
    assert classify_route("kendini incele", "programlama") is ProgRoute.INSTANT


def test_kutuphane_envanteri_sirali_ve_modelsiz():
    assert wants_bilgisayar_envanter("kütüphanende hangi bilgiler var")
    assert wants_bilgisayar_envanter("Kütüphanende neler var?")
    assert not wants_bilgisayar_envanter("python ile site nasıl yapılır")
    text = format_bilgisayar_envanter()
    assert "model yok" in text
    assert "Bilgisayar mühendisliği" in text
    assert "1. " in text
    assert "sayısal mantık" in text
    assert "yazılım tasarımı" in text
    assert text.index("Donanım çekirdeği") < text.index("Programlama uzmanlığı")
    assert text.index("Programlama uzmanlığı") < text.index("Programlama dilleri")
    assert text.index("sayısal mantık") < text.index("yazılım tasarımı")
    assert "HTML dili" in text
    assert "Küçük Python uygulaması" in text
    assert "Kavram: 45" in text


def test_genel_sohbet_programlamaya_duser_atolye_aninda_cevaplar():
    assert should_delegate_to_programlama("kendini incele", "genel")
    assert should_delegate_to_programlama("kütüphanende hangi bilgiler var", "genel")
    assert not should_delegate_to_programlama("kendini incele", "programlama")
    reply = maybe_programlama_instant_reply(
        "kütüphanende hangi bilgiler var",
        "programlama",
    )
    assert isinstance(reply, str)
    assert "Kavram:" in reply
    assert "knowledge/ortak_kaynak/alanlar/bilgisayar_muhendisligi" in reply


def test_dil_notlari_modelsiz_cevaplanir():
    html = try_bilgisayar_reply("html nedir") or ""
    css = try_bilgisayar_reply("css nedir") or ""
    js = try_bilgisayar_reply("javascript nasıl çalıştırılır") or ""
    py = try_bilgisayar_reply("python nasıl sınanır") or ""
    site = try_bilgisayar_reply("site nasıl kurulur") or ""
    app = try_bilgisayar_reply("küçük uygulama nasıl kurulur") or ""
    assert "Tarayıcı" in html or "tarayıcı" in html
    assert "görünüş" in css
    assert "konsolu" in js
    assert "pytest" in py
    assert "index.html" in site
    assert "uygulama.py" in app
    assert try_bilgisayar_reply("fotosentez nedir") is None
