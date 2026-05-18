# RÜZGAR — Güncel Durum Raporu (Handoff)

> **Tarih:** 2026-05-18  
> **Hazırlayan:** Cursor ajan oturumu (Ümit & Gökçenur projesi)  
> **Amaç:** Başka geliştirici asistanına teknik devir  
> **Repo kökü:** `D:\CURSOR PROJELER\YAPAY ZEKA`

---

## 1. Özet

Rüzgar, **Electron masaüstü kabuğu** (`ruzgar-desktop/`) + **yerel FastAPI sunucusu** (`ilim-assistant/desktop_server.py`, varsayılan `http://127.0.0.1:8777`) + **Python zeka çekirdeği** (`ilim-assistant/ilim_assistant/`) üçlüsünden oluşur.

**Faz 0–7** (UI, atölyeler, Ana Motor, UX cila) büyük ölçüde tamam. **Faz 8–12** yol haritası onaylı; uygulama kısmen devam ediyor (bkz. `RUZGAR_USTA_PLAN_FAZ8-12.md`).

**Son büyük iş paketi (commit dışı / working tree):** Merkezi Zihin Havuzu v2, Programlama motoru tam implementasyon, Video motoru (yt-dlp + görsel timeline kurgu), masaüstü v5 editör paneli.

**Son commit (main):** `cd15a59` — *feat(programlama): güvenli dosya I/O, exec preset'leri ve tam programlama motoru*

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
| `POST /api/chat/stream`, `WS /ws/chat` | Ana sohbet |
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

**Branch:** `main` (origin ile senkron; son push `cd15a59`)

**Commit edilmemiş değişiklikler (~702 satır):**

```
M  ilim-assistant/desktop_server.py          (+/api/video/edit/mix)
M  ilim-assistant/ilim_assistant/merkezi_zihin_havuzu.py  (shim → motorlar)
M  ilim-assistant/ilim_assistant/motorlar/ruzgar_cekirdegi.py
M  ilim-assistant/ilim_assistant/video_ffmpeg.py
M  ilim-assistant/ilim_assistant/video_motoru.py  (shim)
M  ilim-assistant/video_hafiza.json
M  ruzgar-desktop/app.js, index.html, styles.css
?? ilim-assistant/ilim_assistant/motorlar/merkezi_zihin_havuzu.py
?? ilim-assistant/ilim_assistant/motorlar/video_motoru.py
?? ilim-assistant/hafiza/merkezi_zihin_havuzu.db
?? ilim-assistant/hafiza/video_indirilen/
```

**Öneri:** Adım D + Merkezi Havuzu paketi tek commit ile `feat(video): timeline editor ve merkezi havuz entegrasyonu` benzeri mesajla kaydedilmeli; DB ve büyük indirilen videolar `.gitignore`’da tutulmalı.

---

## 8. Bilinen boşluklar (plan vs kod)

| Konu | Durum |
|------|--------|
| Self-correction (bilgi/kod) | Faz 9.6 / 10.6 — **yok** |
| Programlama otonom debug döngüsü | Faz 10.4 — **yok** |
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

## 10. Handoff kontrol listesi

- [ ] `git status` — untracked `motorlar/*.py` dosyalarını stage et
- [ ] Video panel v5: timeline + mix uçtan uca test
- [ ] `merkezi_zihin_havuzu.db` commit’e girmesin
- [ ] `.cursorrules` boot listesi ↔ `desktop_server._boot_motorlar_anaonce` uyumu doğrula
- [ ] Sonraki iş: Faz 10.4 programlama debug döngüsü veya Faz 9.6 bilgi reflection

---

*Bu dosya workspace kökünde güncellenebilir; handoff için tek kaynak olarak kullanın.*
