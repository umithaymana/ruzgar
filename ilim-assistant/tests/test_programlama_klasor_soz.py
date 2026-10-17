# Created by Ümit & Gökçenur
"""Kilitli klasör: düz cümle yazar, geri okur, düşen adımda durur."""

from pathlib import Path

import pytest

from ilim_assistant.motorlar.programlama_proje_masasi import klasor_oku_dosya, klasor_soz


@pytest.fixture(autouse=True)
def _pin(tmp_path, monkeypatch):
    monkeypatch.setenv("RUZGAR_CALISMA_PIN", str(tmp_path / "pin.json"))


@pytest.fixture
def masa(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "ilim-assistant").mkdir()
    (repo / "ruzgar-desktop").mkdir()
    (repo / ".git").mkdir()
    el = tmp_path / "ruzgar-el"
    el.mkdir()
    return repo, el


def _kilitle(repo: Path, el: Path):
    sonuc = klasor_soz(repo, f"çalışma klasörü: {el}")
    assert sonuc["handled"] is True
    assert "Klasör kilitlendi" in sonuc["reply"]
    return sonuc


def test_duz_cumle_yazar_ve_geri_okur(masa):
    repo, el = masa
    _kilitle(repo, el)
    yaz = klasor_soz(repo, "merhaba dosyasına selam mimar yaz")
    assert yaz["handled"] is True
    assert yaz["gorunum"] == "kod"
    assert yaz["text"] == "selam mimar"
    assert "Yazıldı: klasor/merhaba.txt" in yaz["reply"]
    assert "selam mimar" in yaz["reply"]
    assert (el / "merhaba.txt").read_text(encoding="utf-8") == "selam mimar"
    oku = klasor_soz(repo, "merhaba dosyasını oku")
    assert oku["gorunum"] == "kod"
    assert oku["text"] == "selam mimar"
    assert "okundu" in oku["reply"]
    boru = klasor_soz(repo, "dosyaya yaz: merhaba.txt | selam mimar")
    assert boru["text"] == "selam mimar"


def test_html_beyaz_sayfada_metin_kodda(masa):
    repo, el = masa
    _kilitle(repo, el)
    klasor_soz(repo, "dosyaya yaz: index.html | <p>selam mimar</p>")
    goster = klasor_soz(repo, "index.html dosyasını oku")
    assert goster["gorunum"] == "proje"
    assert goster["onizleme"] is True
    assert goster["text"] == "<p>selam mimar</p>"
    metin = klasor_soz(repo, "not dosyasını oku")
    assert "Okunamadı" not in metin["reply"]
    assert metin["reply"].startswith("Dosya yok") or "Dosya yok" in metin["reply"]


def test_sayfa_baslik_paragraf_buton(masa):
    repo, el = masa
    _kilitle(repo, el)
    sayfa = klasor_soz(repo, "deneme sayfası yap")
    assert sayfa["onizleme"] is True
    assert (el / "deneme.html").is_file()
    baslik = klasor_soz(repo, "başlığı selam yap")
    govde = (el / "deneme.html").read_text(encoding="utf-8")
    assert "<title>selam</title>" in govde
    assert "<h1>selam</h1>" in govde
    assert "selam" in baslik["reply"]
    klasor_soz(repo, "paragraf ekle: <script>alert(1)</script>")
    govde = (el / "deneme.html").read_text(encoding="utf-8")
    assert "<script>" not in govde
    assert "&lt;script&gt;" in govde
    klasor_soz(repo, "buton ekle: tıkla")
    govde = (el / "deneme.html").read_text(encoding="utf-8")
    assert "<button" in govde
    assert "tıkla" in govde
    goster = klasor_soz(repo, "sayfayı göster")
    assert goster["gorunum"] == "proje"
    assert goster["rel"] == "klasor/deneme.html"
    assert "selam" in goster["text"]


def test_is_listesi_ve_dusen_adim(masa):
    repo, el = masa
    _kilitle(repo, el)
    zincir = klasor_soz(repo, "deneme sayfası yap, başlığı selam yap, sayfayı göster")
    assert "Sayfa yazıldı" in zincir["reply"]
    assert "Başlık yazıldı" in zincir["reply"]
    assert "Sayfa açık" in zincir["reply"]
    assert zincir["gorunum"] == "proje"
    assert "<title>selam</title>" in (el / "deneme.html").read_text(encoding="utf-8")
    dur = klasor_soz(repo, "deneme sayfası yap, yok dosyasını oku, sayfayı göster")
    assert dur["reply"].startswith("2. adım durdu")
    assert "Dosya yok" in dur["reply"]
    assert "Önceki adımlar yazıldı" in dur["reply"]
    assert "Sayfa açık" not in dur["reply"]
    with pytest.raises(ValueError):
        klasor_oku_dosya(repo, "yok.txt")


def test_usta_kabul_cumlesi(masa):
    repo, el = masa
    _kilitle(repo, el)
    isim = "deneme sayfasına başlığı selam yap, hoş geldin yaz, tıkla butonu koy, sayfayı göster"
    sonuc = klasor_soz(repo, isim)
    govde = (el / "deneme.html").read_text(encoding="utf-8")
    assert sonuc["handled"] is True
    assert sonuc["gorunum"] == "proje"
    assert sonuc["onizleme"] is True
    assert "<title>selam</title>" in govde
    assert "<h1>selam</h1>" in govde
    assert "<p>hoş geldin</p>" in govde
    assert "<button" in govde and "tıkla" in govde
    assert "Sayfa açık" in sonuc["reply"]


def test_usta_cozulmeyen_yazmaz(masa):
    repo, el = masa
    _kilitle(repo, el)
    red = klasor_soz(repo, "deneme sayfasına başlığı selam yap, şunu tasarla")
    assert red["handled"] is True
    assert "Bunu yapmadım" in red["reply"]
    assert not (el / "deneme.html").exists()
    tasarla = klasor_soz(repo, "sayfayı baştan tasarla")
    assert tasarla["handled"] is True
    assert "Dosya değişmedi" in tasarla["reply"]
    assert list(el.iterdir()) == []
    yarim = klasor_soz(repo, "deneme sayfasına başlığı selam yap, yok dosyasını oku, sayfayı göster")
    assert yarim["reply"].startswith("3. adım durdu") or "adım durdu" in yarim["reply"]
    assert "Sayfa açık" not in yarim["reply"]
    assert (el / "deneme.html").is_file()
    assert not (el / "yok.txt").exists()


def test_yerine_bir_kez_ve_yoksa_durur(masa):
    repo, el = masa
    _kilitle(repo, el)
    klasor_soz(repo, "deneme sayfası yap")
    klasor_soz(repo, "başlığı selam yap")
    once = (el / "deneme.html").read_text(encoding="utf-8")
    assert once.count("selam") == 2
    sonuc = klasor_soz(repo, "deneme sayfasında selam yerine merhaba yaz")
    govde = (el / "deneme.html").read_text(encoding="utf-8")
    assert sonuc["onizleme"] is True
    assert "<title>merhaba</title>" in govde
    assert "<h1>selam</h1>" in govde
    assert "selam yerine merhaba" in sonuc["reply"]
    klasor_soz(repo, "paragraf ekle: <script>alert(1)</script>")
    kacis = klasor_soz(repo, "deneme sayfasında alert yerine <b>kalın</b> yaz")
    govde = (el / "deneme.html").read_text(encoding="utf-8")
    assert "<b>" not in govde
    assert "&lt;b&gt;kalın&lt;/b&gt;" in govde
    assert "yerine" in kacis["reply"]
    sabit = govde
    yok = klasor_soz(repo, "deneme sayfasında olmayan yerine x yaz")
    assert "Metin dosyada yok" in yok["reply"]
    assert (el / "deneme.html").read_text(encoding="utf-8") == sabit
    klasor_soz(repo, "dosyaya yaz: merhaba.txt | selam selam")
    klasor_soz(repo, "merhaba.txt içinde selam yerine günaydın yaz")
    metin = (el / "merhaba.txt").read_text(encoding="utf-8")
    assert metin == "günaydın selam"
    zincir = klasor_soz(repo, "deneme sayfasını oku, selam yerine merhaba yaz, sayfayı göster")
    assert "Sayfa açık" in zincir["reply"]
    assert "<h1>merhaba</h1>" in (el / "deneme.html").read_text(encoding="utf-8")
    dur_once = (el / "deneme.html").read_text(encoding="utf-8")
    dur = klasor_soz(repo, "deneme sayfasını oku, yokmetin yerine x yaz, sayfayı göster")
    assert "adım durdu" in dur["reply"]
    assert "Sayfa açık" not in dur["reply"]
    assert (el / "deneme.html").read_text(encoding="utf-8") == dur_once
    klasor_soz(repo, "dosyaya yaz: index.html | <p>diger</p>")
    cok_once = (el / "deneme.html").read_text(encoding="utf-8")
    cok = klasor_soz(repo, "selam yerine merhaba yaz")
    assert "Birden fazla sayfa" in cok["reply"]
    assert (el / "deneme.html").read_text(encoding="utf-8") == cok_once


def test_yerine_klasor_yoksa_projects_yoluna_birakir(masa):
    repo, el = masa
    sonuc = klasor_soz(repo, "selam yerine merhaba yaz")
    assert sonuc["handled"] is False
    assert list(el.iterdir()) == []


def _sahte_soyleyen(monkeypatch, cevap):
    cagrilar = []

    def sahte(metin):
        cagrilar.append(metin)
        if callable(cevap):
            return cevap(metin)
        return cevap

    monkeypatch.setattr(
        "ilim_assistant.motorlar.programlama_proje_masasi._soyleyen",
        sahte,
    )
    return cagrilar


def test_bak_soyler_uygula_bir_kez(masa, monkeypatch):
    repo, el = masa
    _kilitle(repo, el)
    klasor_soz(repo, "deneme sayfası yap")
    klasor_soz(repo, "başlığı selam yap")
    once = (el / "deneme.html").read_text(encoding="utf-8")
    cagrilar = _sahte_soyleyen(monkeypatch, "başlığı merhaba yap")
    bak = klasor_soz(repo, "deneme sayfasına bak ve söyle")
    assert cagrilar and len(cagrilar[0]) <= 1200
    assert "selam" in cagrilar[0]
    assert "<title>" not in cagrilar[0]
    assert "<h1>" not in cagrilar[0]
    assert (el / "deneme.html").read_text(encoding="utf-8") == once
    assert bak["onizleme"] is True
    assert "Gördüm: selam" in bak["reply"]
    assert "Önerim: başlığı merhaba yap" in bak["reply"]
    assert "Uygula dersen bunu yaparım." in bak["reply"]
    uygulanan = klasor_soz(repo, "uygula")
    govde = (el / "deneme.html").read_text(encoding="utf-8")
    assert "<title>merhaba</title>" in govde
    assert "Başlık yazıldı" in uygulanan["reply"]
    ikinci = klasor_soz(repo, "uygula")
    assert "Bekleyen öneri yok." in ikinci["reply"]
    assert (el / "deneme.html").read_text(encoding="utf-8") == govde


def test_bak_uc_nokta_ve_gorunen_yazi(masa, monkeypatch):
    repo, el = masa
    _kilitle(repo, el)
    klasor_soz(repo, "deneme sayfası yap")
    klasor_soz(repo, "başlığı selam yap")
    klasor_soz(repo, "paragraf ekle: hoş geldin")
    klasor_soz(repo, "buton ekle: tıkla")
    govde = (el / "deneme.html").read_text(encoding="utf-8")
    nokta = govde.replace("<title>selam</title>", "<title>...</title>").replace("<h1>selam</h1>", "<h1>...</h1>")
    (el / "deneme.html").write_text(nokta, encoding="utf-8")
    cagrilar = _sahte_soyleyen(monkeypatch, "başlığı ... yap")
    red = klasor_soz(repo, "deneme sayfasına bak ve söyle")
    assert "Gördüm: ..." in red["reply"]
    assert "Bu tarif değil. Dosya aynı." in red["reply"]
    assert (el / "deneme.html").read_text(encoding="utf-8") == nokta
    assert "..." not in cagrilar[0]
    assert "<p>" not in cagrilar[0]
    assert "hoş geldin" in cagrilar[0]
    assert "tıkla" in cagrilar[0]
    _sahte_soyleyen(monkeypatch, "yok yerine var yaz\nhoş geldin yerine merhaba yaz")
    kabul = klasor_soz(repo, "deneme sayfasına bak ve söyle")
    assert "Önerim: hoş geldin yerine merhaba yaz" in kabul["reply"]
    assert (el / "deneme.html").read_text(encoding="utf-8") == nokta
    klasor_soz(repo, "uygula")
    assert "merhaba" in (el / "deneme.html").read_text(encoding="utf-8")
    assert "<title>...</title>" in (el / "deneme.html").read_text(encoding="utf-8")


def test_bak_tarif_degilse_ve_susarsa_yazmaz(masa, monkeypatch):
    repo, el = masa
    _kilitle(repo, el)
    klasor_soz(repo, "deneme sayfası yap")
    once = (el / "deneme.html").read_text(encoding="utf-8")
    cagrilar = _sahte_soyleyen(monkeypatch, "menüyü lacivert yap")
    red = klasor_soz(repo, "deneme sayfasına bak ve söyle")
    assert "Bu tarif değil. Dosya aynı." in red["reply"]
    assert (el / "deneme.html").read_text(encoding="utf-8") == once
    assert "Bekleyen öneri yok." in klasor_soz(repo, "uygula")["reply"]
    cagrilar.clear()
    _sahte_soyleyen(monkeypatch, "")
    sus = klasor_soz(repo, "deneme sayfasına bak ve söyle")
    assert "Öneri çıkmadı. Dosya aynı." in sus["reply"]
    assert "Gördüm:" in sus["reply"]
    assert (el / "deneme.html").read_text(encoding="utf-8") == once


def test_bak_karisik_ve_dosya_yok_beyni_cagirmaz(masa, monkeypatch):
    repo, el = masa
    _kilitle(repo, el)
    klasor_soz(repo, "deneme sayfası yap")
    once = (el / "deneme.html").read_text(encoding="utf-8")

    def yasak(_metin):
        raise AssertionError("beyin çağrılmamalı")

    _sahte_soyleyen(monkeypatch, yasak)
    karisik = klasor_soz(repo, "deneme sayfasına bak ve söyle, paragraf ekle: selam")
    assert "Bunu yapmadım" in karisik["reply"]
    assert (el / "deneme.html").read_text(encoding="utf-8") == once
    zincir = klasor_soz(repo, "uygula, paragraf ekle: selam")
    assert "Bunu yapmadım" in zincir["reply"]
    assert (el / "deneme.html").read_text(encoding="utf-8") == once
    yok = klasor_soz(repo, "yok sayfasına bak ve söyle")
    assert "Dosya yok" in yok["reply"]
    assert (el / "deneme.html").read_text(encoding="utf-8") == once


def test_bak_klasorsuz_ve_metin_dosyasi(masa, monkeypatch):
    repo, el = masa
    cagrilar = _sahte_soyleyen(monkeypatch, "selam yerine günaydın yaz")
    bak = klasor_soz(repo, "deneme sayfasına bak ve söyle")
    uyg = klasor_soz(repo, "uygula")
    assert bak["handled"] is True and "seçilmedi" in bak["reply"]
    assert uyg["handled"] is True and "seçilmedi" in uyg["reply"]
    assert cagrilar == []
    assert list(el.iterdir()) == []
    _kilitle(repo, el)
    klasor_soz(repo, "dosyaya yaz: merhaba.txt | selam selam")
    baktim = klasor_soz(repo, "merhaba.txt dosyasına bak ve söyle")
    assert baktim["gorunum"] == "kod"
    assert "Gördüm: selam selam" in baktim["reply"]
    assert "Önerim: selam yerine günaydın yaz" in baktim["reply"]
    assert (el / "merhaba.txt").read_text(encoding="utf-8") == "selam selam"
    klasor_soz(repo, "uygula")
    assert (el / "merhaba.txt").read_text(encoding="utf-8") == "günaydın selam"
    assert "Bekleyen öneri yok." in klasor_soz(repo, "uygula")["reply"]


def test_masa_bak_tarif_ayrir_ve_yazmaz(masa, monkeypatch):
    from ilim_assistant.motorlar.programlama_proje_masasi import bekleyen_birak, masa_bak_soz

    repo, el = masa
    cagrilar = []

    def sahte(ad, metin):
        cagrilar.append((ad, metin))
        return {
            "belge": "belgeye ... yaz",
            "tablo": "tabloda A1 e 10 yaz",
            "cizim": "çizime kutu çiz",
            "sunum": "sunuma Hoş geldin slaytı ekle: bugün",
        }[ad]

    monkeypatch.setattr(
        "ilim_assistant.motorlar.programlama_proje_masasi._masa_soyleyen",
        sahte,
    )
    bos = masa_bak_soz("belge", "")
    assert "Öneri çıkmadı" in bos["reply"]
    assert bos["eylem"] is None
    assert cagrilar == []
    red = masa_bak_soz("belge", "selam")
    assert "Bu tarif değil" in red["reply"]
    assert red["eylem"] is None
    assert "<" not in cagrilar[0][1]
    monkeypatch.setattr(
        "ilim_assistant.motorlar.programlama_proje_masasi._masa_soyleyen",
        lambda ad, metin: "belgeye selam yaz" if ad == "belge" else "tabloda B1 e 99 yaz",
    )
    kabul = masa_bak_soz("belge", "selam")
    assert kabul["eylem"] == {"eylem": "belge.yaz", "metin": "selam"}
    assert "Önerim: belgeye selam yaz" in kabul["reply"]
    yanlis = masa_bak_soz("tablo", "A1: 10")
    assert yanlis["eylem"] is None
    dogru = masa_bak_soz("tablo", "A1: 10")
    monkeypatch.setattr(
        "ilim_assistant.motorlar.programlama_proje_masasi._masa_soyleyen",
        lambda ad, metin: "tabloda A1 e 10 yaz",
    )
    dogru = masa_bak_soz("tablo", "A1: 10")
    assert dogru["eylem"]["hucre"] == "A1"
    assert dogru["eylem"]["deger"] == "10"
    ciz = masa_bak_soz("cizim", "Çizim boş.")
    monkeypatch.setattr(
        "ilim_assistant.motorlar.programlama_proje_masasi._masa_soyleyen",
        lambda ad, metin: "çizime kutu çiz",
    )
    ciz = masa_bak_soz("cizim", "Çizim boş.")
    assert ciz["eylem"]["eylem"] == "cizim.kutu"
    sunum = masa_bak_soz("sunum", "Slayt 1: Hoş geldin | bugün")
    monkeypatch.setattr(
        "ilim_assistant.motorlar.programlama_proje_masasi._masa_soyleyen",
        lambda ad, metin: "sunuma Hoş geldin slaytı ekle: bugün",
    )
    sunum = masa_bak_soz("sunum", "Slayt 1: Hoş geldin | bugün")
    assert sunum["eylem"]["baslik"] == "Hoş geldin"
    assert sunum["eylem"]["metin"] == "bugün"
    _kilitle(repo, el)
    klasor_soz(repo, "deneme sayfası yap")
    monkeypatch.setattr(
        "ilim_assistant.motorlar.programlama_proje_masasi._soyleyen",
        lambda metin: "başlığı merhaba yap",
    )
    klasor_soz(repo, "deneme sayfasına bak ve söyle")
    assert bekleyen_birak(repo)["birakildi"] is True
    assert bekleyen_birak(repo)["birakildi"] is False
    assert list(el.glob("*.html"))


def test_bilinmeyen_ve_kapi(masa, tmp_path):
    repo, el = masa
    yok = klasor_soz(repo, "menüyü lacivert yap")
    assert yok["handled"] is False
    assert not any(el.iterdir())
    acik = klasor_soz(repo, "merhaba dosyasına selam yaz")
    assert acik["handled"] is True
    assert "seçilmedi" in acik["reply"]
    assert not (el / "merhaba.txt").exists()
    baslik = klasor_soz(repo, "başlığı selam yap")
    assert baslik["handled"] is False
    uygulama = klasor_soz(repo, f"çalışma klasörü: {repo / 'ilim-assistant'}")
    assert uygulama["handled"] is True
    assert "Klasör açılmadı" in uygulama["reply"]
    ust = klasor_soz(repo, f"çalışma klasörü: {tmp_path}")
    assert "Klasör açılmadı" in ust["reply"]
    _kilitle(repo, el)
    kacak = klasor_soz(repo, r"..\gizli.txt dosyasına olmaz yaz")
    assert kacak["handled"] is True
    assert "geçersiz" in kacak["reply"]
    assert not (tmp_path / "gizli.txt").exists()
    assert not (el / "gizli.txt").exists()
