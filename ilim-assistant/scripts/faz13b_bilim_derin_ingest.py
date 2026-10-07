# -*- coding: utf-8 -*-
"""Bilim derinleştirme (Faz 13b) — astronomi/fizik-kimya/biyoloji/matematik.

İnce özetleri genişletir. Tıbbi teşhis yok. Tehlikeli deney protokolü yok.
Uydurma kesin rakam yok (mertebe/eğitim).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "knowledge" / "ortak_kaynak" / "alanlar" / "bilim"
KUTUP = ROOT / "knowledge" / "kutuphane" / "raflar"
ORTAK = ROOT / "knowledge" / "ortak_kaynak" / "KAYNAK_KAYIT.json"
KAV = OUT / "kavramlar_bilim.jsonl"
CATALOG = OUT / "catalog.json"
KAT = OUT / "katmanlar" / "derin"

DEEP_MD: dict[str, dict[str, str]] = {
    "01_astronomi_uzay": {
        "008_ay_dunya_iliski.md": """# Ay–Dünya ilişkisi — derin özet

Kaynak notu: Eğitim. Sayılar mertebe düzeyindedir.

## Gelgit
Ay’ın (ve Güneş’in) kütleçekimi okyanuslarda gelgit oluşturur. Ay dolunay/yeniayda Güneş ile hizalanınca gelgit genliği artabilir (kısa özet).

## Evreler (hatırlatma)
Yeniay → hilal → ilk dördün → dolunay → son dördün. Evreler Dünya’dan görülen aydınlık kısımdır; Ay’ın «kaybolması» değildir.

## Tutulma
Güneş tutulması: Ay, Dünya ile Güneş arasına girer. Ay tutulması: Dünya’nın gölgesi Ay’a düşer.
""",
        "009_yildiz_evrim_kisa.md": """# Yıldız evrimi — kısa

Kaynak notu: Basitleştirilmiş eğitim modeli.

## Yakıt
Yıldızlar çekirdekte füzyonla ışır. Güneş gibi yıldızlar hidrojeni helyuma çevirir.

## Sonlar (kabaca)
Kütleye göre: beyaz cüce, nötron yıldızı veya kara delik yolları anlatılır. Detaylı astrofizik hesabı bu paketin konusu değildir.

## Süpernova
Büyük yıldızların patlaması; ağır elementlerin uzaya saçılması bağlamında anılır.
""",
        "010_buyuk_patlama_cerceve.md": """# Büyük Patlama — çerçeve

Kaynak notu: Bilimsel model özeti; dinî yorum değildir.

## Fikir
Evrenin geçmişte daha sıcak ve yoğun bir durumdan genişlediği modeli. Kanıt çerçeveleri: kozmik mikrodalga arka plan, galaksi uzaklaşma (kızıl kayma) eğitimde anılır.

## Sınır
Bu paket teolojik iddia taşımaz; fizik modeli özetidir.
""",
    },
    "02_fizik_kimya": {
        "007_isi_sicaklik_iletkenlik.md": """# Isı, sıcaklık, iletkenlik

Kaynak notu: Lise düzeyi.

## Fark
Sıcaklık: ortalama kinetik enerjiyle ilişkili ölçü. Isı: sıcaklık farkından dolayı enerji aktarımı.

## İletim yolları
İletim (katı), konveksiyon (akışkan), ışıma (elektromanyetik). Metaller genelde iyi iletkendir.
""",
        "008_asit_baz_ph_kisa.md": """# Asit–baz ve pH — kısa

Kaynak notu: Genel kimya. Laboratuvar güvenlik protokolü değildir.

## Asit–baz
Asitler proton verebilir (Brønsted çerçevesi eğitimde). Bazlar proton alabilir. Nötrleşme tuz ve su üretebilir.

## pH
0–14 ölçeği (sulı çözeltiler için yaygın eğitim modeli): <7 asidik, 7 nötr, >7 bazik. Kesin laboratuvar ölçümü bu metnin konusu değildir.
""",
        "009_dalga_ses_isik.md": """# Dalga, ses, ışık — kısa

Kaynak notu: Eğitim özeti.

## Dalga
Enerji taşır; madde taşımak zorunda değildir. Frekans, dalga boyu, hız ilişkisi eğitimde anılır.

## Ses
Ortam gerektirir (havada). Işık elektromanyetiktir; boşlukta da yayılabilir.
""",
        "010_kimyasal_tepkimeler.md": """# Kimyasal tepkimeler — çerçeve

Kaynak notu: Kavram. Tehlikeli deney tarifi yok.

## Korunum
Atomlar yeniden düzenlenir; kütle korunumu eğitim ilkesi. Yanma: oksijenle tepkime örneği.

## Karışım–bileşik
Karışım: oran değişebilir. Bileşik: sabit oranlı kimyasal bağ.
""",
    },
    "03_biyoloji_dunya": {
        "007_sindirim_solunum_kisa.md": """# Sindirim ve solunum — kısa

Kaynak notu: Genel vücut bilgisi. Tıbbi teşhis/tedavi değildir.

## Sindirim
Besinlerin parçalanıp emilime hazırlanması (ağız → mide → bağırsak çerçevesi).

## Solunum
Gaz alışverişi: oksijen alınır, karbondioksit verilir. Hücresel solunum enerji (ATP) üretimi bağlamında anılır.
""",
        "008_sinir_duyu_kisa.md": """# Sinir ve duyu — kısa

Kaynak notu: Eğitim. Klinik teşhis değildir.

## Sinir sistemi
Beyin, omurilik, sinirler; bilgi iletimi. Duyu organları çevreden uyarı alır.

## Refleks
Hızlı, çoğu zaman bilinç dışı yanıt örneği eğitimde anılır.
""",
        "009_evrim_cerceve.md": """# Evrim — bilimsel çerçeve

Kaynak notu: Biyoloji modeli özeti; dinî tartışma/fetva değildir.

## Doğal seçilim
Popülasyonda kalıtsal çeşitlilik + çevreye uyum farkı → nesillerde özellik değişimi modeli.

## Sınır
Bu paket inanç hükmü vermez; müfredat biyolojisi çerçevesidir.
""",
        "010_besin_gruplari_ekoloji.md": """# Besin grupları ve ekoloji bağı

Kaynak notu: Genel sağlık bilgisi değil; ekoloji bağlantısı.

## Üretici–tüketici
Bitkiler üretici (fotosentez). Otçul/etçil tüketiciler. Ayrıştırıcılar madde döngüsünü tamamlar.

## Dengeler
Aşırı avlanma veya habitat kaybı zinciri bozabilir (kavram).
""",
    },
    "06_matematik": {
        "007_kesir_ondalik_yuzde.md": """# Kesir, ondalık, yüzde

Kaynak notu: Günlük matematik.

## Dönüşüm
1/2 = 0,5 = %50. Pay/payda; ondalık basamak; yüzde = /100.

## Oran
a:b ile a/b aynı ilişkiyi anlatır. Tarif ve ölçek problemlerinde kullanılır.
""",
        "008_denklem_bilinmeyen.md": """# Denklem ve bilinmeyen — kısa

Kaynak notu: Temel cebir.

## Denklem
Eşitliğin iki yanı dengededir. Bilinmeyene işlem uygulanırken eşitlik korunur.

## Örnek fikir
x + 3 = 10 → x = 7. Günlük «kaç eksik/fazla» sorularına model olur.
""",
        "009_olasilik_kisa.md": """# Olasılık — kısa

Kaynak notu: Temel. Kumar tavsiyesi değildir.

## Klasik fikir
Eşit olasılıklı sonuçlarda P = uygun / tüm. Yazı-tura: 1/2.

## İstatistik bağı
Ortalama, medyan, mod veri özetler; olasılık gelecek belirsizliğini modeller.
""",
        "010_koordinat_grafik.md": """# Koordinat ve grafik

Kaynak notu: Temel.

## Düzlem
x (yatay), y (dikey). Nokta (x,y). Doğru grafik ilişki gösterir.

## Okuma
Eksenleri ve birimleri okumak, eğim fikri (rise/run) eğitimde anılır.
""",
    },
}

KAVRAMLAR = [
    {
        "id": "bilim",
        "baslik": "bilim",
        "aliases": ["bilim nedir", "fen", "fen bilimleri", "pozitif bilim"],
        "metin": (
            "Bilim: gözlem, ölçüm, hipotez ve sınamayla doğayı anlamaya çalışan yöntemli bilgi. "
            "Rüzgar’da astronomi, fizik–kimya, biyoloji, matematik özetleri ve İslâm bilim mirası "
            "kavramı vardır. Tıbbi teşhis vermez."
        ),
        "kaynak_notu": "Bilim — derin raf.",
    },
    {
        "id": "astronomi",
        "baslik": "astronomi",
        "aliases": ["astronomi", "gok bilimi", "gök bilimi", "uzay bilimi"],
        "metin": (
            "Astronomi: gök cisimleri ve evren. Güneş Sistemi, yıldız evrimi, galaksiler, "
            "kara delik ve Büyük Patlama çerçevesi bu rafta özetlenir."
        ),
        "kaynak_notu": "Bilim — astronomi.",
    },
    {
        "id": "gunes_sistemi",
        "baslik": "gunes sistemi",
        "aliases": ["gunes sistemi", "güneş sistemi", "gezegenler", "sekiz gezegen"],
        "metin": (
            "Güneş merkezde; sekiz gezegen Merkür’den Neptün’e. Cüce gezegenler, asteroid "
            "kuşağı, kuyruklu yıldızlar. Dünya sıvı su ve yaşam koşullarıyla özeldir."
        ),
        "kaynak_notu": "Bilim — astronomi.",
    },
    {
        "id": "galaksi",
        "baslik": "galaksi",
        "aliases": ["galaksi", "samanyolu", "samanyolu galaksisi"],
        "metin": "Galaksi: yıldız+gaz+toz sistemi. Dünya Samanyolu’ndadır.",
        "kaynak_notu": "Bilim — astronomi.",
    },
    {
        "id": "yildiz",
        "baslik": "yildiz",
        "aliases": ["yildiz", "yıldız", "yildiz evrimi", "super nova", "süpernova"],
        "metin": (
            "Yıldız: füzyonla ışık üreten plazma küresi. Evrim kütleye bağlıdır; "
            "süpernova büyük yıldızların patlamasıdır."
        ),
        "kaynak_notu": "Bilim — astronomi.",
    },
    {
        "id": "kara_delik",
        "baslik": "kara delik",
        "aliases": ["kara delik", "karadelik", "black hole"],
        "metin": (
            "Kara delik: ışığın kaçamayacağı kadar güçlü kütleçekimli bölge. "
            "Gözlemler dolaylıdır (yörünge, gölge görüntüsü vb.)."
        ),
        "kaynak_notu": "Bilim — astronomi.",
    },
    {
        "id": "buyuk_patlama",
        "baslik": "buyuk patlama",
        "aliases": ["buyuk patlama", "büyük patlama", "big bang"],
        "metin": (
            "Büyük Patlama: evrenin sıcak–yoğun geçmişten genişlediği bilimsel model. "
            "Dinî yorum/fetva değildir."
        ),
        "kaynak_notu": "Bilim — kozmoloji çerçevesi.",
    },
    {
        "id": "ay_evreleri",
        "baslik": "ay evreleri",
        "aliases": ["ay evreleri", "ay tutulmasi", "güneş tutulması", "gelgit"],
        "metin": (
            "Ay evreleri Dünya’dan görülen aydınlık kısımdır. Tutulmalar gölge geometrisidir. "
            "Gelgitte Ay ve Güneş kütleçekimi etkilidir."
        ),
        "kaynak_notu": "Bilim — astronomi.",
    },
    {
        "id": "fizik",
        "baslik": "fizik",
        "aliases": ["fizik", "fizik nedir"],
        "metin": (
            "Fizik: madde, enerji, hareket, kuvvet, ısı, elektrik, dalga. "
            "Newton yasaları ve basit modeller bu raftadır."
        ),
        "kaynak_notu": "Bilim — fizik.",
    },
    {
        "id": "kimya",
        "baslik": "kimya",
        "aliases": ["kimya", "kimya nedir", "element", "periyodik tablo"],
        "metin": (
            "Kimya: atom, element, bileşik, tepkime, asit–baz. Periyodik tablo elementleri "
            "düzenler. Tehlikeli deney tarifi yoktur."
        ),
        "kaynak_notu": "Bilim — kimya.",
    },
    {
        "id": "atom",
        "baslik": "atom",
        "aliases": ["atom", "atom nedir", "proton elektron", "molekul", "molekül"],
        "metin": (
            "Atom: proton–nötron çekirdek + elektron. Molekül: bağlı atom grubu. "
            "Element tek tür atomdan oluşur."
        ),
        "kaynak_notu": "Bilim — kimya.",
    },
    {
        "id": "enerji",
        "baslik": "enerji",
        "aliases": ["enerji", "enerji nedir", "kinetik", "potansiyel"],
        "metin": (
            "Enerji: iş yapabilme kapasitesi; kinetik, potansiyel, ısı, elektrik vb. "
            "Korunum ilkesi eğitimde anılır."
        ),
        "kaynak_notu": "Bilim — fizik.",
    },
    {
        "id": "newton",
        "baslik": "newton",
        "aliases": ["newton", "newton yasalari", "kuvvet", "f=ma", "eylemsizlik"],
        "metin": (
            "Newton hareket yasaları: eylemsizlik, F=ma çerçevesi, etki–tepki. "
            "Günlük hareketi modellemek için temeldir."
        ),
        "kaynak_notu": "Bilim — fizik.",
    },
    {
        "id": "elektrik",
        "baslik": "elektrik",
        "aliases": ["elektrik", "magnetizma", "manyetizma", "akim", "akım"],
        "metin": (
            "Elektrik: yüklerin hareketi ve alanları. Manyetizma ile yakından ilişkilidir. "
            "Basit devre fikri eğitim özetindedir."
        ),
        "kaynak_notu": "Bilim — fizik.",
    },
    {
        "id": "asit_baz",
        "baslik": "asit baz",
        "aliases": ["asit", "baz", "asit baz", "ph", "pH"],
        "metin": (
            "Asit–baz: proton alışverişi çerçevesi; pH asidik/bazik ölçeği (eğitim modeli). "
            "Laboratuvar güvenlik protokolü değildir."
        ),
        "kaynak_notu": "Bilim — kimya.",
    },
    {
        "id": "isi",
        "baslik": "isi sicaklik",
        "aliases": ["isi", "sıcaklık", "sicaklik", "iletkenlik", "isi nedir"],
        "metin": (
            "Sıcaklık ortalama enerji ölçüsü; ısı aktarımdır. İletim, konveksiyon, ışıma "
            "yolları vardır."
        ),
        "kaynak_notu": "Bilim — fizik.",
    },
    {
        "id": "dalga",
        "baslik": "dalga",
        "aliases": ["dalga", "ses", "isik", "ışık", "frekans"],
        "metin": (
            "Dalga enerji taşır. Ses ortama ihtiyaç duyar; ışık elektromanyetiktir ve "
            "boşlukta yayılabilir."
        ),
        "kaynak_notu": "Bilim — fizik.",
    },
    {
        "id": "biyoloji",
        "baslik": "biyoloji",
        "aliases": ["biyoloji", "biyoloji nedir", "canli bilimi"],
        "metin": (
            "Biyoloji: hücreden ekolojiye canlıları inceler. Bu raf genel eğitimdir; "
            "tıbbi teşhis koymaz."
        ),
        "kaynak_notu": "Bilim — biyoloji; klinik değil.",
    },
    {
        "id": "hucre",
        "baslik": "hucre",
        "aliases": ["hucre", "hücre", "hucre nedir", "hücre nedir"],
        "metin": "Hücre yaşamın temel birimidir; organeller işlevleri paylaşır.",
        "kaynak_notu": "Bilim — biyoloji.",
    },
    {
        "id": "fotosentez",
        "baslik": "fotosentez",
        "aliases": ["fotosentez", "fotosentez nedir"],
        "metin": (
            "Fotosentez: ışıkla CO₂ ve sudan glikoz ve oksijen üretimi. "
            "Ekosistemin enerji girişidir."
        ),
        "kaynak_notu": "Bilim — biyoloji.",
    },
    {
        "id": "ekosistem",
        "baslik": "ekosistem",
        "aliases": ["ekosistem", "besin zinciri", "besin piramidi"],
        "metin": (
            "Ekosistem: canlı–cansız etkileşim. Besin zinciri üretici → tüketici → "
            "ayrıştırıcı akışını gösterir."
        ),
        "kaynak_notu": "Bilim — biyoloji.",
    },
    {
        "id": "dna",
        "baslik": "dna",
        "aliases": ["dna", "genetik", "gen", "kalitim", "kalıtım"],
        "metin": (
            "DNA kalıtsal bilgiyi taşır; genler işlevsel birimlerdir. "
            "Klinik genetik danışmanlık değildir."
        ),
        "kaynak_notu": "Bilim — biyoloji; klinik değil.",
    },
    {
        "id": "solunum_sindirim",
        "baslik": "solunum sindirim",
        "aliases": ["solunum", "sindirim", "akciger", "mide"],
        "metin": (
            "Sindirim besini parçalar; solunum gaz alışverişi ve hücresel enerjiyle ilişkilidir. "
            "Eğitim özeti; hastalık teşhisi yoktur."
        ),
        "kaynak_notu": "Bilim — biyoloji; klinik değil.",
    },
    {
        "id": "evrim",
        "baslik": "evrim",
        "aliases": ["evrim", "dogal secilim", "doğal seçilim", "evrim teorisi"],
        "metin": (
            "Evrim: popülasyonlarda kalıtsal değişim modeli; doğal seçilim ana mekanizmalardan. "
            "Dinî hüküm/fetva değildir; biyoloji çerçevesidir."
        ),
        "kaynak_notu": "Bilim — biyoloji modeli.",
    },
    {
        "id": "matematik",
        "baslik": "matematik",
        "aliases": ["matematik", "matematik nedir", "hesap"],
        "metin": (
            "Matematik: sayı, oran, geometri, denklem, olasılık, grafik. "
            "Günlük problemleri modellemek için araçtır."
        ),
        "kaynak_notu": "Bilim — matematik.",
    },
    {
        "id": "geometri",
        "baslik": "geometri",
        "aliases": ["geometri", "alan", "cevre", "hacim"],
        "metin": "Geometri: şekil, açı, alan, hacim ilişkileri.",
        "kaynak_notu": "Bilim — matematik.",
    },
    {
        "id": "yuzde",
        "baslik": "yuzde",
        "aliases": ["yuzde", "yüzde", "kesir", "ondalik", "ondalık"],
        "metin": "Yüzde = /100. Kesir ve ondalıkla dönüşür (1/2 = 0,5 = %50).",
        "kaynak_notu": "Bilim — matematik.",
    },
    {
        "id": "denklem",
        "baslik": "denklem",
        "aliases": ["denklem", "bilinmeyen", "cebir", "denklem nedir"],
        "metin": (
            "Denklem: eşitliğin korunduğu bilinmeyenli ifade. Temel cebir günlük "
            "«kaç eksik» sorularını modeller."
        ),
        "kaynak_notu": "Bilim — matematik.",
    },
    {
        "id": "olasilik",
        "baslik": "olasilik",
        "aliases": ["olasilik", "olasılık", "ihtimal"],
        "metin": (
            "Olasılık: belirsiz olayın ölçüsü. Klasik P = uygun/tüm. Kumar tavsiyesi değildir."
        ),
        "kaynak_notu": "Bilim — matematik.",
    },
    {
        "id": "bilimsel_yontem",
        "baslik": "bilimsel yontem",
        "aliases": [
            "bilimsel yontem",
            "bilimsel yöntem",
            "hipotez",
            "deney",
            "gozlem",
            "gözlem",
        ],
        "metin": (
            "Bilimsel yöntem: soru → veri → hipotez → sınama → sonuç/revizyon. "
            "Tekrarlanabilirlik önemlidir."
        ),
        "kaynak_notu": "Bilim Faz 2 — yöntem.",
    },
    {
        "id": "islam_bilim_mirasi",
        "baslik": "islam bilim mirasi",
        "aliases": [
            "islam bilim mirasi",
            "islâm bilim mirası",
            "islam bilimi",
            "beytul hikmet",
            "beytü'l-hikme",
        ],
        "metin": (
            "İslâm bilim mirası: klasik dönemde matematik, tıp, astronomi, optik birikimi. "
            "Kavram/özet; fetva değildir."
        ),
        "kaynak_notu": "Bilim Faz 2 — miras.",
    },
    {
        "id": "harizmi",
        "baslik": "harizmi",
        "aliases": ["harizmi", "hârizmî", "al khwarizmi", "cebir", "algoritma"],
        "metin": (
            "Hârizmî: cebir ve algoritma geleneğiyle anılır. Sayfa uydurulmaz."
        ),
        "kaynak_notu": "Bilim Faz 2 — miras.",
    },
    {
        "id": "ibn_heysem",
        "baslik": "ibn heysem",
        "aliases": ["ibn heysem", "ibnul heysem", "ibn al haytham", "optik"],
        "metin": (
            "İbnü'l-Heysem: optik ve deneysel yönteme katkılarıyla anılır. Kavram/özet."
        ),
        "kaynak_notu": "Bilim Faz 2 — miras.",
    },
    {
        "id": "disiplinler",
        "baslik": "fen disiplinleri",
        "aliases": ["fen disiplinleri", "bilim dallari", "bilim dalları", "hangi bilim"],
        "metin": (
            "Ana raflar: astronomi/uzay, fizik, kimya, biyoloji, matematik. "
            "Coğrafya ve teknoloji ayrı alanlardır."
        ),
        "kaynak_notu": "Bilim — harita.",
    },
]


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_mds() -> int:
    n = 0
    for raf, files in DEEP_MD.items():
        dest = KUTUP / raf / "incremental"
        dest.mkdir(parents=True, exist_ok=True)
        for name, body in files.items():
            path = dest / name
            path.write_text(body.lstrip(), encoding="utf-8")
            n += 1
            print(f"  [w] {raf}/{name}")
    return n


def _scan() -> dict:
    out = {}
    total_md = 0
    total_ch = 0
    for raf in ("01_astronomi_uzay", "02_fizik_kimya", "03_biyoloji_dunya", "06_matematik"):
        files = list((KUTUP / raf).rglob("*.md"))
        ch = sum(len(p.read_text(encoding="utf-8")) for p in files)
        out[raf] = {"md": len(files), "char": ch}
        total_md += len(files)
        total_ch += ch
    out["_toplam"] = {"md": total_md, "char": total_ch}
    return out


def _write_katman() -> dict:
    dest = KAT
    incr = dest / "incremental"
    if incr.exists():
        for old in incr.glob("*.md"):
            old.unlink()
    incr.mkdir(parents=True, exist_ok=True)
    body = [
        "# Bilim derin katman indeksi",
        "",
        "Kaynak: Rüzgar bilim 13b. Eğitim. Tıbbi teşhis yok. Tehlikeli deney yok.",
        "",
        "## Eklenenler",
        "",
        "Astronomi: Ay–Dünya, yıldız evrimi, Büyük Patlama çerçevesi. "
        "Fizik–kimya: ısı, asit–baz, dalga, tepkime. "
        "Biyoloji: sindirim/solunum, sinir, evrim çerçevesi, ekoloji. "
        "Matematik: kesir–yüzde, denklem, olasılık, grafik.",
        "",
        "## Sınır",
        "",
        "Klinik teşhis, laboratuvar protokolü ve uydurma kesin kozmik rakam yoktur.",
        "",
    ]
    (incr / "derin_batch_0001.md").write_text("\n".join(body), encoding="utf-8")
    man = {
        "katman_id": "derin",
        "baslik": "Bilim derin katman indeksi",
        "kaynak_id": "bilim_katman_derin",
        "ilim_alani": "bilim",
        "faz": "1b_derin",
        "dosya_yolu": "knowledge/ortak_kaynak/alanlar/bilim/katmanlar/derin",
        "updated_utc": _utc(),
    }
    (dest / "manifest.json").write_text(
        json.dumps(man, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return man


def _update_ortak(man: dict) -> None:
    data = json.loads(ORTAK.read_text(encoding="utf-8")) if ORTAK.is_file() else {"kayitlar": []}
    rows = data.get("kayitlar") or []
    entry = {
        "kaynak_id": man["kaynak_id"],
        "kaynak_adi": man["baslik"],
        "yazar": None,
        "ilim_alani": "bilim",
        "eser_turu": "katman",
        "dil": "tr",
        "yayin": None,
        "cilt": None,
        "bolum": None,
        "sayfa": None,
        "dosya_yolu": man["dosya_yolu"],
        "guvenilirlik": "orta",
        "kaynak_sinifi": "kalici",
        "durum": "hazir",
        "not": "Bilim derinleştirme indeksi.",
    }
    found = False
    for r in rows:
        if r.get("kaynak_id") == entry["kaynak_id"]:
            r.update(entry)
            found = True
            break
    if not found:
        rows.append(entry)
    data["kayitlar"] = rows
    data["guncelleme"] = _utc()
    ORTAK.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    print("=== derin md ===")
    n = _write_mds()
    man = _write_katman()
    _update_ortak(man)
    KAV.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in KAVRAMLAR) + "\n",
        encoding="utf-8",
    )
    sc = _scan()
    cat = json.loads(CATALOG.read_text(encoding="utf-8")) if CATALOG.is_file() else {}
    cat["updated_utc"] = _utc()
    cat["derinlestirme"] = {
        "script": "faz13b_bilim_derin_ingest.py",
        "ek_md": n,
        "kavram": len(KAVRAMLAR),
        "scan": sc,
        "updated_utc": _utc(),
    }
    cat.setdefault("sayilar", {})
    cat["sayilar"]["md_dosya"] = sc["_toplam"]["md"]
    cat["sayilar"]["karakter"] = sc["_toplam"]["char"]
    cat["sayilar"]["kavram"] = len(KAVRAMLAR)
    CATALOG.write_text(json.dumps(cat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    readme = OUT / "README.md"
    prev = readme.read_text(encoding="utf-8") if readme.is_file() else "# Bilim\n"
    if "13b" not in prev:
        prev = prev.rstrip() + (
            "\n\n## Derinleştirme (13b)\n"
            f"- MD: **{sc['_toplam']['md']}** · karakter ≈ **{sc['_toplam']['char']}** · "
            f"kavram: **{len(KAVRAMLAR)}**\n"
            "- Script: `faz13b_bilim_derin_ingest.py`\n"
        )
        readme.write_text(prev + "\n", encoding="utf-8")

    print(
        f"\nTOPLAM ek_md={n} md={sc['_toplam']['md']} "
        f"char={sc['_toplam']['char']} kavram={len(KAVRAMLAR)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
