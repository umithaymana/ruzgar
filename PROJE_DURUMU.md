# RÜZGAR — oturum özeti (kalıcı)

**Son güncelleme:** 2026-06-17 (Programlama A+B: yazım koruması birleşik, Faz85 UI, E1 KPI filtre)

Bu dosya sohbet sıfırlanınca bağlamı taşımak için tutulur. Kapatmadan önce «durumu güncelle» denmesi yeterli (çarpı ile kapanışta otomatik yazılamaz).

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

Örnek seçenekler: çeviri sonrası **`.srt` üretimi** veya **yumuşak altyazı izi**; arayüz için **çeviri anahtarları**; Programlama **Faz 1.4+**; Ana Motor’dan **tek sohbetten motor orkestrasyonu**. Öncelik her oturumda birlikte seçilir.

## Referans

Geçmiş Cursor oturum özetleri (yerel): `agent-transcripts` altında; örn. programlama / plan tartışması ile ilişkili kayıtlar `2ef431a9-a39f-4e81-90ce-896ec19d93f9`, plan özeti `b8ad8767-ad71-4e4d-8cf0-09b001298000`.

---

## Bekleyen UI — Yardım (? ) motor rehberi (2026-06-03, ertelendi)

Üst **?** penceresine motor başına madde madde rehber — **motorlar sağlam çalıştıktan sonra** (önce güçlendirme/test, sonra yazım).  
**Plan:** `ruzgar-desktop/docs/RUZGAR_YARDIM_MOTOR_PLANI.md`

---

**Not:** Yeni oturumda önce bu dosyayı okuyarak devam et; özellikle **Kuzey yıldızı** bölümü proje kararları için bağlayıcı vizyondur.
