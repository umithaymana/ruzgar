# RÜZGAR — oturum özeti (kalıcı)

**Son güncelleme:** 2026-10-07 — push `5fd9071` (ortak kaynak + tasavvuf 09)

Bu dosya sohbet sıfırlanınca bağlamı taşımak için tutulur. Kapatmadan önce «durumu güncelle» denmesi yeterli (çarpı ile kapanışta otomatik yazılamaz).

### Yarın kaldığımız yer (öncelik)

1. **Doğal sohbet P2** — oturum/thread cilası; `use_web=false` iken «web taraması / güven düşük» gürültüsünü azalt
2. **RAG indeks** — `ingest_cli --incremental` arka planda başladı (venv `ruzgar`; ~3096 batch embedding); bitince ForceRestart
3. İsteğe bağlı: Kimyâ-yı Saâdet daha dolu nüsha; Arapça Fütûh/Feth; İbnü'l-Arabî şerhleri

### 2026-10-07 — Tasavvuf (`09_ahlak_tasavvuf`) dolum

**Kaynak:** OpenITI (Gazâlî İhyâ/Kimyâ, İbnü'l-Arabî Fütûhât/Fusûs, Geylânî Gunye) + Internet Archive (Fütûhu'l-Gayb, Feth-i Rabbânî, Mesnevî, Divân, Mektûbât — çoğunlukla EN çeviri OCR)

- **10 eser** · ~**16.892** chunk · smoke `smoke_tasavvuf.py`
- Anlık: `ruzgar_tasavvuf_kutuphane.py` (siyer sonrası early path)
- Script: `faz9_tasavvuf_download.py` + `faz9_tasavvuf_ingest.py`
- Ortak kayıt: `KAYNAK_KAYIT.json` → `durum: hazir`
- **Politika:** Fetva yok · sayfa/cilt uydurma yasak

**Dene:** «tasavvuf nedir» · «ihya nedir» · «mesnevi nedir» · «kalbin hastaliklari nelerdir»

### 2026-10-07 — Ortak kütüphane / kaynak altyapısı

- `knowledge/ortak_kaynak/` — SEMA + ALANLAR (9 alan) + KAYNAK_KAYIT + web_cache yer tutucu
- Modül: `ruzgar_ortak_kaynak.py` · köprü: `ana_motor_kaynak.py` (güvenli atıf, uydurma yasak)
- Smoke: `python scripts/smoke_ortak_kaynak.py` · Kapat: `RUZGAR_ORTAK_KAYNAK=0`

### 2026-10-06 — Ollama + anlat/dost (push `aae43ae`)

- Yerel modeller zaten `D:\ÜMİT\PROGRAMLAR\Ollama\models` (~10.8 GB: `llama3.1:8b`, `llama3.2:3b`, `qwen2.5-coder:7b`)
- Ollama Unicode `ÜMİT` yolunu saymıyordu → `D:\OllamaModels` junction + `OLLAMA_MODELS` (`Ruzgar.ps1` / `RuzgarMasaustuBaslat.ps1`)
- «hicreti daha açık anlat» dost şeridine kaçmasın: `ruzgar_tek_beyin` + `ruzgar_dogal_sohbet_faz91` (sohbet daveti hariç)
- Canlı: `instant_gundelik=False`, beyin `denge/llama3.1:8b`, `RUZGAR_OLLAMA_ONLY=1`

### 2026-10-06 — Doğal sohbet P0+P1

- P0: video panel tuzağı kapandı; lookup anlık / anlat→LLM ayrımı
- P1: kütüphane ipucu LLM’e enjekte; session echo ilim/sohbeti ezmez; devam cümleleri genişledi
- LLM yokken «anlat» için yumuşak kütüphane özeti (`soft_library_synth_fallback`)
- Smoke: `smoke_dogal_sohbet_p0.py` · Kapat: `RUZGAR_ANLIK_NIYET_GATE=0`

### 2026-10-06 — Siyer (`08_siyer`)

**Kaynak:** OpenITI (İbn Hişâm, Vâkıdî, İbn Sa'd, Taberî, İbn Kesîr)

- **9 eser** · ~**33.913** chunk · smoke `smoke_siyer.py` **8/8**
- Asıl: İbn Hişâm Sîre · Megâzî: Vâkıdî · Tabakât: İbn Sa'd · Tarih: Taberî · Muteber: Fusûl + Bidâye (İbn Kesîr) · Tercüme: Zehebî Siyer · Erken: Ridde, Fütûhu'ş-Şâm
- Anlık: `ruzgar_siyer_kutuphane.py` (hadis sonrası early path)
- **Politika:** Fetva yok

**Dene:** «siyer nedir» · «hicret nedir» · «bedir nedir» · «ibn hisham nedir»

**Sonraki kütüphane:** `09_ahlak_tasavvuf`

### 2026-10-06 — Usûl-i fıkıh (`07_usul_fikh`)

**Kaynak:** OpenITI (Cüveynî, Gazzâlî, Pezdevî, Serahsî, Âmidî, Beyzâvî, Zerkeşî)

- **10 eser** · ~**7.102** chunk · smoke `smoke_usul_fikh.py` **8/8**
- Matın: Varakât, Minhâcü'l-vusûl · Muteber: Burhân, Mustasfâ, Menhûl, Pezdevî, Serahsî, İhkâm, Bahru'l-muhît · Kavâid: Mensûr
- Anlık: `ruzgar_usul_fikh_kutuphane.py` (fıkıh sonrası early path)
- **Politika:** Fetva yok

**Dene:** «usul fıkıh nedir» · «kıyas nedir» · «varakat nedir» · «mustasfa nedir»

### 2026-10-06 — Fıkıh (`06_fikh`) 4 mezhep + ilmihal matınları · push `1d3f406` (+ RAG fix `10d3291`)

**Kaynak:** arabic-digital-humanities/fiqh (OpenITI / Şâmile kökenli Arapça)

| Mezhep | Matın / ilmihal | Muteber |
|--------|-----------------|---------|
| Hanefî | Kudûrî, İhtiyâr, Lübâb | Bedâi', Reddü'l-muhtâr |
| Mâlikî | Kâfî, Düsûkî | Muvatta', Zehîra, Tâc |
| Şâfiî | Minhâc, Kifâyetü'l-ahyâr | Ümm, Tuhfe, Nihâye |
| Hanbelî | Hırakî, Ravzü'l-murbi' | Muğnî, Müntehâ |

- **19 eser** · ~**49.514** metin parçası · smoke `smoke_fikh.py` **8/8**
- Anlık: `ruzgar_fikh_kutuphane.py` (hadis sonrası early path)
- TR: kavramlar + ilmihal rehberi + mezhep tarihçesi
- Script: `faz6_fikh_download.py` + `faz6_fikh_ingest.py`
- **Politika:** Fetva yok

**Dene:** «fıkıh nedir» · «hanefi mezhebi» · «ilmihal nedir» · «minhac nedir» · «kuduri nedir»

**Dönünce sırada:** alan süzgeci · akaid Luma OCR · veya usûl-i fıkıh genişletme

### 2026-10-06 — Hadis tamam (matın + usûl + tarihçe) · push OK

**Commit:** `bf2b1f4` → `origin/main`  
**Canlı:** `.\Ruzgar.ps1 -ForceRestart` (RAG chunks yerelde; `python -m ilim_assistant.ingest_cli --incremental`)

**Kutüb-i Sitte:** 6 raf · **34.153** hadis  
**Usûl:** İbnü's-Salâh (437 paket) · Nuhbe · Beykûniyye  
**TR:** tedvin tarihçesi · muhaddisler · 28 kavram · smoke **10/10**  
**RAG:** ~72.302 parça (chunks.jsonl gitignore — GitHub 100MB)

### 2026-10-06 — Hadis (`05_hadis`) Kutüb-i Sitte

**Bitti:**
- Kaynak: `fawazahmed0/hadith-api@1` Arapça matın (6 eser ayrı raf)
- Toplam **34.153** hadis · `kutub_i_sitte/{buhari,muslim,ebu_davud,tirmizi,nesai,ibn_mace}/`
- Anlık: `ruzgar_hadis_kutuphane.py` + early path (akaid sonrası)
- Kavramlar + usûl/tarihçe · smoke `scripts/smoke_hadis.py` **10/10**
- İncegest: `faz5_hadis_kutub_sitte_ingest.py` + `faz5b_hadis_usul_tarih_ingest.py`
- RAG: ~72.302 parça

**Usûl RAG güncelleme:** ibn_salah/nukhba/bayquniyya + TR

**Dene:** «hadis nedir» · «kutub-i sitte nedir» · «buhari 1» · «muslim 1» · «tirmizi 1»

**Akaid:** çekirdek tamam; ara verildi (Luma OCR / bekleyen_tr sonra).

### 2026-10-06 — Neredeyiz (önceki çıkış)

**Bitti (çekirdek):**
1. **Akaid** `04_akaid` — Arapça corpus + 18 TR kavram + anlık yol + RAG · smoke 8/8
2. **Sohbet karıştırma kökleri** — fuzzy özne, kimlik anlık, geçmiş `sordum`, Kur’an meta/aşır, sure adı sınırı
3. **Sistematik anlam kilidi** `ruzgar_anlam_koruma.py` — fuzzy + oturum yankısı
4. **RAG/LLM koruma:** chunk içerik süzgeci · `RAG_SCORE_MIN` varsayılan **0.32** · cevap `guard_assistant_reply` · otomatik öğrenme zehir kilidi · `smoke_anlam_koruma` 8/8

**Canlı:** `.\Ruzgar.ps1 -ForceRestart`

### Sonraki adım planı
1. Alan süzgeci (akaid/tefsir/hadis raftı)
2. Smoke setini CI’ya bağla (`smoke_hadis` + akaid + anlam)
3. el-Luma‘ OCR (akaid)
4. İsteğe bağlı: Muvatta / Müsned Ahmed (Sitte dışı)

### 2026-10-06 — Sohbet yanlış cevap kökleri (düzeltildi)

**Bulunan hatalar (Mimar sohbet kaydı):**
- «senin adın ne» → anne adı (fuzzy özne kayması)
- «…adını sordum» → geçmiş soru listesi (çıplak `sordum` cue)
- «tefsir nedir» / «aşır nedir» → yanlış yol veya kavram eksik
- «bakara … kaçıncı/kaç ayet/nüzul» → 1. ayet (örnek ayet genişletmesi)
- «cin … türkçe» → Tûr sûresi (`tur` ∈ `türkçe`)

**Düzeltme:** fuzzy özne filtresi · asistan kimlik anlık yol · geçmiş sohbet cue sıkılaştırma · Kur'an meta/aşır · `detect_sure_no` kelime sınırı

### 2026-10-06 — Akaid (`04_akaid`) tamam (çekirdek)

**Bugün bitti:**
- Staging PDF: Mâtürîdî Tevhîd (Huleyf + Topaloğlu–Aruçi), Eş‘arî Luma‘, Makâlât → `arsiv/_ilim_staging/04_akaid/`
- Archive OCR metin → knowledge paketleri: Tevhîd ~788 + Makâlât ~654 batch (`scripts/faz4_akaid_ingest.py`)
- TR kavramlar: `kavramlar_akaid.jsonl` (18 madde) — fetva değil, kaynaklı özet
- Anlık yol: `ruzgar_akaid_kutuphane.py` + `desktop_server` early path (Kur’an/Arapça sonrası, iki blok)
- Smoke: `python scripts/smoke_akaid.py` → **8/8**
- `ingest_cli` `_KNOWLEDGE_ROOT` uyumluluk düzeltmesi (`rag_store`)
- RAG incremental ingest OK — indeks **42.502** parça (akaid md indekste)

**Canlı için:** `.\Ruzgar.ps1 -ForceRestart` → dene: «akaid nedir» · «maturidi kimdir» · «tevhid nedir» · «senin adın ne» · «aşır nedir»

**Luma notu:** PDF tarama-only; konu iskeleti MD var. Tam OCR sonra (Tesseract yoktu).

**TR çeviriler:** Telifli modern baskılar Mimar’ın `bekleyen_tr/` klasörüne yasal dosya koymasıyla eklenir.

**Sırada:**
1. Luma OCR (Tesseract/ara kurulum) veya senin TR PDF’lerin
2. Daha dolu AR–TR sözlük
3. Nebula untracked batch kararı
4. Git push (yerel ahead)

### 2026-10-05 — İlim din kütüphanesi (Kur’an/tefsir/Arapça)

**Bitti:** Gizlilik gitignore · Kur’an+tefsir · Arapça lügat · early path düzeltmeleri · smoke 9/9  
**Akaid:** 6 Ekim’de tamamlandı (yukarı).

### 2026-10-03 — Bilgi sohbeti kilidi (prepare_turn hang)

**Kök neden:** `analyze_turn` ↔ `should_use_personal_hafiza_first` ↔ `should_stay_on_ana_motor_bilgi` ↔ `looks_like_encyclopedic_fact_question` ↔ `personal_hafiza_blocks_bilgi_path` sonsuz döngü.

**Düzeltme:**
- `ruzgar_tek_beyin.py` — `_idrak_reentry` + reentry’de hafif kişisel kontrol
- `ana_motor_idrak_zihin.py` — reentry bayrağı (v2)
- `ana_motor_plan.py` — ansiklopedik sınıflandırmadan kişisel-hafıza çağrısı kaldırıldı
- `chat_core.py` / `weather_live.py` — «Su kaç derecede kaynar?» hava yanlış sınıflaması düzeltildi

**Ollama:** User `OLLAMA_MODELS` = `D:\ÜMİT\PROGRAMLAR\Ollama\models` (3 model). Tray/serve bazen env görmeden boş liste veriyor → Ollama’yı env ile yeniden başlat. ASCII junction: `D:\UMIT_PROGRAMLAR_Ollama_models`.

**Doğrulama (hedef):** selam anında · fotosentez/uydu bilgi yolu kilit değil · kaynar ≠ hava.

**Devam (kalite):** `Ruzgar.ps1` OLLAMA_MODELS garantisi · arka plan `preload_primary_chat_model` · Ollama-only talimat sızıntısı yasağı · aritmetik anında (`2+2=4`) · Ay mikro gerçek · scrub güçlendirildi.

**Canlı (2026-10-03):** selam/2+2/Ay anında · kaynar/fotosentez ~3–5 sn · Ollama preload OK · push bekliyor (ahead).

### 2026-10-03 — Yeni PC taşıma + Ollama-only sohbet (ara verildi)

**Donanım:** Ryzen 5 5500 · 16 GB RAM · RTX 4060 8 GB · Ollama 0.35

**D: kurulumlar (`D:\ÜMİT\PROGRAMLAR\`):**
- Ollama modelleri → `Ollama\models` (`OLLAMA_MODELS`)
- Python 3.12 + venv → `venvs\ruzgar` (`RUZGAR_PYTHON`)
- Node LTS → `Nodejs` · cache’ler → `Caches\`
- Git → `Git\cmd`

**Modeller:** `llama3.2:3b` (hizli) · `llama3.1:8b` (denge) · `qwen2.5-coder:7b` (kod)

**`.env` (git’te yok):** `RUZGAR_OLLAMA_ONLY=1` · Gemini/Groq kapalı · RAG warmup açık · `RUZGAR_EMBED_DEVICE=cpu` · `ENABLE_WEB_SEARCH=1` + `RUZGAR_WEB_ARASTIRMA_PRO=1` + `RUZGAR_WEB_SECONDARY_ONLY_ON_EMPTY=1` (yerel-önce; yoksa/zayıfsa veya canlı kur-haber → web) · `fx_live` (DDG/doviz.com anlık kur)

**Kod (bu oturum):**
- `Ruzgar.ps1` — D: venv önceliği · lite health’te `ollama_only` döngü düzeltmesi · `py` yerine `PyExe`
- `RuzgarMasaustuBaslat.ps1` + `scripts/Masaustune_Kisayol.ps1` — masaüstü kısayol / D: yolları
- `llm_ollama.py` — `num_ctx` + `keep_alive`
- `prompts.py` — Ollama-only sohbet üslubu
- `rag_store.py` — gömme cihazı CPU (VRAM çakışması)
- `chat_core.py` — aritmetik soruda fuzzy hafıza atlama

**Doğrulama:** Selam / anlık yollar OK · bilgi sorularında `prepare_turn` hâlâ takılabiliyor (sonraki oturum hedefi).

**Masaüstü kısayol:** `C:\Users\hayma\Desktop\RUZGAR.lnk`

**Sırada (dönünce):**
1. Bilgi sohbeti kilidi — `prepare_turn` / plan / retrieval hang’ini çöz
2. Sohbet kalitesini ölç (bellek + dolu cevap)
3. İsteğe bağlı: kontrollü bulut geri açma (kota korumalı)
4. 6b–6c (programlama / tek yüz) — önceki plandan

### 2026-06-18 — Sıra 6a: bilgi turu (devam: 6b…)

**Git:** Sıra 5 push edildi (`2c66853` · `origin/main`). Sıra 6a yerelde — commit bekliyor.

**6a tamamlandı:**
- `ana_motor_bilgi_turu.py` — merkezi bilgi turu politikası (hafıza → RAG → web → LLM)
- Yerel-RAG-önce: ansiklopedik/bilgi sorularında bulut hızlı yol RAG prefetch'i atlamaz
- Zayıf RAG → web açık kalır (güçlü eşleşmede kapatılabilir)
- `MAIN_ONLY_GENEL_HAFIZA` kapalı = tam güç (health + smoke doğrulama)
- Health `/api/health` → `ana_motor.bilgi_turu` durum kartı

**Sırada:** 6b (programlama çok dosya / E2), 6c (tek yüz pilot), 6d (offline gate), 6e (isteğe bağlı temizlik).

### 2026-06-17 — Programlama motoru oturumu (kapandı)

**Git (push edildi, `origin/main`):**

| Commit | Özet |
|--------|------|
| `2d0dd7c` | Faz85 scope yönlendirme (kullanıcı niyeti > oturum kapsamı) |
| `5b91c00` | Ajan scope sabitleme + boş yazım koruması |
| `7f7f151` | Upgrade raporu S10 11/11 |
| `72a89b3` | Geçersiz Python/JSON syntax yazım koruması + `version 2.0.0` parse |
| `2ef5634` | E1 KPI, UI overlay, terminal yolu, ana motor köprüsü (sıra 1–4) |
| `cb62964` | Faz85 erken kapı + scope önceliği (`iter_fast_path_early` bağlı) |

**Faz85 durumu:** Çekirdek hızlı yol `cb62964` · anında bayraklar/UI `2ef5634` — **push edildi**, geride dosya yok.

**Offline gate (son koşu):** `programlama_upgrade_runner.py --strict` → **11/11** · parity full **8/8**.

**Canlı doğrulama (UI):** `görev: smoke-live-test health endpointine version 2.0.0 ekle pytest geçir` → **Faz 85 hızlı yol OK** (~2.3 sn, LLM yok, yeşil). `projects/smoke-live-test/app/main.py` → `version: "2.0.0"` · pytest **2/2**.

**Yerel commit edilmemiş:** sıra 6a (bilgi turu).

**Hızlı başlatma:** `.\Ruzgar.ps1 -ForceRestart` · port **8779** · build `2026-06-15-ruzgar-programlama-pro-v4`.

## Kuzey yıldızı — asıl amaç

**Rüzgar’ı dijital kayıt cihazı veya dar bir araç değil; bağlam kuran, tam teşekküllü bir asistan yapmak istiyoruz.** Hedef, ChatGPT veya Gemini’ye benzeyen çizgide: geniş bilgi ve akıl yürütme, sorulara anlamlı yanıt, problemleri çözmeye çalışma, gerektiğinde program üretip projeyi çalışır hale getirebilme — yani **her şeyi bilen tek bir devasa liste değil**, katmanlı hafıza + bilgi + dil modeli ve motorlarla **gerçek bir yapay zekâ yardımcısı** oluşturmak. Atölyeler (video, programlama, tercüme vb.) bu vizyonun **parçaları**; amaç bunların üzerinde birleşen **tek yüz ve güçlü akıl**.

## Mimar protokolü (Cursor + Rüzgar)

- **Döngü:** Planla → Uygula → Doğrula → Revize.
- **Kalıcı kurallar:** kök `.cursorrules` + bu dosya.
- **Rüzgar sohbet talimatı:** `ilim_assistant/prompts.py` — hatırla vs kitap ingest ayrımı.

## Nebula politikası (2026-05-20 — Mimar ile net)

| Kanal | Ne zaman | Nereye | Biçim |
|--------|----------|--------|--------|
| **Sohbet «hatırla»** | Siz açıkça söylediğinizde | `ruzgar_genel_hafiza.json` | Kısa kişisel not; her tur otomatik yazılmaz |
| **Kitap / ansiklopedi** | «Şu dosyayı oku, hafızana kaydet» komutu | `knowledge/nebula/<koleksiyon>/incremental/` | Konu/başlık paketleri (`##` + `nebula_batch_*.md`) + RAG |
| **TDK / Tarih (mevcut)** | Protokol veya ingest | `knowledge/tdk/`, `knowledge/TARIH_VE_KULTUR/` | Aynı kademeli paket mantığı |

Modül: `ilim_assistant.nebula_kitap_hafiza` — `desktop_server` sohbetinde kitap komutu önce işlenir.

**Ne zaman diskte ne var (2026-05-20):**
- **TDK + büyük tarih:** 11 Mayıs ingest tamam (`tdk` 185 paket, `TARIH_VE_KULTUR` 25 paket, ~10k+ RAG parça) — Rüzgar sohbetten otomatik okumadı; protokol ile alındı.
- **Nebula demo:** Geliştirme testinde yalnızca küçük `tarih_kaynak.json` (318 kayıt) → `knowledge/nebula/tarih_kaynak/`. Siz sohbetten henüz büyük kitap komutu vermediyseniz nebula’da sadece bu demo olabilir.
- **Faz 2:** `RUZGAR_FAST_LOCAL_RAG_FIRST=1` (varsayılan) — bilgi sorularında fast path RAG’i atlamaz; prefetch + tarih + nebula birleşik arama.

### Sunucu yeniden başlatma (zorunlu kontrol)

1. `Ruzgar_TemizBaslat.bat` veya `.\Ruzgar.ps1 -ForceRestart` (yönetici gerekebilir — eski PID).
2. `ruzgar-desktop/ruzgar_remote_api.txt` → `http://127.0.0.1:8779` (8777 eski).
3. Dashboard şeridi: `build 2026-06-14-ruzgar-idrak-zihin-faz-an` · **Faz AN İdrak Zihin**.
4. Smoke: `cd ilim-assistant` → `python scripts/ana_motor_smoke.py` (0 hata hedefi).
4. `tarih_kaynak_buyuk.json` komutu → **anında**: «zaten tarih hafızasında 12190 kayıt» (tekrar yükleme gerekmez). Zorla nebula kopyası: mesaja `zorla nebula` ekle (arka planda, 2–8 dk; «nebula durum» ile izle).
5. Kitap komutu «Hatırladım» **değil**; büyük dosyada zaman aşımı olmamalı (`nebula-v2-async`).

**Not:** `tarih_kaynak_buyuk.json` zaten `TARIH_VE_KULTUR` (25 paket) + RAG’te; nebula komutu isteğe bağlı ikinci kopya.

## Ana motor, hafıza önbelleği ve teknik akış (özet)

- **Genel hafıza (`ruzgar_genel_hafiza.json`):** `HafizaIRuzgar` dosyayı RAM’e alır; fuzzy + token kapsaması ile eşleşme arar. `chat_core.prepare_turn` içinde **ilk bakılan yer** burasıdır; cevap bulunursa çoğu zaman tur burada biter (RAG/web/LLM’e çıkmadan).
- **RAG / İlim hazinesi (`rag_store`, `knowledge/`):** Yerel bilgi parçaları + gömme önbelleği; `main_engine` ile arşiv önceliği ve güçlü eşleşmede doğrudan pasaj yolu mümkün.
- **Kritik anahtar — `RUZGAR_MAIN_ONLY_GENEL_HAFIZA`:** Dar mod yalnızca ortamda **açıkça** `1`, `true`, `yes` veya `on` ile açılır. **Boş string veya tanınmayan değer tam güç sayılır** (önceden boş değer yanlışlıkla dar moda düşürebiliyordu). Dar mod açıkken `genel` modda JSON eşleşmezse yalnızca “öğrenmedim”; RAG/web/LLM kapalı.
- **Genel hafıza (`chat_core.try_genel_hafiza_reply`):** «Henüz öğrenmedim» yer tutucusu anında cevap sayılmaz; `ENABLE_RUZGAR_GENEL_HAFIZA=0` (veya `ENABLE_OGRENME_MERKEZI=0`) ile JSON kısayolu tamamen kapatılabilir.
- **Genel hafıza (`hafiza_i_ruzgar.HafizaIRuzgar`):** Birebir, normalize ve **fuzzy** aramada cevabı yer tutucu (“henüz öğrenmedim…” kalıbı) olan satırlar **aday olmaz**; böylece bir soruya yanlış satır üzerinden «öğrenmedim» zorlanmaz, sıra RAG/LLM’e kalır.
- **Tam boru hattı:** Kısıt kapalıyken sıra tipik olarak: genel hafıza → (yoksa) RAG parçaları + isteğe bağlı web/bağlantı + Ollama ile üretim.

## İlk ne yapılmalı — yardımcı motorları ana motora ne zaman bağlarız?

**Tam güç ana motor:** Varsayılan kod yolu `RUZGAR_MAIN_ONLY_GENEL_HAFIZA` olmadan **RAG + web + LLM**’e izin verir. Önce **Ollama**’nın ayakta olduğunu ve bir soruda gerçekten model yanıtı geldiğini doğrula.

**Yardımcı motorların ana motora bağlanması — zamanlama:**

1. **Önce** ana sohbet boru hattı net ve güvenilir olsun (yukarıdaki kilit + model + bağlam limitleri). Atölyeler zaten ayrı sekmede güçlü; “tek yüz” birleştirmesi bunun üstüne inşa edilir.
2. **Sonra** sırayla veya önceliğe göre **niyet / tetikleyici** katmanı: kullanıcı cümlesi hangi moda (video, programlama, tercüme…) ait, `normalize_mode` veya hafif bir yönlendirici ile seçilir; ilgili `/api/...` veya mevcut masaüstü işlevleri çağrılır. İlk bağlama adayı genelde **Programlama** veya **Tercüme** (metin tabanlı, API hazır) olur; **Video** dosya yolu ve FFmpeg gerektirdiği için bir adım sonra.
3. **`.cursorrules`** ile uyum: Sunucuda motor başlatma sırası zaten kilitli; ana motordan “motor çağrısı” **bu sırayı bozmadan** sadece **iş akışı** olarak eklenir (import sırasını değiştirmeden).

Özet: **Yardımcı motorları ana motora bağlamak**, ana boru hattı tam açıldıktan ve bir iki pilot senaryo (ör. “şu metni çevir”, “şu kodu çalıştır”) netleştikten **hemen sonraki mühendislik turu** olarak planlanır; takvim olarak “önce ana güç, sonra orkestrasyon”.

## Bu oturumda netleşenler

- **Sunucu yeniden başlatma:** Rüzgar/Electron penceresini kapatmak **Python sunucusunu** (`ilim-assistant` içinde `desktop_server.py`) yenilemez. Kod veya ortam değişince eski işlemi durdurup sunucuyu yeniden başlat; tam yeniden başlatmada **Ollama + `desktop_server`** oturumunun da temiz kalktığından emin ol.
- **Sohbet belleği:** Bilgisayar/kapanış sonrası model bağlamı sıfırlanır; tam çözüm **bu dosya + anlamlı commit mesajları**.
- **Plan özeti (önceki oturumlardan):** Katmanlı akıl (hafıza + RAG + LLM); beş ara motor (Ses, Video, Okuma, Tercüme, Programlama) güçlenir, sonra Ana Motor’da orkestrasyon; `.cursorrules` motor sırasına uy.
- **Programlama Atölyesi:** Build rev `2026-06-15-ruzgar-programlama-pro-v4`. Offline gate **11/11 + 8/8 parity**. **Faz 85** hızlı yol (health+version+pytest, LLM yok); **yazım koruması** (boş/syntax/patch tek kapı). UI’da Faz85 kartı + tam ajan uyarısı. Basit görev örneği: `görev: smoke-live-test health endpointine version 2.0.0 ekle pytest geçir`. Tam ajan yalnızca karmaşık işlerde; `RUZGAR_FAZ85=0` ile zorlanır.
- **Video Atölyesi:** **v1–v4** tarafında temel işlevler kodlandı (kesim, dönüştürme, birleştirme, altyazı gömme, ses bağlama, zaman çizelgesi, altyazıyı Tercüme’ye gönderme). FFmpeg ortamı doğrulanmıştı.
- **Arayüz:** Kullanıcıya dönük metinler Türkçeleştirildi; çok dillilik sonra bağlanacak.
- **Doğrulama:** `ruzgar-desktop` içinde `npm run test:phase11` — kod kartı fenced ayrıştırma senkron kontrolü.

### 2026-05-11 / 12 — Rüzgar «zihin ayarı» ve Git

- **TDK ↔ Tarih çakışması:** `chat_core` içinde tarih niyeti varken genel RAG havuzundan **TDK kaynaklı** pasajlar birleşik bağlama alınmıyor. `rag_store._source_is_tarih_hafiza` yolu düzeltildi (`tarih_ve_kultur` + eski yazım uyumu). `source_is_tdk` / `source_is_tarih_hafiza` dışa açıldı.
- **Kelime / TDK sorgusu:** Kısa veya sözlük kalıbında (`nedir`, `anlamı`, ≤3 kelime ve kısa mesaj vb.) **`search_tdk_exact_lemma`** — yalnızca chunk içindeki **`##` başlıkları** ile tam eşleşme (900 karakterlik dilimler yüzünden tüm başlıklar taranıyor). Eşleşme yoksa vektörle yakın maddeye **zıplanmıyor** (Hayalet/Haya tipi karışma riski azaltıldı). Kapatmak: `RUZGAR_TDK_EXACT_LEMMA=0`.
- **Bilge üslubu:** `prompts.pick_system` → `ASSISTANT_SYSTEM + _bilge_voice_suffix()` (tok, samimi, bilge anlatım). Kapatmak: `RUZGAR_BILGE_VOICE=0`.
- **İndeks:** `python -m ilim_assistant.ingest_cli --incremental` çalıştırıldı. Kök ve `ilim-assistant/.gitignore` içinden **`ilim-assistant/.rag_index/`** çıkarıldı; indeks dosyaları repoda tutuluyor (yaklaşık 10k+ chunk; `embeddings.npy` + `chunks.jsonl` + manifest).
- **Mühür satırı:** `desktop_server` startup ve `gradio_chat` `__main__` sonunda konsola: *Rüzgar Kullanıma Hazır, Sistemi Yeniden Başlatabilirsiniz.* Kapatmak: `RUZGAR_PRINT_READY_SEAL=0`.
- **Tarih bilgi seti (repo):** `knowledge/TARIH_VE_KULTUR/` (incremental md + JSON), `tarih_incremental_protocol.py`, `tarih_kaynak_fetch.py`, `ingest_cli.py` güncellemeleri commit’lendi.
- **Push:** `origin/main` güncel (ör. `fdccbdb` ve önceki Rüzgar/indeks commit’i aynı push dalında).

**Yarın kaldığımız yer:** Kod ve indeks GitHub’da; yerelde çalıştırmadan önce `git pull` yeterli. Bilgi ekledikten sonra indeks tazelemek için yine `ilim-assistant` klasöründe `python -m ilim_assistant.ingest_cli --incremental` (kilit mesajı çıkarsa `--allow-other-knowledge`). İstersen bir sonraki turda: TDK tam yolunun tetikleyicilerini genişletme/daraltma, `bilge_modu` ile `bilge_heartbeat` entegrasyonu, veya aşağıdaki «Sıradaki adım» maddelerinden biri.

## Sıradaki adım (devam)

**Öncelik — programlama:** Faz85’i LLM’den önce çalıştır (`iter_fast_path_early` bağla) · E1 %70+ · isteğe bağlı karmaşık görevlerde Yol C (tam ajan optimizasyonu).

Diğer seçenekler: çeviri `.srt` / yumuşak altyazı · çeviri anahtarları · Ana Motor tek sohbet orkestrasyonu.

## Referans

Geçmiş Cursor oturum özetleri (yerel): `agent-transcripts` altında; örn. programlama / plan tartışması ile ilişkili kayıtlar `2ef431a9-a39f-4e81-90ce-896ec19d93f9`, plan özeti `b8ad8767-ad71-4e4d-8cf0-09b001298000`.

---

## Bekleyen UI — Yardım (? ) motor rehberi (2026-06-03, ertelendi)

Üst **?** penceresine motor başına madde madde rehber — **motorlar sağlam çalıştıktan sonra** (önce güçlendirme/test, sonra yazım).  
**Plan:** `ruzgar-desktop/docs/RUZGAR_YARDIM_MOTOR_PLANI.md`

---

**Not:** Yeni oturumda önce bu dosyayı okuyarak devam et; özellikle **Kuzey yıldızı** bölümü proje kararları için bağlayıcı vizyondur.
