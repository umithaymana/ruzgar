# RÜZGAR — Sohbet · Kütüphane · Ses · Mobil Büyük Plan

**Tarih:** 2026-11-17  
**Kaynak:** Mimar ile sohbet (Earth/sahne rotasından dönüş → motor analizi → kütüphane → Gemini/yerel → mobil/ses → gizli zararlar)  
**Durum:** **MÜHÜR** — 2026-11-17 F0–F9 dilimleri `[x]` · F6.3 5 dk telefon sahası = Mimar ölçümü  
**Dal notu:** `cursor/sohbet-akicilik-a-f` · güvenli liman 2026-11-12

---

## 0) Bu plan neyi çözmek için?

Rüzgar’ın kütüphanesi dolu, motorları var; ama senin yaşadığın şey şu:

- Kolay soruda cevap yok / geç geliyor / «öğretir misin?»
- Bazen çok güzel konuşuyor (çoğu zaman bulut), bazen saçmalıyor (çoğu zaman yerel + kapılar)
- Mobil sürekli ses: ses gitmiyor, cevap gelmiyor
- Yazarak sohbet yavaş; ses robot ve geriden
- «Rüzgar» hissi ile «Gemini konuşuyor» hissi karışıyor

Bu plan; sohbette konuşulan **artı / eksi / gizli zarar**ların tamamını kapsar. Sahne/Dünya Gezgini bu turda **ikinci planda** (bilinçli erteleme).

---

## 1) Hedef (senin dilinle)

| Alan | Hedef | Kısa ad |
|------|--------|---------|
| **İlim / güvenilir kaynak** | Kütüphane + hafızadan doğru, seri, güzel cevap; mümkün olduğunca yerelde | **A** |
| **Genel kültür / muhabbet** | Güzel ve doğal konuşsun; kimlik Rüzgar kalsın; hibrit (yerel + gerekirse bulut) | **B** |
| **Mobil + sürekli ses** | Konuş → duysun → cevap → (istenirse) sesli cevap; kesintisiz his | **S** |
| **Ses kalitesi** | Daha az robot, daha az gecikme, barge-in çalışır | **V** |

**Başarı cümlesi (tek satır):**  
«İlimde Rüzgar kendi raftından doğru konuşur; günlük sohbette doğal ve hızlıdır; telefonda sürekli sesli konuşulur; güzel cevap hissi yalnızca Gemini’ye bağlı değildir; kendine, motorlarına ve kütüphanesine dair sorularda abartmadan doğru konuşur.»

---

## 2) Bilinçli tercihler (kilit)

1. **İlim = A:** Kaynaklı yerel öncelik. Gemini ilimde «son yedek / stil cilası» olabilir; asıl bilgi kütüphaneden gelmeli.  
2. **Genel kültür = B hibrit:** Doğal cümle öncelik; provider şeffaf etiketlenebilir (ileride «yerel / bulut» rozeti).  
3. **Uydurma yasağı kalkmaz:** Filtreler «kör açılmaz»; akıllandırılır.  
4. **Ana yüz kilidi korunur:** `index.html` / kilitli CSS / ana `app.js` yüzü — sohbet UX’i mümkünse kilit dışı veya onaylı dilim.  
5. **Boot sırası dokunulmaz.**  
6. **Sahne/OSM/CameraRig:** Bu plan bitene veya Mimar «sahneye dön» deyene kadar yeni dilim yok (mevcut yarım işler commit kararı ayrı madde).  
7. **Serbest kod / 32B / halka açılış / %90 programlama:** P3 — bu planda yok.

---

## 3) Konuşulanların envanteri (hiçbir konu atlanmasın)

### 3.1 Motorlar — artı / eksi

| Motor | Artı | Eksi / zarar |
|-------|------|----------------|
| Video, programlama, tercüme | Hub + dispatch kuvvetli | Hub fazla çekerse sohbeti «atölye» yapar |
| Ses | API/profil var | STT ile dinleme ayrık; TTS robot/gecikme |
| Mimar | Hub erken | Okuma/bilim buraya map → ilim sohbeti bozulabilir |
| Hafıza | Hub’da | «Hatırla» vs motor sekmesi; yanlış kart pekişmesi |
| Hızır | Hub’da | Boot dışı; domain kısıtlı |
| Okuma / bilim | Arşiv bağlamı güçlü | Bağımsız hub hedefi yok (`okuma`/`bilim` → `mimar`) |
| Gelişim | Dosya var | Hub/UI/smoke yok (yetim) |
| Dinleme | Düşük seviye STT | Hub dışı; canlı yol ses API |
| Çekirdek orkestra | Çok motor şablonu | Hub ile uyumsuz envanter; prompt şişmesi |
| Ana Motor | Bilgi/RAG omurga | Motor dispatcher değil; sohbet kalitesi buraya bağlı |

### 3.2 Kütüphane / cevap — kök sebepler

1. İndeks **var** (~389k ana + Şamile ~8M) — «ulaşamama» değil  
2. Usable / lexik / anlam kapısı → LLM’siz «öğret»  
3. Şamile turda 1–3 kategori + süre bütçesi  
4. UMED süre vs Şamile arama çatışması  
5. top_k 2–4 → çok eser sentezi zayıf  
6. Grounding «yalnızca K*» + uydurma yasağı (doğru ama sentezi zorlar)

### 3.3 Gemini / yerel

- Güzel cevap ≈ sık bulut; saçma ≈ yerel + kapı + süre  
- Local-first emri var; ChatGPT-tarzı yollarda Gemini öne çıkabiliyor  
- Prompt şişmesi 8B’yi boğuyor → A hedefini sabote eder

### 3.4 Mobil / ses (S + V)

- Sürekli sohbet (VAD) var ama canlıda: ses gitmiyor / cevap yok  
- HTTPS mic / Wake Lock / STT / tur kopması  
- Working tree mobil değişiklikleri tutarsız (`with_tts`, history, STT fast)  
- TTS: Edge, first-byte gecikme, robot ton, geriden gelme

### 3.5 Gizli / sessiz zararlar (Mimar’ın kolay kaçırdığı)

1. Yanlışın **üçlü yazımı** (genel hafıza + learned + nebula)  
2. «Öğret» maskesinin süre/model hatasını gizlemesi  
3. Yeşil «hazır» ≠ ılık beyin (ilk tur cezası)  
4. Prompt + RAG yığını yerel modeli boğma  
5. Smoke yeşil ≠ canlı sohbet kalitesi  
6. Yüz kilidi → UX borcu birikimi  
7. LAN + CORS gevşek yüzey  
8. Public mode header spoof (gerçek auth değil)  
9. `PROJE_DURUMU` üst–alt çelişkisi → ajan sapması  
10. İndeks kilidi: «kaydedildi» ama sorguya düşmez

### 3.6 Diğer kod eksikleri (özet)

- Ollama/env kırılganlığı  
- İstemci timeout vs ağır bilgi turu  
- Şamile ürünleşme + ilim smoke CI dışı  
- Nebula/learned yığını belirsiz  
- Programlama ~%70 (bu planda derin değil)  
- Video V3+ (bu planda derin değil)  
- Commit’siz OSM/CameraRig/harita (karar maddesi)

---

## 4) Büyük resim — 9 ana faz

```
F0  Ölçüm & dürüst teşhis (kör yama yok)
F1  Sohbet borusu sağlığı (süre, warmup, miss maskesi, timeout)
F2  Kütüphane → cevap (İlim-A omurgası)
F3  Hafıza hijyeni (yanlışın pekişmesini kes)
F4  Doğal sohbet stili + hibrit B (prompt inceliği, provider politika)
F5  Motor kimlik & hub (okuma≠mimar, orkestra hizası, yetimler)
F6  Mobil + sürekli sesli sohbet (S)
F7  Ses kalitesi TTS/STT (V)
F8  Güvenlik yüzeyi + doküman tek gerçek + mühür
F9  Öz-bilgi & dürüst kapasite (Rüzgar kendini doğru tanıtsın)  ← SON FAZ
```

**Sıra mantığı:** Önce «ne kırık» görülür → sohbet ölmesin → ilim doğru aksın → hafıza zehiri kesilsin → dil güzelleşsin → motorlar karıştırmasın → mobil/ses → güvenlik/doküman → **en sonda Rüzgar’ın kendini / motorlarını / kütüphanesini doğru anlatması**.

Bağımlılık: F6, F2’nin tamamen bitmesini beklemez; ama F1 (süre/timeout) olmadan mobil “cevap yok” düzelmez. F3, F2 ile paralel başlayabilir (yazma kapısı).  
**F9**, F2+F5+F8’den beslenir (canlı envanter + motor kartları + tek gerçek); uygulama sırası **son dalga**.

---

## 5) Fazlar — detay (anlaşılır dil)

### F0 — Ölçüm ve dürüst teşhis  
**Amaç:** Kör yama yok. Her şikâyet için «hangi kapı / hangi süre / hangi provider» kaydı.

| Dilim | Ne yapılır | Senin göreceğin | Bitti sayılır | Durum |
|-------|------------|-----------------|---------------|--------|
| F0.1 | Canlı tur log kartı: hits sayısı, usable?, seçilen Şamile cats, süre ms, provider (ollama/gemini/miss), thin_pipe? | Bir «nedir» sorusunda neden öğret/gecikme olduğu net | 5 örnek tur kartı doldu | **[x]** `ruzgar_tur_teshis_f0` + `/api/tur-teshis` |
| F0.2 | Miss sınıfları ayrılır: `no_hits` / `filtered` / `timeout` / `weak_llm` / `budget` | «Öğret» artık tek torba değil | UI veya log’da sınıf görünür (en az log) | **[x]** classify + orch `miss_class` |
| F0.3 | Warmup durumu: RAG/Ollama/Whisper/TTS ılık mı? | İlk tur cezası ölçülür | Health’te «ılık/soğuk» ayrımı | **[x]** `brain_warmth` + `/api/tur-teshis/warmup` |
| F0.4 | Mobil sürekli: mic → STT → chat → TTS zincir kırılma noktası | Ses mi, STT mi, API mi net | 1 sayfalık kırılma haritası | **[x]** `docs/F0_MOBIL_SUREKLI_KIRILMA_HARITASI_2026-11-17.md` |

**Risk:** Log gürültüsü. **Kural:** Kullanıcıya spam yok; geliştirici/telemetri.  
**Smoke:** `python scripts/smoke_tur_teshis_f0.py`  
**Sıradaki:** F3.1–F3.2 (hafıza yazma kapısı) → F2.

---

### F1 — Sohbet borusu sağlığı (cevap gelsin)  
**Amaç:** «Cevap yok / geç / yanlış timeout» sınıfını kes.  
**Durum:** 2026-11-17 dilimler uygulandı (smoke + mobil timeout).

| Dilim | Ne | Neden | Ölçüt | Durum |
|-------|----|-------|-------|--------|
| F1.1 | UMED bütçe ↔ Şamile arama bütçesi hizala | 20 sn arama vs 15 sn tur çatışması | Bilgi turunda arama LLM’e yer bırakır | **[x]** `shamela_search_budget_sec` ≤ %40 tur |
| F1.2 | İstemci timeout (PC + mobil) bilgi turuna göre uzasın / dürüst hata | 60 sn kesilip «Ollama» sanılma | Hata metni gerçek sınıf | **[x]** mobil PWA ilim 55–120sn; PC zaten 180sn |
| F1.3 | Warmup bitmeden «hazır» iddiası yumuşasın | İlk tur rastgeleliği | Soğukta «ısınma» durumu | **[x]** mühür metni `brain_warmth` |
| F1.4 | Ollama/env sağlık: boş model, tray, `OLLAMA_MODELS` | A yolu sessiz düşmesin | Health: model listesi dolu / uyarı | **[x]** warmup’ta ollama_models / warn |
| F1.5 | Miss maskesi: timeout ≠ «öğret kütüphane» | Eğitim kuyruğu şişmesin | Timeout ayrı cümle veya sınıf | **[x]** `TIMEOUT_PHRASE` + öğret kuyruğu yok |

**Artı:** Sohbet yeniden «yaşıyor» hissi.  
**Eksi risk:** Bütçe artınca yavaşlık — F2 ile birlikte «hızlı yol / derin yol» ayrımı gerekir.  
**F3.2 kısmi:** timeout/miss `auto_learn` regex’e eklendi.

---

### F2 — Kütüphane → cevap (İlim-A omurgası)  
**Amaç:** Raftaki eser **cevaba** dönüşsün; uydurma kapıları yıkılmadan.

| Dilim | Ne | Anlaşılır açıklama | Ölçüt | Durum |
|-------|----|-------------------|-------|--------|
| F2.1b | **Niyet düzeltme** (yazım/STT/klavye) | Yanlış/eksik metinde «ne demek istedi» → RAG+LLM+guard | «foto senrez» doğru cevap | **[x]** `ruzgar_soru_yazim` v2 + pretreat + STT |
| F2.1 | Usable / lexik kapısını **akıllandır** | Arapça pasaj + Türkçe soru örtüşmez diye silme; anlam skoru + kategori | Kolay «nedir»de öğret oranı düşer | **[x]** soft usable + lexik yumuşatma |
| F2.2 | İki kademeli cevap | (1) hızlı yerel özet K* (2) süre varsa derin Şamile | İlk token / ilk cümle hızlanır | **[x]** extractive + `search_shamela_shards(deep=)` |
| F2.3 | top_k / çok eser sentez (kontrollü) | Aynı konuda 3–5 pasajdan **kaynaklı** kısa özet | «Birçok eserden» 3 pilot | **[x]** top_k=5 + F2.3 directive + extractive multi-K · `smoke_f2_3_cok_eser.py` |
| F2.4 | Şamile kategori seçimi iyileştir | Yanlış 3 kategori = boş his | Pilot ilim setinde cat isabeti | **[x]** fen skip + ipucu/siyer |
| F2.5 | İlim smoke seti + CI’ya bağlama | Akaid/hadis/tarih kısa batarya | Regresyon sessiz kaçmasın | **[x]** `smoke_f2_ilim_batarya` + provider cats |
| F2.6 | İlim provider politikası | Raftan usable → yerel; Gemini bilgi uydurmasın | K* baskın | **[x]** cloud-first varsayılan 0 + local-first zincir |

**Önemli:** Bu faz «Gemini’yi sil» demez; **ilimde bilginin sahibi kütüphane** olur.  
**Smoke:** `python scripts/smoke_f2_f3_kutuphane_hafiza.py`

---

### F3 — Hafıza hijyeni (zehiri kes)  
**Amaç:** Bir yanlış tur üç yere kazınmasın.

| Dilim | Ne | Zarar kestiği | Ölçüt | Durum |
|-------|----|---------------|-------|--------|
| F3.1 | Tek doğruluk kapısı | learned / genel hafıza / nebula yazmadan önce | Yanlış otomatik çoğalmaz | **[x]** `learn_trust_ok` |
| F3.2 | Miss/timeout turları **öğrenmeye yazılmaz** | «Öğret» ve timeout zehiri | auto_learn kapalı | **[x]** |
| F3.3 | Lale-benzeri çift kayıt temizliği (araç + politika) | Fuzzy yanlış kart | Örnek zehir kümesi azalır | **[x]** `hafiza_zehir_temiz_f33.py` (+apply) |
| F3.4 | «Kaydedildi ama indeks yok» | Öğrenme sonrası indeks kilidi dürüst durum | UI/log: indeks bekliyor | **[x]** `index_pending` orch + status |
| F3.5 | Nebula untracked yığını kararı | Ya ingest planı ya «dokunma» etiketi | Belirsizlik kalkar | **[x]** dokunma etiketi + inventory |

---

### F4 — Doğal sohbet stili + hibrit B  
**Amaç:** Günlük muhabbet doğal; ilim kaynaklı; Gemini «gizli kahraman» olmasın (veya bilinçli yedek olsun).

| Dilim | Ne | Ölçüt | Durum |
|-------|----|-------|--------|
| F4.1 | Prompt inceliği: genel sohbet kısa sistem; ilimde RAG+grounding ayrı paket | Yerel 8B selam/muhabette boğulmaz | **[x]** `pick_system(thin_pipe=)` |
| F4.2 | Provider rozeti (en az log; isteğe UI) | «Bu tur yerel / bulut / raftan» görünür — güven | **[x]** `provider_rozet` + F0 kart |
| F4.3 | Genel kültür hibrit sırası net | B: doğal öncelik; kota/yavaşlıkta yedek | **[x]** `RUZGAR_GENEL_HIBRIT_B` local-first |
| F4.4 | İlimde A sırası net | Raftan usable yoksa Gemini’ye «bilgi uydur» yok | **[x]** `ilim_no_cloud_invent` |
| F4.5 | Hub sohbet çalma azaltma | Bilgi/görüş → Ana Motor’da kal (mevcut kuralı sıkılaştır + smoke) | **[x]** stay geniş + smoke_f4 |

---

### F5 — Motor kimlik ve orkestra  
**Amaç:** Sohbet atölyeye kaymasın; yetimler netleşsin.

| Dilim | Ne | Ölçüt | Durum |
|-------|----|-------|--------|
| F5.1 | `okuma` / `ilim` hub hedefi ≠ görsel `mimar` (veya net alt-mod) | İlim sorusu mimar paneline zorla düşmez | **[x]** alias→genel; arşiv hub stay |
| F5.2 | `bilim` alias gözden geçir | Bilgi sohbeti mimar bağlamına gitmez | **[x]** `bilim`→`genel` |
| F5.3 | `ruzgar_cekirdegi` envanteri hub ile hizala | Mimar/hafıza/hızır bilinçli; gereksiz şişme kes | **[x]** seçimli bağlam + envanter |
| F5.4 | Gelişim: bağla **veya** «yardımcı — hub dışı» diye mühürle | Yetim belirsizliği bitsin | **[x]** `HUB_DISI_YARDIMCILAR` |
| F5.5 | Dinleme: Ses/STT alt katmanı olarak tekilleştir | Çift STT yüzeyi kalksın | **[x]** `/api/stt` → ses_stt_pipeline |
| F5.6 | JS hub + Python hub niyet smoke tek paket | Çift katman regresyonu | **[x]** `smoke_f5_cekirdek_hub_stt` |

**Not:** Programlama/video derin olgunluk (V3+, %90) bu fazda yok — sadece sohbeti bozan bağlantılar.

---

### F6 — Mobil + sürekli sesli sohbet (S)  
**Amaç:** Telefonda kesintisiz konuşma hissi.

| Dilim | Ne | Senin testin | Ölçüt | Durum |
|-------|----|--------------|-------|--------|
| F6.1 | Working tree mobil değişikliklerini gözden geçir / kararlı hale getir | ForceRestart sonrası aynı davranış | Tek canlı yol | **[x]** MediaRecorder→/api/stt→tur→TTS |
| F6.2 | Mic izin + HTTPS 8443 + Wake Lock doğrulama checklist | «Ses gitmiyor» ayrımı: izin/HTTPS/STT | Checklist yeşil | **[x]** `F6_MOBIL_…CHECKLIST` |
| F6.3 | Sürekli VAD: konuşma sonu → STT → tur → tekrar dinle | 5 dakikalık doğal konuşma | Kopma < X / tur | **[x]** VAD loop + checklist F6.3; **5 dk saha = Mimar telefon** |
| F6.4 | Tur sırasında barge-in (konuşunca TTS kes) | Kes-konuş | V4 ile hizalı mobil | **[x]** VAD→`stopAllSpeech` |
| F6.5 | Cevap yok: F0 kırılma noktası + F1 timeout mobil | Yazı ve ses aynı API sınıfı | Aynı hata dili | **[x]** timeout/miss metinleri |
| F6.6 | Kısa history / `with_tts` politikası | Sesli cevap isteniyorsa tutarlı | Belge + smoke | **[x]** with_tts=false + checklist |
| F6.7 | PC ↔ mobil parity (sohbet kritikleri) | Anayasa: mobil = masaüstü his | Sahne ACL ayrı (varsayılan kapalı kalabilir) | **[x]** STT/barge/with_tts sözleşme · `smoke_f6_pc_mobil_parity.py` |

**Önkoşul:** F1 (süre/timeout) ve F0.4 (kırılma haritası).

---

### F7 — Ses kalitesi (V)  
**Amaç:** Daha az robot, daha az geriden.

| Dilim | Ne | Ölçüt | Durum |
|-------|----|-------|--------|
| F7.1 | TTS first-byte ölçümü (PC + mobil) yeniden baseline | V0/V3 ile karşılaştır | **[x]** `/api/ses/f7-baseline` |
| F7.2 | Streaming / chunk oynatma cilası | Kelime kelime geriden his azalır | **[x]** mobil ilk cümle chunk |
| F7.3 | Profil seçimi (Alim/Edip/Asistan) + hız/ton | Kullanıcı «daha doğal» der | **[x]** f7-status profiller |
| F7.4 | İsteğe bağlı: klon/ses stüdyo yolu (varsa) yalnızca onaylı dilim | Robot hissi azalır | **[x]** auto→klon_onay |
| F7.5 | STT ısınma + hızlı yol (mobil sürekli) | «Ses → metin» gecikmesi düşer | **[x]** `/api/stt/warmup` |

**Not:** Mükemmel insan sesi bu planda garanti değil; **ölçülebilir gecikme + ton** hedef.

---

### F8 — Güvenlik, doküman, mühür  
**Amaç:** Sessiz zararlar ve ajan sapması bitsin.

| Dilim | Ne | Ölçüt | Durum |
|-------|----|-------|--------|
| F8.1 | LAN açıkken CORS/uyarı: ev ağı risk notu + sıkılaştırma seçeneği | Varsayılan bilinçli | **[x]** `F8_LAN_PUBLIC_UYARI` |
| F8.2 | Public mode: «bu auth değil» uyarısı; spoof notu | Dokümanda net | **[x]** aynı doc |
| F8.3 | `PROJE_DURUMU` arşiv/üst ayrımı temizle | Tek güncel «sırada» | **[x]** ŞİMDİ SIRADA + sahne/eski «kaldığımız yer» ARŞİV |
| F8.4 | Bu planın ilerleme işaretleri | Faz dilimleri `[x]/` | **[x]** F0–F9 işaretlendi |
| F8.5 | Canlı sohbet smoke (kısa e2e) ≠ sadece P/S/V/M | Selam + 2 ilim + 1 mobil ses | **[x]** `smoke_f8_5_canli_e2e.py` (8779; yoksa SKIP) |
| F8.6 | Commit kararı: OSM/CameraRig/harita yarım iş — bu plandan **ayır** veya «dondur» | Working tree kirliliği azalır | **[x]** doc: dondurulmuş |

---

### F9 — Öz-bilgi & dürüst kapasite (SON FAZ)  
**Amaç:** Rüzgar; «neler biliyorsun / neler yapabilirsin / zayıf-kuvvetli / kütüphanende ne var / motorların ne» gibi sorulara **uydurmadan, abartmadan, canlı veriden** cevap versin.  
**İlke:** Bu sorularda asıl kaynak = **öz-bilgi kartı + canlı envanter**; LLM yalnız Türkçe cümleyi düzeltebilir, içerik uyduramaz.

#### F9.0 — Soru kataloğu (Mimar + benzerleri; smoke listesi)

**A) Benlik / kapasite (senin sordukların)**  
- Neler biliyorsun?  
- Neler yapabilirsin? / Ne yapamazsın?  
- Az bildiğin şeyler neler? Çok bildiklerin neler?  
- İyi olduğun / zayıf kaldığın yanlar?  
- Hafızanda ne tür bilgiler / eserler var?  
- Kütüphanende ne var? (alan, cilt/kitap özeti, Şamile vs ana indeks)

**B) Motorlar (senin eklediğin)**  
- Motorların neler? Kaç motorun var?  
- Her motorun hüneri / ne işe yarar?  
- Güçlü yanları / zayıf yanları?  
- Hangisi ana motora bağlı, hangisi yetim / kısmi?  
- Hangi işi hangi motora sormalıyım?  
- «Okuma» ile «mimar» farkı nedir? (kimlik netliği)

**C) Senin unutmuş olabileceğin benzer sorgular (dahil)**  
- Sen kimsin? / Seni kim yaptı? / Ümit & Gökçenur?  
- Şu an hangi moddasın? (genel / ses / video / …)  
- Cevabı nereden buldun? (raftan / hafızadan / yerel model / bulut)  
- İnternete bakıyor musun? Ne zaman bakarsın?  
- Offline ne yapabilirsin?  
- Sesli / mobil / sürekli sohbet yapabilir misin? Nasıl?  
- Bana bir şey öğretebilir miyim? Nasıl hatırlarsın?  
- Bugün / bu oturumda ne öğrendin?  
- Hangi dilleri biliyorsun? (konuşma + tercüme)  
- Programlamada ne kadar iyisin? (dürüst tavan ~%70 notu)  
- Video / mimar / Hızır ne kadar hazır?  
- Limitlerin neler? (serbest kod yok, dosya silme yok, uydurma yasağı…)  
- Şu an ılık mısın / ısınıyor musun? (warmup)  
- Hangi port / nasıl bağlanırım? (mobil LAN / HTTPS mic — kısa)  
- Yardım / `?` — motor rehberi özeti  
- «Kendini tara» / «durumunu söyle» / «hub durum» / «orkestra özeti»

#### F9 dilimleri

| Dilim | Ne | Anlaşılır açıklama | Ölçüt | Durum |
|-------|----|-------------------|-------|--------|
| F9.1 | **Canlı envanter API / özet** | RAG chunk sayısı, Şamile cat/kitap özeti, alan listesi, learned/genel hafıza sayımı (abartısız) | «Kütüphanende ne var?» canlı sayıyla | **[x]** `/api/oz-bilgi` |
| F9.2 | **Dürüst kapasite kartı** (sabit + sürüm) | Yapabilir / yapamaz / kuvvetli / zayıf / tavan notları (programlama, video, ses, mobil…) | Abartı yok; kart sürümü güncel | **[x]** `KAPASITE_KARTI` |
| F9.3 | **Motor hüner kartları** | Her motor: ne işe yarar, hünerler, güçlü, zayıf, hub/boot durumu, örnek cümle | «Motorların neler?» karttan | **[x]** `MOTOR_KARTLARI` |
| F9.4 | **Öz-bilgi niyet kapısı** | Katalogdaki sorular → LLM’siz veya «kart + kısa cümle»; Gemini şişirmesin | Smoke: katalogdan ≥12 soru | **[x]** `smoke_f9` n=16 |
| F9.5 | Hub / `?` yardım ile hizala | `motor_kabiliyetleri` + ertelenmiş yardım planı içeriği sohbetle aynı gerçek | UI `?` ile sohbet çelişmez | **[x]** `/api/oz-bilgi` `hub_help` ← `ana-motor-hub.js` |
| F9.6 | Periyodik yenileme | İndeks/boot değişince envanter özeti tazelenir (stale kart yok) | Warmup sonrası özet güncel | **[x]** 45s TTL + force |
| F9.7 | Dürüst zayıflık cümleleri | Yetim motor, ~%70 programlama, ilim-A yarımken «her şeyi bilirim» yok | Zayıf yan sorusunda yalan yok | **[x]** smoke |

**Bağımlılık:** F5 (motor kimlik) + F2 (kütüphane gerçek sayılar) + F8.3 (doküman tek gerçek) besler; F9 onları **kullanıcı diline** çevirir.  
**Artı:** Güven — Rüzgar abartmaz, kendini bilir.  
**Risk:** Kart eski kalırsa yine yalan; F9.6 şart.  
**İlgili eski iş:** `RUZGAR_YARDIM_MOTOR_PLANI.md` (erteli `?` rehberi) — F9.5 ile sohbet + yardım tek kaynak.

---

## 6) Bilinçli ertelenenler (bu planda YOK)

- Dünya Gezgini C6+ / planet OSM yeni dilimler  
- Programlama %90 / Adım 5–6 derin KPI  
- Video V3–V6 süper editör  
- Hızır canlı pazar API  
- 32B/70B, Ollama’yı ağa açmak  
- Halka açılış kimlik+TLS ürünü  
- Ana yüz büyük redesign (kilit)

Bunlar artı değil; **şimdilik bilinçli kapalı** — sohbet/kütüphane/ses odaklı kalmak için.

---

## 7) Önerilen uygulama sırası (takvim değil, bağımlılık)

**Dalga 1 — Canlı tut (1–2 oturum):** F0 → F1 → F3.1–F3.2  
**Dalga 2 — İlim-A (2–4 oturum):** F2 (F2.1→F2.6) + F3 kalan  
**Dalga 3 — Dil & kimlik (1–2 oturum):** F4 + F5  
**Dalga 4 — Mobil/ses (2–3 oturum):** F6 → F7  
**Dalga 5 — Kapanış zemini:** F8 mühür + canlı e2e  
**Dalga 6 — Öz-bilgi (SON):** F9 (envanter + motor hüner + meta soru smoke) + (isteğe) commit

Her dilimde: **ölç → yama → smoke → canlı 3 soru → işaretle**.

---

## 8) Başarı tablosu (Mimar kontrol listesi)

| # | Senaryo | Beklenen |
|---|---------|----------|
| 1 | Kolay ilim «nedir» | Raftan kaynaklı kısa doğru cevap; öğret oranı düşük |
| 2 | Aynı konuda 2. soru | Takip doğal; kaynaklı |
| 3 | Genel muhabbet | Doğal, hızlı; hibrit OK |
| 4 | Provider | İlimde K* baskın; güzel cevap yalnız Gemini’ye bağlı değil |
| 5 | Yazı PC | Bilgi turu kesilmeden; dürüst hata |
| 6 | Mobil sürekli 5 dk | Ses gider, cevap gelir, yeniden dinler |
| 7 | Ses | First-byte iyileşir; barge-in |
| 8 | Yanlış öğretme | Timeout/miss learned’a yazılmaz |
| 9 | Soğuk açılış | «Isınıyor» bilinir; rastgele «bozuk» hissi azalır |
| 10 | Doküman | Tek sırada listesi; ajan sapması azalır |
| 11 | «Neler biliyorsun / yapabilirsin?» | Kart + canlı envanter; abartı yok |
| 12 | «Motorların neler / hüner / zayıf?» | Motor hüner kartlarından; hub gerçekliğiyle uyumlu |
| 13 | «Kütüphanende ne var?» | Canlı sayı/alan özeti; uydurma eser listesi yok |
| 14 | «Cevabı nereden buldun?» | Provider/raf/hafıza dürüst (en az log + sohbet cümlesi) |

---

## 9) Riskler

| Risk | Önlem |
|------|--------|
| Filtre gevşeyince uydurma | F2’de usable akıl + grounding; S0–S3 batarya |
| Süre artınca daha yavaş | İki kademe (hızlı/derin) |
| Mobil iOS/Android farkı | F6 checklist cihaz başına |
| Yüz kilidine sapma | UX işleri kilit dışı dosya veya onay |
| Çok büyük PR | Dilim dilim; her dilim smoke |
| Sahne yarım iş karışır | F8.6 dondur / ayrı dal |
| Öz-bilgi kartı bayatlar | F9.6 yenileme; smoke katalog |
| LLM kapasite şişirmesi | F9.4 niyet kapısı — içerik karttan |

---

## 10) Mimar kapısı

- Bu dosya **plan**. Uygulama için: «yap», «başla», «F1’den başla» vb.  
- «dur» → dilim ortasında dur; güvenli limana saygı.  
- «planını güncelle» → bu dosya + `PROJE_DURUMU` üst özet.  
- Commit ayrı emir.

---

## 11) Tek cümlelik özet

Önce **dürüst ölçüm ve cevap borusunu** düzelt; sonra **kütüphaneyi cevaba bağla (İlim-A)** ve **hafıza zehirini kes**; ardından **doğal hibrit sohbet + motor kimlik**; sonra **mobil sürekli ses ve TTS**; **güvenlik ve tek gerçek doküman**; en sonda **F9 öz-bilgi** — Rüzgar kendini, motorlarını, hüner/zayıf yanlarını ve kütüphane envanterini uydurmadan anlatsın. Sahne ve ağır atölye olgunluğu bu turun dışında.

---

## 12) Mühür notu (2026-11-17 cila)

- Plan dilimleri F0–F9 **kod + smoke** ile kapatıldı.
- **Açık saha (bilinçli):** F6.3 — 5 dk sürekli sohbet kopma oranı Mimar telefonunda.
- **Bilinçli dışı:** sahne/OSM, video süper editör, Hızır canlı API, programlama %90, halka açılış (§6).
- Commit ayrı Mimar emri.
