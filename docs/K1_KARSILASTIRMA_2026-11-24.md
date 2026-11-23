# K1 karşılaştırma raporu — «Ham pasaj dökümünü kapat, hep sentez»

**Tarih:** 2026-11-24 (gece) · **Ölçüm:** Altın set, 240 soru, web kapalı · **Koşucu:** `ilim-assistant/scripts/altin_set_kos.py`
**Karar:** K1 **🟢 Yeşil** (ölçüt kanıtlandı; kalan sorunlar K1 dışı, aşağıda).

## 1) Önce / sonra

| Ölçüt | Başlangıç (K0) | K1 sonrası | Not |
|-------|---------------|-----------|-----|
| Doğru cevap | %35,4 | **%77,9** | hedef ≥ %55 ✔ |
| «Bulamadım» | %6,7 | **%4,2** | arttı değil, azaldı ✔ |
| Ham döküm (soru sayısı) | 104 | **0** | ✔ |
| `kutuphane_extractive` yolundan gelen cevap | 104 (5'i doğru) | **0** | ✔ |
| «Ümit abi» ön eki | %65,4 | %13,8 | doğallık |
| Medyan süre | 1,31 sn | 3,04 sn | LLM'li sentez olduğu için beklenen artış |
| P90 süre | 10,92 sn | 11,23 sn | süre bütçeleri içinde ✔ |
| Ort. kapsama | 0,423 | 0,815 | |
| Doğallık el puanı (ajan puanı, 24 cevap) | 2,29 / 5 | **3,50 / 5** | Mimar yerine ajan; aynı 24 soru kimliği |
| Hata | 0 | 0 | |

Sağlayıcı dağılımı: başlangıç `kutuphane_extractive` 104 · gemini 62 · hazır kart 59 · miss 10 · hizli 5 → K1 sonrası gemini 174 · hazır kart 58 · miss 8.
Sentez yoluna (Gemini) geçen 174 sorunun **%89,1'i doğru** (başlangıçta ham döküm yolu %4,8).

## 2) Raf bazında doğru % (başlangıç → K1)

| Raf | Başlangıç | K1 |
|-----|----------|----|
| fizik | 40 | 95 |
| tıp-biyoloji | 20 | 90 |
| tarih | 45 | 90 |
| genel kültür | 45 | 85 |
| hukuk | 30 | 85 |
| kimya | 40 | 85 |
| coğrafya | 45 | 80 |
| matematik | 30 | 80 |
| teknoloji | 35 | 80 |
| felsefe | 25 | 70 |
| dil-edebiyat | 30 | 55 |
| din | 40 | **40** (değişmedi) |

Hiçbir rafta gerileme yok. Tek tek sorularda: 108 soru düzeldi, 6 soru kötüleşti (2'si din «bulamadım», 4'ü Gemini'nin yarım kesilmesi / hazır kart).

## 3) Ne değişti (kök neden ve çözüm)

**Kök neden:** Kütüphane araması eserleri başlık/yol eşleşmesiyle buluyordu; «nedir / nelerdir» gibi soru kalıpları da eşleşmeye girdiği için hemen her soruya «Güneş Sistemi» çıkıyordu. Bulgu «kullanılamaz» sayılınca da sistem tam tersine bu ilgisiz metni **ham olarak** kullanıcıya döküyordu.

**K1 davranışı:**
1. Ham arşiv/kütüphane dökümü varsayılan **kapalı** (`try_archive_rag_direct_reply` ve «extractive» yolu).
2. Kütüphane bağlamı artık yalnız soruyla **sözcük örtüşmesi** olan eserleri kanıt paketine alır (Türkçe çekim ekine dayanıklı).
3. Kanıt yoksa/zayıfsa kanıt paketine girmez; zincir **kanıtsız** devam eder (Ollama → Gemini → Groq → web ikincil → «bulamadım» sırası aynı).
4. Din/âlim alanında kanıt yoksa eski mühür korunur: uydurmak yerine «bulamadım, öğret».
5. Sentez modeline kısa talimat: sade, doğal, öğretmen gibi; kaynağı cümle içinde an (en çok 1–2); pasajı yapıştırma; konuyu adıyla anan cümleyle başla.
6. Ham metin yalnız açık «kaynağı göster / pasajı oku / aslını göster» isteğinde döner.
7. Küçük ek düzeltme: «Kalp kaç odacıklıdır?» gibi bilgi soruları Arapça kök sözlüğü kartına düşmüyor.

**Geri alma:** `RUZGAR_KUTUPHANE_HAM_DOKUM=1` → eski davranış (ham döküm + süzgeçsiz bağlam + eski talimat). Varsayılan 0.

## 4) K1 turları (dürüst kayıt)

- **Tur 1 (ilk kod):** doğru %73,8 · ham 0 · bulamadım %5,4. Arızalar: (a) Gemini'yi bitirmeyen küçük yerel model (hizli) talimat metnini cevaba kopyaladı; (b) mevcut «bilgi doğrulama» bekçisi, kaynaksız ama doğru kısa cevapları (ör. «Sofra tuzu → sodyum klorür») «net yanıt veremedim» ile değiştirdi (4 → 7 soru).
- **Tur 2 (talimat cilası):** kaynak/raf sözcüklerini talimattan çıkarıp «konuyu adıyla anan cümleyle başla» eklendi → bekçi kaybı 7 → 3, sızıntı 2 → 0. 13 soruluk hedefli kontrol: 9/13 düzeldi. Sonra 240 sorunun tamamı yeniden koşuldu: **%77,9**.
- Tur 1 sonucu delil olarak saklı: `eval/altin_set/sonuclar/k1_sonrasi_tur1.jsonl`.

## 5) K1 dışında kalan, ölçümde görünen sorunlar (sıradaki kartlar için)

1. **Hazır kart / kestirme isabetsizliği (başarısızların yarısı: 26/53).** «Sıfat nedir?» → Akaid kartı; «Matris/Vektör nedir?» → aynı Lineer cebir kartı; «Halk edebiyatı nedir?», «Zekât kimlere verilir?», «İman esasları nelerdir?», «Vitir namazı nedir?» → Arapça kök sözlüğü kartı; «Descartes/Nietzsche…» → «Otomatik → İngilizce çeviri»; «Sinüs ve kosinüs nedir?» → terminal komutu onayı; «Medeni hukuk ile ceza hukuku…» → «Mekkî sûreler» kartı. → **O1 (Tek Niyet Kararı)** ve kestirme envanteri; kartların soruyla örtüşme doğrulaması.
2. **Gemini cevaplarının ~%20'si cümle ortasında kesiliyor** (başlangıçta da aynı oran; hedefli denemede tekrarlandı, doğrudan Gemini çağrısında görülmedi → sunucudaki akış/zincir katmanı). Doğallığı ve doğruluğu doğrudan düşürüyor. Ayrı hata kartı önerilir.
3. **Din rafı %40'ta kaldı** (8 soru «bulamadım»): abdest, namaz şartları, oruç, hac… yerel kütüphanede bulunamıyor; mühür gereği uydurulmuyor. → **K3/K5** (raf içeriği + arama).
4. **«X kimdir?» bekçisi** (`ruzgar_tek_beyin_bilgi_guard`): kaynaksız ama doğru yazar/şair cevaplarını «net yanıt veremedim» ile değiştiriyor (Nâzım Hikmet, Sait Faik, Wi-Fi). Bekçinin kaynak/web durumuyla ilişkilendirilmesi gerek.
5. **Gemini kuyruk gecikmesi:** 14 soru 38 sn'yi aştı (başlangıçta 8), en uzun ~93 sn; P90 etkilenmedi. Gemini kotası dolunca (45 dk soğuma) küçük yerel model (3B) devreye giriyor ve kalitesiz cevap üretiyor; ilk koşuda 10 soruyu etkiledi.

## 6) Doğrulama özeti

- Tam pytest (`ilim-assistant/tests`): **450 geçti** (önceki 429 + 21 yeni K1 testi) · node (`ruzgar-desktop/*.test.js`): geçti · ilgili duman testleri (kütüphane, lügat, süre/bulamadım, tür teşhisi): geçti.
- Sunucu yeniden başlatıldı: `build.rev = 2026-11-09-dalga-a-raf-v1`, `nebula_kitap: true` (health).
- Dokunulmayanlar: motor boot sırası, arayüz kilidi dosyaları, Ümit cevap emri sırası ve süre bütçeleri.
