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
    assert "TypeScript dili" in text
    assert "Go dili" in text
    assert "Python döngüsü" in text
    assert "Kavram: 1181" in text


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


def test_yaygin_dil_karttan_okunur_ve_modele_birakilmaz():
    from ilim_assistant.ruzgar_anlik_niyet_gate import (
        is_strict_library_lookup,
        should_defer_library_instant,
    )
    from ilim_assistant.ruzgar_bilgisayar_kutuphane import _load_kavramlar

    _load_kavramlar.cache_clear()
    ts = try_bilgisayar_reply("typescript ile ne yazılır") or ""
    go = try_bilgisayar_reply("go nedir") or ""
    c_dili = try_bilgisayar_reply("c dili nedir") or ""
    assert "tipli" in ts
    assert "sunucu" in go
    assert "gömülü" in c_dili
    assert is_strict_library_lookup("typescript ile ne yazılır")
    assert is_strict_library_lookup("go nedir")
    assert is_strict_library_lookup("c dili nedir")
    assert should_defer_library_instant("go nedir") is False
    assert should_defer_library_instant("typescript ile ne yazılır") is False
    assert try_bilgisayar_reply("fotosentez nedir") is None


def test_dil_teferruati_ayri_karttan_okunur():
    from ilim_assistant.ruzgar_bilgisayar_kutuphane import _load_kavramlar

    _load_kavramlar.cache_clear()
    dongu = try_bilgisayar_reply("python döngüsü nedir") or ""
    hata = try_bilgisayar_reply("go hatası nedir") or ""
    kutu = try_bilgisayar_reply("css veri yapısı nedir") or ""
    assert "while" in dongu
    assert "error" in hata
    assert "flex" in kutu
    assert "JavaScript" not in hata


def test_dil_nerede_ve_nasil_karttan_okunur():
    from ilim_assistant.motorlar.programlama_motoru import is_code_agent_task_message
    from ilim_assistant.ruzgar_anlik_niyet_gate import (
        is_strict_library_lookup,
        should_defer_library_instant,
    )
    from ilim_assistant.ruzgar_bilgisayar_kutuphane import (
        _load_kavramlar,
        dil_mufredat_raporu,
    )

    _load_kavramlar.cache_clear()
    nerede = try_bilgisayar_reply("python nerede kullanılır") or ""
    nasil = try_bilgisayar_reply("python nasıl kullanılır") or ""
    js = try_bilgisayar_reply("javascript nerede kullanılır") or ""
    sec = try_bilgisayar_reply("hangi dil") or ""
    assert "Python dili" in nerede
    assert "Java dili" not in nerede
    assert "çalıştırmaz" in nasil
    assert "JavaScript dili" in js
    assert "Java dili" not in js
    assert "Sayfa iskeleti: HTML" in sec
    assert "Android uygulaması: Kotlin" in sec
    assert is_strict_library_lookup("python nerede kullanılır")
    assert is_strict_library_lookup("python nasıl kullanılır")
    assert is_strict_library_lookup("hangi dil")
    assert should_defer_library_instant("python nerede kullanılır") is False
    assert is_code_agent_task_message("python nerede kullanılır", "programlama") is False
    rapor = dil_mufredat_raporu()
    assert len(rapor) == 19
    assert all(satir["slot"] == 45 for satir in rapor)
    assert all(satir["yuzde"] == 100 for satir in rapor)


def test_dil_ikinci_on_bes_kart_okunur():
    from ilim_assistant.motorlar.programlama_motoru import is_code_agent_task_message
    from ilim_assistant.ruzgar_anlik_niyet_gate import (
        is_strict_library_lookup,
        should_defer_library_instant,
    )
    from ilim_assistant.ruzgar_bilgisayar_kutuphane import _load_kavramlar

    _load_kavramlar.cache_clear()
    ornek = try_bilgisayar_reply("python örneği nedir") or ""
    zaman = try_bilgisayar_reply("python ne zaman seçilir") or ""
    degil = try_bilgisayar_reply("python ne zaman seçilmez") or ""
    java = try_bilgisayar_reply("java örneği nedir") or ""
    assert "def topla" in ornek
    assert "hesap" in zaman
    assert "dosya" in zaman
    assert "HTML" in degil
    assert "int topla" in java
    assert "def topla" not in java
    assert is_strict_library_lookup("python ne zaman seçilir")
    assert is_strict_library_lookup("python ne zaman seçilmez")
    assert is_strict_library_lookup("c dili ne zaman seçilir")
    assert should_defer_library_instant("python ne zaman seçilir") is False
    assert is_code_agent_task_message("python ne zaman seçilir", "programlama") is False


def test_dil_ucuncu_on_bes_kart_okunur():
    from ilim_assistant.motorlar.programlama_motoru import is_code_agent_task_message
    from ilim_assistant.ruzgar_anlik_niyet_gate import (
        is_strict_library_lookup,
        should_defer_library_instant,
    )
    from ilim_assistant.ruzgar_bilgisayar_kutuphane import (
        _load_kavramlar,
        dil_mufredat_raporu,
    )

    _load_kavramlar.cache_clear()
    islec = try_bilgisayar_reply("python işleci nedir") or ""
    bos = try_bilgisayar_reply("python boş değeri nedir") or ""
    java = try_bilgisayar_reply("java boş değeri nedir") or ""
    sinir = try_bilgisayar_reply("python el sınırı nedir") or ""
    assert "==" in islec
    assert "None" in bos
    assert "null" in java
    assert "None" not in java
    assert "çalıştırmaz" in sinir
    assert is_strict_library_lookup("python işleci nedir")
    assert is_strict_library_lookup("python boş değeri nedir")
    assert is_strict_library_lookup("c dili işleci nedir")
    assert should_defer_library_instant("python işleci nedir") is False
    assert is_code_agent_task_message("python işleci nedir", "programlama") is False
    rapor = dil_mufredat_raporu()
    assert len(rapor) == 19
    assert all(satir["slot"] == 45 and satir["yuzde"] == 100 for satir in rapor)


def test_python_stdlib_modulleri_karttan_okunur():
    from ilim_assistant.motorlar.programlama_motoru import is_code_agent_task_message
    from ilim_assistant.ruzgar_anlik_niyet_gate import (
        is_strict_library_lookup,
        should_defer_library_instant,
    )
    from ilim_assistant.ruzgar_bilgisayar_kutuphane import _load_kavramlar

    _load_kavramlar.cache_clear()
    os_karti = try_bilgisayar_reply("python os modülü nedir") or ""
    json_modul = try_bilgisayar_reply("python json modülü nedir") or ""
    json_dil = try_bilgisayar_reply("json nedir") or ""
    ic = try_bilgisayar_reply("python _thread modülü nedir") or ""
    assert "klasör" in os_karti
    assert "çalıştırmaz" in os_karti
    assert "sözlük" in json_modul
    assert "JSON dilinin kartı ayrıdır" in json_modul
    assert "veri dosyası" in json_dil
    assert "JSON dilinin kartı ayrıdır" not in json_dil
    assert "iç modül" in ic
    assert is_strict_library_lookup("python os modülü nedir")
    assert should_defer_library_instant("python os modülü nedir") is False
    assert is_code_agent_task_message("python os modülü nedir", "programlama") is False
    yarar = try_bilgisayar_reply("python os modülü ne işe yarar") or ""
    yapar = try_bilgisayar_reply("python pathlib modülü ne yapar") or ""
    dongu = try_bilgisayar_reply("python döngüsü ne işe yarar") or ""
    assert "klasör" in yarar
    assert "yol" in yapar
    assert "while" in dongu
    assert is_strict_library_lookup("python os modülü ne işe yarar")
    assert should_defer_library_instant("python os modülü ne işe yarar") is False
    assert is_code_agent_task_message("python os modülü ne işe yarar", "programlama") is False
    rows = _load_kavramlar()
    moduller = [r for r in rows if str(r.get("id") or "").startswith("python_modul_")]
    assert len(moduller) == 297
    assert all(len(str(r.get("metin") or "")) >= 80 for r in moduller)


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
