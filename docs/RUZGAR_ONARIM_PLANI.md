# Rüzgar Onarım Planı

**Tarih:** 20 Kasım 2026 (Europe/Istanbul)  
**Kaynak:** `RUZGAR_TAM_TESEKKULLU_ANALIZ_RAPORU.md` + main kod doğrulama (read-only)  
**Tür:** **PLAN** — bu belgede kod yok; uygulama ancak Mimar «yap» deyince başlar  
**Kod kökü:** `ruzgar-work/ilim-assistant` + `ruzgar-desktop`

---

## 0) Kısa özet

Rüzgar çökmüyor; sohbet yolu aşırı kalabalık. Bilgi soruları (~15+ anlık kütüphane kartı) RAG’e (yerel indeks arama) ve çok kaynaklı senteze hiç ulaşmadan tek kartla bitiyor. Selam/resume, `RUZGAR_SOHBET_ONCE=1` ve `has_prior_session=False` yüzünden oturumu «kaldığın yerden» açmıyor. Lexical filtre (soru–pasaj kelime örtüşmesi) bazen dolu indekste bile boş hit → yanlış «öğret / MISS» yolu. İlim turunda cloud-first (Gemini/Groq önce) umed local-first kuralını eziyor; UI hâlâ eski hata dili kullanıyor. Okuma/bilim modu `_MODE_ALIASES` ile mimar atölyesine düşüyor; Hafıza modunda çoğu turda 5’li çekirdek enjekte, `hafiza_motoru` bağlanmıyor. Planın hedefi: kırık bağları faz faz onarmak — yeni özellik yok, büyük yeniden yazım yok.

---

## 1) Öncelik sırası (fazlar)

### Faz 1 — Anlık kapı orkestrası (P0)

- **Amaç:** Bilgi/karşılaştırma/anlat sorularında anlık kart RAG’i baypas etmesin; tek politika, tek sıra.
- **Yapılacak işler:**
  1. `desktop_server.py` içindeki çift anlık blokları (aynı `try_*_reply` zinciri iki kez) tek blokta birleştir.
  2. Kütüphane anlık kapılarını tek registry’ye topla (ör. ortak liste / `_library_instant_or_none` çağrıları): akaid, hadis, siyer, tasavvuf, felsefe, psikoloji, edebiyat, ek raf, bilim, coğrafya, bilgisayar, teknoloji, usul, fıkıh, genel kütüphane, bilgi instant…
  3. `ruzgar_kutuphane_gorev.instant_covers_query` sıkılaştır: tek token = True gevşekliğini kaldır; karşılaştır / anlat / niyet gibi niyetlerde kart yasak → RAG zorunlu.
  4. Hadis çift kapıyı tek politikaya indir: `ruzgar_hadis_anlik.try_hadis_instant_reply` ile `ruzgar_hadis_kutuphane.try_hadis_reply` — biri bırakırsa diğeri erken tek kart basmasın; derin soruda ikisi de RAG’e bıraksın.
  5. Saf gündelik (hava, döviz, «nasılsın» dışı kısa kartlar) registry’de ayrı «izinli» kova — bilgi sorusuna karışmasın.
- **Doğrulama:**
  - «Niyet hadisi nedir?» → anlık kart yok; RAG/çok kaynak log’u görünür.
  - «Tirmizî ile Buhârî karşılaştır» → tek raf kartı yok; ≥2 eser veya sentez yolu.
  - «Hicret’i anlat» → anlat niyeti anlık kartı keser.
  - Saf «selam» / hava gibi kısa gündelik hâlâ anlık kalabilir (Faz 2 ile hizalanır).
- **Risk:** Çok sıkı kapı → bazı doğru tek-pasaj kartları yavaşlar (LLM/RAG’e düşer). Ölçülü tut; saf tanım kartlarını tamamen öldürme.
- **Bağımlılık:** Yok (ilk iş).

### Faz 2 — Selam ve oturum (P0)

- **Amaç:** Boş oturumda sahte «dün konuştuk» yok; dolu oturumda resume (kaldığın yerden) çalışsın; sohbet-once selamı öldürmesin.
- **Yapılacak işler:**
  1. `chat_fast_lane.py` ve `ana_motor_plan.maybe_gundelik_instant_reply`: `canonical_selam_reply(..., history=…, has_prior_session=…)` — sabit `False` kaldır.
  2. `ruzgar_sohbet_once`: saf selam + session resume için istisna (şu an `sohbet_once_enabled()` → gündelik anlık tamamen `None`).
  3. `ruzgar_tek_beyin_karsilama.try_session_resume_greeting` ile tek kapı (`ruzgar_sohbet_tek_kapi`) uyumlu kalsın; çift selam metni üretilmesin.
  4. Mevcut testleri genişlet: `tests/test_sohbet_tutarlilik.py` — history’li / history’siz.
- **Doğrulama:**
  - Boş history + «selam» → standart selam; «dün konuştuk» yok.
  - Dolu history + «selam» → resume / kaldığın yerden.
  - `RUZGAR_SOHBET_ONCE=1` açıkken de aynı davranış.
- **Risk:** Resume metni yanlış geçmişe bağlanırsa kullanıcıyı şaşırtır — history penceresini kısa ve net tut.
- **Bağımlılık:** Faz 1 önerilir (anlık sıra temizken selam kapısı netleşir); acilse bağımsız da alınabilir.

### Faz 3 — RAG çeşitlilik ve MISS (P0/P1)

- **Amaç:** İndekste veri varken yanlış boş hit / erken MISS olmasın; 3–5 eser hedefi `hits[:rag_k]` ile 2’ye düşmesin.
- **Yapılacak işler:**
  1. `chat_core.py`: diversify (`diversify_hits_by_book`) sonrası `hits = good_hits[:rag_k_clamped]` dilimini gözden geçir — çok kaynak turunda `rag_k` / `RUZGAR_COK_KAYNAK_RAG_TOP_K` ile dilim **öncesi** veya dilim eşiğini yükselt (pack’e 3–5 eser kalsın).
  2. `ruzgar_kutuphane_gorev.filter_hits_lexically`: Türkçe soru + Arapça pasaj için örtüşmeyi ölçülü gevşet (Arapça köprü / genişletilmiş sorgu); yüksek skorlu hit’i hemen silme.
  3. `hits_usable_for_kutuphane` eşiğini gözden geçir: usable false → hemen boşaltıp «öğret» yerine ikinci geçiş veya genişletilmiş sorgu.
  4. Varsayılan `RAG_TOP_K=2` ile genel/ilim boost (`RUZGAR_GENEL_RAG_TOP_K`, `RUZGAR_BILGI_RAG_TOP_K`) tutarlı kalsın; log’da `rag_k_clamped` görünsün.
- **Doğrulama:**
  - Bilinen dolu indeks + bilinen soru → hit sayısı ≥1; yanlış MISS yok.
  - Çok kaynak senaryosu → log’da ≥3 farklı eser (veya mevcut indeks kadar).
  - `tests/test_cok_kaynak_sentez.py` yeşil kalsın.
- **Risk:** Lexical aşırı gevşerse yanlış raf (usul ↔ siyer) geri gelir — peygamber/kimdir temizlik kurallarını koru.
- **Bağımlılık:** Faz 1 (RAG’e gerçekten ulaşılsın); Faz 2 şart değil.

### Faz 4 — Beyin + süre sözleşmesi (P0/P1)

- **Amaç:** İlim turunda hangi beyin önce çalışacak net olsun; UI ile sunucu süreleri çelişmesin; hata dili güncel olsun.
- **Yapılacak işler:**
  1. `RUZGAR_ILIM_RAG_CLOUD_FIRST` vs umed local-first: tek karar tablosu (env + kod yorumu); ilim/RAG turunda local-first kazanır veya cloud-first yalnız açık bayrakla.
  2. Prefetch süresini umed bütçesine dahil et (prefetch bitince bütçe sıfırlanmasın).
  3. UI 180s vs sunucu 15/38s uyumsuzluğunu tek sözleşmeye bağla (timeout mesajı + `desktop_server` / client).
  4. `ruzgar-desktop/app.js` → `classifyChatError`: «Gemini daemon» eski dilini local-first / umed / Ollama diline güncelle.
  5. Prompt yığını (ince borç): küçük Ollama için gereksiz orkestra/prompt eklerini kısaltmaya dair **küçük** dokunuş — büyük prompt yeniden yazımı yok.
- **Doğrulama:**
  - İlim sorusu log’unda önce local / sonra cloud sırası tabloya uyar.
  - Zaman aşımında UI mesajı güncel dil.
  - Prefetch’li turda bütçe aşımı ölçülür, sessizce «anlamsız timeout» olmaz.
- **Risk:** Cloud-first kapatan değişiklik Colab/uzak beyin kullanan kurulumları yavaşlatabilir — env ile geri açılabilir bırak.
- **Bağımlılık:** Faz 3 ile birlikte veya hemen sonra (RAG yolu açıkken beyin sırası anlamlı).

### Faz 5 — Motor routing (P0/P1)

- **Amaç:** Okuma ≠ mimar; Hafıza modunda doğru motor; boot ile çekirdek listesi çelişmesin.
- **Yapılacak işler:**
  1. `chat_core._MODE_ALIASES`: `"okuma": "mimar"` ve `"bilim": "mimar"` kaldır veya okuma→okuma / bilim→okuma (ilim arşivi); mimar yalnız görsel atölye.
  2. `prepare_turn` / orkestra: `m == "hafiza"` iken `hafiza_motoru.build_motor_context` enjekte; `_orkestra_context_for_turn` hafıza’da 5’li çekirdeği (ses/video/…) zorla basmasın.
  3. `motorlar/ruzgar_cekirdegi.build_core_context` ↔ `_boot_motorlar_anaonce`: mimar + hafıza ya çekirdeğe bilinçli eklenir ya da dokümanda «boot ısınır, orkestra çağırmaz» diye netleşir — kayma kalksın.
  4. Bilim/okuma isim kayması: boot=`okuma_motoru`, çekirdek=`bilim_motoru` — tek isim politikası (shim kalsın, kullanıcıya görünen ad net).
  5. `publish_shared`: ses / tercüme / mimar / okuma / hafıza için eksik yazımları en azından hafif köprü (programlama+video seviyesinde zorunlu değil; tutarlılık için minimal).
- **Doğrulama:**
  - UI «Okuma» → mimar atölyesi instant’ı yok; okuma/ilim yolu.
  - UI «Hafıza» → payload’da hafıza bağlamı; ses/video çekirdek bloğu yok (veya bayrakla).
  - Boot log’u ile çekirdek motor listesi dokümanda aynı hikâyeyi anlatır.
- **Risk:** Alias kaldırmak eski istemci/kısayolları kırabilir — bir sürüm `bilim`→`okuma` köprüsü bırak.
- **Bağımlılık:** Faz 1–2 sonrası tercih; sohbet kapıları temizken mod testi kolay.

### Faz 6 — Temizlik / borç (P2)

- **Amaç:** Ölü kod ve yanıltıcı doküman kullanıcıyı / çırakı şaşırtmasın.
- **Yapılacak işler:**
  1. `gelisim_motoru` / `dinleme_motoru`: import edilmiyorsa arşivle veya «yan / kullanılmıyor» etiketle; STT `stt_whisper` kaldığını dokümante et.
  2. Eski «5 motor» handoff / `run_desktop_api` docstring → güncel boot listesi.
  3. `/api/hafiza/genel-bak` + `app.js` `skipGenelBak=true`: ya UI’yi bağla ya endpoint’i bakıma al (ölü vaat kalmasın).
  4. Port 8777 kalıntılarını 8779 ile hizala (CSP / eski string — çoğu yerde 8779; kalanları temizle).
  5. UI «çırak günlüğü» (tercüme paneli) ≠ `docs/cirak_hafiza` — kısa kullanıcı/not ayrımı (etiket veya doküman cümlesi).
- **Doğrulama:** Grep ile ölü import yok; doküman boot listesiyle uyumlu; genel-bak ya çalışır ya «kapalı» der.
- **Risk:** Düşük — davranış değişikliği az; yanlış silinen shim’e dikkat.
- **Bağımlılık:** Faz 1–5 sonrası (önce kırıkları düzelt).

### Faz 7 — Canlı doğrulama

- **Amaç:** Onarımların birlikte çalıştığını Mimar’ın göreceği senaryolarla mühürle.
- **Yapılacak işler:**
  1. Smoke senaryoları (elle veya script):
     - Niyet hadisi  
     - Tirmizî karşılaştır  
     - Hicret anlat  
     - Selam boş oturum / dolu oturum  
  2. Log assert: anlık bypass yok (bilgi), RAG hit / diversify / sentez bayrakları, selam kapısı kaynağı.
  3. Regresyon: `tests/test_sohbet_tutarlilik.py`, `tests/test_cok_kaynak_sentez.py`, ilgili smoke script’ler.
  4. Kısa «usta doğrulama» notu (geçti/kaldı) — kod değil, kanıt listesi.
- **Doğrulama:** Dört senaryo + log; kırmızı varsa ilgili faza geri dönüş.
- **Risk:** Ortamda Şamile/indeks yoksa MISS doğru olabilir — «indeksli ortam» ile «indeksiz ortam» ayrı işaretlensin.
- **Bağımlılık:** Faz 1–5 (ve istenirse 6) bitmiş olmalı.

---

## 2) «yap» komutu ile nasıl ilerleriz

Mimar onayladıktan sonra:

1. **İlk «yap»** → varsayılan **Faz 1** (Anlık kapı orkestrası). En çok kullanıcıyı etkileyen kırık bağ bu.
2. Her faz bitince çırak kısa rapor verir: ne değişti, hangi dosyalar, smoke sonucu, risk kalanı.
3. Sonraki «yap» ile sıradaki faz (2, 3, …) alınır.
4. Birden fazla faz istenirse açık yazın, örneğin:  
   - «yap faz 1 ve 2»  
   - «yap faz 1–3»  
   - «yap faz 5 (motor routing)»
5. Faz atlamak mümkün ama gerekçeli olsun (örn. yalnız selam acilse «yap faz 2»).
6. Bu plan belgesi kod değildir; «yap» demeden commit/push/onarım yok.

---

## 3) YapılMAYACAKlar (kapsam dışı)

- Yeni motor, yeni UI ekranı, HIZIR ticareti, Şamile 13GB dolumu, Colab altyapısı.
- Sohbet yolunun sıfırdan yeniden yazımı; 119+ `try_*` / `maybe_*`’nin toptan silinmesi (registry + politika yeter).
- Büyük prompt/LLM modeli değiştirme; yeni vektör DB.
- `cursor/sohbet-akicilik-a-f` birikimini bu planda merge etmek.
- Uygulama sohbet hafızasını `docs/cirak_hafiza` ile birleştirmek (ayrı sistemler).
- Bu plan turunda: kod yazmak, dosya değiştirmek, commit/push.

---

## 4) Çırak notu

Onarım başlayınca çırak önce `docs/cirak_hafiza/CIRAK_HAFIZA_OKU.md` + `INDEX.md` okur (main’de mevcut; FROZEN kural). Benzer kayıtlar: çok-kaynak sentez, sohbet tutarlılık, main-al. Her faz sonrası `kayitlar/YYYY-MM-DD_<slug>.md` + `kayitlar.jsonl` + `INDEX.md` satırı düşülür — doğru/yanlış, tuzaklar, bir daha yapma, dokunulan dosyalar. UI’daki «çırak günlüğü» (tercüme) bu defter değildir; karıştırılmaz.

---

## Ek — Kaynak ↔ faz eşlemesi (hızlı bakış)

| Öncelik | Bulgu | Faz |
|---------|--------|-----|
| P0 | Anlık kartlar RAG baypas (~15 try_*); instant_covers gevşek; desktop çift blok; hadis çift kapı | 1 |
| P0 | SOHBET_ONCE selam/resume keser; has_prior_session=False | 2 |
| P0/P1 | Lexical aşırı katı; diversify sonrası hits[:rag_k]; usable → MISS | 3 |
| P0/P1 | ILIM_RAG_CLOUD_FIRST vs umed; prefetch/timeout; classifyChatError | 4 |
| P0/P1 | okuma/bilim→mimar alias; hafıza orkestra; çekirdek↔boot; publish_shared | 5 |
| P2 | gelisim/dinleme ölü; 5-motor doküman; genel-bak; port; isim karışıklığı | 6 |
| — | Canlı senaryolar + log | 7 |

*Son: Mimar «yap» demeden uygulama yok. Bu dosya yalnızca onarım planıdır.*

---

## Uygulama durumu (2026-11-20 — Mimar «yap» sonrası)

**Dal:** `cursor/ruzgar-onarim-fazlari-9eeb` (repo: `umithaymana/ruzgar`)  
**Doğrulama:** `/opt/cursor/artifacts/RUZGAR_ONARIM_DOGRULAMA.md`  
**Motor planı:** `/opt/cursor/artifacts/RUZGAR_MOTOR_ONARIM_PLANI.md`

| Faz | Durum | Commit (kısa) | Not |
|-----|--------|---------------|-----|
| 1 Anlık kapı | **yeşil** | `817c10f80` | tek registry; covers sıkı; hadis RAG |
| 2 Selam/oturum | **yeşil** | `c27f69b0f` | history’li selam; SOHBET_ONCE istisna |
| 3 RAG çeşitlilik | **yeşil** | `96e9b9389` | pack_k; lexical/usable; unit OK — canlı indeks ayrı |
| 4 Beyin+süre | **yeşil** | `05d0b3081` | cloud-first default off; prefetch bütçe |
| 5 Motor routing | **yeşil** | `f08c1c675` | okuma≠mimar; hafıza bağlamı |
| 6 Temizlik P2 | **yeşil** | `ae54db39f` | genel-bak bakım; 7-motor docstring |
| 7 Doğrulama | **yeşil** | 6360de98e | 37 pytest + 9 smoke senaryo |

PR açılmadı.
