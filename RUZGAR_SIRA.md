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
| 29 | Yoğun dilleri rafa yaz | bitti | `faz20_programlama_dilleri_ingest.py` |
| 30 | Dil sorusu kartı okur | bitti | `test_yaygin_dil_karttan_okunur_ve_modele_birakilmaz` |
| 31 | Orta işi şablondan kur | bitti | `test_orta_is_sablondan_yazar_calistirmaz` |
| 32 | On dokuz dilin teferruatını rafa yaz | bitti | `test_dil_teferruati_ayri_karttan_okunur` |
| 33 | Nerede ve nasıl karttan okunur | bitti | `test_dil_nerede_ve_nasil_karttan_okunur` |
| 34 | İkinci on beş kart raftan okunur | bitti | `test_dil_ikinci_on_bes_kart_okunur` |
| 35 | Üçüncü on beş kart raftan okunur | bitti | `test_dil_ucuncu_on_bes_kart_okunur` |
| 36 | Python 3.14.5 standart kütüphane adları | bitti | `test_python_stdlib_modulleri_karttan_okunur` |
| 37 | Raf sorusu modelden önce kartı açar | bitti | `test_python_stdlib_modulleri_karttan_okunur` |
| 38 | Sohbet cilası | bitti | `test_sohbet_cilasi_kart_tekrar_ve_uydurma_sayiyi_birakir` |
| 39 | Dört masa sohbette | bitti | `test_masa_sohbeti_modelden_once_durur` |
| 40 | Orta işi söyle | bitti | `test_orta_isi_soyler_yazmaz_calistirmaz` |

**Denenecek cümle:** `orta işi söyle`

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

**29. iş bitti.** 2026 anketinde yüzde 10 ve üstü diller rafa yazıldı. HTML, CSS, JavaScript ve Python duruyordu. Ek: TypeScript, SQL, Bash, Java, C#, PowerShell, C++, C, Rust, PHP, Go, Kotlin. Eşlikçi: JSON, Markdown, SQLite. Her birinde dört not. Kod çalıştırılmaz.

**30. iş bitti.** `go nedir` ve `typescript ile ne yazılır` kartın metnini okur. Model serbest anlatmaz.

**31. iş bitti.** `orta iş yap` kilitli klasöre `orta/index.html`, `site.css`, `site.js` ve `arac.py` şablonunu yazar. Varsa üstüne yazmaz. Çalıştırmaz.

**32. iş bitti.** On dokuz dilde on bir teferruat kartı rafa yazıldı: sözdizimi, tür, atama, fonksiyon, koşul, döngü, veri, modül, hata, standart kütüphane, sınır. `python döngüsü nedir` o kartı okur.

**33. iş bitti.** `python nerede kullanılır` dil kartını, `python nasıl kullanılır` çalıştırma ve sınır kartını okur. `hangi dil` işin hangi dile gittiğini raftan dizer. Ajan bu cümleyi almaz. Dil çalıştırılmaz.

**34. iş bitti.** On dokuz adın her birine on beş kart daha yazıldı: örnek, adlandırma, yorum, girdi, metin, sayı, gezme, dosya okuma, hata örneği, karıştığı dil, ne zaman seçilir, ne zaman seçilmez, küçük iş, orta iş, el cümlesi. `python örneği nedir` ve `python ne zaman seçilir` o kartı açar. Otuz kart, dilin tamamı değildir. Kod çalıştırılmaz.

**35. iş bitti.** On dokuz adın her birine on beş kart daha yazıldı: işleç, karşılaştırma, mantık, boş değer, tür dönüşümü, metin biçimi, koleksiyon, kapsam, giriş noktası, çıktı, dosya yolu, uzantı, paket, yazım, el sınırı. `python işleci nedir` ve `python boş değeri nedir` o kartı açar. Kırk beş kart, dilin tamamı değildir. Kod çalıştırılmaz.

**36. iş bitti.** CPython 3.14.5 `stdlib_module_names.h` listesindeki 297 ad rafa yazıldı. 194 açık adın işi bir cümledir. 103 iç ad, kullanıcının doğrudan çağırmadığı modüldür. `python os modülü nedir` o kartı açar. `json nedir` JSON dilinde kalır. Alt modüller ve her işlev bu listede yoktur. Modül yüklenmez ve çalıştırılmaz.

**37. iş bitti.** `ne işe yarar` ve `ne yapar`, `nedir` ile aynı kartı açar. Programlama sohbetinde bu soru ajan ve modelden önce raftan okunur.

**38. iş bitti.** Cevaptan ses kartı, tekrar talimatı ve aynı paragraf çıkar. Kaynağı olmayan üç haneli özel okul sayısı yerine «rafta bulamadım» kalır. Kaynak adresi duran sayı durur.

**39. iş bitti.** `belgeye selam yaz`, `tabloda A1 e 10 yaz`, `çizime kutu çiz` ve `sunuma Hoş geldin slaytı ekle: bugün` ana motor ve programlama sohbetinde masaya gider. Model bu cümlede dosya yazmaz. Çözülemeyen parça masayı değiştirmez.

**40. iş bitti.** `orta işi söyle` kilitli klasördeki dört orta dosyayı okur ve ne olduklarını söyler. Dosya yoksa yazmaz. Varsa üstüne yazmaz. Çalıştırmaz.

**Bilerek kapalı:** dosya silmek, modelin ürettiği kodu çalıştırmak, uygulama klasörüne yazmak, klasör dışına çıkmak, 32B/70B, telefon.

**Deneme klasörü:** `C:\Users\hayma\Desktop\ruzgar-el`
