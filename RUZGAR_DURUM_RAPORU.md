# RÜZGAR — Güncel Durum Raporu (Handoff)

> **Tarih:** 2026-05-20 (güncellendi)  
> **Hazırlayan:** Cursor ajan oturumu (Ümit & Gökçenur projesi)  
> **Amaç:** Başka geliştirici asistanına teknik devir  
> **Repo kökü:** `D:\CURSOR PROJELER\YAPAY ZEKA`

---

## 1. Özet

Rüzgar, **Electron masaüstü kabuğu** (`ruzgar-desktop/`) + **yerel FastAPI sunucusu** (`ilim-assistant/desktop_server.py`, varsayılan `http://127.0.0.1:8777`) + **Python zeka çekirdeği** (`ilim-assistant/ilim_assistant/`) üçlüsünden oluşur.

**Faz 0–7** (UI, atölyeler, Ana Motor, UX cila) büyük ölçüde tamam. **Faz 8–12** yol haritası onaylı; uygulama kısmen devam ediyor (bkz. `RUZGAR_USTA_PLAN_FAZ8-12.md`).

**Son büyük iş paketi (commit dışı / working tree):** Merkezi Zihin Havuzu v2, Programlama motoru tam implementasyon, Video motoru (yt-dlp + görsel timeline kurgu), masaüstü v5 editör paneli.

**Son commit (main):** `9a93a37` — *feat(ruzgar): kalıcı hafıza context, full chat ve UI polling* (push edildi)

**Son oturum paketi (push edildi):** Oturum başına kalıcı hafıza özeti → `prepare_turn`; `POST /api/chat/full` (masaüstünde streaming kapalı, 60 sn timeout); manifest 3 sn polling; otonom debug raporu (`ruzgar_debug_report.py`); `GET /api/system-health-report`.

---

## 2. Mimari (yüksek seviye)

```
ruzgar-desktop/          → Electron UI (index.html, app.js, preload.js, main.js)
        │ fetch / ws
        ▼
ilim-assistant/desktop_server.py   → FastAPI (video, hafıza, chat/stream, workspace, STT, HIZIR)
        │
        ├── ilim_assistant/main_engine.py      → Karar ağacı (RAG/web/arsiv önceliği)
        ├── ilim_assistant/chat_core.py        → prepare_turn, mod normalizasyonu
        ├── ilim_assistant/stream_orchestra.py → SSE/WS sohbet orkestrasyonu
        ├── ilim_assistant/rag_store.py        → Yerel embedding indeksi
        ├── ilim_assistant/hafiza_i_ruzgar.py  → ruzgar_genel_hafiza.json (Soru=Cevap)
        │
        ├── motorlar/ruzgar_cekirdegi.py       → Çoklu motor bağlam birleştirici
        └── motorlar/merkezi_zihin_havuzu.py   → SQLite + JSON birleşik bellek
```

### Kilitli boot sırası (`.cursorrules`)

1. `ilim_assistant.main_engine`
2. `ilim_assistant.motorlar.ruzgar_cekirdegi`
3. Beş ara motor (sırayla): `ses_motoru` → `video_motoru` → `okuma_motoru` → `tercume_motoru` → `programlama_motoru`
4. Yardımcı ısınmalar (RAG, Whisper, TTS, hatırlatıcı) **arka planda**, 1–3 tamamlandıktan sonra

Manifest: `desktop_server.py` → `_boot_motorlar_anaonce()` (`.cursorrules` ile senkron olmalı).

### Önemli isimlendirme notu

| Boot listesi (`.cursorrules`) | Orkestra (`ruzgar_cekirdegi`) |
|------------------------------|-------------------------------|
| `okuma_motoru`               | `bilim_motoru` → içeride `okuma_motoru.build_motor_context` çağırır |

`bilim_motoru.py` bir **uyumluluk sarmalayıcısıdır**; boot’ta `okuma_motoru` import edilir, çekirdek bağlamında “Bilim (ilim/tarih)” olarak geçer.

---

## 3. Modüller / motorlar — durum tablosu

| Modül | Konum | Aşama | Notlar |
|-------|--------|-------|--------|
| **Ana Motor** | `main_engine.py`, `ana_motor_plan.py`, `ana_motor_agent.py` | **Üretim** | Decision tree v2; RAG/arsiv/web önceliği; mini ajan (workspace okuma). Self-reflection **planlı, yok** (Faz 9.6). |
| **Merkezi Zihin Havuzu** | `motorlar/merkezi_zihin_havuzu.py` (+ shim `merkezi_zihin_havuzu.py`) | **Yeni / entegre** | SQLite `hafiza/merkezi_zihin_havuzu.db`, JSON depolar, `publish_shared`, `motor_kv`, RAG köprüsü. Video motoru aktif yazar; programlama henüz yazmıyor. |
| **Rüzgar Çekirdeği** | `motorlar/ruzgar_cekirdegi.py` | **Üretim** | Ses+Video+Bilim+Tercüme+Programlama bağlamlarını birleştirir. |
| **Ses motoru** | `motorlar/ses_motoru.py` | **Üretim (Faz 4)** | Edge-TTS profilleri (Alim/Edip/Asistan); masaüstü oynatıcı tamponu `app.js`. |
| **Video motoru** | `motorlar/video_motoru.py` (+ shim) | **Faz 5 genişletilmiş** | yt-dlp indirme, havuz metadata, **timeline mix** (`mix_timeline_clips`, parça ≤5 dk). |
| **Okuma motoru** | `okuma_motoru.py` | **Üretim (Faz 2)** | Arşiv vizyonu, metin türü (hadis/gazel/tasavvufi), RAG ağaçları. |
| **Tercüme motoru** | `tercume_motoru.py` | **Üretim (Faz 3)** | Atölye + `build_motor_context`. |
| **Programlama motoru** | `motorlar/programlama_motoru.py` (+ shim) | **Faz 10 kısmi** | `ProgramlamaAraclari`: güvenli read/write, `@@write`, pytest/ruff preset. **Otonom debug döngüsü yok** (10.4–10.6 planlı). |
| **Bilim motoru** | `bilim_motoru.py` | **Shim → okuma** | Çekirdek orkestrasında kullanılır. |
| **Gelişim motoru** | `gelisim_motoru.py` | **Temel** | `build_motor_context` var; derin otonomi planlı. |
| **Dinleme motoru** | `dinleme_motoru.py` | **Yardımcı** | STT hattına bağlı. |
| **Hafıza (Soru=Cevap)** | `hafiza_i_ruzgar.py` | **Üretim** | `ruzgar_genel_hafiza.json`; fuzzy eşleşme; sohbet önceliği. |
| **Kuvve-i Hafıza** | `hafiza/gecmis_sohbetler.db` | **Üretim** | Kalıcı sohbet; `prepare_turn` enjeksiyonu. |
| **HIZIR (ticaret)** | `ilim_assistant/hizir/*` | **Ayrı alt sistem** | Pazar tarama, scraper, `global_market_engine`, Trendyol resilience. API: `/api/hizir/*`. Git’te ayrı değişiklik dalı olabilir. |
| **Arşiv ileri** | `motorlar/arsiv_ileri_motoru.py` | **Destek** | İleri arşiv işlemleri. |
| **Video FFmpeg** | `video_ffmpeg.py` | **Üretim** | trim, concat, transcode, burn-sub, mux; `concat_many_files` (mix). |
| **RAG** | `rag_store.py` | **Üretim** | `.rag_index/`; warmup startup’ta. |
| **LLM** | `llm_ollama.py` | **Üretim** | Yerel Ollama; Faz 8’de çoklu profil planlı. |

---

## 4. En son çalışılan özellik (Adım D)

### Ne üzerinde çalışıldı?

| Katman | Dosyalar |
|--------|----------|
| **Backend motor** | `ilim_assistant/motorlar/video_motoru.py` (yeni), `video_ffmpeg.py`, `desktop_server.py` |
| **Merkezi havuz** | `motorlar/merkezi_zihin_havuzu.py` (yeni), shim güncellemesi |
| **Masaüstü UI** | `ruzgar-desktop/index.html`, `app.js`, `styles.css` |

### Eklenen özellik: Görsel Editör / Timeline (v5)

1. **Görsel timeline:** Başlangıç/bitiş tutamaçları (sürüklenebilir), oynatıcı scrub, kesim bandı.
2. **Kurgu mantığı:** Parça listesi, sürükleyerek sıralama, harici dosya ekleme, `POST /api/video/edit/mix` → FFmpeg trim + `concat_many_files`.
3. **Hafıza:** Her mix → `video_hafiza.json` `edits[]`, `motor_kv` `video:edit:{id}`, `publish_shared` `video:kurgu:{id}`.

**Parça süre sınırı:** `EDIT_CLIP_MAX_SEC = 300` (5 dakika).

### Canlı test (önceki oturum — Adım C)

- yt-dlp ile YouTube indirme → `hafiza/video_indirilen/`
- Metadata merkezi havuza yazıldı (başarılı)

---

## 5. Merkezi veri havuzu — bağlantı durumu

### Sınıf: `MerkeziZihinHavuzu` (`get_havuz()` singleton)

| Bileşen | Yol / mekanizma |
|---------|------------------|
| SQLite | `ilim-assistant/hafiza/merkezi_zihin_havuzu.db` |
| Tablolar | `shared_context`, `motor_kv`, `meta` |
| JSON depolar | `merkezi_bellek.json`, `ruzgar_genel_hafiza.json`, `programlama_hafiza.json`, `video_hafiza.json`, `hafiza_arsivi.json` |
| RAG köprüsü | `build_motor_pool_context()` → `rag_store` |
| Dosya/exec | `local_tools`, `approved_executor` (havuz içinden preset çağrılabilir) |

### Kim yazıyor / okuyor?

| Kaynak | Havuz kullanımı |
|--------|-----------------|
| **Video motoru** | **Aktif** — indirme + kurgu metadata (`save_to_central_pool`, `save_edit_to_central_pool`) |
| **main_engine** | `no_rag_modes()` shim üzerinden |
| **Programlama motoru** | **Henüz doğrudan yazmıyor** (araçlar `local_tools` kullanır) |
| **Hafıza I Rüzgar** | Ayrı kanal: yalnızca `ruzgar_genel_hafiza.json` (klasik Soru=Cevap) |
| **Sohbet geçmişi** | `gecmis_sohbetler.db` (ayrı SQLite) |

### Ortam değişkenleri

- `RUZGAR_MERKEZI_ZIHIN=1` (varsayılan açık)
- `RUZGAR_MERKEZI_ZIHIN_INCLUDE_ALL_MODES=0` → video/ses/hızlı modlarda RAG atlama davranışı
- `RUZGAR_VIDEO_EDITS_MAX`, `RUZGAR_VIDEO_EDIT_TTL` — kurgu kayıt limitleri

---

## 6. Masaüstü API özeti (`desktop_server.py`)

| Endpoint | İşlev |
|----------|--------|
| `GET /api/health` | ffprobe/ffmpeg durumu |
| `POST /api/chat/stream`, `WS /ws/chat` | Ana sohbet (SSE/WS) |
| **`POST /api/chat/full`** | **Tek JSON cevap (masaüstü varsayılan)** |
| **`GET /api/system-health-report`** | **Sağlık + hafıza kapasitesi + son debug** |
| `GET /api/ui-manifest` | UI manifest (`generated_at`) |
| `POST /api/video/probe` | Medya özeti |
| `POST /api/video/trim` | Kesim |
| `POST /api/video/transcode` | H.264 dönüşüm |
| `POST /api/video/concat` | İki dosya birleştir |
| **`POST /api/video/edit/mix`** | **Timeline kurgu (yeni)** |
| `POST /api/video/burn-subtitles` | Altyazı gömme |
| `POST /api/video/mux-audio` | Harici ses |
| `GET /api/workspace/*` | Proje dosya okuma/liste |
| `POST /api/code/run` | Kod çalıştırma |
| `POST /api/hizir/*` | Ticaret vitrin |
| `GET /api/merkezi-bellek` | Merkezi bellek vitrin |

Çıktı klasörü: `.ruzgar-video-export/` (repo kökü altında).

---

## 7. Git durumu (rapor anı)

**Branch:** `main` — son push `9a93a37` (kaynak kod paketi)

**Yerel / runtime (commit edilmemeli):**

```
M  ilim-assistant/merkezi_bellek.json
M  ilim-assistant/ruzgar_genel_hafiza.json
M  ilim-assistant/video_hafiza.json
?? ilim-assistant/hafiza/*.db
?? ilim-assistant/hafiza/video_indirilen/
```

Kök `.gitignore`: `hafiza/*.db`, `video_indirilen/`, `son_debug_raporu.txt`, `chat_stream_probe.txt`.  
Eski takip edilen JSON hafıza dosyaları hâlâ `git status`’ta `M` görünebilir; tamamen yerel tutmak için `git rm --cached` (isteğe bağlı).

---

## 8. Bilinen boşluklar (plan vs kod)

| Konu | Durum |
|------|--------|
| Self-correction (bilgi/kod) | Faz 9.6 / 10.6 — **yok** |
| Programlama otonom debug döngüsü | Faz 10.4 — **kısmi** (`ruzgar_debug_report`, pytest sonrası rapor; tam Cursor-döngüsü değil) |
| Masaüstü full chat (streaming kapalı) | **var** — `POST /api/chat/full`, `app.js` 60 sn timeout |
| Oturum kalıcı hafıza context | **var** — `ruzgar_session_context.py`, `RUZGAR_SESSION_*` |
| Çoklu model / bulut API | Faz 8 — **planlı** |
| Video Faz 5 resmi kapanış | v2–v5 UI var; plan dokümanı hâlâ “devam (v2)” |
| Programlama → Merkezi Havuz yazma | **eksik** |
| HIZIR global market | Ayrı geliştirme hattı; ana motor boot’unda değil |

---

## 9. Hızlı başlatma (geliştirici)

```powershell
# 1) API
cd "D:\CURSOR PROJELER\YAPAY ZEKA\ilim-assistant"
python desktop_server.py

# 2) Masaüstü (ayrı terminal)
cd "D:\CURSOR PROJELER\YAPAY ZEKA\ruzgar-desktop"
npm start
```

Gereksinimler: Python deps (`requirements-api.txt`), Ollama, FFmpeg PATH, isteğe bağlı `yt-dlp`.

---

## 10. Git durumu (18 Mayıs 2026 — güncel)

**Remote:** `origin/main` — https://github.com/umithaymana/ruzgar.git (güncel)

| Commit | Özet |
|--------|------|
| `bd707f3` | Video timeline editor + merkezi havuz |
| `5ecb37a` | Google Gemini API + Süper Beyin (`llm_gemini`, `llm_brain`) |

**Commit dışı (yerel):** `ilim-assistant/.env` (API anahtarı), `hafiza/*.db`, `hafiza/video_indirilen/`

---

## 11. Son oturum özeti — yarın devam (18 Mayıs 2026)

### Tamamlananlar
- **Adım A–C:** Programlama motoru, Merkezi Zihin Havuzu, Video motoru (yt-dlp + canlı test).
- **Adım D:** Görsel timeline / kurgu paneli (v5), `POST /api/video/edit/mix`, FFmpeg `concat_many_files`.
- **Süper Beyin (Faz 8 başlangıç):** `llm_brain.py` + `llm_gemini.py`; bulut = **yalnızca Google Gemini** (OpenAI kaldırıldı).
- **`.env`:** `ilim-assistant/.env` oluşturuldu; `desktop_server.py` → `_load_env_file()` ile yükleniyor.
- **Doğrulama:** `/api/health` → `super_brain.gemini_configured: true`, zincir: `gemini → denge → hizli → kod`.
- **Push:** `main` güncel (`5ecb37a`).

### Son kullanıcı testi / gözlem
- Soru: *«osmanlı devletini kim kurdu»* — UI’da **45+ sn** «Yerel indeks taranıyor…» (plan: ilim/tarih, arşiv+indeks, Web ara açık).
- **Sonuç:** Mimari olarak beklenen (önce RAG/web, sonra LLM); bu tür sorular için **fazla yavaş** — optimizasyon adayı.

### Yarın önerilen sıra
1. **Hız (isteğe bağlı ilk iş):** Tarih/bilgi sorularında «önce Gemini, RAG hafif/paralel» veya Web kapalıyken benchmark.
2. **Faz 9.6:** Bilgi self-reflection (cevap → kontrol turu).
3. **Faz 10.4–10.6:** Programlama otonom debug döngüsü.
4. Video v5: uçtan uca mix test (isteğe bağlı).

### Yarın başlarken (komutlar)
```powershell
# 1) API (ilim-assistant klasöründe — .env otomatik okunur)
cd "D:\CURSOR PROJELER\YAPAY ZEKA\ilim-assistant"
python desktop_server.py

# 2) Masaüstü
cd "D:\CURSOR PROJELER\YAPAY ZEKA\ruzgar-desktop"
npm start
```
Kontrol: http://127.0.0.1:8777/api/health → `gemini_configured: true`

### Ortam hatırlatması
- Gemini: `GOOGLE_GEMINI_API_KEY` + `RUZGAR_GEMINI_MODEL=gemini-2.0-flash` → `RUZGAR_BRAIN.env.example` şablonu.
- API anahtarı sohbette göründüyse Google AI Studio’dan **yenilemek** iyi olur.

### Yeni asistana tek cümle
> «Rüzgar: video+kurgu ve Gemini Süper Beyin push edildi; yarın önce tarih sorularında RAG gecikmesini iyileştirmek veya Faz 9–10’a geçmek istiyoruz.»

---

*Bu dosya workspace kökünde handoff kaynağıdır; yarın `@RUZGAR_DURUM_RAPORU.md` ile devam edin.*
