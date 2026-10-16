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


def test_tarif_site_ve_python_yazar_bilinmeyeni_yazmaz():
    import tempfile
    from pathlib import Path

    from ilim_assistant.motorlar.programlama_tarif import wants_tarif

    assert wants_tarif("basit site yap")
    assert wants_tarif("küçük python aracı yap")
    assert not wants_tarif("site nasıl kurulur")
    assert wants_tarif("react uygulama yap")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        site = maybe_programlama_instant_reply(
            "basit site yap: vitrin",
            "programlama",
            workspace_root=root,
        )
        assert isinstance(site, str)
        assert "Model yok" in site
        assert (root / "projects" / "vitrin" / "index.html").is_file()
        tool = maybe_programlama_instant_reply(
            "küçük python aracı yap: sayac",
            "programlama",
            workspace_root=root,
        )
        assert isinstance(tool, str)
        main_py = root / "projects" / "sayac" / "main.py"
        assert main_py.is_file()
        compile(main_py.read_text(encoding="utf-8"), str(main_py), "exec")
        before = {p.name for p in (root / "projects").iterdir()}
        miss = maybe_programlama_instant_reply(
            "react uygulama yap",
            "programlama",
            workspace_root=root,
        )
        assert isinstance(miss, str)
        assert "rafta yok" in miss
        after = {p.name for p in (root / "projects").iterdir()}
        assert before == after
    assert should_delegate_to_programlama("basit site yap", "genel")


def test_derin_inceleme_sirali_ve_yazmaz():
    from ilim_assistant.motorlar.programlama_derin_inceleme import format_derin_inceleme

    text = format_derin_inceleme(scan_text="TARAMA-TAMAM")
    assert "Çekirdek paketler" in text
    assert "Çalışma zamanı" in text
    assert "Bilgi rafları" in text
    assert "Programlama dilleri" in text
    assert "Dil araçları" in text
    assert "Python" in text
    assert "TARAMA-TAMAM" in text
    assert "onayla 1" in text
    assert text.index("Çekirdek paketler") < text.index("Bilgi rafları")
    assert text.index("Bilgi rafları") < text.index("Dil araçları")
    assert text.index("Dil araçları") < text.index("Son tarama")


def test_acik_uc_tarifin_yerine_gecmez():
    from ilim_assistant.motorlar.programlama_acik_uc import (
        format_acik_uc_report,
        open_end_chain,
        wants_acik_uc,
    )
    from ilim_assistant.motorlar.programlama_faz26 import faz26_directive

    assert wants_acik_uc("açık uç")
    assert not wants_acik_uc("basit site yap")
    chain = open_end_chain()
    assert chain[:3] == ["kod", "denge", "hizli"]
    assert chain[-1] == "web"
    report = format_acik_uc_report(ollama_up=False)
    assert "web" in report
    assert "yerine geçmez" in report
    assert "dosya uydurulmaz" in report
    assert "AÇIK UÇ" in faz26_directive()
    assert should_delegate_to_programlama("açık uç", "genel")
    assert classify_route("açık uç", "programlama") is ProgRoute.INSTANT
