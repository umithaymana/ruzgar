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

**Denenecek cümle:** `aynı bağlantıları teke indir`

**13. iş bitti.** Kilitli klasör sayar, metin dosyası açar, ara başlık, http bağlantı, başlık rengi, klasördeki resim ve sayfa adı değişir. Dört masa: belgede bir kez değiştir, hücre sil, sütun topla, renkli çiz, slayt başlığı. Bak bu tariflerden yazı ve rengi önerebilir. Bağlantı, resim ve ad değiştirme yalnız sen söyleyince olur. `uygula` yine son bakışı bir kez çalıştırır.

**14. iş bitti.** Renk, ara başlık, bağlantı ve resim sayfa adı alır. Büyük başlık yoksa pencere başlığından görünür başlık boyanır. Aynı parça ikinci kez eklenmez. Zincir yarım kalırsa dosya eski hâline döner. `deneme dosyasını oku` metin dosyası yoksa sayfayı açar. Son bakış yeniden açılışta da durur.

**15. iş bitti.** `aynı bağlantıları teke indir`, `aynı ara başlıkları teke indir` ve `aynı resimleri teke indir` fazla kopyayı bırakır, farklı olanı silmez. Dosyanın kendisi silinmez. `başlığı mavi yap` başlığın yazısını «mavi» yapmaz, rengi boyar.

**Bilerek kapalı:** dosya silmek, modelin ürettiği kodu çalıştırmak, uygulama klasörüne yazmak, klasör dışına çıkmak, 32B/70B, telefon.

**Deneme klasörü:** `C:\Users\hayma\Desktop\ruzgar-el`
