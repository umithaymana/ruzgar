# RÜZGAR — Kuzey Yıldızı Yol Haritası (kart panosu)

**Kayıt:** 2026-11-23 · Mimar `kaydet` · Kaynak: İkinci Denetim Raporu (düzeltilmiş vizyon)
**Başlangıç skoru:** 41/100 · **Hedef:** 365 günde 85+ · **Durum:** P0 — **K0 🟢 · K1 🟢 · D1 🟢** (3/23 yeşil, 2026-11-24) · K3 🟡 (TR→AR + BM25) · D2 🟡 (künye yolu) · sıradaki: **din 130 ölçüm** / **bge-m3 gece** / **K2**

---

## 0) Kuzey Yıldızı (Mimar, 2026-11-23)

Rüzgar, birden çok motordan oluşur; her motor kendi dalında **usta** olma yolundadır. Hepsinin başında **orkestra şefi Ana Motor** vardır.

1. **Orkestra:** Tüm motorlar Ana Motor'a bağlı, tek yerden yönetilir. Yoğun işte konuşma doğrudan ilgili motora geçer ve orada devam eder.
2. **Sahne:** Gösteri alanı + kanıt tahtası. Tek sözle çok fonksiyonlu akıllı tahta.
3. **Kütüphane:** Her alanda zengin (fizik, kimya, matematik, coğrafya, tarih, tıp, hukuk, felsefe, genel kültür…), sohbette **doğal** kullanılır. **ACİL.**
4. **Web:** Çok gelişmiş arama motoru; kütüphanede yoksa anında güncel cevap.
5. **Bulut:** Bağımlılık asgari; yerel öncelikli.
6. **Programlama ajanı:** Rüzgar'ın omurgası. Kendini geliştirir, eller serbest kod yazar, projeleri yönetir.
7. Diğer motorlar da kendi dalında uzman.

## 1) Çalışma sözleşmesi (bu panonun kuralları)

- **Kart durumu:** `⬜ Bekliyor` → `🟡 Yapılıyor` → `🟢 Yeşil`. Bir kart **yalnız** "Yeşil ölçütü" kanıtlanınca yeşile döner (test çıktısı / ölçüm / Mimar gözü).
- **Sıra:** Kartlar P0 → P1 → P2 → P3. Bağımlılık sütunu bağlayıcıdır. Mimar sırayı değiştirebilir.
- **Onay kapısı:** Her kartın koda başlaması için Mimar `yap`/`evet` der. Kart bitince kısa rapor + kanıt verilir; Mimar `yeşil` der ya da düzeltme ister.
- **Bozma yasağı:** Mühürlü arka (sohbet, kütüphane, ses V0–V5, mobil F0–F9) ve FROZEN kurallar (motor boot sırası, arayüz kilidi, anayasa, onay kapısı, cevap emri) açık Mimar `evet` olmadan değişmez. Arayüz kilidine dokunan kartlar (S-kartları) **dar izin** ister.
- **Anayasa:** Evrensel dünya, hardcode/demo yasağı, mobil eşitlik, raporlar tek kod bloğu.
- **Her kartta:** geri alma yolu (env bayrağı veya commit) + test + `PROJE_DURUMU.md` satırı.
- **Ölçmeden değiştirme yok:** K-kartlarında önce ölçüm (altın set), sonra değişiklik, sonra tekrar ölçüm.

## 2) Pano özeti

| Dalga | Kartlar | Yeşil | Hedef süre |
|-------|---------|-------|-----------|
| P0 — Doğallık ve güvenlik | 7 (D1 eklendi) | **3/7** (K0 🟢 · K1 🟢 · D1 🟢) | ilk 2 hafta |
| P1 — Temel | 9 (D2 eklendi) | 0/9 · K3 🟡 · D2 🟡 | 2–8 hafta |
| P2 — Derinlik | 5 | 0/5 | 2–4 ay |
| P3 — Temizlik | 2 | 0/2 | sürekli |
| **Toplam** | **23** | **3/23** | |

---

## 3) P0 — İlk 2 hafta

### K0 — Altın soru seti (ölçüm çizgisi) · 🟢 Yeşil (2026-11-24 · Mimar «doğrusu neyse yap» devriyle ajan kapattı)
- **Yeşil gerekçesi:** koşucu **tek komutla** çalışıyor (`python scripts/altin_set_kos.py kos --etiket X`, ardından `rapor` / `karsilastir`); başlangıç çizgisi dosyada (`ALTIN_SET_BASLANGIC_2026-11-23.md/.json` + `eval/altin_set/sonuclar/baslangic.jsonl`); doğallık el puanı **ajan puanıyla** (Mimar yerine, devriyle) yazıldı: **2,29 / 5** (n=24 — sayfada 30 değil 24 cevap var, 12 raf × 2). Mimar isterse puanların üzerine yazabilir.
- **Teslim (2026-11-23):** `ilim-assistant/eval/altin_set/sorular.json` (12 raf × 20 = 240 soru) · koşucu `ilim-assistant/scripts/altin_set_kos.py` (`kos` / `rapor` / `el-puani` / `karsilastir`; K1 ile `--bekle` ve `--ids` seçenekleri eklendi) · test `tests/test_altin_set_kosucu.py` (3 yeşil) · başlangıç raporu `ilim-assistant/docs/ALTIN_SET_BASLANGIC_2026-11-23.md` (+ `.json`) · el puanı sayfası `ilim-assistant/docs/ALTIN_SET_EL_PUANI_BASLANGIC_2026-11-23.md` (24 cevap, 1–5 puan, **Ajan puanı**).
- **Başlangıç çizgisi (web kapalı, 240 soru):** geçti **%35,4** · bulamadım **%6,7** · ort. kapsama **0,423** · ham döküm **104/240 (%43)** · «Ümit abi» ön eki **%65** · medyan 1,3 sn · P90 10,9 sn · 2 zaman aşımı.
- **Ana bulgu:** `kutuphane_extractive` yolu 104 soruyu karşıladı, **yalnız 5'i doğru** (%5). Cevaplar ilgisiz eserden geliyor (Pisagor → «Güneş Sistemi», en uzun nehir → «Birimler»). Bu yolun dışındakiler %58,8 geçti. Yani K1 (ham dökümü kapat → sentez) ilk büyük kazanç.

- **Neden:** Ölçülmeyen şey iyileştirilemez. Kütüphane ve orkestra kartlarının hepsi buna bağlı.
- **Yapılacak:** 12 raf × 20 soru (fizik, kimya, matematik, coğrafya, tarih, tıp, hukuk, felsefe, genel kültür, din, dil-edebiyat, teknoloji). Her soruda beklenen kaynak/doğru cevap notu. Otomatik koşucu: isabet (recall@5), kütüphanede yanıtlanma oranı, gecikme, ham-döküm sayısı. Mimar'a "doğallık" için 30 soruluk el puanı.
- **Bağımlılık:** yok
- **Yeşil ölçütü:** Koşucu tek komutla çalışır; bugünkü başlangıç çizgisi raporlanmış ve dosyaya kaydedilmiş.

### K1 — Ham pasaj dökümünü kapat, hep sentez · 🟢 Yeşil (2026-11-24 · KN-2)
- **Yapılacak:** `try_archive_rag_direct_reply` yolu varsayılan kapanır; kütüphane bulgusu "kanıt paketi" olarak sentez modeline gider; kullanıcıya doğal cevap + en çok 1–2 kısa kaynak anışı. Ham metin yalnız "kaynağı göster" isteğinde.
- **Bağımlılık:** K0 (önce ölçüm)
- **Yeşil ölçütü:** Altın sette ham-döküm sayısı 0; doğallık el puanı başlangıca göre artmış; mevcut testler yeşil. Geri alma: env bayrağı.
- **Kanıt (240 soru, web kapalı):** doğru **%35,4 → %77,9** · bulamadım %6,7 → %4,2 · ham döküm **104 → 0** · `kutuphane_extractive` 104 → 0 · doğallık (ajan puanı, aynı 24 soru) **2,29 → 3,50** · medyan 1,3 → 3,0 sn · P90 10,9 → 11,2 sn · hiçbir rafta gerileme yok (din 40 → 40). Ayrıntı: `docs/K1_KARSILASTIRMA_2026-11-24.md`. Testler: pytest **450 geçti** (429 + 21 yeni), node yeşil.
- **Nasıl:** kütüphane bağlamı yalnız soruyla sözcük örtüşen eserleri alır (kök neden: «nedir/nelerdir» kalıpları başlık eşleşmesine giriyordu) · zayıf/ilgisiz bulgu kanıt paketine girmez, zincir kanıtsız sürer · din/âlim alanında kanıt yoksa eski mühür (uydurma yok, «bulamadım») korunur · sentez talimatı: sade, doğal, kaynak cümle içinde 1–2 · ham metin yalnız açık «kaynağı göster / pasajı oku / aslını göster». Kod: `ruzgar_kutuphane_gorev.py`, `ruzgar_kutuphane.py`, `chat_core.py`, `ruzgar_arapca_lugat.py` (küçük).
- **Geri alma:** `RUZGAR_KUTUPHANE_HAM_DOKUM=1` (varsayılan 0) → eski ham döküm davranışı.
- **K1 dışı bulgular (sıradaki kartlara):** hazır kart/kestirme isabetsizliği (başarısızların yarısı → O1) · Gemini cevaplarının ~%20'si cümle ortasında kesiliyor (ayrı hata) · din rafı %40'ta (abdest/namaz/oruç/hac kütüphanede yok; Arapça kaynak + Türkçe soru → K3, D1/D2) · «X kimdir?» bekçisi doğru kaynaksız cevapları reddediyor · Gemini kotası dolunca 3B yerel model kalitesiz.

### K2 — Üslubu niyete bağla · ⬜ Bekliyor (KN-6) — *Mimar notu: din niyetinde varsayılan = âlim edası + herkesin anlayacağı açıklık (bkz. 6b); "sade öğretmen" yalnız din dışı*
- **Yapılacak:** Üslup profilleri: sohbet / sade öğretmen (varsayılan) / akademik / âlim. "Vakur ve edebî" yalnız din/âlim niyetinde. Kaynak cümle içinde doğal anılır.
- **Bağımlılık:** K0
- **Yeşil ölçütü:** Fizik/gündelik sorularda vaaz tonu yok (Mimar gözü + altın set); Kur'an/hadis/tefsirde vakur ton korunur (mevcut mühür testleri yeşil).

### O1 — Tek Niyet Kararı · ⬜ Bekliyor (OR-1, KN-5)
- **Yapılacak:** Her turda bir kez üretilen tek `Karar` kaydı: niyet · hedef motor · canlı bilgi ihtiyacı · kütüphane uygunluğu · üslup · zaman bütçesi · güven. Kestirmeler bu karara tabi olur. 6 yönlendirici ve 168 kestirme için envanter + kullanım ölçümü; ölü olanlar P3'te emekliye.
- **Bağımlılık:** K0
- **Yeşil ölçütü:** `prepare_turn` kararı tek yerden alır; aynı soru her koşuda aynı yolu izler (tekrarlanabilirlik testi); altın sette gerileme yok. Boot sırası değişmez.

### G1 — Güvenlik kapısı · ⬜ Bekliyor (önceki rapor K1/K2, PR-7)
- **Yapılacak:** Kimliksiz proje çalıştırma uçlarına kimlik; 8443 proxy yol filtresi; CORS daraltma; çalıştırma izolasyonu (kaynak/ağ sınırı).
- **Bağımlılık:** yok (paralel yürür)
- **Yeşil ölçütü:** Kimliksiz istek reddedilir (test); LAN'dan yetkisiz uç çağrısı 401/403; mobil PWA ve masaüstü normal çalışır.

### T1 — Çalışma alanı temizliği · ⬜ Bekliyor (PR-3)
- **Yapılacak:** Kök `projects/` altındaki ~1.148 test artığı klasör için **önce liste + Mimar onayı**, sonra arşive/silme. Testler geçici alana yazar ve kendini temizler. Gerçek projeler için proje kataloğu.
- **Bağımlılık:** yok
- **Yeşil ölçütü:** `projects/` yalnız gerçek projeleri içerir; test koşusu sonrası artık kalmaz (test ile doğrulanır).

---

## 4) P1 — 2–8 hafta

### K3 — Hibrit arama + reranker + sorgu yeniden yazma · 🟡 Yapılıyor (KN-3, KN-7 · 2026-11-24)
- **Yapılan:** TR→AR sözlük + Arapça sorgu + kelime sıralama · **BM25 hibrit** (aday havuzu Okapi, saf Python; `RUZGAR_K3_BM25=0` kapatır) · kapat `RUZGAR_K3_DIN_SORGU=0`.
- **Yardımcı onarım:** `embeddings.npy` onarımı · miss-hafıza kilidi · TDK-din sapması · altın set ayrı `device_id`.
- **Kanıt (din 130, web kapalı):** %36,2 → **%57,7** (`din_k3_tdkfix`); BM25 sonrası **yeniden ölçüm bekliyor**.
- **Kalan (yeşil için):** bge-m3 yan indeks (05:30 gece işi) · yerel reranker · din 130’da recall hedefi · gerileme yok.
- **Bağımlılık:** K0, K1
- **Yeşil ölçütü:** recall@5 başlangıca göre anlamlı artış (hedef ≥ +25 puan); gerileyen alan yok.

### K4 — ANN indeks + raf yönlendirme · ⬜ Bekliyor (KN-4)
- **Yapılacak:** Raf başına sıkıştırılmış ANN (HNSW/IVF-PQ) + mmap; önce raf seçimi sonra arama.
- **Bağımlılık:** K3
- **Yeşil ölçütü:** Kütüphane araması medyan < 1 sn; şamela aramasında zaman aşımı kesilmesi yok.

### K5 — Evrensel kütüphane: ilk 3 genel raf · ⬜ Bekliyor (bölüm 4)
- **Yapılacak:** Künye şeması (alan, dil, lisans, kaynak, tarih, güven). İlk raflar: genel kültür (Vikipedi TR), fen/matematik (OpenStax + yerel tercüme özeti), hukuk (mevzuat). **Her kaynak için lisans kontrolü ve Mimar onayı.**
- **Bağımlılık:** K3 (indeks hazır), Ok1
- **Yeşil ölçütü:** 3 rafın her biri altın sette hedef isabeti sağlar; künyesiz belge yok; lisans kaydı tam.

### Ok1 — Okuma motoru → Kütüphane Besleme Motoru · ⬜ Bekliyor
- **Yapılacak:** PDF/EPUB/OCR → temizleme → parçalama → künye → raf hattı.
- **Bağımlılık:** yok
- **Yeşil ölçütü:** Örnek 10 belge uçtan uca rafa girer, aranabilir ve sohbette doğal kullanılır.

### O2 — Motor Sözleşmesi + Odak Oturumu ("motorda kal") · ⬜ Bekliyor (OR-2, OR-3)
- **Yapılacak:** Sözleşme: yetenek listesi, niyet örnekleri, araçlar, girdi/çıktı, sağlık, usta karnesi. Odak oturumu: aynı motora 2–3 tur → odak o motorda; "ana motora dön" geri alır; bağlam paketi devri.
- **Bağımlılık:** O1
- **Yeşil ölçütü:** Programlama, ses, tercüme ile 3 senaryoda odak girip çıkar (test); boot sırası değişmez.

### W1 — Web: yerel meta arama + gövde çıkarıcı · ⬜ Bekliyor (WB-1, WB-2)
- **Yapılacak:** Yerel meta arama motoru (SearXNG sınıfı) + makale gövdesi çıkarıcı + yerel reranker; DDG yedek. Web metni "güvenilmeyen içerik" (araç tetikleyemez).
- **Bağımlılık:** O1
- **Yeşil ölçütü:** DDG kapalıyken web cevabı çalışır; 30 güncel soruluk testte kaynaklı cevap oranı hedefte; local-first sırası korunur.

### P-1 — Tek ajan çekirdeği + kod indeksi + kademeli zeka · ⬜ Bekliyor (PR-1, PR-4, PR-5)
- **Yapılacak:** Tek döngü: planla → düzenle → test et → düzelt (araçlar: oku/ara/düzenle/çalıştır/test/git; adım bütçesi, durma kuralları). Kendi kodu için sembol+semantik indeks. Kademeli zeka: rutin → yerel 7B coder, orta → yerel 14B, zor → bulut danışman (sayaçlı, onaylı).
- **Bağımlılık:** G1, T1
- **Yeşil ölçütü:** P-2 karnesinde yerel yolun geçme oranı hedefte; bulut çağrısı oranı raporlanır.

### P-2 — Usta karneleri (programlama + diğer motorlar) · ⬜ Bekliyor (OR-4, PR-8)
- **Yapılacak:** Programlama için 100 görevlik sabit sınav; diğer motorlar için 50–200 görevlik setler; haftalık puan + gerileme alarmı; yerel ve bulut ayrı ölçülür.
- **Bağımlılık:** K0 mantığı (koşucu iskeleti)
- **Yeşil ölçütü:** Her motorun karnesi tek komutla üretilir ve `docs/` altına tarihli yazılır.

---

## 5) P2 — 2–4 ay

### S1 — Sahne kanıt kartları · ⬜ Bekliyor (SH-1) — *dar izin gerekir*
- Cevabın kaynakları Sahne'de kart olarak görünür (kaynak, raf, alıntı, güven, "aç"). `ruzgar-masa.js/css` tarafında geliştirilir; kilitli dosyalara dokunulmaz.
- **Bağımlılık:** K1, K3
- **Yeşil ölçütü:** Kütüphane cevabında kartlar çıkar; masaüstü ve mobilde aynı; arayüz kilidi testi yeşil.

### S2 — Sahne Yönetmeni · ⬜ Bekliyor (SH-2) — *dar izin gerekir*
- İçerik türüne göre yerleşim: formül · diyagram · tablo/grafik · zaman çizelgesi · harita · slayt; yalnız izinli masa komutlarıyla.
- **Bağımlılık:** S1, O1
- **Yeşil ölçütü:** 6 içerik türünün her biri tek sözle sahnede doğru biçimde açılır.

### K6 — Öğrenen kütüphane + hafıza yazma kapısı · ⬜ Bekliyor (KN-8, önceki K3)
- Aday bilgi kuyruğu → çoklu kaynak doğrulama → (isteğe bağlı) Mimar onayı → sürümlü giriş + geri alma. Hafıza zehirlenmesine karşı yazma kapısı.
- **Bağımlılık:** W1, K5
- **Yeşil ölçütü:** Yanlış bilgi enjeksiyon testleri kapıdan geçemez; onaylı bilgi kütüphanede aranabilir.

### P-3 — Kendini geliştirme hattı · ⬜ Bekliyor (PR-6)
- Öneri → ayrı dal → tam test → fark özeti → Mimar onayı → birleştir → geri alma noktası. FROZEN kurallara dokunan değişiklik otomatik reddedilir.
- **Bağımlılık:** P-1, P-2
- **Yeşil ölçütü:** Ajan küçük bir iyileştirmeyi uçtan uca dalda getirir, testler yeşil, Mimar onayıyla birleşir.

### W2 — Haber ve güncellik katmanı · ⬜ Bekliyor (WB-3)
- RSS havuzu + olay akışı; "son 24 saat"; tek kaynaktan cevap yok.
- **Bağımlılık:** W1
- **Yeşil ölçütü:** Güncel haber sorularında ≥ 2 bağımsız kaynaklı cevap.

---

## 6) P3 — Sürekli

### X1 — Eski yönlendirici/kestirme emekliliği · ⬜ Bekliyor
- O1 ölçümüne göre kullanılmayanlar arşive; bayrak (848) envanteri.
- **Yeşil ölçütü:** Kestirme sayısı ölçülüp hedefe indirilmiş; testler yeşil.

### X2 — Kütüphane verisini depodan ayır + mobil sahne eşitliği (SH-3) · ⬜ Bekliyor
- Büyük veri artefakt deposuna; sahne bileşenleri mobil yerleşim profili.
- **Yeşil ölçütü:** Depo boyutu küçülmüş; mobilde sahne kartları çalışır.

---

## 6b) MİMAR ÖNCELİĞİ — DİN (2026-11-23 gece, Mimar'ın kendi sözleriyle)

> Din birinci önceliğim. Ehl-i Sünnet itikadı üzerine tam bir âlim edasıyla, istendiğinde kaynak verebilmeli. Bir değil birkaç eserden sentez yapabilmeli. Özellikle tasavvufa çok meyilliyim; Rüzgar bu konuları çok iyi bilmeli ve her insanın anlayabileceği açıklıkta cevap vermeli.

**Bu önceliğin plana etkisi (bağlayıcı):**
1. **Din her kartta "bozulmaması gereken ilk alan"dır.** K1/K2/K3/O1 değişiklikleri din rafında altın sette geriletemez; din cevabında ham döküm yok ama vakur âlim edası ve kaynak anışı korunur.
2. **K2 düzeltmesi:** Varsayılan "sade öğretmen" yalnız din dışı alanlar içindir. Din/itikat/tasavvuf niyetinde varsayılan = **âlim edası + herkesin anlayacağı açıklık** (terimi açar, hüküm-yorum-ayrımı yapar, kısa ve net).
3. **Uydurma kaynak yasağı:** Dinî cevapta verilen her kaynak (eser, bölüm, hadis, ayet) yalnız geri getirilen (retrieved) pasajdan gelir. Kütüphanede kaynak yoksa Rüzgar uydurmaz; "bu konuda elimdeki eserlerde net bulamadım" der.

> **Ek (Mimar, 2026-11-23 gece):** Şâmile'deki eserler çok kıymetli; özellikle yaratılıştan günümüze **İslâmî değerler ışığında yazılmış dünya tarihi** eserleri önemli. Hedef: İslâm'ın başından sonuna her konuya rahatlıkla ulaşıp cevap verebilmek. **Kur'ân-ı Kerîm, tefsir, akaid, hadis olmazsa olmaz.**

**Din kapsam matrisi ("olmazsa olmaz" çekirdek + geniş alan) — D1 ve D2 bu matrisle ölçülür/doldurulur:**
| Katman | Alan | Durum |
|--------|------|-------|
| Çekirdek (olmazsa olmaz) | Kur'ân-ı Kerîm (ayet/meal), Tefsir, Akaid (Eş'arî-Mâtürîdî), Hadis (Kütüb-i Sitte + şerhler) | Ölçülecek; eksik/zayıf alan raporlanacak |
| Geniş | Fıkıh (dört mezhep), Siyer, Kelam, Tasavvuf, Usûl, Ahlak | Ölçülecek |
| Tarih | Yaratılıştan günümüze İslâmî tarih eserleri (kıssa-i enbiyâ, siyer, hilafet, Osmanlı vb.) | Şâmile'de hangi eserler var envanteri çıkarılacak |
- **Önemli teknik not (kök neden):** Şâmile eserleri **Arapça**, sorular **Türkçe**. Mevcut arama modeli (MiniLM) Türkçe→Arapça eşleştirmede zayıf; baseline'daki «abdesti bozan şeyler → bulamadım» sonucunun asıl nedeni bu. Bu yüzden **K3 (çok dilli arama + TR→AR sorgu çevirisi + terim sözlüğü) din için kritik**: K3 önceliği din rafı açısından yükseltilmiştir (K1'den hemen sonra). Cevap Türkçe verilir; Arapça kaynak metin gerekirse tercüme motoruyla açıklanır, **kaynak künyesi Arapça orijinale işaret eder**.
- **Şâmile envanteri (D1'in ilk işi):** hangi eserler var, hangi katmanı kapsıyor, hangileri indekste, hangileri eksik → `docs/DIN_KAPSAM_ENVANTERI_*.md`. Eksikler Mimar'a **liste** olarak sunulur; kaynak ekleme/lisans kararı Mimar'dadır.

### D1 — Din altın seti: Ehl-i Sünnet itikadı + tasavvuf + kaynak verme ölçümü · 🟢 Yeşil (2026-11-24)
- **Yeşil gerekçesi:** koşucu `din-rapor` / `din-sade` canlı · din rafı **130 soru** (temel/akaid/fıkıh/hadis/tefsir/tasavvuf/siyer/kissa/tarih + «kaynak göster» varyantları) · başlangıç çizgisi `docs/DIN_RAPOR_DIN_BASLANGIC_2026-11-24.md` · uydurma kaynak denetleyicisi `scripts/din_olcut.py` · Şâmile envanteri `docs/DIN_KAPSAM_ENVANTERI_2026-11-24.md` · ikinci çizgi `docs/DIN_RAPOR_DIN_K3_TDKFIX_2026-11-24.md` (doğru %57,7).
- **Ölçüm notu (D2'ye aktarılır):** kaynak künye %0 · çoklu eser %0 · uydurma şüphe hâlâ var (19 soru) · fıkıh/kıssa zayıf. D1 ölçüm kartıdır; kalite yükseltme D2 + K3 kalanıdır.
- **Bağımlılık:** K0
- **Yeşil ölçütü:** Koşucu din rafını ayrı raporlar; başlangıç çizgisi kaydedilmiş; uydurma kaynak denetleyicisi çalışıyor.

### D2 — Âlim modu: çoklu eserden sentez + kaynak künyesi + sade açıklık · 🟡 Yapılıyor (P1 · 2026-11-24)
- **Yapılan:** eser çeşitlendirme (`cesitlendir_eser`) · kanıt künyesi (`kaynak_kunye`) · cevap sonu gerçek «Kaynak izi» (`cevap_kaynak_izi_uygula`) · idrak `clear()` bug’ı kapandı (hits/künye silinmiyor) · model uydurma izi kesilir · din/kütüphane casual hızlı yolu kapatılır.
- **Canlı kanıt:** «Cuma namazı nasıl kılınır? Kaynak göster» → hits 5 · usable · 4 farklı eser künyesi (uydurma yok).
- **Kalan (yeşil için):** din 130’da kaynak/çoklu eser oranı hedefe · uydurma 0 · fıkıh/kıssa zayıf sorular · tasavvuf eser listesi Mimar’a.
- **Bağımlılık:** K1, K3, D1
- **Yeşil ölçütü:** D1 din rafında doğru cevap, kaynak verme ve çoklu eser sentezi hedefte; uydurma kaynak 0; Kur'an/hadis/tefsir mühür testleri yeşil.

## 7) Mimar'ın vereceği kararlar (bekleyen)

| # | Karar | Seçenekler | Gereken kart |
|---|-------|-----------|--------------|
| D1 | Donanım yükseltmesi | 16–24 GB VRAM + 64 GB RAM (yerel 30B coder) / mevcut 8 GB ile hibrit | P-1 |
| D2 | Hızır motoru | Haber/piyasa gözcüsü olarak web motoruna katıl / dondur | W2 |
| D3 | İçerik kaynakları ve lisanslar | Vikipedi TR, OpenStax, mevzuat, MedlinePlus/PubMed özet — her biri ayrı onay | K5 |
| D4 | `projects/` temizliği | Önce liste, sonra arşiv/silme onayı | T1 |
| D5 | Bulut danışman bütçesi | Aylık üst sınır + onay şekli | P-1 |

## 8) 30 / 90 / 365 gün hedefleri

- **30 gün:** P0 yeşil; kütüphane cevaplarında 0 ham döküm; Tek Niyet Kararı canlı.
- **90 gün:** K3–K5, O2, W1, P-1, P-2, S1 yeşil; kütüphane araması < 1 sn; 3 genel raf dolu; yerelde çözülen tur ≥ %85.
- **365 gün:** 12 ana raf; öğrenen kütüphane; Sahne Yönetmeni; ajan dal+test+onayla kendini geliştirir; mobil eşitlik; (donanım yükselirse) yerel 30B coder.

## 9) Kart günlüğü

| Tarih | Kart | Olay |
|-------|------|------|
| 2026-11-23 | — | Pano kaydedildi. 21 kart, 0 yeşil. |
| 2026-11-23 | K0 | 🟡 Kanıt hazır: 240 soruluk set + koşucu + başlangıç çizgisi (geçti %35,4; ham döküm %43, bunların %5'i doğru). Mimar `yeşil` bekliyor. |
| 2026-11-24 | K0 | 🟢 Yeşil: koşucu tek komut + başlangıç çizgisi dosyada + doğallık ajan puanı 2,29/5 (Mimar devriyle; n=24). |
| 2026-11-24 | K1 | 🟢 Yeşil: 240 soruda doğru %35,4 → %77,9 · ham döküm 104 → 0 · bulamadım %6,7 → %4,2 · doğallık 2,29 → 3,50 · hiçbir rafta gerileme yok. Geri alma `RUZGAR_KUTUPHANE_HAM_DOKUM=1`. Sayaç 2/23. Sıradaki: K2. |
| 2026-11-24 | D1 | 🟢 Yeşil: din 130 soru + `din-rapor` + başlangıç çizgisi + uydurma denetleyici + Şâmile envanteri. Sayaç 3/23. |
| 2026-11-24 | K3 | 🟡 İlk dilim: TR→AR sözlük + Şâmile Arapça sorgu; din doğru %36,2 → %57,7 (`din_k3_tdkfix`). Kalan: BM25 / bge-m3 / reranker (indirme onayı). Yan onarım: `embeddings.npy` yeniden gömüldü; miss-hafıza kilidi; TDK-din sapması. |
| 2026-11-24 | K3 | Mimar yönetici izni + «05:30 indir». Görev `Ruzgar-BGE-M3-Gece` 25.11.2026 05:30: bge-m3 iner, gömme yan klasöre (`shamela_bge_m3`). Canlı MiniLM silinmez, arama kendiliğinden geçmez. |
| 2026-11-24 | D2 | 🟡 Künye yolu: idrak `clear()` bug kapandı; canlı kaynak izi gerçek künyeden. Test `test_d2_kunye_orch`. |
| 2026-11-24 | K3 | 🟡 BM25 hibrit (aday Okapi, indirme yok). Kapat `RUZGAR_K3_BM25=0`. Din 130 yeniden ölçüm sırada. |
