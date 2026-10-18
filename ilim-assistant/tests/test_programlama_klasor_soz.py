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
