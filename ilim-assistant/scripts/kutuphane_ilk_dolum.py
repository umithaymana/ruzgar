# Created by Ümit & Gökçenur
"""Rüzgar Kütüphanesi — ilk dolum (detaylı raflar). Bir kez çalıştırılır."""

from __future__ import annotations

from pathlib import Path

from ilim_assistant.ruzgar_kutuphane import (
    RAF_TANIMLARI,
    ensure_dirs,
    kutuphane_root,
    rebuild_katalog,
)

ROOT = kutuphane_root()
RAFLAR = ROOT / "raflar"


def _w(raf: str, name: str, body: str) -> None:
    d = RAFLAR / raf / "incremental"
    d.mkdir(parents=True, exist_ok=True)
    path = d / name
    path.write_text(body.strip() + "\n", encoding="utf-8")
    print("OK", path.relative_to(ROOT))


def main() -> None:
    ensure_dirs()
    readme = ROOT / "README.md"
    readme.write_text(
        """# Rüzgar Kütüphanesi

Ümit & Gökçenur — yerel, raflı bilgi deposu.

- Katalog: `KATALOG.json`
- Manifest: `manifest.json`
- Raflar: `raflar/<raf_id>/incremental/*.md`
- Sohbet: «kütüphane durum» · «kütüphane ara …»
- RAG: `knowledge/` altındaki tüm `.md` dosyaları indeks taramasına girer

Bu kütüphane **kişisel hafıza** (`hatırla`) ve **nebula kitap ingest** ile karışmaz;
genel kültür / ansiklopedik bilgi için düzenli raflardır.
""".strip()
        + "\n",
        encoding="utf-8",
    )

    # --- 01 Astronomi ---
    _w(
        "01_astronomi_uzay",
        "001_gunes_sistemi.md",
        """
# Güneş Sistemi — Rüzgar Kütüphanesi

Kaynak notu: Genel astronomi özeti (eğitim amaçlı). Sayılar yuvarlak; güncel ölçümler NASA/ESA ile doğrulanabilir.

## Güneş nedir
Güneş, Güneş Sisteminin merkezindeki bir **sarı cüce yıldızdır** (spektral sınıf yaklaşık G2V).
Enerjisini çekirdeğindeki **hidrojen füzyonundan** üretir. Dünya’daki yaşam için ışık ve ısı kaynağıdır.
Güneş’e ortalama uzaklık yaklaşık **1 astronomik birim (AU)** ≈ 149,6 milyon km’dir.

## Gezegenler (içten dışa)
1. **Merkür** — en küçük, Güneş’e en yakın; ince atmosfer.
2. **Venüs** — kalın CO₂ atmosferi; sera etkisiyle çok sıcak yüzey.
3. **Dünya** — sıvı su, oksijenli atmosfer, yaşam.
4. **Mars** — kızıl gezegen; ince atmosfer, kutup buzulları.
5. **Jüpiter** — en büyük gaz devi; Büyük Kırmızı Leke.
6. **Satürn** — belirgin halka sistemi.
7. **Uranüs** — buz devi; ekseni aşırı yatık.
8. **Neptün** — uzak buz devi; güçlü rüzgârlar.

## Cüce gezegen ve küçük cisimler
**Plüton** 2006’dan beri cüce gezegen sınıfındadır. Ayrıca asteroid kuşağı (Mars–Jüpiter arası),
Kuiper Kuşağı ve kuyruklu yıldızlar Güneş Sisteminin parçasıdır.

## Ay ve gelgit
Dünya’nın tek doğal uydusu **Ay**’dır. Ay’ın kütleçekimi **gelgit** olaylarında önemli rol oynar.
Ay’ın Dünya’ya bakış yüzü (yaklaşık) hep aynıdır; buna **bağlı dönüş** denir.

## Kısa özet
Güneş merkezdedir; sekiz gezegen yörüngededir; Dünya yaşam için özel koşullara sahiptir.
""",
    )

    _w(
        "01_astronomi_uzay",
        "002_galaksiler_samanyolu.md",
        """
# Galaksiler ve Samanyolu

## Galaksi nedir
Galaksi; yıldızlar, gaz, toz ve karanlık maddenin kütleçekimiyle bir arada tutulduğu büyük sistemdir.
Şekiller: **sarmal**, **eliptik**, **düzensiz**.

## Samanyolu
Dünya’nın içinde bulunduğu galaksi **Samanyolu**’dur (Milky Way).
Samanyolu bir **çubuklu sarmal** galaksidir. Güneş, sarmal kollardan birinin yakınında,
merkezden yaklaşık **26.000–28.000 ışık yılı** uzaklıktadır (yaklaşık değer).

## Yerel Grup
Samanyolu’nun içinde bulunduğu galaksi grubuna **Yerel Grup** denir.
En büyük komşulardan biri **Andromeda (M31)** galaksisidir; çok uzak gelecekte
Samanyolu ile etkileşime girebileceği modeller vardır.

## Işık yılı
Işık yılı, ışığın boşlukta bir yılda aldığı yoldur (≈ 9,46 trilyon km).
Uzaklık birimidir; «zaman» birimi değildir.

## Sık soru — Dünyamız hangi galakside?
**Samanyolu** galaksisindedir.
""",
    )

    _w(
        "01_astronomi_uzay",
        "003_yildizlar_ve_isik.md",
        """
# Yıldızlar, ışık ve uzaklık

## Yıldız nasıl parlar
Yıldızlar çekirdekteki füzyonla enerji üretir. Yıldızın rengi/sıcaklığı spektral sınıfını etkiler
(O, B, A, F, G, K, M — kabaca mavi-sıcak → kırmızı-serin).

## Süpernova
Büyük kütleli yıldızlar yaşamlarının sonunda şiddetli patlamayla **süpernova** olabilir.
Bu olaylar ağır elementleri uzaya yayar.

## Kara delik (kısa)
Çok yoğun kütleçekimli bölgelerdir; olay ufku ötesinden ışık kaçamayabilir.
Her kara delik «her şeyi emer ve galaksiyi yutar» değildir; ölçek ve mesafe kritiktir.

## Takımyıldız
Takımyıldızlar gökyüzünde insanlarca gruplanmış yıldız desenleridir; fiziksel olarak
birbirine bağlı olmayabilirler (perspektif).
""",
    )

    # --- 02 Fizik Kimya ---
    _w(
        "02_fizik_kimya",
        "001_maddenin_halleri_isi.md",
        """
# Maddenin halleri ve ısı

## Temel haller
- **Katı:** sabit şekil ve hacim (genelde).
- **Sıvı:** sabit hacim, değişken şekil.
- **Gaz:** değişken hacim ve şekil.
- **Plazma:** iyonlaşmış gaz (yıldızlar, şimşek).

## Erime ve kaynama
Saf maddelerde erime/kaynama noktası karakteristiktir.
**Su (1 atm):** erime ≈ 0 °C, kaynama ≈ **100 °C**.
Basınç değişince kaynama noktası değişir (dağda su daha düşük sıcaklıkta kaynar).

## Isı ve sıcaklık
**Sıcaklık** moleküllerin ortalama kinetik enerjisiyle ilgilidir.
**Isı** sıcaklık farkından dolayı transfer olan enerjidir.

## Genleşme
Çoğu madde ısınınca genleşir. Su 0–4 °C aralığında anomali gösterir (yoğunluk maksimumu ≈ 4 °C).
""",
    )

    _w(
        "02_fizik_kimya",
        "002_atom_element_periyodik.md",
        """
# Atom, element ve periyodik tablo

## Atom
Atom; proton, nötron (çekirdek) ve elektronlardan oluşur.
Elementi proton sayısı (**atom numarası**) belirler.

## Molekül ve bileşik
Aynı veya farklı atomların kimyasal bağlarla birleşmesi molekül/bileşik oluşturur.
Örnek: H₂O (su), CO₂ (karbondioksit), O₂ (oksijen gazı).

## Periyodik tablo
Elementler artan atom numarasına göre düzenlenir.
Aynı grup (dikey) benzer kimyasal özellikler gösterebilir.

## Asit–baz (basit)
pH ≈ 7 nötr (saf su idealinde). pH < 7 asidik, pH > 7 bazik eğilimlidir (sulü çözeltiler için yaygın ölçek).
""",
    )

    _w(
        "02_fizik_kimya",
        "003_enerji_hareket_basit.md",
        """
# Enerji ve hareket — temel

## Enerji türleri (örnek)
Kinetik (hareket), potansiyel (konum), ısı, elektrik, kimyasal, ışık.

## Korunum
Kapalı sistemlerde enerji yoktan var olmaz; biçim değiştirir (klasik fizik çerçevesi).

## Hız, ivme
Hız: konumun zamana göre değişimi.
İvme: hızın zamana göre değişimi.
Newton’un hareket yasaları günlük ölçekte iyi çalışır.

## Ses ve ışık
Ses için ortam gerekir (hava/su); uzay boşluğunda klasik ses yayılmaz.
Işık elektromanyetik dalgadır; boşlukta da yayılır.
""",
    )

    # --- 03 Biyoloji ---
    _w(
        "03_biyoloji_dunya",
        "001_hucre_fotosentez.md",
        """
# Hücre ve fotosentez

## Hücre
Canlıların temel yapı birimidir. Prokaryot (çekirdeksiz) ve ökaryot (çekirdekli) ayrımı vardır.
Bitki hücrelerinde genelde **hücre duvarı** ve **kloroplast** bulunur.

## Fotosentez
Yeşil bitkiler (ve bazı organizmalar) ışık enerjisiyle CO₂ ve sudan organik madde üretir;
yan ürün olarak **oksijen** salınır. Klorofil ışığı yakalamada önemlidir.

Basit ifade:
**karbondioksit + su + ışık → şeker (glikoz) + oksijen** (özet denklem).

## Solunum (kısa)
Hücreler enerji için organik maddeleri parçalar (hücresel solunum).
Fotosentez ile karıştırılmamalıdır: biri üretir, diğeri enerji açığa çıkarır.

## DNA (kısa)
Kalıtsal bilginin taşıyıcısıdır. Çift sarmal yapı popüler betimlemedir.
""",
    )

    _w(
        "03_biyoloji_dunya",
        "002_ekosistem_besin_zinciri.md",
        """
# Ekosistem ve besin zinciri

## Ekosistem
Canlılar + cansız çevre etkileşimi.
Üreticiler (bitkiler), tüketiciler (hayvanlar), ayrıştırıcılar (bakteri/mantar).

## Besin zinciri / ağı
Enerji üreticilerden üst tüketicilere akar; her basamakta enerji kaybı olur.
Gerçek sistemlerde zincirden çok **besin ağı** görülür.

## Biyoçeşitlilik
Tür çeşitliliği ekosistem dayanıklılığı için önemlidir.
Habitat kaybı, kirlilik ve aşırı avlanma tehdit oluşturabilir.

## Su döngüsü (kısa)
Buharlaşma → yoğuşma → yağış → yüzey/yeraltı akışı.
""",
    )

    _w(
        "03_biyoloji_dunya",
        "003_insan_vucudu_genel.md",
        """
# İnsan vücudu — genel bilgi (tıbbi tavsiye değil)

## Sistemler (özet)
Dolaşım, solunum, sindirim, sinir, iskelet-kas, boşaltım, bağışıklık, endokrin.

## Kalp ve kan
Kalp kanı pompalar; oksijen ve besin taşınır.
Bu metin teşhis/tedavi amaçlı değildir.

## Beyin
Merkezi sinir sisteminin kritik organıdır; düşünme, denge, duyusal işlem.

## Uyarı
Sağlık sorunu için hekime başvurulmalıdır. Rüzgar genel kültür verir; reçete yazmaz.
""",
    )

    # --- 04 Coğrafya ---
    _w(
        "04_cografya",
        "001_turkiye_cografyasi.md",
        """
# Türkiye coğrafyası — özet

## Konum
Türkiye; Asya ile Avrupa arasında, Anadolu ve Trakya topraklarında yer alır.
Boğazlar: İstanbul ve Çanakkale.

## Bölgeler (coğrafi)
Karadeniz, Marmara, Ege, Akdeniz, İç Anadolu, Doğu Anadolu, Güneydoğu Anadolu.

## Başkent ve büyük şehirler
Başkent **Ankara**’dır. İstanbul nüfus ve ekonomi açısından öne çıkar;
İzmir, Bursa, Antalya, Adana, Konya önemli merkezlerdendir.

## İklim çeşitliliği
Karadeniz’de yağışlı; İç Anadolu’da karasal; Akdeniz’de yazları sıcak-kurak özellikler yaygındır.
Doğu Anadolu’da kışlar sert olabilir.

## Dağlar ve ovalar
Kuzey Anadolu ve Toros dağ kuşakları belirgindir. Verimli ovalar tarım için önemlidir.

## Komşular (kara)
Gürcistan, Ermenistan, İran, Irak, Suriye, Yunanistan, Bulgaristan (ve deniz komşulukları).
""",
    )

    _w(
        "04_cografya",
        "002_kitalar_okyanuslar.md",
        """
# Kıtalar ve okyanuslar

## Kıtalar (yaygın liste)
Afrika, Antarktika, Asya, Avrupa, Kuzey Amerika, Güney Amerika, Avustralya/Okyanusya
(sınıflandırmada Okyanusya ayrıca anılabilir).

## Okyanuslar
Pasifik (en büyük), Atlantik, Hint, Güney (Antarktik), Arktik.

## Ekvator ve kutuplar
Ekvator Dünya’yı kuzey–güney yarımkürelere böler.
Kuzey Kutbu okyanus üzerindedir; Güney Kutbu Antarktika kıtasındadır.

## Saat dilimleri
Dünya 360° / 24 ≈ 15° dilimlerle saat dilimlerine ayrılır (politik sınırlar kaydırabilir).
Türkiye’de yaygın olarak **UTC+3** kullanılır.
""",
    )

    _w(
        "04_cografya",
        "003_harita_yon_olcek.md",
        """
# Harita, yön ve ölçek

## Ana yönler
Kuzey, güney, doğu, batı. Ara yönler: kuzeydoğu vb.

## Ölçek
Haritadaki uzunluğun gerçek uzunluğa oranıdır.
Büyük ölçek → daha ayrıntılı (küçük alan); küçük ölçek → geniş alan, az ayrıntı.

## Enlem–boylam
Enlem ekvatora göre kuzey/güney; boylam Greenwich’e göre doğu/batı konumunu verir.
Konum bu iki değerle tarif edilebilir.
""",
    )

    # --- 05 Tarih ---
    _w(
        "05_tarih",
        "001_osmanli_ozet.md",
        """
# Osmanlı İmparatorluğu — kısa özet

## Kuruluş
Geleneksel anlatıya göre Osmanlı Devleti **1299** civarında Söğüt/Domaniç yöresinde,
Osman Bey döneminde kurulmuştur. Kesin tarihler tarihçilikte tartışılabilir; okul özeti bu yöndedir.

## İstanbul’un fethi
**1453**’te II. Mehmed (Fatih) İstanbul’u fethetti; Doğu Roma (Bizans) başkenti düştü.
Bu olay dünya tarihinde bir dönüm noktası kabul edilir.

## Klasik dönem temaları
Merkezî yönetim, tımar sistemi, askerî teşkilat (yeniçeri vb.), mimari ve kültür üretimi.

## Son dönem ve yıkılış
19.–20. yüzyılda reformlar, savaşlar ve toprak kayıpları; I. Dünya Savaşı sonrası
imparatorluk çözülmüş, yerine Türkiye Cumhuriyeti kurulmuştur (1923).

## Not
Detaylı madde için Nebula/TARIH_VE_KULTUR rafları ve RAG indeksi kullanılabilir.
""",
    )

    _w(
        "05_tarih",
        "002_cumhuriyet_temel.md",
        """
# Türkiye Cumhuriyeti — temel bilgiler

## İlân
Türkiye Cumhuriyeti **29 Ekim 1923**’te ilân edilmiştir.
İlk cumhurbaşkanı **Mustafa Kemal Atatürk**’tür.

## Başkent
Ankara başkent yapılmıştır.

## Harf inkılabı (kısa)
Latin temelli Türk alfabesine geçiş, okur-yazarlık ve eğitimde önemli bir adımdır (1928).

## Çağdaşlaşma temaları
Eğitim, hukuk, kıyafet, kadın hakları gibi alanlarda köklü reformlar yapılmıştır.
Tarih yorumu çeşitlilik gösterebilir; bu metin okul düzeyinde özetdir.
""",
    )

    _w(
        "05_tarih",
        "003_dunya_tarihi_kilometre.md",
        """
# Dünya tarihi — kilometre taşları (çok kısa)

## Tarım devrimi
İnsanların yerleşik yaşama ve üretime geçişi uygarlıkların temelidir.

## Yazının icadı
Mezopotamya’da çivi yazısı gibi erken yazı sistemleri idare ve kültürü kalıcılaştırdı.

## Antik uygarlıklar
Mısır, Mezopotamya, Anadolu, Yunan, Roma, Çin, Hint uygarlıkları bilgi ve kurum bıraktı.

## Coğrafi keşifler / sanayi
Deniz yolları, küresel ticaret; sonra sanayi devrimi üretim ve kentleşmeyi değiştirdi.

## 20. yüzyıl
İki dünya savaşı, Soğuk Savaş, teknoloji sıçraması; sonuçları hâlâ tartışılır.
""",
    )

    # --- 06 Matematik ---
    _w(
        "06_matematik",
        "001_temel_islemler_oran.md",
        """
# Temel işlemler ve oran

## Dört işlem
Toplama, çıkarma, çarpma, bölme. İşlem önceliği: parantez → çarpma/bölme → toplama/çıkarma
(okul kuralı; bağlama göre notasyon değişebilir).

## Kesir ve yüzde
1/2 = 0,5 = %50. Yüzde, «yüzde bir» oranıdır.

## Oran–orantı
«a/b = c/d» ilişkisi günlük tarif, harita ölçeği, hız problemlerinde kullanılır.

## Ortalama
Aritmetik ortalama: toplam / adet.
""",
    )

    _w(
        "06_matematik",
        "002_birimler_ceviri.md",
        """
# Birimler ve çeviriler

## Uzunluk
1 km = 1000 m · 1 m = 100 cm · 1 cm = 10 mm

## Kütle
1 kg = 1000 g · 1 t = 1000 kg

## Hacim / sıvı
1 L = 1000 mL · 1 m³ = 1000 L

## Zaman
1 saat = 60 dakika = 3600 saniye · 1 gün = 24 saat

## Sıcaklık
Celsius–Kelvin: K ≈ °C + 273,15
""",
    )

    _w(
        "06_matematik",
        "003_geometri_kisa.md",
        """
# Geometri — kısa

## Açı
Tam tur 360°. Dik açı 90°.

## Üçgen
İç açılar toplamı 180°. Dik üçgende Pisagor: a² + b² = c² (hipotenüs c).

## Alan / çevre (örnek)
Dikdörtgen alan = a×b · çevre = 2(a+b)
Daire alan = πr² · çevre = 2πr

## π (pi)
Dairenin çevresinin çapına oranı; yaklaşık 3,14159.
""",
    )

    # --- 07 Dil ---
    _w(
        "07_dil_turkce",
        "001_yazim_sik_hatalar.md",
        """
# Türkçe yazım — sık karışanlar

## bir şey / hiçbir şey
Ayrı yazılır: **bir şey**, **hiçbir şey**, **her şey**.

## Ki bağlacı
«ki» bağlaçken ayrı: gördüm ki… · ek hâlinde bitişik: evdeki, benimki.

## De/da bağlacı
Bağlaçken ayrı ve sertleşme yok: evde değil → **ev de** güzel.
Bulunma hâli eki bitişik: evde.

## mı/mi soru eki
Ayrı yazılır: geldi mi?

## Not
Ayrıntılı madde için TDK rafı (`knowledge/tdk`) birincil kaynaktır.
""",
    )

    _w(
        "07_dil_turkce",
        "002_cumle_anlatim.md",
        """
# Cümle ve anlatım — pratik

## Net cümle
Özne–yüklem uyumu; gereksiz uzatmadan kaçınmak.
Rüzgar cevaplarında: önce net cevap, sonra gerekçe.

## Anlatım bozukluğu (örnek tipler)
Gereksiz sözcük, yanlış anlamda kelime, özne–yüklem uyumsuzluğu.

## Noktalama
Soru cümlesinde soru işareti; alıntılarda tırnak.
""",
    )

    # --- 08 Teknoloji ---
    _w(
        "08_teknoloji",
        "001_bilgisayar_temel.md",
        """
# Bilgisayar temelleri

## Donanım / yazılım
Donanım: fiziksel parçalar (işlemci, bellek, disk).
Yazılım: programlar ve işletim sistemi.

## CPU, RAM, depolama
CPU işlem yapar; RAM geçici hızlı bellek; SSD/HDD kalıcı depolama.

## Dosya ve klasör
Veri dosyalarda tutulur; klasörler düzenler.
Yedekleme veri kaybına karşı önemlidir.

## İnternet (kısa)
Ağların ağı. Tarayıcı ile web sayfaları; e-posta ve mesajlaşma uygulamaları.
""",
    )

    _w(
        "08_teknoloji",
        "002_yapay_zeka_kavram.md",
        """
# Yapay zekâ — kavramsal özet

## Ne yapar
Örüntü tanıma, dil üretme, öneri sistemleri, otomasyon.
**Rüzgar**: yerel hafıza + RAG + (isteğe bağlı) web + dil modeli ile asistanlık eder.

## Ne yapmaz
Kesin gerçeklik garantisi vermez; kaynak kontrolü gerekir.
Kişisel hafıza ile ansiklopedi karıştırılmamalıdır.

## Yerel / bulut
Yerel model (Ollama) gizlilik ve kota avantajı sağlar; bulut modeller güncel bilgi için yedek olabilir.

## İyi kullanım
Net soru sor; kaynak iste; canlı olaylarda web’i doğrula.
""",
    )

    _w(
        "08_teknoloji",
        "003_guvenlik_temel.md",
        """
# Temel dijital güvenlik

## Parola
Uzun ve benzersiz parolalar; mümkünse parola yöneticisi.
İki adımlı doğrulama (2FA) hesabı güçlendirir.

## Şüpheli bağlantı
Kimlik avı (phishing) e-posta/SMS ile gelir; linke acele tıklama.
Bilinmeyen ekleri açma.

## Güncelleme
İşletim sistemi ve uygulamaları güncel tutmak güvenlik açıklarını azaltır.

## Rüzgar notu
Rüzgar zararlı yazılım üretmez; güvenlik konusunda genel bilinç verir.
""",
    )

    # --- 09 Kültür ---
    _w(
        "09_kultur_yasam",
        "001_bayramlar_selamlasma.md",
        """
# Bayramlar ve selamlaşma — kültür notları

## Dinî bayramlar (Türkiye)
Ramazan Bayramı ve Kurban Bayramı toplumda ziyaret, ikram ve dayanışma ile yaşanır.

## Ulusal günler
29 Ekim Cumhuriyet Bayramı; 23 Nisan, 19 Mayıs, 30 Ağustos gibi günler resmî/toplumsal öneme sahiptir.

## Selamlaşma
«Merhaba», «selamün aleyküm» gibi ifadeler bağlama göre kullanılır.
Rüzgar Ümit abi’ye sıcak ve saygılı hitap eder.
""",
    )

    _w(
        "09_kultur_yasam",
        "002_misafirlik_ikram.md",
        """
# Misafirlik ve ikram kültürü

## Geleneksel izler
Çay, kahve, tatlı ikramı; ayakkabı çıkarma; büyüklere saygı — bölgeler arası çeşitlilik vardır.

## Ortak değer
Misafire yer açmak, sohbet, yardımlaşma.
Modern yaşamda biçimler değişse de öz benzer kalabilir.
""",
    )

    # --- 10 Hızlı referans SSS ---
    _w(
        "10_hizli_referans",
        "001_sss_fen_uzay.md",
        """
# Hızlı referans — fen ve uzay

## Dünyamız hangi galakside
Samanyolu galaksisindedir.

## Su kaç derecede kaynar
Standart atmosfer basıncında (1 atm) saf su yaklaşık **100 °C**’de kaynar. Basınç değişirse nokta değişir.

## Fotosentez nedir
Bitkilerin ışık enerjisiyle karbondioksit ve sudan besin üretmesi; oksijen açığa çıkar.

## Güneş bir yıldız mıdır
Evet. Güneş, Güneş Sisteminin merkezindeki bir yıldızdır.

## Ay neden bazen hilal görünür
Ay’ın Güneş’e göre konumu değiştikçe aydınlanan kısmı Dünya’dan farklı görünür (evreleme).

## Işık yılı nedir
Işığın bir yılda aldığı yol; bir **uzaklık** birimidir.
""",
    )

    _w(
        "10_hizli_referans",
        "002_sss_turkiye_tarih.md",
        """
# Hızlı referans — Türkiye ve tarih

## Türkiye'nin başkenti neresi
Ankara.

## Cumhuriyet ne zaman ilan edildi
29 Ekim 1923.

## İstanbul ne zaman fethedildi
1453 (Fatih Sultan Mehmet).

## Osmanlı ne zaman kuruldu
Geleneksel okul özetinde 1299 civarı (Osman Bey).

## Türkiye hangi kıtalarda yer alır
Anadolu Asya’da, Trakya Avrupa’dadır; iki kıta üzerindedir.
""",
    )

    _w(
        "10_hizli_referans",
        "003_sss_matematik_dil.md",
        """
# Hızlı referans — matematik ve dil

## Yüzde elli kaçtır
0,5 veya 1/2.

## Bir kilometre kaç metre
1000 metre.

## Pi yaklaşık kaçtır
Yaklaşık 3,14159.

## Hiçbir şey nasıl yazılır
Ayrı: **hiçbir şey**.

## Soru eki nasıl yazılır
Ayrı: geldi **mi**?
""",
    )

    _w(
        "10_hizli_referans",
        "004_sss_teknoloji.md",
        """
# Hızlı referans — teknoloji

## RAM ne işe yarar
Çalışan programların geçici olarak tutulduğu hızlı bellektir; kapanınca içeriği kaybolur.

## SSD ile HDD farkı (kısa)
SSD genelde daha hızlı ve sessizdir; HDD dönen disk kullanır.

## Rüzgar kimdir
Ümit & Gökçenur Haymana’nın ortak projesi olan yerel yapay zekâ asistanıdır.

## Yerel model ne demek
İnternete zorunlu bağlı olmadan bilgisayarında çalışan dil modeli (ör. Ollama).
""",
    )

    # Ek derin eserler — ince ayrıntı
    _w(
        "01_astronomi_uzay",
        "004_gezegen_karsilastirma.md",
        """
# Gezegen karşılaştırma notları

## Merkür
Gündüz–gece sıcaklık farkı büyüktür; atmosfer çok incedir.

## Venüs
Atmosfer basıncı çok yüksektir; yüzey insan yaşamına elverişli değildir.

## Dünya
Sıvı su, uygun sıcaklık aralığı, manyetik alan ve atmosfer yaşamı destekler.

## Mars
Keşif araçlarıyla incelenir; geçmişte su izleri tartışılır; kolonizasyon senaryoları varsayımsaldır.

## Gaz devleri
Jüpiter ve Satürn hidrojen–helyum ağırlıklıdır; katı «yer» yüzeyi Dünya gibi değildir.
""",
    )

    _w(
        "02_fizik_kimya",
        "004_elektrik_magnetizma_kisa.md",
        """
# Elektrik ve manyetizma — kısa

## Akım ve gerilim
Gerilim (volt) «itici güç»; akım (amper) yük akışı; direnç (ohm) akıma karşı koyma.
Basit ilişki (Ohm): V = I × R.

## Devre
Kapalı yol gerekir. Sigorta/aşırı akım koruması güvenlik içindir.

## Manyetizma
Mıknatısların kuzey–güney kutupları vardır. Dünya’nın manyetik alanı pusulayı etkiler;
uzay radyasyonuna karşı da kısmen kalkan görevi görür.
""",
    )

    _w(
        "03_biyoloji_dunya",
        "004_bitkiler_hayvanlar.md",
        """
# Bitkiler ve hayvanlar — sınıflama özeti

## Bitkiler
Üretici canlılardır (çoğu fotosentetik). Tohumlu / tohumsuz ayrımı okul düzeyinde öğretilir.

## Omurgalılar
Balıklar, amfibiler, sürüngenler, kuşlar, memeliler.

## Omurgasızlar
Böcekler, yumuşakçalar, solucanlar vb. tür çeşitliliğinin büyük kısmını oluşturur.

## Uyum
Canlılar çevrelerine uyum özellikleri geliştirir (doğal seçilim çerçevesi biyoloji dersinin konusudur).
""",
    )

    _w(
        "04_cografya",
        "004_iklim_tipleri.md",
        """
# İklim tipleri — pratik

## Akdeniz
Yazlar sıcak ve kurak, kışlar ılık ve yağışlı (klasik tanım).

## Karasal
Yaz–kış farkı belirgin; yağış az olabilir.

## Okyanusal / nemli ılıman
Yıl boyu daha dengeli sıcaklık, daha düzenli yağış.

## Muson
Mevsimlik rüzgâr ve yağış rejimleriyle karakterize bölgeler.

## Küresel ısınma notu
İnsan kaynaklı sera gazı artışı iklim sistemini etkiler; ayrıntı bilimsel raporlarla izlenir.
""",
    )

    _w(
        "05_tarih",
        "004_anadolu_uygarliklari_kisa.md",
        """
# Anadolu uygarlıkları — çok kısa

## Hititler
Anadolu’da güçlü bir bronz çağı / demir çağı devletidir; başkent Hattuşa.

## Urartu, Frig, Lidya
Doğu ve batı Anadolu’da etkili krallıklar; kültür ve ticaret izleri.

## Antik Yunan–Roma etkisi
Batı Anadolu kıyılarında polisler; sonra Roma ve Bizans katmanları.

## Selçuklu
Malazgirt (1071) sonrası Türkmen yerleşimi ve Anadolu Selçuklu Devleti kültürü.
""",
    )

    _w(
        "06_matematik",
        "004_hiz_yol_zaman.md",
        """
# Hız–yol–zaman

## Temel formül
yol = hız × zaman · hız = yol / zaman · zaman = yol / hız
Birimler tutarlı olmalı (km ve saat → km/s).

## Ortalama hız
Toplam yol / toplam zaman (anlık hızdan farklı olabilir).

## Pratik ipucu
Birimleri önce çevir; sonra işlemi yap.
""",
    )

    _w(
        "07_dil_turkce",
        "003_anlam_es_zit.md",
        """
# Anlam: eş / zıt / mecaz

## Eş anlamlı
Benzer anlam (büyük–iri gibi); nüans farkı olabilir.

## Zıt anlamlı
Karşıt anlam (sıcak–soğuk).

## Mecaz
Sözcüğün gerçek anlamı dışında kullanımı.
Rüzgar cevaplarında mecazı abartmamaya; netliğe öncelik verir.
""",
    )

    _w(
        "08_teknoloji",
        "004_ag_ve_url.md",
        """
# Ağ, URL ve DNS — kısa

## URL
Tarayıcı adres çubuğundaki adrestir (https://örnek.com/yol).

## DNS
İnsan okunur adı (örnek.com) sayısal IP’ye çevirir.

## HTTP / HTTPS
HTTPS şifreli bağlantıdır; özellikle giriş/ödeme sayfalarında tercih edilir.

## Gecikme (ping)
Paketin gidiş–dönüş süresi; düşük olması oyun/görüşmede iyidir.
""",
    )

    _w(
        "09_kultur_yasam",
        "003_yemek_cay_kulturu.md",
        """
# Çay ve sofra kültürü — not

## Çay
Türkiye’de günlük sohbet ve ikramın simgelerindendir; ince belli bardak yaygın imgedir.

## Sofra
Paylaşmak, birlikte yemek, selamlaşma — bölgesel çeşitlilikle yaşar.

## Coğrafi işaret (kavram)
Belirli yöreye özgü ürünlerin korunması fikridir (detay mevzuata bağlıdır).
""",
    )

    _w(
        "10_hizli_referans",
        "005_sss_gunluk.md",
        """
# Hızlı referans — günlük

## Bir gün kaç saattir
24 saat.

## Bir hafta kaç gündür
7 gün.

## Bir yıl yaklaşık kaç gündür
365 gün (artık yılda 366).

## Pusula nereyi gösterir
Manyetik kuzeyi gösterir (coğrafi kuzeyle küçük fark olabilir).

## Gökyüzü neden mavi görünür
Güneş ışığındaki kısa dalga boyları atmosferde saçılarak gökyüzünü mavi gösterir (Rayleigh saçılması özeti).
""",
    )

    kat = rebuild_katalog()
    print(
        f"DONE raflar={kat.get('raf_sayisi')} eser={kat.get('eser_sayisi')} "
        f"baslik={kat.get('toplam_baslik')} karakter={kat.get('toplam_karakter')}"
    )


if __name__ == "__main__":
    main()
