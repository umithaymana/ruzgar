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
    assert "geri alındı" in yarim["reply"]
    assert "Sayfa açık" not in yarim["reply"]
    assert not (el / "deneme.html").exists()
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


def test_masa_bak_beyin_kaliba_yaklasinca_alir(monkeypatch):
    from ilim_assistant.motorlar.programlama_proje_masasi import masa_bak_soz

    def sahte(ad, metin):
        return {
            "belge": "Belgeye gördüğün söz: selam mimar",
            "cizim": "Cevap: çizime kutu çiz",
            "sunum": "Slayt 1: Başlık | Metin",
        }[ad]

    monkeypatch.setattr(
        "ilim_assistant.motorlar.programlama_proje_masasi._masa_soyleyen",
        sahte,
    )
    belge = masa_bak_soz("belge", "selam mimar")
    assert belge["eylem"] == {"eylem": "belge.yaz", "metin": "selam mimar"}
    ciz = masa_bak_soz("cizim", "Çizim boş.")
    assert ciz["eylem"]["eylem"] == "cizim.kutu"
    sunum = masa_bak_soz("sunum", "Slayt 1: Başlık | Metin")
    assert sunum["eylem"] is None
    assert "Bu tarif değil" in sunum["reply"]


def test_tavan_tarif_yazar_ve_tehlikeyi_yemez(masa, monkeypatch):
    from ilim_assistant.motorlar.programlama_proje_masasi import masa_bak_soz

    repo, el = masa
    _kilitle(repo, el)
    klasor_soz(repo, "deneme sayfası yap")
    klasor_soz(repo, "başlığı selam yap")
    once = (el / "deneme.html").read_text(encoding="utf-8")
    say = klasor_soz(repo, "klasördekileri say")
    assert "deneme.html" in say["reply"]
    assert (el / "deneme.html").read_text(encoding="utf-8") == once
    notlar = klasor_soz(repo, "not defteri yap")
    assert (el / "notlar.txt").read_text(encoding="utf-8") == ""
    assert "Yazıldı: klasor/notlar.txt" in notlar["reply"]
    (el / "notlar.txt").write_text("eski", encoding="utf-8")
    duran = klasor_soz(repo, "notlar dosyası yap")
    assert "Dosya duruyor" in duran["reply"]
    assert (el / "notlar.txt").read_text(encoding="utf-8") == "eski"
    ara = klasor_soz(repo, "ara başlık ekle: iç kapı")
    assert "<h2>iç kapı</h2>" in (el / "deneme.html").read_text(encoding="utf-8")
    assert "Ara başlık yazıldı" in ara["reply"]
    renk = klasor_soz(repo, "başlık rengini mavi yap")
    assert 'style="color:#1d4e89"' in (el / "deneme.html").read_text(encoding="utf-8")
    assert "Başlık rengi yazıldı" in renk["reply"]
    bag = klasor_soz(repo, "bağlantı ekle: Rüzgar | https://ornek.com/yol")
    assert 'href="https://ornek.com/yol"' in (el / "deneme.html").read_text(encoding="utf-8")
    assert "Bağlantı yazıldı" in bag["reply"]
    (el / "foto.png").write_bytes(b"\x89PNG\r\n")
    (el / "logo.svg").write_text("<svg></svg>", encoding="utf-8")
    svg_once = (el / "deneme.html").read_text(encoding="utf-8")
    svg = klasor_soz(repo, "resim koy: logo.svg")
    assert "konmaz" in svg["reply"]
    assert (el / "deneme.html").read_text(encoding="utf-8") == svg_once
    yok = klasor_soz(repo, "resim koy: yok.png")
    assert "Dosya yok" in yok["reply"]
    assert (el / "deneme.html").read_text(encoding="utf-8") == svg_once
    resim = klasor_soz(repo, "resim koy: foto.png")
    assert '<img src="foto.png"' in (el / "deneme.html").read_text(encoding="utf-8")
    assert "Resim kondu" in resim["reply"]
    ad = klasor_soz(repo, "deneme sayfasının adını merhaba yap")
    assert not (el / "deneme.html").exists()
    assert "Ad değişti: klasor/merhaba.html" in ad["reply"]
    assert ">selam</h1>" in (el / "merhaba.html").read_text(encoding="utf-8")
    klasor_soz(repo, "index sayfası yap")
    dolu = (el / "merhaba.html").read_text(encoding="utf-8")
    carpisma = klasor_soz(repo, "merhaba sayfasının adını index yap")
    assert "duruyor" in carpisma["reply"]
    assert (el / "merhaba.html").read_text(encoding="utf-8") == dolu
    zehir = klasor_soz(repo, "deneme sayfası yap, bağlantı ekle: selam | javascript:alert(1)")
    assert "Bunu yapmadım" in zehir["reply"]
    assert not (el / "deneme.html").exists()
    kacak = klasor_soz(repo, "merhaba sayfasının adını .. yap")
    assert (el / "merhaba.html").is_file()
    assert "geçersiz" in kacak["reply"]
    monkeypatch.setattr(
        "ilim_assistant.motorlar.programlama_proje_masasi._soyleyen",
        lambda metin: "ara başlık ekle: selam",
    )
    bak = klasor_soz(repo, "merhaba sayfasına bak ve söyle")
    assert "Önerim: ara başlık ekle: selam" in bak["reply"]
    assert (el / "merhaba.html").read_text(encoding="utf-8") == dolu
    uygulandi = klasor_soz(repo, "uygula")
    assert "<h2>selam</h2>" in uygulandi["text"]
    monkeypatch.setattr(
        "ilim_assistant.motorlar.programlama_proje_masasi._soyleyen",
        lambda metin: "bağlantı ekle: selam | https://ornek.com",
    )
    bag_bak = klasor_soz(repo, "merhaba sayfasına bak ve söyle")
    assert "Bu tarif değil" in bag_bak["reply"]
    monkeypatch.setattr(
        "ilim_assistant.motorlar.programlama_proje_masasi._masa_soyleyen",
        lambda ad, metin: "belgede selam yerine merhaba yaz",
    )
    belge = masa_bak_soz("belge", "selam merhaba")
    assert belge["eylem"]["eylem"] == "belge.yerine"
    assert belge["eylem"]["eski"] == "selam"
    monkeypatch.setattr(
        "ilim_assistant.motorlar.programlama_proje_masasi._masa_soyleyen",
        lambda ad, metin: "A sütununu topla",
    )
    tablo = masa_bak_soz("tablo", "A1: 10")
    assert tablo["eylem"] == {"eylem": "tablo.topla", "sutun": "A"}
    monkeypatch.setattr(
        "ilim_assistant.motorlar.programlama_proje_masasi._masa_soyleyen",
        lambda ad, metin: "çizime mavi kutu çiz",
    )
    ciz = masa_bak_soz("cizim", "Çizim boş.")
    assert ciz["eylem"]["renk"] == "mavi"
    assert ciz["eylem"]["eylem"] == "cizim.kutu"
    monkeypatch.setattr(
        "ilim_assistant.motorlar.programlama_proje_masasi._masa_soyleyen",
        lambda ad, metin: "slaytın başlığını Hoş geldin yap",
    )
    sunum = masa_bak_soz("sunum", "Slayt 1: Hoş geldin | bugün")
    assert sunum["eylem"] == {"eylem": "sunum.baslik", "baslik": "Hoş geldin"}
    monkeypatch.setattr(
        "ilim_assistant.motorlar.programlama_proje_masasi._masa_soyleyen",
        lambda ad, metin: "çizime ortaya mavi kutu çiz",
    )
    orta = masa_bak_soz("cizim", "Çizim boş.")
    assert orta["eylem"]["x"] == 680
    assert orta["eylem"]["y"] == 430
    monkeypatch.setattr(
        "ilim_assistant.motorlar.programlama_proje_masasi._masa_soyleyen",
        lambda ad, metin: "slaytın metnini bugün yap",
    )
    govde = masa_bak_soz("sunum", "Slayt 1: Hoş geldin | bugün")
    assert govde["eylem"] == {"eylem": "sunum.metin", "metin": "bugün"}


def test_el_sayfa_renk_okuma_ve_geri(masa, monkeypatch):
    from ilim_assistant.motorlar import programlama_proje_masasi as kapi

    repo, el = masa
    _kilitle(repo, el)
    (el / "index.html").write_text("<title>selam</title>\n<p>selam mimar</p>\n", encoding="utf-8")
    (el / "merhaba.html").write_text("<h1>selam</h1>\n", encoding="utf-8")
    renk = klasor_soz(repo, "index sayfasının başlık rengini mavi yap")
    index = (el / "index.html").read_text(encoding="utf-8")
    assert '<h1 style="color:#1d4e89">selam</h1>' in index
    assert "Başlık rengi yazıldı: klasor/index.html" in renk["reply"]
    assert (el / "merhaba.html").read_text(encoding="utf-8") == "<h1>selam</h1>\n"
    ara = klasor_soz(repo, "merhaba sayfasına ara başlık ekle: iç kapı")
    assert "<h2>iç kapı</h2>" in (el / "merhaba.html").read_text(encoding="utf-8")
    assert "<h2>" not in (el / "index.html").read_text(encoding="utf-8")
    assert "Ara başlık yazıldı" in ara["reply"]
    tekrar = klasor_soz(repo, "merhaba sayfasına ara başlık ekle: iç kapı")
    assert "Zaten var" in tekrar["reply"]
    assert (el / "merhaba.html").read_text(encoding="utf-8").count("<h2>iç kapı</h2>") == 1
    bag = klasor_soz(repo, "index sayfasına bağlantı ekle: Rüzgar | https://ornek.com")
    assert bag["reply"].startswith("Bağlantı yazıldı")
    ikinci = klasor_soz(repo, "index sayfasına bağlantı ekle: Rüzgar | https://ornek.com")
    assert "Zaten var" in ikinci["reply"]
    assert (el / "index.html").read_text(encoding="utf-8").count("https://ornek.com") == 1
    oku = klasor_soz(repo, "merhaba dosyasını oku")
    assert "klasor/merhaba.html okundu" in oku["reply"]
    assert "sayfa açıldı" in oku["reply"]
    once = (el / "merhaba.html").read_text(encoding="utf-8")
    kirik = klasor_soz(repo, "merhaba sayfasına ara başlık ekle: yeni kapı, yok dosyasını oku")
    assert "geri alındı" in kirik["reply"]
    assert (el / "merhaba.html").read_text(encoding="utf-8") == once
    monkeypatch.setattr(kapi, "_soyleyen", lambda metin: "başlık rengini yeşil yap")
    bak = klasor_soz(repo, "index sayfasına bak ve söyle")
    assert "Önerim: başlık rengini yeşil yap" in bak["reply"]
    kapi._BEKLEYEN.clear()
    uygulandi = klasor_soz(repo, "uygula")
    assert 'style="color:#1f7a4d"' in uygulandi["text"]
    assert "Bekleyen öneri yok" in klasor_soz(repo, "uygula")["reply"]


def test_teke_ve_renk_kelimesi(masa):
    repo, el = masa
    _kilitle(repo, el)
    klasor_soz(repo, "deneme sayfası yap")
    klasor_soz(repo, "başlığı selam yap")
    renk = klasor_soz(repo, "başlığı mavi yap")
    govde = (el / "deneme.html").read_text(encoding="utf-8")
    assert "<title>selam</title>" in govde
    assert 'style="color:#1d4e89"' in govde
    assert ">mavi</h1>" not in govde
    assert "Başlık rengi yazıldı" in renk["reply"]
    (el / "index.html").write_text(
        "<title>selam</title>\n"
        "<h2>iç kapı</h2>\n<h2>iç kapı</h2>\n<h2>dış kapı</h2>\n"
        '<a href="https://ornek.com">Rüzgar</a>\n'
        '<a href="https://ornek.com">Rüzgar</a>\n'
        '<a href="https://ornek.com">Rüzgar</a>\n'
        '<a href="https://baska.com">Başka</a>\n',
        encoding="utf-8",
    )
    inen = klasor_soz(repo, "index sayfasındaki aynı bağlantıları teke indir")
    html = (el / "index.html").read_text(encoding="utf-8")
    assert html.count('href="https://ornek.com"') == 1
    assert 'href="https://baska.com"' in html
    assert html.count("<h2>iç kapı</h2>") == 2
    assert "2 kopya indi" in inen["reply"]
    duran = klasor_soz(repo, "index sayfasındaki aynı bağlantıları teke indir")
    assert "Zaten tek" in duran["reply"]
    baslik = klasor_soz(repo, "index sayfasındaki aynı ara başlıkları teke indir")
    html = (el / "index.html").read_text(encoding="utf-8")
    assert html.count("<h2>iç kapı</h2>") == 1
    assert "<h2>dış kapı</h2>" in html
    assert "1 kopya indi" in baslik["reply"]
    sil = klasor_soz(repo, "index dosyasını sil")
    assert sil["handled"] is False
    assert (el / "index.html").is_file()
    assert (el / "deneme.html").is_file()


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


def test_python_ne_yapiyor_calistirmaz(masa):
    repo, el = masa
    _kilitle(repo, el)
    kaynak = (
        '"""İki sayıyı toplar."""\n'
        "import os\n"
        "def topla(a, b):\n"
        "    return a + b\n"
        "def yaz():\n"
        "    open('iz.txt', 'w', encoding='utf-8').write('calisti')\n"
    )
    (el / "hesap.py").write_text(kaynak, encoding="utf-8")
    once = (el / "hesap.py").read_bytes()
    soyle = klasor_soz(repo, "hesap.py dosyasının ne yaptığını söyle")
    assert soyle["handled"] is True
    assert soyle["gorunum"] == "kod"
    assert "topla" in soyle["reply"]
    assert "yaz" in soyle["reply"]
    assert "Çalıştırmadım" in soyle["reply"]
    assert "Dosya aynı" in soyle["reply"]
    assert "calisti" not in soyle["reply"]
    assert (el / "hesap.py").read_bytes() == once
    assert not (el / "iz.txt").exists()
    kisa = klasor_soz(repo, "hesap.py ne yapıyor")
    assert "topla" in kisa["reply"]
    assert (el / "hesap.py").read_bytes() == once
    assert not (el / "iz.txt").exists()
    calistir = klasor_soz(repo, "hesap.py çalıştır")
    assert "çalıştırmadım" in calistir["reply"].lower()
    assert (el / "hesap.py").read_bytes() == once
    assert not (el / "iz.txt").exists()
    bozuk = el / "kirik.py"
    bozuk.write_text("def (", encoding="utf-8")
    red = klasor_soz(repo, "kirik.py ne yapıyor")
    assert "açılmadı" in red["reply"]
    assert bozuk.read_text(encoding="utf-8") == "def ("
    yok = klasor_soz(repo, "yok.py ne yapıyor")
    assert "Dosya yok" in yok["reply"]
    assert not (el / "yok.py").exists()
    from ilim_assistant.motorlar.programlama_motoru import is_code_agent_task_message
    from ilim_assistant.motorlar.programlama_proje_masasi import py_kilit_cumlesi

    assert py_kilit_cumlesi("hesap.py ne yapıyor") is True
    assert is_code_agent_task_message("hesap.py ne yapıyor", "programlama") is False


def test_python_fonksiyon_imzasi(masa):
    repo, el = masa
    _kilitle(repo, el)
    (el / "hesap.py").write_text(
        '"""Dosya."""\n'
        "def topla(a, b):\n"
        '    """İki sayıyı toplar."""\n'
        "    return a + b\n"
        "def yaz():\n"
        "    open('iz.txt', 'w', encoding='utf-8').write('calisti')\n",
        encoding="utf-8",
    )
    once = (el / "hesap.py").read_bytes()
    sonuc = klasor_soz(repo, "hesap.py içinde topla ne yapıyor")
    assert sonuc["handled"] is True
    assert "topla(a, b)" in sonuc["reply"]
    assert "İki sayıyı toplar" in sonuc["reply"]
    assert "Çalıştırmadım" in sonuc["reply"]
    assert "calisti" not in sonuc["reply"]
    assert (el / "hesap.py").read_bytes() == once
    assert not (el / "iz.txt").exists()
    yok = klasor_soz(repo, "hesap.py içinde carp ne yapıyor")
    assert "carp bu dosyada yok" in yok["reply"]
    assert (el / "hesap.py").read_bytes() == once
    from ilim_assistant.motorlar.programlama_motoru import is_code_agent_task_message

    assert is_code_agent_task_message("hesap.py içinde topla ne yapıyor", "programlama") is False


def test_python_fonksiyon_donusu(masa):
    repo, el = masa
    _kilitle(repo, el)
    (el / "hesap.py").write_text(
        "def topla(a, b):\n"
        "    return a + b\n"
        "def yaz():\n"
        "    open('iz.txt', 'w', encoding='utf-8').write('calisti')\n"
        "    return yaz()\n"
        "def sus():\n"
        "    a = 1\n",
        encoding="utf-8",
    )
    once = (el / "hesap.py").read_bytes()
    sonuc = klasor_soz(repo, "hesap.py içinde topla ne döndürüyor")
    assert sonuc["handled"] is True
    assert "a + b döndürür" in sonuc["reply"]
    assert "Çalıştırmadım" in sonuc["reply"]
    assert (el / "hesap.py").read_bytes() == once
    assert not (el / "iz.txt").exists()
    yaz = klasor_soz(repo, "hesap.py içinde yaz ne döndürüyor")
    assert "yaz() döndürür" in yaz["reply"]
    assert not (el / "iz.txt").exists()
    sus = klasor_soz(repo, "hesap.py içinde sus ne döndürüyor")
    assert "Bir değer döndürmez" in sus["reply"]
    assert (el / "hesap.py").read_bytes() == once
    from ilim_assistant.motorlar.programlama_motoru import is_code_agent_task_message

    assert is_code_agent_task_message("hesap.py içinde topla ne döndürüyor", "programlama") is False


def test_python_fonksiyon_cagrisi(masa):
    repo, el = masa
    _kilitle(repo, el)
    (el / "hesap.py").write_text(
        "def topla(a, b):\n"
        "    return a + b\n"
        "def yaz():\n"
        "    open('iz.txt', 'w', encoding='utf-8').write('calisti')\n"
        "    return yaz()\n",
        encoding="utf-8",
    )
    once = (el / "hesap.py").read_bytes()
    sonuc = klasor_soz(repo, "hesap.py içinde topla kimi çağırıyor")
    assert sonuc["handled"] is True
    assert "Kimseyi çağırmaz" in sonuc["reply"]
    assert "Çalıştırmadım" in sonuc["reply"]
    assert (el / "hesap.py").read_bytes() == once
    yaz = klasor_soz(repo, "hesap.py içinde yaz kimi çağırıyor")
    assert "open" in yaz["reply"]
    assert "yaz" in yaz["reply"]
    assert "calisti" not in yaz["reply"]
    assert "iz.txt" not in yaz["reply"]
    assert not (el / "iz.txt").exists()
    yok = klasor_soz(repo, "hesap.py içinde carp kimi çağırıyor")
    assert "carp bu dosyada yok" in yok["reply"]
    assert (el / "hesap.py").read_bytes() == once
    from ilim_assistant.motorlar.programlama_motoru import is_code_agent_task_message

    assert is_code_agent_task_message("hesap.py içinde topla kimi çağırıyor", "programlama") is False


def _ajan_degil(cumle: str) -> None:
    from ilim_assistant.motorlar.programlama_motoru import is_code_agent_task_message

    assert is_code_agent_task_message(cumle, "programlama") is False


def test_python_fonksiyon_yeri(masa):
    repo, el = masa
    _kilitle(repo, el)
    (el / "hesap.py").write_text(
        "def topla(a, b):\n"
        "    return a + b\n"
        "def yaz():\n"
        "    open('iz.txt', 'w', encoding='utf-8').write('calisti')\n",
        encoding="utf-8",
    )
    once = (el / "hesap.py").read_bytes()
    sonuc = klasor_soz(repo, "hesap.py içinde topla nerede")
    assert sonuc["handled"] is True
    assert "1. satırdan 2. satıra." in sonuc["reply"]
    assert "return" not in sonuc["reply"]
    assert "Çalıştırmadım" in sonuc["reply"]
    assert (el / "hesap.py").read_bytes() == once
    assert not (el / "iz.txt").exists()
    yok = klasor_soz(repo, "hesap.py içinde carp nerede")
    assert "carp bu dosyada yok" in yok["reply"]
    assert (el / "hesap.py").read_bytes() == once
    _ajan_degil("hesap.py içinde topla nerede")


def test_python_fonksiyon_yazdigi(masa):
    repo, el = masa
    _kilitle(repo, el)
    (el / "hesap.py").write_text(
        "def topla(a, b):\n"
        "    return a + b\n"
        "def yaz():\n"
        "    iz = open('iz.txt', 'w', encoding='utf-8')\n"
        "    iz.write('calisti')\n",
        encoding="utf-8",
    )
    once = (el / "hesap.py").read_bytes()
    bos = klasor_soz(repo, "hesap.py içinde topla neye yazıyor")
    assert "Bir şeye yazmaz" in bos["reply"]
    assert "Çalıştırmadım" in bos["reply"]
    yaz = klasor_soz(repo, "hesap.py içinde yaz neye yazıyor")
    assert "iz yazar" in yaz["reply"]
    assert "calisti" not in yaz["reply"]
    assert "iz.txt" not in yaz["reply"]
    assert not (el / "iz.txt").exists()
    assert (el / "hesap.py").read_bytes() == once
    _ajan_degil("hesap.py içinde topla neye yazıyor")


def test_python_fonksiyon_kosulu(masa):
    repo, el = masa
    _kilitle(repo, el)
    (el / "hesap.py").write_text(
        "def topla(a, b):\n"
        "    return a + b\n"
        "def yaz(a):\n"
        "    if a > 0:\n"
        "        open('iz.txt', 'w', encoding='utf-8').write('calisti')\n"
        "    while a < 3:\n"
        "        a = a + 1\n",
        encoding="utf-8",
    )
    once = (el / "hesap.py").read_bytes()
    bos = klasor_soz(repo, "hesap.py içinde topla neye bakıyor")
    assert "Bir koşula bakmaz" in bos["reply"]
    yaz = klasor_soz(repo, "hesap.py içinde yaz neye bakıyor")
    assert "a > 0" in yaz["reply"]
    assert "a < 3" in yaz["reply"]
    assert "calisti" not in yaz["reply"]
    assert "Çalıştırmadım" in yaz["reply"]
    assert not (el / "iz.txt").exists()
    assert (el / "hesap.py").read_bytes() == once
    _ajan_degil("hesap.py içinde topla neye bakıyor")


def test_python_sinif_imzalari(masa):
    repo, el = masa
    _kilitle(repo, el)
    (el / "hesap.py").write_text(
        "class Hesap:\n"
        "    def topla(self, a, b):\n"
        '        """İki sayıyı toplar."""\n'
        "        return a + b\n"
        "    def yaz(self):\n"
        "        open('iz.txt', 'w', encoding='utf-8').write('calisti')\n"
        "class Baska:\n"
        "    def gizli(self):\n"
        "        open('iz.txt', 'w', encoding='utf-8').write('calisti')\n",
        encoding="utf-8",
    )
    once = (el / "hesap.py").read_bytes()
    sonuc = klasor_soz(repo, "hesap.py içinde Hesap sınıfı ne yapıyor")
    assert sonuc["handled"] is True
    assert "topla(self, a, b)" in sonuc["reply"]
    assert "yaz(self)" in sonuc["reply"]
    assert "gizli" not in sonuc["reply"]
    assert "calisti" not in sonuc["reply"]
    assert "İki sayıyı toplar" not in sonuc["reply"]
    assert "Çalıştırmadım" in sonuc["reply"]
    assert not (el / "iz.txt").exists()
    yok = klasor_soz(repo, "hesap.py içinde Carp sınıfı ne yapıyor")
    assert "Carp bu dosyada yok" in yok["reply"]
    assert (el / "hesap.py").read_bytes() == once
    _ajan_degil("hesap.py içinde Hesap sınıfı ne yapıyor")


def test_python_ice_alma(masa):
    repo, el = masa
    _kilitle(repo, el)
    (el / "hesap.py").write_text(
        "import os\n"
        "from pathlib import Path\n"
        "def yaz():\n"
        "    open('iz.txt', 'w', encoding='utf-8').write('calisti')\n",
        encoding="utf-8",
    )
    once = (el / "hesap.py").read_bytes()
    sonuc = klasor_soz(repo, "hesap.py neyi içe alıyor")
    assert sonuc["handled"] is True
    assert "os" in sonuc["reply"]
    assert "pathlib" in sonuc["reply"]
    assert "Çalıştırmadım" in sonuc["reply"]
    assert not (el / "iz.txt").exists()
    (el / "bos.py").write_text("def topla(a, b):\n    return a + b\n", encoding="utf-8")
    bos = klasor_soz(repo, "bos.py neyi içe alıyor")
    assert "Bir şey içe almaz" in bos["reply"]
    assert (el / "hesap.py").read_bytes() == once
    _ajan_degil("hesap.py neyi içe alıyor")


def test_orta_is_sablondan_yazar_calistirmaz(masa):
    repo, el = masa
    _kilitle(repo, el)
    sonuc = klasor_soz(repo, "orta iş yap")
    assert sonuc["handled"] is True
    assert "Çalıştırmadım" in sonuc["reply"]
    html = (el / "orta" / "index.html").read_text(encoding="utf-8")
    css = (el / "orta" / "site.css").read_text(encoding="utf-8")
    js = (el / "orta" / "site.js").read_text(encoding="utf-8")
    py = (el / "orta" / "arac.py").read_text(encoding="utf-8")
    assert "site.css" in html and "site.js" in html
    assert "font-family" in css
    assert "Sayıldı" in js
    assert "eval" not in js
    import ast

    agac = ast.parse(py)
    adlar = [d.name for d in agac.body if isinstance(d, ast.FunctionDef)]
    assert adlar == ["satir_say"]
    assert not (el / "orta" / "iz.txt").exists()
    once = (el / "orta" / "arac.py").read_bytes()
    ikinci = klasor_soz(repo, "orta iş yap")
    assert "Orta iş duruyor" in ikinci["reply"]
    assert (el / "orta" / "arac.py").read_bytes() == once
    from ilim_assistant.motorlar.programlama_motoru import is_code_agent_task_message

    assert is_code_agent_task_message("orta iş yap", "programlama") is False


def test_orta_isi_soyler_yazmaz_calistirmaz(masa):
    repo, el = masa
    _kilitle(repo, el)
    bos = klasor_soz(repo, "orta işi söyle")
    assert bos["handled"] is True
    assert "orta/index.html yok." in bos["reply"]
    assert "Çalıştırmadım" in bos["reply"]
    assert not (el / "orta").exists()
    klasor_soz(repo, "orta iş yap")
    once = {
        ad: (el / "orta" / ad).read_bytes()
        for ad in ("index.html", "site.css", "site.js", "arac.py")
    }
    soz = klasor_soz(repo, "orta işi söyle")
    assert "satir_say" in soz["reply"]
    assert "Çalıştırmadım. Dosya aynı." in soz["reply"]
    sonra = {
        ad: (el / "orta" / ad).read_bytes()
        for ad in ("index.html", "site.css", "site.js", "arac.py")
    }
    assert sonra == once
    from ilim_assistant.motorlar.programlama_motoru import is_code_agent_task_message

    assert is_code_agent_task_message("orta işi söyle", "programlama") is False


def test_orta_notu_yoksa_yazar_varsa_ustune_yazmaz(masa):
    repo, el = masa
    _kilitle(repo, el)
    ilk = klasor_soz(repo, "orta notu yaz: ilk satır")
    assert "Yazıldı: orta/not.txt." in ilk["reply"]
    assert "Çalıştırmadım" in ilk["reply"]
    assert (el / "orta" / "not.txt").read_text(encoding="utf-8") == "ilk satır\n"
    ikinci = klasor_soz(repo, "orta notu yaz: başka satır")
    assert "Üstüne yazmadım" in ikinci["reply"]
    assert "ilk satır" in ikinci["reply"]
    assert (el / "orta" / "not.txt").read_text(encoding="utf-8") == "ilk satır\n"
    from ilim_assistant.motorlar.programlama_motoru import is_code_agent_task_message
    from ilim_assistant.motorlar.programlama_proje_masasi import tarif_cumlesi

    assert tarif_cumlesi("orta işi söyle") is True
    assert tarif_cumlesi("orta notu yaz: selam") is True
    assert tarif_cumlesi("şu gazeli söyle: merhaba dünya bugün") is False
    assert is_code_agent_task_message("orta notu yaz: selam", "programlama") is False


def test_orta_not_okur_yoksa_yazmaz(masa):
    repo, el = masa
    _kilitle(repo, el)
    bos = klasor_soz(repo, "orta notunu oku")
    assert "orta/not.txt yok." in bos["reply"]
    assert "Çalıştırmadım" in bos["reply"]
    assert not (el / "orta" / "not.txt").exists()
    klasor_soz(repo, "orta notu yaz: selam")
    once = (el / "orta" / "not.txt").read_bytes()
    okunan = klasor_soz(repo, "orta notunu oku")
    assert "selam" in okunan["reply"]
    assert "Çalıştırmadım. Dosya aynı." in okunan["reply"]
    assert okunan["text"] == "selam\n"
    assert (el / "orta" / "not.txt").read_bytes() == once
    from ilim_assistant.motorlar.programlama_motoru import is_code_agent_task_message

    assert is_code_agent_task_message("orta notunu oku", "programlama") is False


def test_orta_not_satir_ekler_ustune_yazmaz(masa):
    repo, el = masa
    _kilitle(repo, el)
    yok = klasor_soz(repo, "orta notuna satır ekle: ikinci")
    assert yok["handled"] is True
    assert "Not yok." in yok["reply"]
    assert not (el / "orta").exists()
    klasor_soz(repo, "orta notu yaz: selam")
    ek = klasor_soz(repo, "orta notuna satır ekle: ikinci")
    assert "Satır eklendi: orta/not.txt." in ek["reply"]
    assert "Çalıştırmadım" in ek["reply"]
    assert (el / "orta" / "not.txt").read_text(encoding="utf-8") == "selam\nikinci\n"
    ayni = klasor_soz(repo, "orta notuna satır ekle: selam")
    assert "Bu satır duruyor" in ayni["reply"]
    assert "Üstüne yazmadım" in ayni["reply"]
    assert (el / "orta" / "not.txt").read_text(encoding="utf-8") == "selam\nikinci\n"
    soz = klasor_soz(repo, "orta işi söyle")
    assert "orta/not.txt: selam | ikinci." in soz["reply"]
    assert (el / "orta" / "not.txt").read_text(encoding="utf-8") == "selam\nikinci\n"
    for n in range(6):
        klasor_soz(repo, f"orta notuna satır ekle: satir {n}")
    dolu = klasor_soz(repo, "orta notuna satır ekle: fazla")
    assert "Not doldu" in dolu["reply"]
    assert "Üstüne yazmadım" in dolu["reply"]
    govde = (el / "orta" / "not.txt").read_text(encoding="utf-8")
    assert "fazla" not in govde
    assert govde.startswith("selam\nikinci\n")
    assert len([satir for satir in govde.splitlines() if satir.strip()]) == 8
    from ilim_assistant.motorlar.programlama_motoru import is_code_agent_task_message
    from ilim_assistant.motorlar.programlama_proje_masasi import tarif_cumlesi

    assert tarif_cumlesi("orta notuna satır ekle: ikinci") is True
    assert is_code_agent_task_message("orta notuna satır ekle: ikinci", "programlama") is False


def test_orta_arac_bir_kez_sayar_dosyayi_degistirmez(masa):
    repo, el = masa
    _kilitle(repo, el)
    yok = klasor_soz(repo, "orta aracında notu say")
    assert "orta/arac.py yok." in yok["reply"]
    assert "Çalıştırmadım" in yok["reply"]
    assert not (el / "orta").exists()
    klasor_soz(repo, "orta iş yap")
    arac = el / "orta" / "arac.py"
    notsuz = klasor_soz(repo, "orta aracında notu say")
    assert "orta/not.txt yok." in notsuz["reply"]
    assert "Çalıştırmadım" in notsuz["reply"]
    once = arac.read_bytes()
    klasor_soz(repo, "orta notu yaz: selam")
    klasor_soz(repo, "orta notuna satır ekle: ikinci")
    say = klasor_soz(repo, "orta aracında notu say")
    assert "Sayı: 2" in say["reply"]
    assert "bir kez çalıştı" in say["reply"]
    assert "Dosya aynı" in say["reply"]
    assert arac.read_bytes() == once
    assert (el / "orta" / "not.txt").read_text(encoding="utf-8") == "selam\nikinci\n"
    tek = klasor_soz(repo, "orta aracında satır say: selam")
    assert "Sayı: 1" in tek["reply"]
    assert arac.read_bytes() == once
    kisa = klasor_soz(repo, "orta aracında satır say")
    assert "Sayı: 2" in kisa["reply"]
    assert arac.read_bytes() == once
    red = klasor_soz(repo, "hesap.py çalıştır")
    assert "Kodu çalıştırmadım" in red["reply"]
    arac.write_text("import os\nos.system('echo olmaz')\n", encoding="utf-8")
    bozuk = arac.read_bytes()
    yeme = klasor_soz(repo, "orta aracında satır say: selam")
    assert "Hazır araç değil" in yeme["reply"]
    assert "Sayı:" not in yeme["reply"]
    assert arac.read_bytes() == bozuk
    from ilim_assistant.motorlar.programlama_motoru import is_code_agent_task_message
    from ilim_assistant.motorlar.programlama_proje_masasi import tarif_cumlesi

    assert tarif_cumlesi("orta aracında notu say") is True
    assert tarif_cumlesi("orta aracında satır say") is True


def test_orta_testi_sonucu_soyler_duzeltmez(masa):
    repo, el = masa
    _kilitle(repo, el)
    yok = klasor_soz(repo, "orta testini çalıştır")
    assert "orta/arac.py yok." in yok["reply"]
    klasor_soz(repo, "orta iş yap")
    arac = el / "orta" / "arac.py"
    once = arac.read_bytes()
    gecti = klasor_soz(repo, "orta testini çalıştır")
    assert "Test geçti." in gecti["reply"]
    assert "Düzeltmedim" in gecti["reply"]
    assert "Dosya aynı" in gecti["reply"]
    assert arac.read_bytes() == once
    arac.write_text("import os\n", encoding="utf-8")
    bozuk = arac.read_bytes()
    kaldi = klasor_soz(repo, "orta testini çalıştır")
    assert "Hazır araç değil" in kaldi["reply"]
    assert "Düzeltmedim" in kaldi["reply"]
    assert arac.read_bytes() == bozuk
    from ilim_assistant.motorlar.programlama_motoru import is_code_agent_task_message

    assert is_code_agent_task_message("orta testini çalıştır", "programlama") is False


def test_orta_testi_neden_kaldigini_soyler_duzeltmez(masa):
    repo, el = masa
    _kilitle(repo, el)
    yok = klasor_soz(repo, "orta testi neden kaldı")
    assert "orta/arac.py yok." in yok["reply"]
    klasor_soz(repo, "orta iş yap")
    arac = el / "orta" / "arac.py"
    once = arac.read_bytes()
    gecti = klasor_soz(repo, "orta testi neden kaldı")
    assert "Üç kontrol de geçti." in gecti["reply"]
    assert "Düzeltmedim" in gecti["reply"]
    assert arac.read_bytes() == once
    arac.write_text("import os\n", encoding="utf-8")
    bozuk = arac.read_bytes()
    neden = klasor_soz(repo, "orta testi neden kaldı")
    assert "Hazır araç değil" in neden["reply"]
    assert "Kontrol çalışmadı" in neden["reply"]
    assert "Düzeltmedim" in neden["reply"]
    assert arac.read_bytes() == bozuk
    from ilim_assistant.motorlar.programlama_proje_masasi import _kontrol_kaldi

    def yanlis(metin):
        return 0

    assert "1. kontrol: selam kaldı" in _kontrol_kaldi(yanlis)
    from ilim_assistant.motorlar.programlama_motoru import is_code_agent_task_message

    assert is_code_agent_task_message("orta testi neden kaldı", "programlama") is False


def test_orta_turu_baslat_okur_yazmaz(masa):
    repo, el = masa
    _kilitle(repo, el)
    yok = klasor_soz(repo, "orta turu başlat")
    assert "orta/arac.py yok." in yok["reply"]
    assert "Yazıldı" not in yok["reply"]
    klasor_soz(repo, "orta iş yap")
    arac = el / "orta" / "arac.py"
    once = arac.read_bytes()
    gecti = klasor_soz(repo, "orta turu başlat")
    assert "Üç kontrol de geçti." in gecti["reply"]
    assert "Tur durdu." in gecti["reply"]
    assert "Düzeltmedim" in gecti["reply"]
    assert "Yazıldı" not in gecti["reply"]
    assert arac.read_bytes() == once
    arac.write_text("import os\n", encoding="utf-8")
    bozuk = arac.read_bytes()
    kaldi = klasor_soz(repo, "orta turu başlat")
    assert "Hazır araç değil" in kaldi["reply"]
    assert "Düzeltmedim" in kaldi["reply"]
    assert "Yazıldı" not in kaldi["reply"]
    assert arac.read_bytes() == bozuk
    from ilim_assistant.motorlar.programlama_motoru import is_code_agent_task_message
    from ilim_assistant.motorlar.programlama_proje_masasi import tarif_cumlesi

    assert tarif_cumlesi("orta turu başlat") is True
    assert is_code_agent_task_message("orta turu başlat", "programlama") is False


def test_orta_turu_duzelt_yalniz_kalinca_bilinen_satiri_yazar(masa):
    repo, el = masa
    _kilitle(repo, el)
    arac = el / "orta" / "arac.py"
    erken = klasor_soz(repo, "orta turu düzelt")
    assert "Tur kalmadı" in erken["reply"]
    assert "Yazmadım" in erken["reply"]
    assert not arac.exists()
    klasor_soz(repo, "orta iş yap")
    once = arac.read_bytes()
    klasor_soz(repo, "orta turu başlat")
    gecti = klasor_soz(repo, "orta turu düzelt")
    assert "Tur geçti" in gecti["reply"]
    assert "Yazmadım" in gecti["reply"]
    assert arac.read_bytes() == once
    arac.write_text("import os\n", encoding="utf-8")
    bozuk = arac.read_bytes()
    klasor_soz(repo, "orta turu başlat")
    fazla = klasor_soz(repo, "orta turu düzelt: import os")
    assert "Bu cümle yazmaz" in fazla["reply"]
    assert arac.read_bytes() == bozuk
    yaz = klasor_soz(repo, "orta turu düzelt")
    assert "Yazıldı: orta/arac.py." in yaz["reply"]
    assert _ARAC_SATIR in yaz["reply"]
    assert "Çalıştırmadım" in yaz["reply"]
    from ilim_assistant.motorlar.programlama_proje_masasi import _ORTA_DOSYA

    assert arac.read_text(encoding="utf-8") == _ORTA_DOSYA["orta/arac.py"]
    duran = arac.read_bytes()
    ust = klasor_soz(repo, "orta turu düzelt")
    assert "Üstüne yazmadım" in ust["reply"]
    assert arac.read_bytes() == duran
    from ilim_assistant.motorlar.programlama_motoru import is_code_agent_task_message
    from ilim_assistant.motorlar.programlama_proje_masasi import tarif_cumlesi

    assert tarif_cumlesi("orta turu düzelt") is True
    assert is_code_agent_task_message("orta turu düzelt", "programlama") is False
    assert is_code_agent_task_message("orta turu düzelt: import os", "programlama") is False


def test_orta_turu_bak_bir_kez_bakar_ucuncuye_gecmez(masa):
    repo, el = masa
    _kilitle(repo, el)
    erken = klasor_soz(repo, "orta turu bak")
    assert "Düzeltme yok" in erken["reply"]
    assert "Bakmadım" in erken["reply"]
    klasor_soz(repo, "orta iş yap")
    arac = el / "orta" / "arac.py"
    arac.write_text("import os\n", encoding="utf-8")
    klasor_soz(repo, "orta turu başlat")
    klasor_soz(repo, "orta turu düzelt")
    once = arac.read_bytes()
    fazla = klasor_soz(repo, "orta turu bak tekrar")
    assert "Bu cümle bakmaz" in fazla["reply"]
    assert arac.read_bytes() == once
    bak = klasor_soz(repo, "orta turu bak")
    assert "Test geçti." in bak["reply"]
    assert "Düzeltmedim" in bak["reply"]
    assert arac.read_bytes() == once
    ucuncu = klasor_soz(repo, "orta turu bak")
    assert "Üçüncüye geçmedim" in ucuncu["reply"]
    assert arac.read_bytes() == once
    from ilim_assistant.motorlar.programlama_motoru import is_code_agent_task_message

    assert is_code_agent_task_message("orta turu bak", "programlama") is False


def test_orta_turu_kapat_bakis_gecince_tek_satiri_bitti_yapar(masa):
    repo, el = masa
    _kilitle(repo, el)
    tahta = repo / "RUZGAR_SIRA.md"
    govde = (
        "| Sıra | İş | Durum | Son test |\n"
        "| --- | --- | --- | --- |\n"
        "| 1 | Eski iş | bitti | eski |\n"
        "| 2 | Açık iş | bekliyor | yok |\n"
        "\n"
        "**Denenecek cümle:** `orta turu kapat`\n"
        "**Bilerek kapalı:** dosya silmek\n"
    )
    tahta.write_text(govde, encoding="utf-8")
    erken = klasor_soz(repo, "orta turu kapat")
    assert "Bakış geçmedi" in erken["reply"]
    assert tahta.read_text(encoding="utf-8") == govde
    klasor_soz(repo, "orta iş yap")
    arac = el / "orta" / "arac.py"
    arac.write_text("import os\n", encoding="utf-8")
    klasor_soz(repo, "orta turu başlat")
    klasor_soz(repo, "orta turu düzelt")
    fazla = klasor_soz(repo, "orta turu kapat hemen")
    assert "Bu cümle kapatmaz" in fazla["reply"]
    assert tahta.read_text(encoding="utf-8") == govde
    klasor_soz(repo, "orta turu bak")
    once_satir = tahta.read_text(encoding="utf-8").splitlines()
    once_arac = arac.read_bytes()
    isaret = klasor_soz(repo, "orta turu kapat")
    assert "Açık satır bitti oldu." in isaret["reply"]
    assert "silinmedi" in isaret["reply"]
    assert arac.read_bytes() == once_arac
    sonra = tahta.read_text(encoding="utf-8").splitlines()
    assert len(sonra) == len(once_satir)
    assert "| 1 | Eski iş | bitti | eski |" in sonra
    assert "| 2 | Açık iş | bitti | yok |" in sonra
    assert sonra[-1] == "**Bilerek kapalı:** dosya silmek"
    cok = (
        "| 1 | Bir | bekliyor | a |\n"
        "| 2 | İki | bekliyor | b |\n"
    )
    tahta.write_text(cok, encoding="utf-8")
    red = klasor_soz(repo, "orta turu kapat")
    assert "Birden fazla açık satır" in red["reply"]
    assert tahta.read_text(encoding="utf-8") == cok
    from ilim_assistant.motorlar.programlama_motoru import is_code_agent_task_message

    assert is_code_agent_task_message("orta turu kapat", "programlama") is False


def test_orta_turu_soyle_sirayi_soyler_yazmaz(masa):
    repo, el = masa
    _kilitle(repo, el)
    tahta = repo / "RUZGAR_SIRA.md"
    tahta.write_text("| 1 | Açık iş | bekliyor | yok |\n", encoding="utf-8")
    once_tahta = tahta.read_bytes()
    yok = klasor_soz(repo, "orta turu söyle")
    assert "Sıra: orta turu başlat, orta turu düzelt, orta turu bak, orta turu kapat." in yok["reply"]
    assert "Şimdi: tur yok." in yok["reply"]
    assert "Yazmadım" in yok["reply"]
    assert tahta.read_bytes() == once_tahta
    klasor_soz(repo, "orta iş yap")
    arac = el / "orta" / "arac.py"
    once = arac.read_bytes()
    klasor_soz(repo, "orta turu başlat")
    durdu = klasor_soz(repo, "orta turu söyle")
    assert "Şimdi: tur durdu." in durdu["reply"]
    assert arac.read_bytes() == once
    assert tahta.read_bytes() == once_tahta
    arac.write_text("import os\n", encoding="utf-8")
    bozuk = arac.read_bytes()
    klasor_soz(repo, "orta turu başlat")
    fazla = klasor_soz(repo, "orta turu söyle hemen")
    assert "Bu cümle söylemez" in fazla["reply"]
    assert arac.read_bytes() == bozuk
    kaldi = klasor_soz(repo, "orta turu söyle")
    assert "Şimdi: tur kaldı, düzeltme yok." in kaldi["reply"]
    assert arac.read_bytes() == bozuk
    from ilim_assistant.motorlar.programlama_motoru import is_code_agent_task_message
    from ilim_assistant.motorlar.programlama_proje_masasi import tarif_cumlesi

    assert tarif_cumlesi("orta turu söyle") is True
    assert is_code_agent_task_message("orta turu söyle", "programlama") is False


def test_hazir_arac_turu_yok_demez(masa):
    repo, el = masa
    _kilitle(repo, el)
    from ilim_assistant.motorlar.programlama_proje_masasi import _ORTA_DOSYA

    arac = el / "orta" / "arac.py"
    arac.parent.mkdir()
    arac.write_text(_ORTA_DOSYA["orta/arac.py"], encoding="utf-8")
    (repo / "ilim-assistant" / ".ruzgar").mkdir()
    (repo / "ilim-assistant" / ".ruzgar" / "orta_tur.txt").write_text("kaldi=0\ndurdu=0\n", encoding="utf-8")
    once = arac.read_bytes()
    soyle = klasor_soz(repo, "orta turu söyle")
    assert "dosya hazır, bakış yok." in soyle["reply"]
    assert "tur yok" not in soyle["reply"]
    assert "Yazmadım" in soyle["reply"]
    assert arac.read_bytes() == once


def test_hazir_arac_duzelt_kalmadi_demez(masa):
    repo, el = masa
    _kilitle(repo, el)
    from ilim_assistant.motorlar.programlama_proje_masasi import _ORTA_DOSYA

    arac = el / "orta" / "arac.py"
    arac.parent.mkdir()
    arac.write_text(_ORTA_DOSYA["orta/arac.py"], encoding="utf-8")
    durum = repo / "ilim-assistant" / ".ruzgar" / "orta_tur.txt"
    durum.parent.mkdir(parents=True)
    durum.write_text(
        "duzeltme=0\nbakis=1\ngecti=0\ndurdu=0\nkaldi=0\ntur=0\n",
        encoding="utf-8",
    )
    once = arac.read_bytes()
    duzelt = klasor_soz(repo, "orta turu düzelt")
    assert "Bilinen satır duruyor" in duzelt["reply"]
    assert "Tur kalmadı" not in duzelt["reply"]
    assert "Üstüne yazmadım" in duzelt["reply"]
    assert arac.read_bytes() == once
    govde = durum.read_text(encoding="utf-8")
    assert "duzeltme=1" in govde
    assert "bakis=1" in govde
    assert "tur=1" in govde


def test_eski_gecti_bayragi_bozuk_araci_gizlemez(masa):
    repo, el = masa
    _kilitle(repo, el)
    arac = el / "orta" / "arac.py"
    arac.parent.mkdir()
    arac.write_text("import os\n", encoding="utf-8")
    durum = repo / "ilim-assistant" / ".ruzgar" / "orta_tur.txt"
    durum.parent.mkdir(parents=True)
    durum.write_text(
        "duzeltme=1\nbakis=1\ngecti=1\ndurdu=1\nkaldi=0\ntur=1\n",
        encoding="utf-8",
    )
    once = arac.read_bytes()
    duzelt = klasor_soz(repo, "orta turu düzelt")
    assert "Hazır araç değil" in duzelt["reply"]
    assert "Yazmadım" in duzelt["reply"]
    assert "Tur geçti" not in duzelt["reply"]
    assert arac.read_bytes() == once


def test_hazir_arac_bak_duzeltme_yok_demez(masa):
    repo, el = masa
    _kilitle(repo, el)
    from ilim_assistant.motorlar.programlama_proje_masasi import _ORTA_DOSYA

    arac = el / "orta" / "arac.py"
    arac.parent.mkdir()
    arac.write_text(_ORTA_DOSYA["orta/arac.py"], encoding="utf-8")
    (repo / "ilim-assistant" / ".ruzgar").mkdir()
    (repo / "ilim-assistant" / ".ruzgar" / "orta_tur.txt").write_text("kaldi=0\ndurdu=0\n", encoding="utf-8")
    once = arac.read_bytes()
    bak = klasor_soz(repo, "orta turu bak")
    assert "Test geçti." in bak["reply"]
    assert "Düzeltme yok" not in bak["reply"]
    assert arac.read_bytes() == once
    ikinci = klasor_soz(repo, "orta turu bak")
    assert "Üçüncüye geçmedim" in ikinci["reply"]
    assert arac.read_bytes() == once


def test_orta_turu_baslat_gectiyse_bakis_silinmez(masa):
    repo, el = masa
    _kilitle(repo, el)
    from ilim_assistant.motorlar.programlama_proje_masasi import _ORTA_DOSYA

    arac = el / "orta" / "arac.py"
    arac.parent.mkdir()
    arac.write_text(_ORTA_DOSYA["orta/arac.py"], encoding="utf-8")
    durum = repo / "ilim-assistant" / ".ruzgar" / "orta_tur.txt"
    durum.parent.mkdir(parents=True)
    durum.write_text(
        "duzeltme=1\nbakis=1\ngecti=1\ndurdu=0\nkaldi=0\ntur=1\n",
        encoding="utf-8",
    )
    once = arac.read_bytes()
    baslat = klasor_soz(repo, "orta turu başlat")
    assert "Üç kontrol de geçti." in baslat["reply"]
    assert arac.read_bytes() == once
    govde = durum.read_text(encoding="utf-8")
    assert "bakis=1" in govde
    assert "gecti=1" in govde
    assert "duzeltme=1" in govde
    assert "tur=1" in govde
    assert "durdu=1" in govde


def test_hazir_arac_kapat_bakistan_sonra_tek_satiri_bitti_yapar(masa):
    repo, el = masa
    _kilitle(repo, el)
    from ilim_assistant.motorlar.programlama_proje_masasi import _ORTA_DOSYA

    arac = el / "orta" / "arac.py"
    arac.parent.mkdir()
    arac.write_text(_ORTA_DOSYA["orta/arac.py"], encoding="utf-8")
    (repo / "ilim-assistant" / ".ruzgar").mkdir()
    (repo / "ilim-assistant" / ".ruzgar" / "orta_tur.txt").write_text("kaldi=0\ndurdu=0\n", encoding="utf-8")
    tahta = repo / "RUZGAR_SIRA.md"
    govde = "| 1 | Açık iş | bekliyor | yok |\n"
    tahta.write_text(govde, encoding="utf-8")
    once = arac.read_bytes()
    erken = klasor_soz(repo, "orta turu kapat")
    assert "Bakış geçmedi" in erken["reply"]
    assert tahta.read_text(encoding="utf-8") == govde
    bak = klasor_soz(repo, "orta turu bak")
    assert "Test geçti." in bak["reply"]
    kapat = klasor_soz(repo, "orta turu kapat")
    assert "Açık satır bitti oldu." in kapat["reply"]
    assert "| 1 | Açık iş | bitti | yok |" in tahta.read_text(encoding="utf-8")
    assert arac.read_bytes() == once


def test_hazir_aracta_dort_cumle_ayni_hikayeyi_soyler(masa):
    repo, el = masa
    _kilitle(repo, el)
    from ilim_assistant.motorlar.programlama_proje_masasi import _ORTA_DOSYA

    arac = el / "orta" / "arac.py"
    arac.parent.mkdir()
    arac.write_text(_ORTA_DOSYA["orta/arac.py"], encoding="utf-8")
    (repo / "ilim-assistant" / ".ruzgar").mkdir()
    (repo / "ilim-assistant" / ".ruzgar" / "orta_tur.txt").write_text("kaldi=0\ndurdu=0\n", encoding="utf-8")
    tahta = repo / "RUZGAR_SIRA.md"
    tahta.write_text("| 1 | Açık iş | bekliyor | yok |\n", encoding="utf-8")
    once = arac.read_bytes()
    soyle = klasor_soz(repo, "orta turu söyle")
    duzelt = klasor_soz(repo, "orta turu düzelt")
    bak = klasor_soz(repo, "orta turu bak")
    kapat = klasor_soz(repo, "orta turu kapat")
    sonra = klasor_soz(repo, "orta turu söyle")
    assert "dosya hazır, bakış yok." in soyle["reply"]
    assert "Bilinen satır duruyor" in duzelt["reply"]
    assert "Test geçti." in bak["reply"]
    assert "Açık satır bitti oldu." in kapat["reply"]
    assert "bakış geçti." in sonra["reply"]
    for cevap in (soyle, duzelt, bak, kapat, sonra):
        assert "tur yok" not in cevap["reply"]
        assert "Tur kalmadı" not in cevap["reply"]
        assert "Düzeltme yok" not in cevap["reply"]
        assert "Bakış geçmedi" not in cevap["reply"]
    assert arac.read_bytes() == once
    assert "| 1 | Açık iş | bitti | yok |" in tahta.read_text(encoding="utf-8")


_ARAC_SATIR = "return len([satir for satir in metin.splitlines() if satir.strip()])"


def test_orta_araci_yalniz_bilinen_satiri_yazar(masa):
    repo, el = masa
    _kilitle(repo, el)
    arac = el / "orta" / "arac.py"
    red = klasor_soz(repo, "orta aracını düzelt: import os")
    assert "Bu satır yazılmaz." in red["reply"]
    assert "Çalıştırmadım" in red["reply"]
    assert not arac.exists()
    yaz = klasor_soz(repo, "orta aracını düzelt: " + _ARAC_SATIR)
    assert "Yazıldı: orta/arac.py." in yaz["reply"]
    assert "Çalıştırmadım" in yaz["reply"]
    assert "Sayı:" not in yaz["reply"]
    from ilim_assistant.motorlar.programlama_proje_masasi import _ORTA_DOSYA

    assert arac.read_text(encoding="utf-8") == _ORTA_DOSYA["orta/arac.py"]
    assert not (el / "orta" / "not.txt").exists()
    duran = arac.read_bytes()
    ikinci = klasor_soz(repo, "orta aracını düzelt: " + _ARAC_SATIR)
    assert "Üstüne yazmadım" in ikinci["reply"]
    assert arac.read_bytes() == duran
    arac.write_text("import os\n", encoding="utf-8")
    bozuk = arac.read_bytes()
    yeme = klasor_soz(repo, "orta aracını düzelt: return 1")
    assert "Bu satır yazılmaz." in yeme["reply"]
    assert arac.read_bytes() == bozuk
    geri = klasor_soz(repo, "orta aracını düzelt: " + _ARAC_SATIR)
    assert "Yazıldı: orta/arac.py." in geri["reply"]
    assert arac.read_text(encoding="utf-8") == _ORTA_DOSYA["orta/arac.py"]
    from ilim_assistant.motorlar.programlama_motoru import is_code_agent_task_message

    assert is_code_agent_task_message("orta aracını düzelt: " + _ARAC_SATIR, "programlama") is False


def test_eksik_duzeltme_kapida_kalir_yazmaz(masa):
    repo, el = masa
    _kilitle(repo, el)
    klasor_soz(repo, "orta iş yap")
    arac = el / "orta" / "arac.py"
    once = arac.read_bytes()
    from ilim_assistant.motorlar.programlama_motoru import is_code_agent_task_message
    from ilim_assistant.motorlar.programlama_proje_masasi import tarif_cumlesi

    for cumle in ("orta aracını düzelt", "orta aracını düzelt:"):
        cevap = klasor_soz(repo, cumle)
        assert cevap["handled"] is True
        assert _ARAC_SATIR in cevap["reply"]
        assert "Çalıştırmadım" in cevap["reply"]
        assert "Dosya aynı" in cevap["reply"]
        assert "Yazıldı" not in cevap["reply"]
        assert arac.read_bytes() == once
        assert tarif_cumlesi(cumle) is True
        assert is_code_agent_task_message(cumle, "programlama") is False
    yaz = klasor_soz(repo, "orta aracını düzelt: " + _ARAC_SATIR)
    assert "Üstüne yazmadım" in yaz["reply"]
    assert arac.read_bytes() == once


def test_ikinci_bakis_bir_kez_bakar_ucuncuye_gecmez(masa):
    repo, el = masa
    _kilitle(repo, el)
    erken = klasor_soz(repo, "orta testine ikinci bak")
    assert "Düzeltme yok" in erken["reply"]
    assert not (el / "orta" / "arac.py").exists()
    klasor_soz(repo, "orta aracını düzelt: " + _ARAC_SATIR)
    arac = el / "orta" / "arac.py"
    once = arac.read_bytes()
    bak = klasor_soz(repo, "orta testine ikinci bak")
    assert "Test geçti." in bak["reply"]
    assert "Düzeltmedim" in bak["reply"]
    assert arac.read_bytes() == once
    ucuncu = klasor_soz(repo, "orta testine ikinci bak")
    assert "Üçüncüye geçmedim" in ucuncu["reply"]
    assert arac.read_bytes() == once
    from ilim_assistant.motorlar.programlama_motoru import is_code_agent_task_message

    assert is_code_agent_task_message("orta testine ikinci bak", "programlama") is False


def test_acik_satir_yalniz_gecince_bitti_olur(masa):
    repo, el = masa
    _kilitle(repo, el)
    tahta = repo / "RUZGAR_SIRA.md"
    govde = (
        "| Sıra | İş | Durum | Son test |\n"
        "| --- | --- | --- | --- |\n"
        "| 1 | Eski iş | bitti | eski |\n"
        "| 2 | Açık iş | bekliyor | yok |\n"
        "\n"
        "**Denenecek cümle:** `orta testi neden kaldı`\n"
        "**Bilerek kapalı:** dosya silmek\n"
    )
    tahta.write_text(govde, encoding="utf-8")
    erken = klasor_soz(repo, "açık satırı bitti yap")
    assert "Test geçmedi" in erken["reply"]
    assert tahta.read_text(encoding="utf-8") == govde
    klasor_soz(repo, "orta aracını düzelt: " + _ARAC_SATIR)
    klasor_soz(repo, "orta testine ikinci bak")
    once_satir = tahta.read_text(encoding="utf-8").splitlines()
    isaret = klasor_soz(repo, "açık satırı bitti yap")
    assert "Açık satır bitti oldu." in isaret["reply"]
    assert "silinmedi" in isaret["reply"]
    sonra = tahta.read_text(encoding="utf-8").splitlines()
    assert len(sonra) == len(once_satir)
    assert sonra[0] == once_satir[0]
    assert sonra[2] == once_satir[2]
    assert "| 2 | Açık iş | bitti | yok |" == sonra[3]
    assert sonra[-1] == "**Bilerek kapalı:** dosya silmek"
    assert sonra[-2] == "**Denenecek cümle:** `orta testi neden kaldı`"
    tekrar = klasor_soz(repo, "açık satırı bitti yap")
    assert "Açık satır yok" in tekrar["reply"]
    assert tahta.read_text(encoding="utf-8").splitlines() == sonra
    cok = (
        "| 1 | Bir | bekliyor | a |\n"
        "| 2 | İki | bekliyor | b |\n"
    )
    tahta.write_text(cok, encoding="utf-8")
    red = klasor_soz(repo, "açık satırı bitti yap")
    assert "Birden fazla açık satır" in red["reply"]
    assert tahta.read_text(encoding="utf-8") == cok
    assert (el / "orta" / "arac.py").is_file()
    from ilim_assistant.motorlar.programlama_motoru import is_code_agent_task_message

    assert is_code_agent_task_message("açık satırı bitti yap", "programlama") is False
    assert is_code_agent_task_message("orta aracında notu say", "programlama") is False
    assert is_code_agent_task_message("hesap.py çalıştır", "programlama") is False


def test_uygulama_notu_yalniz_deftere_yazar(masa):
    repo, el = masa
    _kilitle(repo, el)
    bos = klasor_soz(repo, "uygulama notunu oku")
    assert "uygulama_notu.txt yok." in bos["reply"]
    assert "Çalıştırmadım" in bos["reply"]
    assert not (repo / "ilim-assistant" / ".ruzgar" / "uygulama_notu.txt").exists()
    yaz = klasor_soz(repo, "uygulama notu yaz: selam")
    assert "Yazıldı: ilim-assistant/.ruzgar/uygulama_notu.txt." in yaz["reply"]
    assert "Çalıştırmadım" in yaz["reply"]
    defter = repo / "ilim-assistant" / ".ruzgar" / "uygulama_notu.txt"
    assert defter.read_text(encoding="utf-8") == "selam\n"
    assert not (el / "uygulama_notu.txt").exists()
    ikinci = klasor_soz(repo, "uygulama notu yaz: başka")
    assert "Üstüne yazmadım" in ikinci["reply"]
    assert "selam" in ikinci["reply"]
    assert defter.read_text(encoding="utf-8") == "selam\n"
    okunan = klasor_soz(repo, "uygulama notunu oku")
    assert "selam" in okunan["reply"]
    assert "Dosya aynı" in okunan["reply"]
    assert defter.read_text(encoding="utf-8") == "selam\n"
    assert not list((repo / "ilim-assistant").rglob("*.py"))
    from ilim_assistant.motorlar.programlama_motoru import is_code_agent_task_message
    from ilim_assistant.motorlar.programlama_proje_masasi import tarif_cumlesi

    assert tarif_cumlesi("uygulama notu yaz: selam") is True
    assert is_code_agent_task_message("uygulama notu yaz: selam", "programlama") is False


def test_kaynak_satiri_tek_dosyaya_yazar_calistirmaz(masa):
    repo, el = masa
    _kilitle(repo, el)
    yaz = klasor_soz(repo, "kaynak satırı yaz: selam")
    assert "Yazıldı: ilim-assistant/ilim_assistant/kapi_notu.py." in yaz["reply"]
    assert "Çalıştırmadım" in yaz["reply"]
    dosya = repo / "ilim-assistant" / "ilim_assistant" / "kapi_notu.py"
    assert dosya.read_text(encoding="utf-8") == '"""Kapı notu. Çalıştırılmaz."""\n\nSATIR = "selam"\n'
    assert not (el / "kapi_notu.py").exists()
    ikinci = klasor_soz(repo, "kaynak satırı yaz: başka")
    assert "Üstüne yazmadım" in ikinci["reply"]
    assert dosya.read_text(encoding="utf-8").count("SATIR") == 1
    tirnak = klasor_soz(repo, 'kaynak satırı yaz: "kirik')
    assert "tırnak" in tirnak["reply"]
    from ilim_assistant.motorlar.programlama_motoru import is_code_agent_task_message

    assert is_code_agent_task_message("kaynak satırı yaz: selam", "programlama") is False


def test_dis_klasor_okur_yazmaz(masa, tmp_path):
    repo, el = masa
    _kilitle(repo, el)
    yok = klasor_soz(repo, "dış klasörü say")
    assert "Dış klasör seçilmedi" in yok["reply"]
    dis = tmp_path / "dis"
    alt = dis / "alt"
    alt.mkdir(parents=True)
    (alt / "gizli.txt").write_text("gizli\n", encoding="utf-8")
    not_ = dis / "not.txt"
    not_.write_text("dışarı\n", encoding="utf-8")
    (dis / "gizli.env").write_text("sir\n", encoding="utf-8")
    once = not_.read_bytes()
    ic = klasor_soz(repo, f"dış klasör: {el}")
    assert "kilitli klasör" in ic["reply"]
    kok = klasor_soz(repo, "dış klasör: C:\\")
    assert "Sürücü kökü" in kok["reply"]
    uygulama = klasor_soz(repo, f"dış klasör: {repo / 'ilim-assistant'}")
    assert "Uygulama klasörü" in uygulama["reply"]
    ac = klasor_soz(repo, f"dış klasör: {dis}")
    assert "Dış klasör:" in ac["reply"]
    assert "Yazmadım" in ac["reply"]
    say = klasor_soz(repo, "dış klasörü say")
    assert "not.txt" in say["reply"]
    assert "alt" in say["reply"]
    assert "gizli.txt" not in say["reply"]
    assert "Yazmadım. Çalıştırmadım." in say["reply"]
    okunan = klasor_soz(repo, "dış dosyayı oku: not.txt")
    assert "dışarı" in okunan["reply"]
    assert "Dosya aynı" in okunan["reply"]
    assert not_.read_bytes() == once
    env = klasor_soz(repo, "dış dosyayı oku: gizli.env")
    assert "okunmaz" in env["reply"]
    assert (dis / "gizli.env").read_text(encoding="utf-8") == "sir\n"
    kac = klasor_soz(repo, "dış dosyayı oku: alt/gizli.txt")
    assert "geçersiz" in kac["reply"]
    klasor_soz(repo, f"çalışma klasörü: {el}")
    duran = klasor_soz(repo, "dış klasörü say")
    assert "not.txt" in duran["reply"]
    from ilim_assistant.motorlar.programlama_motoru import is_code_agent_task_message
    from ilim_assistant.motorlar.programlama_proje_masasi import tarif_cumlesi

    assert tarif_cumlesi("dış klasörü say") is True
    assert is_code_agent_task_message("dış dosyayı oku: not.txt", "programlama") is False


def test_dis_dosyaya_bir_kez_yazar(masa, tmp_path):
    repo, el = masa
    _kilitle(repo, el)
    dis = tmp_path / "dis-yaz"
    dis.mkdir()
    klasor_soz(repo, f"dış klasör: {dis}")
    yaz = klasor_soz(repo, "dış dosyaya yaz: kapi.txt: selam")
    assert "Yazıldı: kapi.txt." in yaz["reply"]
    assert "Çalıştırmadım" in yaz["reply"]
    assert (dis / "kapi.txt").read_text(encoding="utf-8") == "selam\n"
    ikinci = klasor_soz(repo, "dış dosyaya yaz: kapi.txt: başka")
    assert "Üstüne yazmadım" in ikinci["reply"]
    assert (dis / "kapi.txt").read_text(encoding="utf-8") == "selam\n"
    kac = klasor_soz(repo, "dış dosyaya yaz: alt/kapi.txt: selam")
    assert "geçersiz" in kac["reply"]
    assert not (dis / "alt").exists()
    env = klasor_soz(repo, "dış dosyaya yaz: gizli.env: sir")
    assert "yazılmaz" in env["reply"]
    assert not (dis / "gizli.env").exists()


def test_git_durumu_soyler_gondermez(masa):
    import shutil
    import subprocess

    repo, el = masa
    _kilitle(repo, el)
    shutil.rmtree(repo / ".git")
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    (repo / "a.txt").write_text("bir\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "a.txt"], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(repo), "-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-m", "ilk"],
        check=True,
        capture_output=True,
    )
    bas = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"])
    (repo / "a.txt").write_text("iki\n", encoding="utf-8")
    (repo / "yeni.txt").write_text("x\n", encoding="utf-8")
    soz = klasor_soz(repo, "git ne durumda")
    assert soz["handled"] is True
    assert "Dal:" in soz["reply"]
    assert "Son kayıt:" in soz["reply"]
    assert "a.txt" in soz["reply"]
    assert "yeni.txt" in soz["reply"]
    assert "Göndermedim" in soz["reply"]
    assert subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"]) == bas
    red = klasor_soz(repo, "git gönder")
    assert "Uzak yok" in red["reply"]
    assert "Göndermedim" in red["reply"]
    assert subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"]) == bas
    duz = klasor_soz(repo, "git kaydet")
    assert "Bunu yapmadım" in duz["reply"]
    assert subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"]) == bas
    from ilim_assistant.motorlar.programlama_motoru import is_code_agent_task_message
    from ilim_assistant.motorlar.programlama_proje_masasi import tarif_cumlesi

    assert tarif_cumlesi("git ne durumda") is True
    assert tarif_cumlesi("git gönder") is True
    assert is_code_agent_task_message("git ne durumda", "programlama") is False


def test_git_kaydet_yalniz_kapi_notunu_gonderir(masa, tmp_path):
    import shutil
    import subprocess

    repo, el = masa
    _kilitle(repo, el)
    shutil.rmtree(repo / ".git")
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    (repo / "a.txt").write_text("bir\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "a.txt"], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(repo), "-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-m", "ilk"],
        check=True,
        capture_output=True,
    )
    (repo / "a.txt").write_text("iki\n", encoding="utf-8")
    yok = klasor_soz(repo, "git kaydet: kapi notu")
    assert "Kaynak satırı yok" in yok["reply"]
    assert "a.txt" in subprocess.check_output(["git", "-C", str(repo), "status", "--porcelain"], text=True)
    klasor_soz(repo, "kaynak satırı yaz: selam")
    kayit = klasor_soz(repo, "git kaydet: kapi notu")
    assert "Kaydedildi:" in kayit["reply"]
    assert "Göndermedim" in kayit["reply"]
    adlar = subprocess.check_output(
        ["git", "-C", str(repo), "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"],
        text=True,
    ).strip()
    assert adlar == "ilim-assistant/ilim_assistant/kapi_notu.py"
    kalan = subprocess.check_output(["git", "-C", str(repo), "status", "--porcelain"], text=True)
    assert "a.txt" in kalan
    assert "kapi_notu.py" not in kalan
    tekrar = klasor_soz(repo, "git kaydet: kapi notu")
    assert "Kaydetmedim" in tekrar["reply"]
    yerel = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"])
    uzak = tmp_path / "uzak.git"
    subprocess.run(["git", "init", "--bare", str(uzak)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(repo), "remote", "add", "origin", str(uzak)], check=True, capture_output=True)
    gonder = klasor_soz(repo, "git gönder")
    assert "Gönderildi: origin HEAD." in gonder["reply"]
    assert "Zorlamadım" in gonder["reply"]
    dal = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "--abbrev-ref", "HEAD"], text=True).strip()
    alinan = subprocess.check_output(["git", "--git-dir", str(uzak), "rev-parse", "refs/heads/" + dal])
    assert alinan == yerel
    assert subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"]) == yerel


def test_olcu_soyle_okur_yazmaz(masa):
    repo, el = masa
    _kilitle(repo, el)
    yok = klasor_soz(repo, "orta ölçüsünü söyle")
    assert "orta/olcu.py yok." in yok["reply"]
    assert "Yazmadım" in yok["reply"]
    assert "Çalıştırmadım" in yok["reply"]
    assert not (el / "orta" / "olcu.py").exists()
    klasor_soz(repo, "orta iş yap")
    assert not (el / "orta" / "olcu.py").exists()
    klasor_soz(repo, "orta ölçüsü neden kaldı")
    yaz = klasor_soz(repo, "orta ölçüsünü düzelt")
    assert "Yazıldı: orta/olcu.py." in yaz["reply"]
    olcu = el / "orta" / "olcu.py"
    once = olcu.read_bytes()
    soyle = klasor_soz(repo, "orta ölçüsünü söyle")
    assert "kelime_say" in soyle["reply"]
    assert "return len([kelime for kelime in metin.split() if kelime.strip()])" in soyle["reply"]
    assert "Yazmadım" in soyle["reply"]
    assert "Çalıştırmadım" in soyle["reply"]
    assert olcu.read_bytes() == once
    olcu.write_text("import os\n", encoding="utf-8")
    bozuk = olcu.read_bytes()
    fazla = klasor_soz(repo, "orta ölçüsünü söyle hemen")
    assert "Bu cümle söylemez" in fazla["reply"]
    assert olcu.read_bytes() == bozuk
    degil = klasor_soz(repo, "orta ölçüsünü söyle")
    assert "Hazır ölçü değil" in degil["reply"]
    assert olcu.read_bytes() == bozuk
    from ilim_assistant.motorlar.programlama_motoru import is_code_agent_task_message
    from ilim_assistant.motorlar.programlama_proje_masasi import tarif_cumlesi

    assert tarif_cumlesi("orta ölçüsünü söyle") is True
    assert is_code_agent_task_message("orta ölçüsünü söyle", "programlama") is False


def test_olcu_kelime_say_bir_kez_calisir_dosyayi_degistirmez(masa):
    repo, el = masa
    _kilitle(repo, el)
    klasor_soz(repo, "orta ölçüsü neden kaldı")
    klasor_soz(repo, "orta ölçüsünü düzelt")
    olcu = el / "orta" / "olcu.py"
    once = olcu.read_bytes()
    notsuz = klasor_soz(repo, "orta ölçüsünde kelime say")
    assert "orta/not.txt yok." in notsuz["reply"]
    assert "Çalıştırmadım" in notsuz["reply"]
    assert olcu.read_bytes() == once
    klasor_soz(repo, "orta notu yaz: selam ikinci")
    say = klasor_soz(repo, "orta ölçüsünde kelime say")
    assert "Sayı: 2" in say["reply"]
    assert "bir kez çalıştı" in say["reply"]
    assert "Dosya aynı" in say["reply"]
    assert olcu.read_bytes() == once
    assert (el / "orta" / "not.txt").read_text(encoding="utf-8") == "selam ikinci\n"
    verilen = klasor_soz(repo, "orta ölçüsünde kelime say: selam")
    assert "Sayı: 1" in verilen["reply"]
    assert olcu.read_bytes() == once
    olcu.write_text("import os\n", encoding="utf-8")
    bozuk = olcu.read_bytes()
    red = klasor_soz(repo, "orta ölçüsünde kelime say: selam")
    assert "Hazır ölçü değil" in red["reply"]
    assert "Sayı:" not in red["reply"]
    assert olcu.read_bytes() == bozuk
    from ilim_assistant.motorlar.programlama_motoru import is_code_agent_task_message

    assert is_code_agent_task_message("orta ölçüsünde kelime say", "programlama") is False


def test_olcu_neden_ve_duzelt_yalniz_bilinen_satiri_yazar(masa):
    repo, el = masa
    _kilitle(repo, el)
    erken = klasor_soz(repo, "orta ölçüsünü düzelt")
    assert "Ölçü kalmadı" in erken["reply"]
    assert not (el / "orta" / "olcu.py").exists()
    neden = klasor_soz(repo, "orta ölçüsü neden kaldı")
    assert "orta/olcu.py yok." in neden["reply"]
    assert "Kontrol çalışmadı" in neden["reply"]
    assert "Yazmadım" in neden["reply"]
    fazla = klasor_soz(repo, "orta ölçüsünü düzelt: import os")
    assert "Bu cümle yazmaz" in fazla["reply"]
    assert not (el / "orta" / "olcu.py").exists()
    yaz = klasor_soz(repo, "orta ölçüsünü düzelt")
    assert "Yazıldı: orta/olcu.py." in yaz["reply"]
    assert "Çalıştırmadım" in yaz["reply"]
    olcu = el / "orta" / "olcu.py"
    from ilim_assistant.motorlar.programlama_proje_masasi import _OLCU_SABLON

    assert olcu.read_text(encoding="utf-8") == _OLCU_SABLON
    gecti = klasor_soz(repo, "orta ölçüsü neden kaldı")
    assert "Üç kontrol de geçti." in gecti["reply"]
    assert "Düzeltmedim" in gecti["reply"]
    dur = klasor_soz(repo, "orta ölçüsünü düzelt")
    assert "Ölçü geçti" in dur["reply"]
    assert olcu.read_text(encoding="utf-8") == _OLCU_SABLON
    olcu.write_text("import os\n", encoding="utf-8")
    bozuk = olcu.read_bytes()
    kaldi = klasor_soz(repo, "orta ölçüsü neden kaldı")
    assert "Hazır ölçü değil" in kaldi["reply"]
    assert olcu.read_bytes() == bozuk
    geri = klasor_soz(repo, "orta ölçüsünü düzelt")
    assert "Yazıldı: orta/olcu.py." in geri["reply"]
    assert olcu.read_text(encoding="utf-8") == _OLCU_SABLON
    from ilim_assistant.motorlar.programlama_motoru import is_code_agent_task_message

    assert is_code_agent_task_message("orta ölçüsünü düzelt", "programlama") is False
    assert is_code_agent_task_message("orta ölçüsü neden kaldı", "programlama") is False


def test_selam_iceren_olcu_cumlesi_selamlamaz():
    from ilim_assistant.chat_fast_lane import try_instant_reply
    from ilim_assistant.motorlar.programlama_motoru import is_code_agent_task_message
    from ilim_assistant.motorlar.programlama_proje_masasi import tarif_cumlesi

    cumle = "orta ölçüsünde kelime say: selam ikinci"
    assert tarif_cumlesi(cumle) is True
    assert try_instant_reply(cumle, "genel") is None
    assert try_instant_reply("selam", "genel")
    assert "konuşmaya hazırım" in try_instant_reply("selam", "genel")
    assert is_code_agent_task_message(cumle, "programlama") is False


def test_olcu_satiri_yalniz_bilinen_satiri_yazar(masa):
    repo, _el = masa
    _kilitle(repo, _el)
    yol = repo / "ilim-assistant" / "ilim_assistant" / "olcu_notu.py"
    yok = klasor_soz(repo, "ölçü satırını söyle")
    assert "olcu_notu.py yok." in yok["reply"]
    assert "Yazmadım" in yok["reply"]
    assert not yol.exists()
    fazla = klasor_soz(repo, "ölçü satırı yaz hemen")
    assert "Bu cümle yazmaz" in fazla["reply"]
    assert not yol.exists()
    yaz = klasor_soz(repo, "ölçü satırı yaz")
    assert "Yazıldı: ilim-assistant/ilim_assistant/olcu_notu.py." in yaz["reply"]
    assert "return len([kelime for kelime in metin.split() if kelime.strip()])" in yaz["reply"]
    assert "Çalıştırmadım" in yaz["reply"]
    assert "selam" not in yol.read_text(encoding="utf-8")
    duran = yol.read_bytes()
    ikinci = klasor_soz(repo, "ölçü satırı yaz")
    assert "Üstüne yazmadım" in ikinci["reply"]
    assert yol.read_bytes() == duran
    soyle = klasor_soz(repo, "ölçü satırını söyle")
    assert "Ölçü satırı okundu." in soyle["reply"]
    assert yol.read_bytes() == duran
    from ilim_assistant.motorlar.programlama_motoru import is_code_agent_task_message

    assert is_code_agent_task_message("ölçü satırı yaz", "programlama") is False
    assert is_code_agent_task_message("ölçü satırını söyle", "programlama") is False


def test_dis_olcu_yalniz_olcu_txt_okur(masa, tmp_path):
    repo, el = masa
    _kilitle(repo, el)
    yok = klasor_soz(repo, "dış ölçü dosyasını oku")
    assert "Dış klasör seçilmedi" in yok["reply"]
    dis = tmp_path / "dis-olcu"
    dis.mkdir()
    olcu = dis / "olcu.txt"
    olcu.write_text("iki kelime\n", encoding="utf-8")
    (dis / "not.txt").write_text("baska\n", encoding="utf-8")
    once = olcu.read_bytes()
    klasor_soz(repo, f"dış klasör: {dis}")
    fazla = klasor_soz(repo, "dış ölçü dosyasını oku: not.txt")
    assert "Bu cümle okumaz" in fazla["reply"]
    assert (dis / "not.txt").read_text(encoding="utf-8") == "baska\n"
    okunan = klasor_soz(repo, "dış ölçü dosyasını oku")
    assert "olcu.txt okundu." in okunan["reply"]
    assert "iki kelime" in okunan["reply"]
    assert "Yazmadım" in okunan["reply"]
    assert olcu.read_bytes() == once
    olcu.unlink()
    bos = klasor_soz(repo, "dış ölçü dosyasını oku")
    assert "Dosya yok" in bos["reply"]
    assert not olcu.exists()
    from ilim_assistant.motorlar.programlama_motoru import is_code_agent_task_message

    assert is_code_agent_task_message("dış ölçü dosyasını oku", "programlama") is False


def test_dis_olcu_klasorse_dosya_degil_der(masa, tmp_path):
    repo, el = masa
    _kilitle(repo, el)
    dis = tmp_path / "dis-olcu-klasor"
    dis.mkdir()
    klasor = dis / "olcu.txt"
    klasor.mkdir()
    (klasor / "gizli.txt").write_text("ic\n", encoding="utf-8")
    klasor_soz(repo, f"dış klasör: {dis}")
    okunan = klasor_soz(repo, "dış ölçü dosyasını oku")
    assert "dosya değil" in okunan["reply"]
    assert "gizli" not in okunan["reply"]
    assert "ic" not in okunan["reply"]
    assert klasor.is_dir()
    assert (klasor / "gizli.txt").read_text(encoding="utf-8") == "ic\n"


def test_git_farkini_soyler_yazmaz(masa):
    import shutil
    import subprocess

    repo, el = masa
    _kilitle(repo, el)
    shutil.rmtree(repo / ".git")
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    (repo / "a.txt").write_text("bir\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "a.txt"], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(repo), "-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-m", "ilk"],
        check=True,
        capture_output=True,
    )
    bas = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"])
    yok = klasor_soz(repo, "git farkını söyle")
    assert "kapi_notu.py yok." in yok["reply"]
    assert "Fark yok." not in yok["reply"]
    assert "Göndermedim" in yok["reply"]
    assert not (repo / "ilim-assistant" / "ilim_assistant" / "kapi_notu.py").exists()
    fazla = klasor_soz(repo, "git farkını söyle hemen")
    assert "Bu cümle söylemez" in fazla["reply"]
    klasor_soz(repo, "kaynak satırı yaz: selam")
    izlenen = klasor_soz(repo, "git farkını söyle")
    assert "İzlenmeyen dosya." in izlenen["reply"]
    assert 'SATIR = "selam"' in izlenen["reply"]
    assert subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"]) == bas
    subprocess.run(["git", "-C", str(repo), "add", "--", "ilim-assistant/ilim_assistant/kapi_notu.py"], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(repo), "-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-m", "not"],
        check=True,
        capture_output=True,
    )
    bas = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"])
    notu = repo / "ilim-assistant" / "ilim_assistant" / "kapi_notu.py"
    notu.write_text(notu.read_text(encoding="utf-8").replace("selam", "ikinci"), encoding="utf-8")
    fark = klasor_soz(repo, "git farkını söyle")
    assert "Fark: ilim-assistant/ilim_assistant/kapi_notu.py" in fark["reply"]
    assert "ikinci" in fark["reply"]
    assert "Göndermedim" in fark["reply"]
    assert subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"]) == bas
    from ilim_assistant.motorlar.programlama_motoru import is_code_agent_task_message

    assert is_code_agent_task_message("git farkını söyle", "programlama") is False


def test_olcu_bak_bir_kez_bakar_ucuncuye_gecmez(masa):
    repo, el = masa
    _kilitle(repo, el)
    erken = klasor_soz(repo, "orta ölçüsüne bak")
    assert "Düzeltme yok" in erken["reply"]
    assert "Bakmadım" in erken["reply"]
    assert not (el / "orta" / "olcu.py").exists()
    klasor_soz(repo, "orta ölçüsü neden kaldı")
    klasor_soz(repo, "orta ölçüsünü düzelt")
    olcu = el / "orta" / "olcu.py"
    once = olcu.read_bytes()
    fazla = klasor_soz(repo, "orta ölçüsüne bak hemen")
    assert "Bu cümle bakmaz" in fazla["reply"]
    assert olcu.read_bytes() == once
    bak = klasor_soz(repo, "orta ölçüsüne bak")
    assert "Üç kontrol de geçti." in bak["reply"]
    assert "Düzeltmedim" in bak["reply"]
    assert olcu.read_bytes() == once
    ikinci = klasor_soz(repo, "orta ölçüsüne bak")
    assert "Üçüncüye geçmedim" in ikinci["reply"]
    assert olcu.read_bytes() == once
    olcu.write_text("import os\n", encoding="utf-8")
    bozuk = olcu.read_bytes()
    klasor_soz(repo, "orta ölçüsü neden kaldı")
    klasor_soz(repo, "orta ölçüsünü düzelt")
    assert olcu.read_bytes() != bozuk
    olcu.write_text("import os\n", encoding="utf-8")
    duran = olcu.read_bytes()
    kaldi = klasor_soz(repo, "orta ölçüsüne bak")
    assert "Hazır ölçü değil" in kaldi["reply"]
    assert "Düzeltmedim" in kaldi["reply"] or "Dosya aynı" in kaldi["reply"]
    assert olcu.read_bytes() == duran
    from ilim_assistant.motorlar.programlama_motoru import is_code_agent_task_message

    assert is_code_agent_task_message("orta ölçüsüne bak", "programlama") is False


def test_olcu_kapat_tek_acik_satiri_bitti_yapar(masa):
    repo, el = masa
    _kilitle(repo, el)
    tahta = repo / "RUZGAR_SIRA.md"
    tahta.write_text("| 1 | açık iş | bekliyor | test |\n", encoding="utf-8")
    once_tahta = tahta.read_bytes()
    erken = klasor_soz(repo, "orta ölçüsünü kapat")
    assert "Bakış geçmedi" in erken["reply"]
    assert "Tahtaya yazmadım" in erken["reply"]
    assert tahta.read_bytes() == once_tahta
    klasor_soz(repo, "orta ölçüsü neden kaldı")
    klasor_soz(repo, "orta ölçüsünü düzelt")
    olcu = el / "orta" / "olcu.py"
    once = olcu.read_bytes()
    ara = klasor_soz(repo, "orta ölçüsünü kapat")
    assert "Bakış geçmedi" in ara["reply"]
    assert tahta.read_bytes() == once_tahta
    assert olcu.read_bytes() == once
    klasor_soz(repo, "orta ölçüsüne bak")
    fazla = klasor_soz(repo, "orta ölçüsünü kapat hemen")
    assert "Bu cümle kapatmaz" in fazla["reply"]
    assert tahta.read_bytes() == once_tahta
    tahta.write_text(
        "| 1 | açık iş | bekliyor | test |\n| 2 | ikinci | bekliyor | test |\n",
        encoding="utf-8",
    )
    cok = tahta.read_bytes()
    coklu = klasor_soz(repo, "orta ölçüsünü kapat")
    assert "Ölçü kapandı." in coklu["reply"]
    assert "Birden fazla açık satır" in coklu["reply"]
    assert tahta.read_bytes() == cok
    assert olcu.read_bytes() == once
    tahta.write_text("| 1 | açık iş | bekliyor | test |\n", encoding="utf-8")
    kapat = klasor_soz(repo, "orta ölçüsünü kapat")
    assert "Ölçü kapandı." in kapat["reply"]
    assert "Açık satır bitti oldu." in kapat["reply"]
    assert "Satır eklenmedi" in kapat["reply"]
    assert "bitti" in tahta.read_text(encoding="utf-8")
    assert "açık iş" in tahta.read_text(encoding="utf-8")
    assert olcu.read_bytes() == once
    duran = tahta.read_bytes()
    tekrar = klasor_soz(repo, "orta ölçüsünü kapat")
    assert "Açık satır yok" in tekrar["reply"]
    assert tahta.read_bytes() == duran
    from ilim_assistant.motorlar.programlama_motoru import is_code_agent_task_message

    assert is_code_agent_task_message("orta ölçüsünü kapat", "programlama") is False


def test_olcu_sirasi_soyler_yazmaz(masa):
    repo, el = masa
    _kilitle(repo, el)
    tahta = repo / "RUZGAR_SIRA.md"
    tahta.write_text("| 1 | açık iş | bekliyor | test |\n", encoding="utf-8")
    once_tahta = tahta.read_bytes()
    yok = klasor_soz(repo, "orta ölçü sırasını söyle")
    assert "Sıra: orta ölçüsü neden kaldı" in yok["reply"]
    assert "Şimdi: ölçü yok." in yok["reply"]
    assert "Yazmadım" in yok["reply"]
    assert not (el / "orta" / "olcu.py").exists()
    assert tahta.read_bytes() == once_tahta
    fazla = klasor_soz(repo, "orta ölçü sırasını söyle hemen")
    assert "Bu cümle söylemez" in fazla["reply"]
    klasor_soz(repo, "orta ölçüsü neden kaldı")
    klasor_soz(repo, "orta ölçüsünü düzelt")
    olcu = el / "orta" / "olcu.py"
    once = olcu.read_bytes()
    durum = repo / "ilim-assistant" / ".ruzgar" / "olcu_tur.txt"
    once_durum = durum.read_bytes()
    duz = klasor_soz(repo, "orta ölçü sırasını söyle")
    assert "Şimdi: düzeltildi, bakış yok." in duz["reply"]
    assert olcu.read_bytes() == once
    assert durum.read_bytes() == once_durum
    assert tahta.read_bytes() == once_tahta
    klasor_soz(repo, "orta ölçüsüne bak")
    klasor_soz(repo, "orta ölçüsünü kapat")
    once = olcu.read_bytes()
    once_durum = durum.read_bytes()
    once_tahta = tahta.read_bytes()
    assert b"bitti" in once_tahta
    kapali = klasor_soz(repo, "orta ölçü sırasını söyle")
    assert "Şimdi: ölçü kapandı." in kapali["reply"]
    assert "Tahtaya yazmadım" in kapali["reply"]
    assert olcu.read_bytes() == once
    assert durum.read_bytes() == once_durum
    assert tahta.read_bytes() == once_tahta
    from ilim_assistant.motorlar.programlama_motoru import is_code_agent_task_message

    assert is_code_agent_task_message("orta ölçü sırasını söyle", "programlama") is False


def test_dis_olcu_yaz_yalniz_bilinen_satiri_bir_kez_yazar(masa, tmp_path):
    repo, el = masa
    _kilitle(repo, el)
    yok = klasor_soz(repo, "dış ölçü dosyasına yaz")
    assert "Dış klasör seçilmedi" in yok["reply"]
    dis = tmp_path / "dis-olcu-yaz"
    dis.mkdir()
    (dis / "not.txt").write_text("baska\n", encoding="utf-8")
    klasor_soz(repo, f"dış klasör: {dis}")
    fazla = klasor_soz(repo, "dış ölçü dosyasına yaz: selam")
    assert "Bu cümle yazmaz" in fazla["reply"]
    assert not (dis / "olcu.txt").exists()
    assert (dis / "not.txt").read_text(encoding="utf-8") == "baska\n"
    (dis / "olcu.txt").write_text("eski\n", encoding="utf-8")
    duran_eski = (dis / "olcu.txt").read_bytes()
    eski = klasor_soz(repo, "dış ölçü dosyasına yaz")
    assert "Üstüne yazmadım" in eski["reply"]
    assert (dis / "olcu.txt").read_bytes() == duran_eski
    (dis / "olcu.txt").unlink()
    yaz = klasor_soz(repo, "dış ölçü dosyasına yaz")
    assert "Yazıldı: olcu.txt." in yaz["reply"]
    assert "return len([kelime for kelime in metin.split() if kelime.strip()])" in yaz["reply"]
    assert "Çalıştırmadım" in yaz["reply"]
    olcu = dis / "olcu.txt"
    assert olcu.read_text(encoding="utf-8") == "return len([kelime for kelime in metin.split() if kelime.strip()])\n"
    assert "selam" not in olcu.read_text(encoding="utf-8")
    duran = olcu.read_bytes()
    ikinci = klasor_soz(repo, "dış ölçü dosyasına yaz")
    assert "Üstüne yazmadım" in ikinci["reply"]
    assert olcu.read_bytes() == duran
    assert (dis / "not.txt").read_text(encoding="utf-8") == "baska\n"
    from ilim_assistant.motorlar.programlama_motoru import is_code_agent_task_message

    assert is_code_agent_task_message("dış ölçü dosyasına yaz", "programlama") is False


def test_dis_olcu_yaz_klasorse_dosya_degil_der(masa, tmp_path):
    repo, el = masa
    _kilitle(repo, el)
    dis = tmp_path / "dis-olcu-yaz-klasor"
    dis.mkdir()
    klasor = dis / "olcu.txt"
    klasor.mkdir()
    (klasor / "gizli.txt").write_text("ic\n", encoding="utf-8")
    klasor_soz(repo, f"dış klasör: {dis}")
    yaz = klasor_soz(repo, "dış ölçü dosyasına yaz")
    assert "dosya değil" in yaz["reply"]
    assert "gizli" not in yaz["reply"]
    assert klasor.is_dir()
    assert (klasor / "gizli.txt").read_text(encoding="utf-8") == "ic\n"
    assert not (dis / "olcu.txt").is_file()


def test_git_olcu_farkini_soyler_yazmaz(masa):
    import shutil
    import subprocess

    repo, el = masa
    _kilitle(repo, el)
    shutil.rmtree(repo / ".git")
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    (repo / "a.txt").write_text("bir\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "a.txt"], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(repo), "-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-m", "ilk"],
        check=True,
        capture_output=True,
    )
    bas = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"])
    yok = klasor_soz(repo, "git ölçü farkını söyle")
    assert "olcu_notu.py yok." in yok["reply"]
    assert "Fark yok." not in yok["reply"]
    assert "Göndermedim" in yok["reply"]
    assert not (repo / "ilim-assistant" / "ilim_assistant" / "olcu_notu.py").exists()
    fazla = klasor_soz(repo, "git ölçü farkını söyle hemen")
    assert "Bu cümle söylemez" in fazla["reply"]
    klasor_soz(repo, "kaynak satırı yaz: selam")
    klasor_soz(repo, "ölçü satırı yaz")
    izlenen = klasor_soz(repo, "git ölçü farkını söyle")
    assert "İzlenmeyen dosya." in izlenen["reply"]
    assert "kelime for kelime in metin.split()" in izlenen["reply"]
    assert "kapi_notu.py" not in izlenen["reply"]
    assert "selam" not in izlenen["reply"]
    assert subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"]) == bas
    subprocess.run(
        ["git", "-C", str(repo), "add", "--", "ilim-assistant/ilim_assistant/olcu_notu.py"],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(repo), "-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-m", "olcu"],
        check=True,
        capture_output=True,
    )
    bas = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"])
    notu = repo / "ilim-assistant" / "ilim_assistant" / "olcu_notu.py"
    notu.write_text(notu.read_text(encoding="utf-8").replace("kelime", "sozcuk"), encoding="utf-8")
    fark = klasor_soz(repo, "git ölçü farkını söyle")
    assert "Fark: ilim-assistant/ilim_assistant/olcu_notu.py" in fark["reply"]
    assert "sozcuk" in fark["reply"]
    assert "Göndermedim" in fark["reply"]
    kapi = klasor_soz(repo, "git farkını söyle")
    assert "İzlenmeyen dosya." in kapi["reply"]
    assert "selam" in kapi["reply"]
    assert "sozcuk" not in kapi["reply"]
    assert subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"]) == bas
    from ilim_assistant.motorlar.programlama_motoru import is_code_agent_task_message

    assert is_code_agent_task_message("git ölçü farkını söyle", "programlama") is False


def test_kaynak_satirini_soyler_yoksa_yazmaz(masa):
    repo, _el = masa
    _kilitle(repo, _el)
    yol = repo / "ilim-assistant" / "ilim_assistant" / "kapi_notu.py"
    yok = klasor_soz(repo, "kaynak satırını söyle")
    assert "kapi_notu.py yok." in yok["reply"]
    assert "Yazmadım" in yok["reply"]
    assert not yol.exists()
    fazla = klasor_soz(repo, "kaynak satırını söyle hemen")
    assert "Bu cümle söylemez" in fazla["reply"]
    assert not yol.exists()
    klasor_soz(repo, "kaynak satırı yaz: selam")
    once = yol.read_bytes()
    soyle = klasor_soz(repo, "kaynak satırını söyle")
    assert "Kaynak satırı okundu." in soyle["reply"]
    assert "selam" in soyle["reply"]
    assert "Yazmadım" in soyle["reply"]
    assert yol.read_bytes() == once
    from ilim_assistant.motorlar.programlama_motoru import is_code_agent_task_message

    assert is_code_agent_task_message("kaynak satırını söyle", "programlama") is False


def test_olcu_satiri_kullanici_satirini_yemez(masa):
    repo, el = masa
    _kilitle(repo, el)
    yol = repo / "ilim-assistant" / "ilim_assistant" / "olcu_notu.py"
    yaz = klasor_soz(repo, "ölçü satırı yaz: selam")
    assert "Bu cümle yazmaz" in yaz["reply"]
    assert "return len([kelime for kelime in metin.split() if kelime.strip()])" in yaz["reply"]
    assert not yol.exists()
    assert not (el / "olcu_notu.py").exists()
    from ilim_assistant.motorlar.programlama_motoru import is_code_agent_task_message

    assert is_code_agent_task_message("ölçü satırı yaz: selam", "programlama") is False


def test_hazir_olcu_duzelt_kalmadi_demez(masa):
    repo, el = masa
    _kilitle(repo, el)
    from ilim_assistant.motorlar.programlama_proje_masasi import _OLCU_SABLON

    olcu = el / "orta" / "olcu.py"
    olcu.parent.mkdir()
    olcu.write_text(_OLCU_SABLON, encoding="utf-8")
    durum = repo / "ilim-assistant" / ".ruzgar" / "olcu_tur.txt"
    durum.parent.mkdir(parents=True)
    durum.write_text(
        "kaldi=0\ndurdu=0\nduzeltme=0\nbakis=1\ngecti=0\nkapandi=0\n",
        encoding="utf-8",
    )
    once = olcu.read_bytes()
    duzelt = klasor_soz(repo, "orta ölçüsünü düzelt")
    assert "Bilinen satır duruyor" in duzelt["reply"]
    assert "Ölçü kalmadı" not in duzelt["reply"]
    assert "Üstüne yazmadım" in duzelt["reply"]
    assert olcu.read_bytes() == once
    govde = durum.read_text(encoding="utf-8")
    assert "duzeltme=1" in govde
    assert "bakis=1" in govde
    assert "kapandi=0" in govde


def test_eski_gecti_bayragi_bozuk_olcuyu_gizlemez(masa):
    repo, el = masa
    _kilitle(repo, el)
    olcu = el / "orta" / "olcu.py"
    olcu.parent.mkdir()
    olcu.write_text("import os\n", encoding="utf-8")
    durum = repo / "ilim-assistant" / ".ruzgar" / "olcu_tur.txt"
    durum.parent.mkdir(parents=True)
    durum.write_text(
        "kaldi=0\ndurdu=1\nduzeltme=1\nbakis=1\ngecti=1\nkapandi=0\n",
        encoding="utf-8",
    )
    once = olcu.read_bytes()
    duzelt = klasor_soz(repo, "orta ölçüsünü düzelt")
    assert "Hazır ölçü değil" in duzelt["reply"]
    assert "Yazmadım" in duzelt["reply"]
    assert "Ölçü geçti" not in duzelt["reply"]
    assert olcu.read_bytes() == once


def test_olcu_neden_gectiyse_bakis_silinmez(masa):
    repo, el = masa
    _kilitle(repo, el)
    from ilim_assistant.motorlar.programlama_proje_masasi import _OLCU_SABLON

    olcu = el / "orta" / "olcu.py"
    olcu.parent.mkdir()
    olcu.write_text(_OLCU_SABLON, encoding="utf-8")
    durum = repo / "ilim-assistant" / ".ruzgar" / "olcu_tur.txt"
    durum.parent.mkdir(parents=True)
    durum.write_text(
        "kaldi=0\ndurdu=0\nduzeltme=1\nbakis=1\ngecti=1\nkapandi=0\n",
        encoding="utf-8",
    )
    once = olcu.read_bytes()
    neden = klasor_soz(repo, "orta ölçüsü neden kaldı")
    assert "Üç kontrol de geçti." in neden["reply"]
    assert "kaldı" not in neden["reply"].split(".", 1)[0]
    assert olcu.read_bytes() == once
    govde = durum.read_text(encoding="utf-8")
    assert "duzeltme=1" in govde
    assert "bakis=1" in govde
    assert "gecti=1" in govde
    assert "kapandi=0" in govde
    assert "durdu=1" in govde


def test_hazir_olcu_sira_yok_demez_bakis_bakar(masa):
    repo, el = masa
    _kilitle(repo, el)
    from ilim_assistant.motorlar.programlama_proje_masasi import _OLCU_SABLON

    olcu = el / "orta" / "olcu.py"
    olcu.parent.mkdir()
    olcu.write_text(_OLCU_SABLON, encoding="utf-8")
    (repo / "ilim-assistant" / ".ruzgar").mkdir()
    (repo / "ilim-assistant" / ".ruzgar" / "olcu_tur.txt").write_text("kaldi=0\ndurdu=0\n", encoding="utf-8")
    once = olcu.read_bytes()
    soyle = klasor_soz(repo, "orta ölçü sırasını söyle")
    assert "dosya hazır, bakış yok." in soyle["reply"]
    assert "ölçü yok" not in soyle["reply"]
    assert olcu.read_bytes() == once
    bak = klasor_soz(repo, "orta ölçüsüne bak")
    assert "Üç kontrol de geçti." in bak["reply"]
    assert olcu.read_bytes() == once
    kapat = klasor_soz(repo, "orta ölçüsünü kapat")
    assert "Ölçü kapandı." in kapat["reply"]
    assert olcu.read_bytes() == once


def test_hazir_olcuda_bes_cumle_ayni_hikayeyi_soyler(masa):
    repo, el = masa
    _kilitle(repo, el)
    from ilim_assistant.motorlar.programlama_proje_masasi import _OLCU_SABLON

    olcu = el / "orta" / "olcu.py"
    olcu.parent.mkdir()
    olcu.write_text(_OLCU_SABLON, encoding="utf-8")
    durum = repo / "ilim-assistant" / ".ruzgar" / "olcu_tur.txt"
    durum.parent.mkdir(parents=True)
    durum.write_text("kaldi=0\ndurdu=0\n", encoding="utf-8")
    once = olcu.read_bytes()
    soyle = klasor_soz(repo, "orta ölçü sırasını söyle")
    duzelt = klasor_soz(repo, "orta ölçüsünü düzelt")
    neden = klasor_soz(repo, "orta ölçüsü neden kaldı")
    bak = klasor_soz(repo, "orta ölçüsüne bak")
    kapat = klasor_soz(repo, "orta ölçüsünü kapat")
    sonra = klasor_soz(repo, "orta ölçü sırasını söyle")
    assert "dosya hazır, bakış yok." in soyle["reply"]
    assert "Bilinen satır duruyor" in duzelt["reply"]
    assert "Üç kontrol de geçti." in neden["reply"]
    assert "Üç kontrol de geçti." in bak["reply"]
    assert "Ölçü kapandı." in kapat["reply"]
    assert "ölçü kapandı." in sonra["reply"]
    for cevap in (soyle, duzelt, neden, bak, kapat, sonra):
        assert "ölçü yok" not in cevap["reply"]
        assert "Ölçü kalmadı" not in cevap["reply"]
        assert "Düzeltme yok" not in cevap["reply"]
        assert "Bakış geçmedi" not in cevap["reply"]
    assert olcu.read_bytes() == once
    govde = durum.read_text(encoding="utf-8")
    assert "duzeltme=1" in govde
    assert "bakis=1" in govde
    assert "gecti=1" in govde
    assert "kapandi=1" in govde


def test_uygulama_notuna_satir_ekler_ustune_yazmaz(masa):
    repo, _el = masa
    _kilitle(repo, _el)
    yol = repo / "ilim-assistant" / ".ruzgar" / "uygulama_notu.txt"
    kapi = repo / "ilim-assistant" / "ilim_assistant" / "kapi_notu.py"
    yok = klasor_soz(repo, "uygulama notuna satır ekle: ikinci")
    assert "Not yok" in yok["reply"]
    assert not yol.exists()
    klasor_soz(repo, "uygulama notu yaz: selam")
    fazla = klasor_soz(repo, "uygulama notuna satır ekle hemen")
    assert "Bu cümle eklemez" in fazla["reply"]
    assert yol.read_text(encoding="utf-8") == "selam\n"
    ekle = klasor_soz(repo, "uygulama notuna satır ekle: ikinci")
    assert "Satır eklendi" in ekle["reply"]
    assert yol.read_text(encoding="utf-8") == "selam\nikinci\n"
    ayni = klasor_soz(repo, "uygulama notuna satır ekle: selam")
    assert "Bu satır duruyor" in ayni["reply"]
    assert yol.read_text(encoding="utf-8") == "selam\nikinci\n"
    for n in range(6):
        klasor_soz(repo, "uygulama notuna satır ekle: satir " + str(n))
    dolu = klasor_soz(repo, "uygulama notuna satır ekle: fazla")
    assert "Not doldu" in dolu["reply"]
    assert "fazla" not in yol.read_text(encoding="utf-8")
    assert yol.read_text(encoding="utf-8").startswith("selam\nikinci\n")
    assert not kapi.exists()
    from ilim_assistant.motorlar.programlama_motoru import is_code_agent_task_message

    assert is_code_agent_task_message("uygulama notuna satır ekle: ikinci", "programlama") is False


def test_olcu_testi_sonucu_soyler_duzeltmez(masa):
    repo, el = masa
    _kilitle(repo, el)
    durum = repo / "ilim-assistant" / ".ruzgar" / "olcu_tur.txt"
    yok = klasor_soz(repo, "orta ölçüsünü çalıştır")
    assert "orta/olcu.py yok." in yok["reply"]
    assert "Çalıştırmadım" in yok["reply"]
    assert not (el / "orta" / "olcu.py").exists()
    assert not durum.exists()
    klasor_soz(repo, "orta ölçüsü neden kaldı")
    klasor_soz(repo, "orta ölçüsünü düzelt")
    olcu = el / "orta" / "olcu.py"
    once = olcu.read_bytes()
    once_durum = durum.read_bytes()
    fazla = klasor_soz(repo, "orta ölçüsünü çalıştır hemen")
    assert "Bu cümle çalıştırmaz" in fazla["reply"]
    assert olcu.read_bytes() == once
    assert durum.read_bytes() == once_durum
    gecti = klasor_soz(repo, "orta ölçüsünü çalıştır")
    assert "Test geçti." in gecti["reply"]
    assert "Düzeltmedim" in gecti["reply"]
    assert olcu.read_bytes() == once
    assert durum.read_bytes() == once_durum
    olcu.write_text("import os\n", encoding="utf-8")
    bozuk = olcu.read_bytes()
    kaldi = klasor_soz(repo, "orta ölçüsünü çalıştır")
    assert "Hazır ölçü değil" in kaldi["reply"]
    assert "Düzeltmedim" in kaldi["reply"]
    assert olcu.read_bytes() == bozuk
    dur = klasor_soz(repo, "orta ölçüsünü düzelt")
    assert "Ölçü geçti" in dur["reply"] or "Ölçü kalmadı" in dur["reply"]
    assert olcu.read_bytes() == bozuk
    from ilim_assistant.motorlar.programlama_motoru import is_code_agent_task_message

    assert is_code_agent_task_message("orta ölçüsünü çalıştır", "programlama") is False


def test_dis_olcu_yerini_soyler_icini_acmaz(masa, tmp_path):
    repo, el = masa
    _kilitle(repo, el)
    yok = klasor_soz(repo, "dış ölçü yerini söyle")
    assert "seçilmedi" in yok["reply"]
    dis = tmp_path / "yer"
    dis.mkdir()
    gizli = dis / "gizli.txt"
    gizli.write_text("sır\n", encoding="utf-8")
    klasor_soz(repo, f"dış klasör: {dis}")
    bos = klasor_soz(repo, "dış ölçü yerini söyle")
    assert "olcu.txt yok." in bos["reply"]
    assert "sır" not in bos["reply"]
    klasor = dis / "olcu.txt"
    klasor.mkdir()
    (klasor / "ic.txt").write_text("gizli\n", encoding="utf-8")
    klasor_cevap = klasor_soz(repo, "dış ölçü yerini söyle")
    assert "olcu.txt klasör." in klasor_cevap["reply"]
    assert "gizli" not in klasor_cevap["reply"]
    klasor.rmdir() if not any(klasor.iterdir()) else None
    import shutil
    shutil.rmtree(klasor)
    dosya = dis / "olcu.txt"
    dosya.write_text("iki kelime\n", encoding="utf-8")
    once = dosya.read_bytes()
    dosya_cevap = klasor_soz(repo, "dış ölçü yerini söyle")
    assert "olcu.txt dosya." in dosya_cevap["reply"]
    assert "iki kelime" not in dosya_cevap["reply"]
    assert dosya.read_bytes() == once


def test_uygulama_notunun_satirini_soyler_yazmaz(masa):
    repo, _el = masa
    _kilitle(repo, _el)
    yol = repo / "ilim-assistant" / ".ruzgar" / "uygulama_notu.txt"
    yok = klasor_soz(repo, "uygulama notunun satırını söyle")
    assert "Not yok." in yok["reply"]
    assert not yol.exists()
    klasor_soz(repo, "uygulama notu yaz: selam")
    once = yol.read_bytes()
    say = klasor_soz(repo, "uygulama notunun satırını söyle")
    assert "Satır: 1" in say["reply"]
    assert yol.read_bytes() == once


def test_olcu_kaydini_soyler_yazmaz(masa):
    repo, el = masa
    _kilitle(repo, el)
    yol = repo / "ilim-assistant" / ".ruzgar" / "olcu_tur.txt"
    yok = klasor_soz(repo, "orta ölçü kaydını söyle")
    assert "Kayıt dosyası yok." in yok["reply"]
    assert "kaldi=0" in yok["reply"]
    assert not yol.exists()
    yol.parent.mkdir(parents=True)
    yol.write_text("kaldi=0\ndurdu=1\nduzeltme=1\nbakis=0\ngecti=0\nkapandi=0\n", encoding="utf-8")
    once = yol.read_bytes()
    soyle = klasor_soz(repo, "orta ölçü kaydını söyle")
    assert "durdu=1" in soyle["reply"]
    assert "duzeltme=1" in soyle["reply"]
    assert "Kayıt dosyası yok." not in soyle["reply"]
    assert yol.read_bytes() == once


def test_arac_kaydini_soyler_yazmaz(masa):
    repo, el = masa
    _kilitle(repo, el)
    yol = repo / "ilim-assistant" / ".ruzgar" / "orta_tur.txt"
    yok = klasor_soz(repo, "orta araç kaydını söyle")
    assert "Kayıt dosyası yok." in yok["reply"]
    assert not yol.exists()
    yol.parent.mkdir(parents=True)
    yol.write_text("duzeltme=1\nbakis=0\ngecti=0\ndurdu=0\nkaldi=0\ntur=1\n", encoding="utf-8")
    once = yol.read_bytes()
    soyle = klasor_soz(repo, "orta araç kaydını söyle")
    assert "duzeltme=1" in soyle["reply"]
    assert "tur=1" in soyle["reply"]
    assert yol.read_bytes() == once


def test_git_son_kaydi_soyler_gonderemez(masa):
    import shutil
    import subprocess

    repo, el = masa
    _kilitle(repo, el)
    shutil.rmtree(repo / ".git")
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    bos = klasor_soz(repo, "git son kaydı söyle")
    assert "Kayıt yok." in bos["reply"] or "Bu depo değil." in bos["reply"]
    (repo / "a.txt").write_text("bir\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "a.txt"], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(repo), "-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-m", "ilk kapi"],
        check=True,
        capture_output=True,
    )
    bas = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"])
    soyle = klasor_soz(repo, "git son kaydı söyle")
    assert "Son kayıt:" in soyle["reply"]
    assert "ilk kapi" in soyle["reply"]
    assert "Göndermedim" in soyle["reply"]
    assert subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"]) == bas


def test_kilitli_klasoru_soyler_listelemez(masa):
    repo, el = masa
    _kilitle(repo, el)
    (el / "gizli.txt").write_text("sır\n", encoding="utf-8")
    soyle = klasor_soz(repo, "kilitli klasörü söyle")
    assert "Kilitli klasör:" in soyle["reply"]
    assert str(el) in soyle["reply"] or el.name in soyle["reply"]
    assert "gizli.txt" not in soyle["reply"]
    assert "sır" not in soyle["reply"]


def test_dis_klasoru_soyler_listelemez(masa, tmp_path):
    repo, el = masa
    _kilitle(repo, el)
    dis = tmp_path / "dis-ad"
    dis.mkdir()
    (dis / "gizli.txt").write_text("sır\n", encoding="utf-8")
    klasor_soz(repo, f"dış klasör: {dis}")
    soyle = klasor_soz(repo, "dış klasörü söyle")
    assert "Dış klasör:" in soyle["reply"]
    assert str(dis) in soyle["reply"] or dis.name in soyle["reply"]
    assert "gizli.txt" not in soyle["reply"]
    assert "sır" not in soyle["reply"]


def test_acik_satir_sayisini_soyler_yazmaz(masa):
    repo, el = masa
    _kilitle(repo, el)
    tahta = repo / "RUZGAR_SIRA.md"
    govde = "| 1 | Eski | bitti | a |\n| 2 | Açık | bekliyor | b |\n"
    tahta.write_text(govde, encoding="utf-8")
    soyle = klasor_soz(repo, "açık satır sayısını söyle")
    assert "Açık satır: 1" in soyle["reply"]
    assert "Tahtaya yazmadım" in soyle["reply"]
    assert tahta.read_text(encoding="utf-8") == govde


def test_orta_aracini_soyler_yazmaz(masa):
    repo, el = masa
    _kilitle(repo, el)
    from ilim_assistant.motorlar.programlama_proje_masasi import _ORTA_DOSYA

    arac = el / "orta" / "arac.py"
    yok = klasor_soz(repo, "orta aracını söyle")
    assert "orta/arac.py yok." in yok["reply"]
    assert not arac.exists()
    arac.parent.mkdir()
    arac.write_text(_ORTA_DOSYA["orta/arac.py"], encoding="utf-8")
    once = arac.read_bytes()
    soyle = klasor_soz(repo, "orta aracını söyle")
    assert "satir_say" in soyle["reply"]
    assert "Yazmadım" in soyle["reply"]
    assert arac.read_bytes() == once


def test_okuyan_on_cumle_dosyaya_yazmaz(masa, tmp_path):
    repo, el = masa
    _kilitle(repo, el)
    dis = tmp_path / "on"
    dis.mkdir()
    klasor_soz(repo, f"dış klasör: {dis}")
    tahta = repo / "RUZGAR_SIRA.md"
    tahta.write_text("| 1 | Açık | bekliyor | a |\n", encoding="utf-8")
    once_tahta = tahta.read_bytes()
    cumleler = [
        "dış ölçü yerini söyle",
        "uygulama notunun satırını söyle",
        "orta ölçü kaydını söyle",
        "orta araç kaydını söyle",
        "kilitli klasörü söyle",
        "dış klasörü söyle",
        "açık satır sayısını söyle",
        "orta aracını söyle",
    ]
    for cumle in cumleler:
        klasor_soz(repo, cumle)
    assert tahta.read_bytes() == once_tahta
    assert not (repo / "ilim-assistant" / ".ruzgar" / "uygulama_notu.txt").exists()
    assert not (repo / "ilim-assistant" / ".ruzgar" / "olcu_tur.txt").exists()
    assert not (repo / "ilim-assistant" / ".ruzgar" / "orta_tur.txt").exists()
    assert not (el / "orta" / "arac.py").exists()
    assert not (dis / "olcu.txt").exists()

