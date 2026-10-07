# -*- coding: utf-8 -*-
"""Coğrafya derinleştirme (Faz 14b) — bölge, fiziki, dünya çerçeve.

Mevcut ince özetleri genişletir. Güncel nüfus/istatistik resmi kaynaktan;
uydurma rakam yok. Fetva/propaganda yok.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "knowledge" / "ortak_kaynak" / "alanlar" / "cografya"
RAF_INC = ROOT / "knowledge" / "kutuphane" / "raflar" / "04_cografya" / "incremental"
KAT = OUT / "katmanlar" / "derin"
ORTAK = ROOT / "knowledge" / "ortak_kaynak" / "KAYNAK_KAYIT.json"
KAV = OUT / "kavramlar_cografya.jsonl"
CATALOG = OUT / "catalog.json"

# --- Geniş kavram seti (öncekiler + yeni) ---
KAVRAMLAR = [
    {
        "id": "cografya",
        "baslik": "cografya",
        "aliases": ["cografya", "coğrafya", "cografya nedir", "coğrafya nedir"],
        "metin": (
            "Coğrafya: yeryüzü, doğal ortam ve insan–mekân ilişkisini inceler. "
            "Fiziki (yerşekli, iklim, hidrografya) ve beşeri (nüfus, yerleşme, ekonomi) "
            "kolları vardır. Rüzgar’da Türkiye bölgeleri, fiziki özet ve dünya çerçevesi vardır."
        ),
        "kaynak_notu": "Coğrafya — derin raf.",
    },
    {
        "id": "fiziki_cografya",
        "baslik": "fiziki cografya",
        "aliases": ["fiziki cografya", "fizikî coğrafya", "fiziki cografya nedir"],
        "metin": (
            "Fiziki coğrafya: yerşekilleri, iklim, toprak, bitki örtüsü ve sular. "
            "Türkiye’de dağ kuşakları, platolar, akarsular ve denizler bu kolun konusudur."
        ),
        "kaynak_notu": "Coğrafya derin.",
    },
    {
        "id": "turkiye_cografyasi",
        "baslik": "turkiye cografyasi",
        "aliases": [
            "turkiye cografyasi",
            "türkiye coğrafyası",
            "anadolu",
            "turkiye konumu",
            "turkiye nerede",
        ],
        "metin": (
            "Türkiye; Anadolu (Asya) ve Trakya (Avrupa) üzerinde, boğazlarla iki kıtayı "
            "birleştirir. Üç tarafı deniz: Karadeniz, Ege, Akdeniz; ayrıca Marmara iç denizdir. "
            "Yedi coğrafi bölge okul coğrafyasında temel çerçevedir. Başkent Ankara."
        ),
        "kaynak_notu": "Coğrafya — Türkiye.",
    },
    {
        "id": "bolge_karadeniz",
        "baslik": "karadeniz bolgesi",
        "aliases": ["karadeniz bolgesi", "karadeniz bölgesi", "karadeniz cografya"],
        "metin": (
            "Karadeniz Bölgesi: yağışlı kıyı, dağların denize paralel uzanması, çay–fındık "
            "tarımıyla anılır. Doğu Karadeniz’de eğim ve heyelan riski yüksektir. "
            "Önemli merkezler: Trabzon, Samsun, Ordu, Rize, Zonguldak çevresi."
        ),
        "kaynak_notu": "Coğrafya — bölge.",
    },
    {
        "id": "bolge_marmara",
        "baslik": "marmara bolgesi",
        "aliases": ["marmara bolgesi", "marmara bölgesi", "marmara cografya"],
        "metin": (
            "Marmara Bölgesi: geçiş iklimi, yoğun nüfus ve sanayi–ticaret. İstanbul boğazı "
            "ve Marmara Denizi kritik geçiş alanıdır. Bursa, Kocaeli, Tekirdağ, Edirne "
            "önemli yerleşimlerdendir."
        ),
        "kaynak_notu": "Coğrafya — bölge.",
    },
    {
        "id": "bolge_ege",
        "baslik": "ege bolgesi",
        "aliases": ["ege bolgesi", "ege bölgesi", "ege cografya"],
        "metin": (
            "Ege Bölgesi: bakı etkisi, zeytin–üzüm–turizm, dağların denize dik uzanmasıyla "
            "oluşan ovalar. İzmir merkezî rol oynar; Aydın, Manisa, Muğla, Denizli anılır."
        ),
        "kaynak_notu": "Coğrafya — bölge.",
    },
    {
        "id": "bolge_akdeniz",
        "baslik": "akdeniz bolgesi",
        "aliases": ["akdeniz bolgesi", "akdeniz bölgesi", "akdeniz cografya"],
        "metin": (
            "Akdeniz Bölgesi: yazları sıcak–kurak, kışları ılık–yağışlı iklim; Toroslar "
            "kıyıya paraleldir. Antalya, Adana, Mersin, Hatay; sera ve turizm öne çıkar."
        ),
        "kaynak_notu": "Coğrafya — bölge.",
    },
    {
        "id": "bolge_ic_anadolu",
        "baslik": "ic anadolu bolgesi",
        "aliases": [
            "ic anadolu",
            "iç anadolu",
            "ic anadolu bolgesi",
            "iç anadolu bölgesi",
        ],
        "metin": (
            "İç Anadolu: karasal iklim, bozkır, tahıl tarımı. Ankara başkenttir; "
            "Konya, Kayseri, Eskişehir, Sivas önemli merkezlerdir. Tuz Gölü çevresi "
            "kuraklık ve tuzlulukla anılır."
        ),
        "kaynak_notu": "Coğrafya — bölge.",
    },
    {
        "id": "bolge_dogu_anadolu",
        "baslik": "dogu anadolu bolgesi",
        "aliases": [
            "dogu anadolu",
            "doğu anadolu",
            "dogu anadolu bolgesi",
            "doğu anadolu bölgesi",
        ],
        "metin": (
            "Doğu Anadolu: yüksek plato ve dağlar, sert kış. Erzurum, Van, Malatya, Elazığ, "
            "Ağrı anılır. Van Gölü Türkiye’nin en büyük gölüdür (kapalı havza)."
        ),
        "kaynak_notu": "Coğrafya — bölge.",
    },
    {
        "id": "bolge_guneydogu",
        "baslik": "guneydogu anadolu bolgesi",
        "aliases": [
            "guneydogu anadolu",
            "güneydoğu anadolu",
            "gap bolgesi",
            "güneydoğu bölgesi",
        ],
        "metin": (
            "Güneydoğu Anadolu: sıcak yaz, ovalarda tarım (GAP çerçevesi eğitimde anılır). "
            "Gaziantep, Şanlıurfa, Diyarbakır, Mardin önemli merkezlerdendir."
        ),
        "kaynak_notu": "Coğrafya — bölge.",
    },
    {
        "id": "istanbul",
        "baslik": "istanbul",
        "aliases": ["istanbul", "istanbul cografya", "istanbul nerede"],
        "metin": (
            "İstanbul: Avrupa ve Asya yakaları, Boğaz ile ayrılır; Marmara Bölgesi’nde. "
            "Tarihî ve ekonomik merkez; başkent değildir (başkent Ankara)."
        ),
        "kaynak_notu": "Coğrafya — şehir.",
    },
    {
        "id": "ankara",
        "baslik": "ankara",
        "aliases": ["ankara", "ankara baskent", "başkent ankara"],
        "metin": (
            "Ankara: Türkiye Cumhuriyeti’nin başkenti; İç Anadolu’da. İdari ve eğitim "
            "merkezi olarak öne çıkar."
        ),
        "kaynak_notu": "Coğrafya — şehir.",
    },
    {
        "id": "izmir",
        "baslik": "izmir",
        "aliases": ["izmir", "i̇zmir", "izmir liman"],
        "metin": "İzmir: Ege’nin büyük liman ve ticaret kenti; körfez yerleşimi.",
        "kaynak_notu": "Coğrafya — şehir.",
    },
    {
        "id": "kitalar",
        "baslik": "kitalar",
        "aliases": ["kitalar", "kıtalar", "kita", "kıta", "yedi kita"],
        "metin": (
            "Kıtalar (yaygın liste): Asya, Afrika, Avrupa, Kuzey Amerika, Güney Amerika, "
            "Okyanusya, Antarktika. Asya en büyük; Avrupa–Asya birlikte Avrasya diye de anılır."
        ),
        "kaynak_notu": "Coğrafya — dünya.",
    },
    {
        "id": "okyanuslar",
        "baslik": "okyanuslar",
        "aliases": ["okyanuslar", "okyanus", "pasifik", "atlantik"],
        "metin": (
            "Okyanuslar: Pasifik (en büyük), Atlas/Atlantik, Hint, Güney, Arktik. "
            "Denizler daha küçük ve çoğu karalarla çevrilidir (Akdeniz, Karadeniz vb.)."
        ),
        "kaynak_notu": "Coğrafya — hidrografya.",
    },
    {
        "id": "harita",
        "baslik": "harita",
        "aliases": ["harita", "harita nedir", "olcek", "ölçek", "lejant"],
        "metin": (
            "Harita: seçilmiş coğrafi bilgilerin düzlemde gösterimi. Ölçek, lejant, yön oku "
            "ve projeksiyon temel unsurlardır. Büyük ölçek ayrıntı, küçük ölçek geniş alan gösterir."
        ),
        "kaynak_notu": "Coğrafya — harita.",
    },
    {
        "id": "iklim",
        "baslik": "iklim",
        "aliases": ["iklim", "iklim nedir", "iklim tipleri", "hava durumu"],
        "metin": (
            "İklim uzun dönem ortalamasıdır; hava durumu anlıktır. Türkiye’de kıyıya göre "
            "Karadeniz (nemli), Akdeniz (yaz kurak), iç kesimlerde karasal özellikler yaygındır. "
            "Yükselti ve bakı yerel fark yaratır."
        ),
        "kaynak_notu": "Coğrafya — iklim.",
    },
    {
        "id": "akarsu_dag",
        "baslik": "turkiye akarsu dag",
        "aliases": [
            "turkiye akarsu",
            "türkiye akarsu",
            "turkiye daglari",
            "türkiye dağları",
            "kizilirmak",
            "fırat",
            "dicle",
            "toroslar",
        ],
        "metin": (
            "Dağlar: Kuzey Anadolu Dağları (kıyıya paralel), Toroslar (güney). "
            "Akarsular: Kızılırmak (ülke içi en uzun), Sakarya, Fırat, Dicle, Yeşilırmak, "
            "Seyhan, Ceyhan. Göller: Van (en büyük), Tuz, Beyşehir."
        ),
        "kaynak_notu": "Coğrafya — fiziki Türkiye.",
    },
    {
        "id": "beseri_cografya",
        "baslik": "beseri cografya",
        "aliases": [
            "beseri cografya",
            "beşeri coğrafya",
            "nufus cografyasi",
            "nüfus coğrafyası",
            "yerlesme",
            "goc",
            "göç",
        ],
        "metin": (
            "Beşeri coğrafya: nüfus dağılışı, göç, kır–kent, tarım–sanayi–hizmet mekânı. "
            "Türkiye’de nüfus batı ve kıyılarda daha yoğundur (genel eğilim). "
            "Güncel rakam için TÜİK kullanılır; burada uydurma istatistik yoktur."
        ),
        "kaynak_notu": "Coğrafya — beşeri.",
    },
    {
        "id": "dunya_ulkeleri",
        "baslik": "dunya ulkeleri",
        "aliases": [
            "dunya ulkeleri",
            "dünya ülkeleri",
            "ulke nedir",
            "ülke nedir",
            "devlet siniri",
        ],
        "metin": (
            "Ülke/devlet: egemenlik ve sınırlarla tanımlanan siyasi birim. Kıta ve bölge "
            "çerçevesinde (ör. Batı Avrupa, Ortadoğu, Doğu Asya) gruplanır. "
            "Bu rafta tam ülke ansiklopedisi yoktur; bölgesel çerçeve vardır."
        ),
        "kaynak_notu": "Coğrafya — dünya çerçevesi.",
    },
    {
        "id": "ortadogu",
        "baslik": "ortadogu",
        "aliases": ["ortadogu", "orta doğu", "middle east"],
        "metin": (
            "Ortadoğu: Batı Asya’nın siyasi–coğrafi çerçevesi; petrol, boğazlar ve "
            "tarihî yollarla anılır. Sınırlar ve tanımlar tartışmalıdır; eğitim çerçevesidir."
        ),
        "kaynak_notu": "Coğrafya — dünya bölgesi.",
    },
    {
        "id": "avrupa",
        "baslik": "avrupa",
        "aliases": ["avrupa", "avrupa kitasi", "avrupa kıtası"],
        "metin": (
            "Avrupa: Asya’nın batısında kıta; Atlas Okyanusu ve Akdeniz ile çevrilidir. "
            "Türkiye’nin Trakya kesimi Avrupa’dadır."
        ),
        "kaynak_notu": "Coğrafya — kıta.",
    },
    {
        "id": "asya",
        "baslik": "asya",
        "aliases": ["asya", "asya kitasi", "asya kıtası"],
        "metin": (
            "Asya: yüzölçümü ve nüfus bakımından en büyük kıta. Anadolu Asya’dadır. "
            "Alt bölgeler: Doğu, Güney, Güneydoğu, Orta, Batı Asya vb."
        ),
        "kaynak_notu": "Coğrafya — kıta.",
    },
    {
        "id": "afrika",
        "baslik": "afrika",
        "aliases": ["afrika", "afrika kitasi"],
        "metin": (
            "Afrika: ekvatorun geçtiği büyük kıta; Sahara, Nil ve çeşitli iklim kuşaklarıyla "
            "anılır. Akdeniz üzerinden Avrupa ve Asya’ya komşudur."
        ),
        "kaynak_notu": "Coğrafya — kıta.",
    },
    {
        "id": "islam_cografya_mirasi",
        "baslik": "islam cografya mirasi",
        "aliases": [
            "islam cografya",
            "islâm coğrafya",
            "biruni",
            "bîrûnî",
            "idrisî",
            "idrisi",
        ],
        "metin": (
            "İslâm coğrafya mirası: klasik dönemde dünya tasviri, mesafe ve kıble hesabı, "
            "harita geleneği (Bîrûnî, İdrîsî). Kavram/özet; fetva değildir."
        ),
        "kaynak_notu": "Coğrafya — miras.",
    },
    {
        "id": "bolge",
        "baslik": "bolge",
        "aliases": ["bolge", "bölge", "cografi bolge", "coğrafi bölge", "yedi bolge"],
        "metin": (
            "Türkiye’nin yedi coğrafi bölgesi: Karadeniz, Marmara, Ege, Akdeniz, "
            "İç Anadolu, Doğu Anadolu, Güneydoğu Anadolu. İdarî illerle birebir örtüşmez."
        ),
        "kaynak_notu": "Coğrafya — kavram.",
    },
    {
        "id": "bogazlar",
        "baslik": "bogazlar",
        "aliases": [
            "bogazlar",
            "boğazlar",
            "istanbul bogazi",
            "canakkale bogazi",
            "turkish straits",
        ],
        "metin": (
            "Türk boğazları: İstanbul ve Çanakkale; Karadeniz’i Marmara ve Ege’ye bağlar. "
            "Coğrafi ve jeopolitik geçiş alanıdır. Eğitim çerçevesi; hukuki yorum fetva değildir."
        ),
        "kaynak_notu": "Coğrafya — Türkiye.",
    },
    {
        "id": "enlem_boylam",
        "baslik": "enlem boylam",
        "aliases": ["enlem", "boylam", "enlem boylam", "koordinat"],
        "metin": (
            "Enlem: ekvatora göre kuzey–güney açısal konum (iklimle ilişkilidir). "
            "Boylam: Greenwich’e göre doğu–batı; saat dilimleriyle ilişkilidir."
        ),
        "kaynak_notu": "Coğrafya — konum.",
    },
]

DEEP_MD = {
    "010_bolge_karadeniz.md": """# Karadeniz Bölgesi — derin özet

Kaynak notu: Okul/genel coğrafya. İstatistik uydurulmaz.

## Konum ve yerşekli
Dağlar kıyıya **paralel** uzanır; kıyı ovası dardır. Doğu’da yükselti ve eğim artar.

## İklim ve bitki
Yıl boyunca nemli; doğuya doğru yağış artabilir. Doğal bitki örtüsünde orman önemlidir.

## Ekonomi (genel)
Çay, fındık, balıkçılık ve liman ticareti öne çıkar. Madencilik (ör. Zonguldak çevresi kömür tarihçesi) anılır.

## Merkezler
Trabzon, Samsun, Ordu, Giresun, Rize, Zonguldak, Bolu (kısmen geçiş).
""",
    "011_bolge_marmara.md": """# Marmara Bölgesi — derin özet

Kaynak notu: Eğitim özeti.

## Konum
İstanbul ve Çanakkale boğazları; Avrupa–Asya bağlantısı. Marmara Denizi iç denizdir.

## İklim
Geçiş iklimi: Karadeniz ve Akdeniz etkileri karışır; iç kesimlerde karasallık artar.

## Beşeri
Nüfus ve sanayi yoğunluğu yüksek; ulaştırma ve limanlar kritiktir.

## Merkezler
İstanbul, Bursa, Kocaeli, Tekirdağ, Edirne, Balıkesir (kısmen), Yalova.
""",
    "012_bolge_ege.md": """# Ege Bölgesi — derin özet

Kaynak notu: Eğitim özeti.

## Yerşekli
Dağlar çoğu yerde denize **dik** uzanır → körfez ve verimli ovalar (Bakırçay, Gediz, Büyük Menderes vb.).

## İklim ve tarım
Akdeniz etkisi; zeytin, üzüm, incir, tütün. Turizm (kıyı) önemlidir.

## Merkezler
İzmir, Manisa, Aydın, Muğla, Denizli, Uşak (geçiş).
""",
    "013_bolge_akdeniz.md": """# Akdeniz Bölgesi — derin özet

Kaynak notu: Eğitim özeti.

## Yerşekli
Toroslar kıyıya paralel; kıyı ovası yer yer geniştir (Çukurova).

## İklim
Yaz sıcak–kurak, kış ılık–yağışlı. Seracılık yaygındır.

## Merkezler
Antalya, Adana, Mersin, Hatay, Isparta, Burdur (göller yöresi geçişi).
""",
    "014_bolge_ic_anadolu.md": """# İç Anadolu Bölgesi — derin özet

Kaynak notu: Eğitim özeti.

## Yerşekli ve iklim
Yükselti orta–yüksek; karasal iklim, yaz kuraklığı, bozkır. Tuz Gölü kapalı havza örneğidir.

## Ekonomi
Tahıl (buğday), hayvancılık; Ankara idari merkez.

## Merkezler
Ankara, Konya, Kayseri, Eskişehir, Sivas, Aksaray, Niğde, Karaman.
""",
    "015_bolge_dogu_anadolu.md": """# Doğu Anadolu Bölgesi — derin özet

Kaynak notu: Eğitim özeti.

## Yerşekli
Türkiye’nin en yüksek ve engebeli bölgesi; kışlar sert. Volkanik sahalar (Erciyes–Süphan–Ağrı çizgisi eğitimde anılır).

## Göller ve akarsu
Van Gölü (sodalı, kapalı havza). Fırat ve Dicle’nin yukarı çığırları.

## Merkezler
Erzurum, Van, Malatya, Elazığ, Erzincan, Ağrı, Kars, Bingöl.
""",
    "016_bolge_guneydogu.md": """# Güneydoğu Anadolu Bölgesi — derin özet

Kaynak notu: Eğitim özeti. GAP proje detayı teknik rapor değildir.

## Yerşekli ve iklim
Ovalar ve platolar; yazlar çok sıcak. Sulama tarımı önemlidir.

## Beşeri–ekonomi
Tarımsal üretim ve ticaret kentleri (Gaziantep vb.). Tarihî yerleşim yoğunluğu yüksektir.

## Merkezler
Gaziantep, Şanlıurfa, Diyarbakır, Mardin, Adıyaman, Batman, Siirt, Şırnak, Kilis.
""",
    "017_turkiye_komsular_deniz.md": """# Türkiye komşuları ve denizleri

Kaynak notu: Genel coğrafya. Siyasi yorum/propaganda yok.

## Kara komşuları
Bulgaristan, Yunanistan, Gürcistan, Ermenistan, İran, Irak, Suriye.
(Nahçıvan ile kısa sınır eğitim metinlerinde anılabilir.)

## Denizler
Karadeniz (kuzey), Marmara (iç), Ege (batı), Akdeniz (güney).

## Boğazlar
İstanbul Boğazı, Çanakkale Boğazı — Karadeniz’in açık denizlere çıkışı.
""",
    "018_turkiye_goller_platolar.md": """# Göller, platolar, ovalar — Türkiye

Kaynak notu: Seçme örnekler; tam envanter değildir.

## Göller
- **Van Gölü** — en büyük (yüzölçümü); kapalı havza
- **Tuz Gölü** — sığ, tuzluluk
- **Beyşehir**, Eğirdir — tatlı su örnekleri (göller yöresi)

## Platolar
Doğu Anadolu platosu, İç Anadolu düzlük–plato geçişleri, Teke–Taşeli (Akdeniz).

## Ovalar
Çukurova, Gediz, Büyük Menderes, Çarşamba, Bafra — tarım için önemli.
""",
    "019_dunya_bolgeleri_cerceve.md": """# Dünya bölgeleri — çerçeve

Kaynak notu: Kabaca kültürel–coğrafi çerçeve; sınırlar tartışmalıdır.

## Büyük çerçeveler
- **Avrupa** — batı ucu; AB vb. siyasi örgütler coğrafyadan ayrı konudur
- **Ortadoğu / Batı Asya** — Türkiye’nin doğu–güney komşuluk alanı
- **Afrika** — Sahara kuzeyi ve Sahra-altı
- **Güney / Doğu / Güneydoğu Asya** — muson, yoğun nüfus kuşakları
- **Amerika** — Kuzey ve Güney; Pasifik–Atlas kıyıları
- **Okyanusya** — Avustralya ve ada dünyası

## Öğrenme notu
Ülke bayrağı/başkent ezberi bu paketin amacı değildir; kıta–bölge–geçiş mantığıdır.
""",
    "020_fiziki_beseri_ayrim.md": """# Fiziki ve beşeri coğrafya — ayrım

Kaynak notu: Kavram netliği.

## Fiziki
Yerşekli, iklim, toprak, bitki, su. İnsan etkisi ikincil konu olabilir (erozyon vb.).

## Beşeri
Nüfus, yerleşme, göç, tarım–sanayi–hizmet, ulaşım, turizm.

## Türkiye örneği
Karadeniz’de fiziki (yağış, dağ) ile beşeri (çay, kıyı yerleşme) birlikte okunur.
""",
}

KATMAN_DERIN = {
    "baslik": "Coğrafya derin katman indeksi",
    "kaynak_id": "cografya_katman_derin",
    "parcalar": [
        (
            "Ne eklendi",
            "Yedi bölge ayrıntı md, komşular/denizler, göller–platolar–ovalar, "
            "dünya bölge çerçevesi, fiziki–beşeri ayrım. Anlık kavram sayısı artırıldı.",
        ),
        (
            "Sınır",
            "İl–ilçe ansiklopedisi ve güncel nüfus tablosu yoktur. "
            "Rakam için TÜİK / resmi kaynak gerekir.",
        ),
    ],
}


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_mds() -> int:
    RAF_INC.mkdir(parents=True, exist_ok=True)
    n = 0
    for name, body in DEEP_MD.items():
        path = RAF_INC / name
        path.write_text(body.lstrip(), encoding="utf-8")
        n += 1
        print(f"  [w] {name} ({len(body)} char)")
    return n


def _write_katman() -> dict:
    dest = KAT
    incr = dest / "incremental"
    if incr.exists():
        for old in incr.glob("*.md"):
            old.unlink()
    incr.mkdir(parents=True, exist_ok=True)
    body = [
        f"# {KATMAN_DERIN['baslik']}",
        "",
        "Kaynak: Rüzgar coğrafya derinleştirme. Eğitim. Uydurma istatistik yok.",
        "",
    ]
    for i, (t, x) in enumerate(KATMAN_DERIN["parcalar"], 1):
        body += [f"## {i}. {t}", "", x, ""]
    (incr / "derin_batch_0001.md").write_text("\n".join(body), encoding="utf-8")
    man = {
        "katman_id": "derin",
        "baslik": KATMAN_DERIN["baslik"],
        "kaynak_id": KATMAN_DERIN["kaynak_id"],
        "ilim_alani": "cografya",
        "faz": "1b_derin",
        "dosya_yolu": "knowledge/ortak_kaynak/alanlar/cografya/katmanlar/derin",
        "parca_sayisi": len(KATMAN_DERIN["parcalar"]),
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
        "ilim_alani": "cografya",
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
        "not": "Coğrafya derinleştirme indeksi.",
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

    files = sorted(RAF_INC.glob("*.md"))
    chars = sum(len(p.read_text(encoding="utf-8")) for p in files)
    cat = json.loads(CATALOG.read_text(encoding="utf-8")) if CATALOG.is_file() else {}
    cat["updated_utc"] = _utc()
    cat["derinlestirme"] = {
        "script": "faz14b_cografya_derin_ingest.py",
        "ek_md": n,
        "kavram": len(KAVRAMLAR),
        "updated_utc": _utc(),
    }
    cat.setdefault("sayilar", {})
    cat["sayilar"]["md_dosya"] = len(files)
    cat["sayilar"]["karakter"] = chars
    cat["sayilar"]["kavram"] = len(KAVRAMLAR)
    CATALOG.write_text(json.dumps(cat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    readme = OUT / "README.md"
    prev = readme.read_text(encoding="utf-8") if readme.is_file() else "# Coğrafya\n"
    if "derinleştirme" not in prev.lower():
        prev = prev.rstrip() + (
            "\n\n## Derinleştirme (14b)\n"
            "- Yedi bölge ayrıntı · komşular/deniz · göller/platolar · dünya çerçevesi\n"
            f"- MD: **{len(files)}** · karakter ≈ **{chars}** · kavram: **{len(KAVRAMLAR)}**\n"
            "- Script: `faz14b_cografya_derin_ingest.py`\n"
        )
        readme.write_text(prev + "\n", encoding="utf-8")

    print(f"\nTOPLAM md={len(files)} char={chars} kavram={len(KAVRAMLAR)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
