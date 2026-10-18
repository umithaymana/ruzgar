# Rüzgar sıra tahtası

**Onay:** 2026-10-17 — usta kapısı. İş, kilitli klasörde bilinen tariflere bölünür. Serbest kod, kendi kodu, model büyütme, halka açılış yok.

**Kıvam:** Düz cümle durur. Üstüne, çözülen iş sırayla yazılır ve geri okunur. Çözülemeyen parça dosyaya dokunmaz.

| Sıra | İş | Durum | Son test |
| --- | --- | --- | --- |
| 1 | Sıra tahtası | bitti | bu dosya |
| 2 | Metin kod kutusunda, html beyaz sayfada | bitti | `test_html_beyaz_sayfada_metin_kodda` |
| 3 | Düz cümle, yazınca geri oku | bitti | `test_duz_cumle_yazar_ve_geri_okur` |
| 4 | Sayfa, başlık, paragraf, buton, göster | bitti | `test_sayfa_baslik_paragraf_buton` |
| 5 | İş listesi, düşen adımda dur | bitti | `test_is_listesi_ve_dusen_adim` |
| 6 | Dört masa düz cümle, yüz aynı | bitti | `ruzgar-masa-soz.test.js` |
| 7 | Commit ve push | bitti | `1289384` |
| 8 | Usta kapısı: işi tarife böl | bitti | `test_usta_kabul_cumlesi` |
| 9 | Masa işi: dört masayı tek cümlede böl | bitti | `ruzgar-masa-soz.test.js` |
| 10 | Sayfada oku, bir kez değiştir | bitti | `test_yerine_bir_kez_ve_yoksa_durur` |
| 11 | Bak ve söyle, uygula bir kez | bitti | `test_bak_soyler_uygula_bir_kez` |
| 12 | Dört masa bak ve söyle | bitti | `test_masa_bak_tarif_ayrir_ve_yazmaz` |
| 13 | Güvenli tarif tavanı | bitti | `test_tavan_tarif_yazar_ve_tehlikeyi_yemez` |
| 14 | Sayfa adı, tekrar yok, yarım iş geri | bitti | `test_el_sayfa_renk_okuma_ve_geri` |
| 15 | Aynı kopyayı teke indir, renk kelimesi boyar | bitti | `test_teke_ve_renk_kelimesi` |
| 16 | Masa temizle, slayt metni | bitti | `ruzgar-masa-soz.test.js` |
| 17 | Çizimde üç sabit yer | bitti | `ruzgar-masa-soz.test.js` |
| 18 | Masa zinciri geri alır | bitti | `ruzgar-masa-soz.test.js` |
| 19 | Tuval gözü, dört renk üç yer | bitti | `ruzgar-masa-goz.test.js` |
| 20 | Python dosyasını oku, ne yaptığını söyle | bitti | `test_python_ne_yapiyor_calistirmaz` |
| 21 | Bir fonksiyonun imzasını söyle | bitti | `test_python_fonksiyon_imzasi` |
| 22 | Fonksiyonun döndürdüğü ifadeyi söyle | bitti | `test_python_fonksiyon_donusu` |
| 23 | Fonksiyonun kimi çağırdığını söyle | bitti | `test_python_fonksiyon_cagrisi` |
| 24 | Fonksiyonun satır aralığını söyle | bitti | `test_python_fonksiyon_yeri` |
| 25 | Fonksiyonun yazdığı adları söyle | bitti | `test_python_fonksiyon_yazdigi` |
| 26 | Fonksiyonun baktığı koşulu söyle | bitti | `test_python_fonksiyon_kosulu` |
| 27 | Sınıfın fonksiyon imzalarını söyle | bitti | `test_python_sinif_imzalari` |
| 28 | Dosyanın içe aldıklarını söyle | bitti | `test_python_ice_alma` |

**Denenecek cümle:** okuma eli bitti. Son cümle: `hesap.py neyi içe alıyor`

**13. iş bitti.** Kilitli klasör sayar, metin dosyası açar, ara başlık, http bağlantı, başlık rengi, klasördeki resim ve sayfa adı değişir. Dört masa: belgede bir kez değiştir, hücre sil, sütun topla, renkli çiz, slayt başlığı. Bak bu tariflerden yazı ve rengi önerebilir. Bağlantı, resim ve ad değiştirme yalnız sen söyleyince olur. `uygula` yine son bakışı bir kez çalıştırır.

**14. iş bitti.** Renk, ara başlık, bağlantı ve resim sayfa adı alır. Büyük başlık yoksa pencere başlığından görünür başlık boyanır. Aynı parça ikinci kez eklenmez. Zincir yarım kalırsa dosya eski hâline döner. `deneme dosyasını oku` metin dosyası yoksa sayfayı açar. Son bakış yeniden açılışta da durur.

**15. iş bitti.** `aynı bağlantıları teke indir`, `aynı ara başlıkları teke indir` ve `aynı resimleri teke indir` fazla kopyayı bırakır, farklı olanı silmez. Dosyanın kendisi silinmez. `başlığı mavi yap` başlığın yazısını «mavi» yapmaz, rengi boyar.

**16–18. iş bitti.** `belgeyi temizle`, `tabloyu temizle`, `çizimi temizle`, `sunumu temizle` masayı boşaltır, klasör dosyasına dokunmaz. `slaytın metnini bugün yap` açık slaytın yazısını değiştirir. `çizime ortaya mavi kutu çiz`, `çizime üste çizgi çiz`, `çizime alta daire çiz` sabit yerdedir. Masa işi yarıda kalırsa önceki parça geri alınır.

**19. iş bitti.** Çizime bakınca tuvalin pikseli okunur. Üst, orta, alt ve siyah, mavi, kırmızı, yeşil söylenir. Yeni şekil önerilmez. Klasördeki sayfa hâlâ yazı olarak okunur.

**20. iş bitti.** `hesap.py ne yapıyor` ve `hesap.py dosyasının ne yaptığını söyle` kilitli klasördeki dosyayı okur. Fonksiyon, sınıf ve içe alınan ad söylenir. Kod çalışmaz. `hesap.py çalıştır` reddedilir. Dosya aynı kalır.

**21. iş bitti.** `hesap.py içinde topla ne yapıyor` o fonksiyonun adını ve parametrelerini söyler. Gövdeyi çalıştırmaz. Fonksiyon yoksa dosyaya dokunmaz.

**22. iş bitti.** `hesap.py içinde topla ne döndürüyor` dönüş ifadesini metin olarak söyler. İfadeyi hesaplamaz. Dönüş yoksa bunu söyler. Dosya aynı kalır.

**23. iş bitti.** `hesap.py içinde topla kimi çağırıyor` çağrı adlarını söyler. Çağrıyı yapmaz. Çağrı yoksa bunu söyler. Dosya aynı kalır.

**24. iş bitti.** `hesap.py içinde topla nerede` satır aralığını söyler. Gövdeyi yazmaz. Dosya aynı kalır.

**25. iş bitti.** `hesap.py içinde topla neye yazıyor` değer verilen adları söyler. Değeri hesaplamaz. Yazılan yoksa bunu söyler. Dosya aynı kalır.

**26. iş bitti.** `hesap.py içinde topla neye bakıyor` koşul metnini söyler. Koşulu işletmez. Koşul yoksa bunu söyler. Dosya aynı kalır.

**27. iş bitti.** `hesap.py içinde Hesap sınıfı ne yapıyor` sınıftaki fonksiyon imzalarını söyler. Gövdeyi açmaz. Dosya aynı kalır.

**28. iş bitti.** `hesap.py neyi içe alıyor` içe alınan adları söyler. Modülü yüklemez. İçe alma yoksa bunu söyler. Dosya aynı kalır. Okuma eli burada biter.

**Bilerek kapalı:** dosya silmek, modelin ürettiği kodu çalıştırmak, uygulama klasörüne yazmak, klasör dışına çıkmak, 32B/70B, telefon.

**Deneme klasörü:** `C:\Users\hayma\Desktop\ruzgar-el`
