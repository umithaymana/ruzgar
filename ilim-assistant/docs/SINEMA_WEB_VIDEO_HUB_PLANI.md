# Sinema Web Video Hub — Master Plan

> **Oluşturulma:** 2026-06-03  
> **Onay:** Ümit abi — plan onayı sonrası işleme alınır  
> **Kuzey yıldızı:** Sinema paneli = web’deki videoların **tek merkezi** — link ver, panelde izle, tıkla, indir, kes, kurgu.  
> **İlişkili planlar:** `ruzgar-desktop/docs/VIDEO_MOTOR_OLGUNLASMA_PLANI.md` (editör olgunluğu V1–V6) · `docs/RUZGAR_MOTOR_VIZYON.md` (motor mimarisi)

---

## 1. Vizyon (kesin niyet)

| Katman | Hedef |
|--------|--------|
| **Sinema sahnesi** | Tüm web video kaynakları burada oynatılır; dış tarayıcıya kaçış son çare. |
| **Sohbet** | «panelde aç», «3 numarayı oynat», «indir ve kes» — doğal Türkçe. |
| **İşlem** | Aynı panelden indir → timeline → FFmpeg → `.ruzgar-video-export/`. |
| **Platform** | Önce YouTube tam; sonra yt-dlp destekli siteler; en son doğrudan URL / HLS / gömülü web. |

**Prensipler (kilitli):**

1. Sinema `<video>` + sunucu proxy **birincil** yol (hafif, kesime hazır akış).
2. Electron **BrowserView** yalnızca akış çözülemediğinde (bot, DRM, gömülü sayfa).
3. İndirme her zaman **virüs kalkanı**ndan geçer (mevcut kural).
4. Her faz **Ctrl+Shift+R smoke** + küçük commit; büyük tek PR yok.

---

## 2. Mevcut durum (2026-06-03)

### Çalışan

| Bileşen | Durum | Dosya / API |
|---------|--------|-------------|
| YouTube sinema **canlı akış** | ✓ | `video_youtube_stream.py`, `POST /api/video/youtube/prepare`, `GET …/stream/{token}` |
| YouTube **indir** + havuz | ✓ | `video_motoru.py`, `/api/video/download` |
| **FFmpeg** işleri (kes, mux, kurgu…) | ✓ | `desktop_server.py`, `video_ffmpeg.py` |
| Sohbet **panelde aç / indir** | ✓ | `video-chat-brain.js`, `app.js` |
| YouTube **isimle arama** (sohbet metni) | ✓ | `video_faz84.py`, `/api/video/search` |
| Electron **BrowserView** yedek | ✓ | `main.js`, `preload.js` |
| Sinema UI + dock | ✓ | `video-atolye.js`, `video-atolye.css` |

### Eksik (vizyona göre)

| Eksik | Etki |
|-------|------|
| Arama sonuçları **tıklanabilir sinema listesi** yok | «3 numarayı panelde aç» yok; sadece metin + «indir» |
| Akış API **yalnızca YouTube** | Vimeo, X, TikTok… indirilir ama panelde oynatılmaz |
| URL tanıma **YouTube odaklı** | `extractVideoDownloadUrl` youtube/youtu.be filtreliyor |
| **Playlist** panel akışı yok | Tek video |
| **Doğrudan .mp4 / HLS** yolu yok | Bazı siteler sadece ham URL verir |
| **Genel web gezgini** yok | URL çubuğu + sinema birleşimi ileri faz |

**Genel olgunluk (web hub açısından):** ~**35/100** — omurga var; **tek kapı** ve **keşif UI** eksik.

---

## 3. Hedef mimari

```text
                    ┌─────────────────────────────────────┐
  Sohbet / arama    │  Video Keşif Katmanı                 │
  Link yapıştır     │  · arama sonuçları (tıklanabilir)    │
  Son indirmeler    │  · URL alanı · son kaynaklar         │
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────┐
                    │  Kaynak Çözücü (backend)             │
                    │  1) yt-dlp stream → proxy token      │
                    │  2) doğrudan video URL               │
                    │  3) HLS (.m3u8) proxy                │
                    │  4) gömülü sayfa → BrowserView       │
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────┐
                    │  SİNEMA SAHNESİ (frontend)           │
                    │  <video> · BrowserView · metadata    │
                    │  timeline · dock (kes / indir / …)   │
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────┐
                    │  İşlem hattı (mevcut)               │
                    │  indir · virüs · FFmpeg · export     │
                    └─────────────────────────────────────┘
```

**API hedefi (birleşik):**

| Endpoint | Amaç |
|----------|------|
| `POST /api/video/stream/prepare` | Her desteklenen URL → `{ token, stream_path, title, site, … }` |
| `GET /api/video/stream/{token}` | Range destekli proxy (mevcut YouTube proxy genelleştirilir) |
| `POST /api/video/search` | Genişletilir: platform + «N oynat» modu |
| Mevcut `/api/video/download`, `/trim`, … | Değişmez; sinema → indir köprüsü eklenir |

---

## 4. Faz programı (SW-0 … SW-5)

> **SW** = Sinema Web. Her faz bitince: smoke checklist, cache bump, kısa commit.

---

### SW-0 — YouTube sinema akışı · **TAMAMLANDI ✓**

### SW-1 — YouTube’u tam bitir · **TAMAMLANDI ✓** (2026-06-03)

### SW-2 — Evrensel yt-dlp akış · **TAMAMLANDI ✓** (2026-06-03)

### SW-3 — Doğrudan video URL + HLS · **TAMAMLANDI ✓** (2026-06-03)

### SW-4 — Gömülü web / mini gezgin · **TAMAMLANDI ✓** (2026-06-03)

### SW-5 — Birleşik iş akışı + playlist · **TAMAMLANDI ✓** (2026-06-03)

> Playlist: `RUZGAR_YTDLP_PLAYLIST=1` ile yt-dlp playlist modu (ileri kullanım).  
> DRM (Netflix vb.): bilinçli kapsam dışı — ileride SW-6 notu.

---

### SW-0 — YouTube sinema akışı · **TAMAMLANDI ✓** (detay)

| # | İş | Durum |
|---|-----|--------|
| SW-0.1 | yt-dlp → proxy → `<video>` | ✓ |
| SW-0.2 | Electron BrowserView yedek | ✓ |
| SW-0.3 | Sohbet «panelde aç» mesajları | ✓ |

**Kabul:** Bir YouTube linki sinemada oynar; dış tarayıcı otomatik açılmaz.

---

### SW-1 — YouTube’u tam bitir · **TAMAMLANDI ✓** (2026-06-03)

**Hedef:** YouTube = panel içi tam deneyim — arama, tıklama, indir, işlem aynı yerden.

**Süre tahmini:** 2–3 oturum

| # | İş | Dosyalar | Kabul kriteri |
|---|-----|----------|----------------|
| SW-1.1 | Sinema altında **arama sonuç kartları** (tıklanabilir) | `app.js`, `video-atolye.css`, `index.html` | «video ara: …» sonrası panelde 8 sonuç; tık → sinemada oynar |
| SW-1.2 | Sohbet: «**N numarayı oynat / panelde aç**» | `video_faz84.py`, `video-chat-brain.js` | «3 numarayı oynat» → indirmeden sinema |
| SW-1.3 | Sonuç kartında **İzle · İndir · Kes** kısayolları | `app.js` | Tek tıkla mod seçimi |
| SW-1.4 | Oynatılan kaynak **metadata şeridi** (başlık, süre, site) | `app.js`, sinema deck | Probe alanı güncellenir |
| SW-1.5 | Hata UX: bot / çerez → Türkçe + «Tekrar dene / Gömülü aç» | `app.js`, `video_youtube_stream.py` | Anlaşılır mesaj |
| SW-1.6 | Smoke: `docs/VIDEO_MOTOR_SMOKE.md` genişlet | docs | 5 yeni madde |
| SW-1.7 | Yardım metni güncelle | `index.html` | «panelde aç» akışı anlatılır |

**SW-1 test senaryoları:**

1. Link + «panelde aç» → sinema `<video>`.
2. «tarih belgeseli ara» → listeden #2 tık → sinema.
3. «2 numarayı indir» → havuz + timeline.
4. Sinemadayken «kes 0:10-0:40» → FFmpeg çıktı oynatıcıda.

**Çıktı cümlesi:** «YouTube’u Rüzgar panelinden baştan sona yönetiyorum.»

---

### SW-2 — Evrensel yt-dlp akış (tüm platformlar)

**Hedef:** YouTube dışı linkler de **aynı sinema yolu** — Vimeo, Dailymotion, X/Twitter, TikTok, Bilibili… (yt-dlp desteklediği sürece).

**Süre tahmini:** 2 oturum

| # | İş | Dosyalar | Kabul kriteri |
|---|-----|----------|----------------|
| SW-2.1 | `video_youtube_stream.py` → **`video_stream.py`** (generic) | yeni modül | `prepare_stream(url)` site bağımsız |
| SW-2.2 | API: `/api/video/stream/prepare` + `/stream/{token}`; YouTube eski yol alias | `desktop_server.py` | Geriye uyumlu |
| SW-2.3 | Frontend: `loadStreamInPanel(url)` — YouTube wrapper | `app.js` | Tek giriş fonksiyonu |
| SW-2.4 | URL tanıma: **http(s) video linki** (platform listesi değil, yt-dlp dene) | `app.js`, `video-chat-brain.js` | Vimeo link + «oynat» çalışır |
| SW-2.5 | Site rozeti + hata mesajı («Bu site desteklenmiyor») | UI | Kullanıcı bilgilendirilir |
| SW-2.6 | `motor_kabiliyetleri.json` route genişlet | json | «vimeo oynat» video motoruna gider |

**Bilinen sınırlar (dokümante edilecek):**

- DRM (Netflix, Disney+…) → SW-2’de **hayır**; SW-4 BrowserView veya red.
- Üyelik / yaş / bölge → çerez + yedek; %100 garanti yok.

**Çıktı cümlesi:** «Verdiğim link yt-dlp ise panelde açılır.»

---

### SW-3 — Doğrudan video URL + HLS

**Hedef:** `.mp4`, `.webm`, `.m3u8` gibi **doğrudan akış adresleri** proxy veya native ile sinemada.

**Süre tahmini:** 2 oturum

| # | İş | Kabul kriteri |
|---|-----|----------------|
| SW-3.1 | URL sınıflandırıcı: `direct` / `hls` / `ytdlp` / `embed` | Doğru dal seçilir |
| SW-3.2 | HLS proxy veya `hls.js` entegrasyonu | `.m3u8` sinemada oynar |
| SW-3.3 | Doğrudan mp4 → proxy (CORS bypass) veya doğrudan src | Sunucu dosyası / uzak mp4 |
| SW-3.4 | Sohbet: «şu mp4 linkini oynat» | Çalışır |

**Risk:** HLS segment proxy yükü — oturum TTL + cache sınırı (`RUZGAR_STREAM_TTL_SEC`).

---

### SW-4 — Gömülü web / mini gezgin (Electron ağırlıklı)

**Hedef:** Akış çözülemeyen sayfalar için **panel içi web** — genelleştirilmiş BrowserView, isteğe URL çubuğu.

**Süre tahmini:** 3–4 oturum

| # | İş | Kabul kriteri |
|---|-----|----------------|
| SW-4.1 | BrowserView **site bağımsız** (`showWebCinema(url)`) | Her https sayfa sinema alanında |
| SW-4.2 | Sinema **URL çubuğu** + «Aç» | Kullanıcı adres yapıştırır |
| SW-4.3 | «Sayfadaki videoyu yakala» (yt-dlp veya DOM hint — kademeli) | İleri özellik; v1 opsiyonel |
| SW-4.4 | Pencere resize → bounds sync (mevcut YouTube IPC genelle) | `main.js` |

**Not:** Bu faz «web’deki her şey» hedefinin **sigorta katmanı**; birincil yol SW-2/3 kalır.

---

### SW-5 — Birleşik iş akışı + playlist

**Hedef:** Sinema ↔ indir ↔ kes ↔ kurgu **tek hikâye**; isteğe playlist.

**Süre tahmini:** 2–3 oturum (VIDEO_MOTOR V3 ile örtüşür)

| # | İş | Kabul kriteri |
|---|-----|----------------|
| SW-5.1 | Sinema toolbar: **İndir · Kesime al · Kurgu binine ekle** | Tek tık |
| SW-5.2 | «Şimdi oynatılanı indir» API köprüsü | Aktif stream URL → download job |
| SW-5.3 | Playlist (opt-in): sıradaki parça otomatik sinema | `RUZGAR_YTDLP_PLAYLIST=1` |
| SW-5.4 | Ana Motor hub: «video aç» delege | `ana-motor-hub.js` |

---

## 5. VIDEO_MOTOR (V1–V6) ile ilişki

| Sinema Web (SW) | Editör olgunluğu (V) |
|-----------------|----------------------|
| SW-1…2: **içerik getir** | V1–V2: panel sağlam + sohbet FFmpeg |
| SW-5: sinema → işlem köprüsü | V3: timeline klavye, altyazı pipeline |
| SW-4: web gezgin | V4: waveform, görsel timeline |
| — | V5–V6: AI plan, proje dosyası |

**Önerilen paralellik:** SW-1 bitene kadar V4+’e girme; sinema **içerik kapısı** önce tamamlansın.

---

## 6. Uygulama sırası (onaylı yol)

```text
SW-0 ✓  →  SW-1  →  SW-2  →  SW-3  →  SW-4  →  SW-5
           YouTube   Platform  MP4/HLS  Web view  Pipeline
           tam       akışı
```

| Sprint | Faz | Ümit abi görür |
|--------|-----|----------------|
| **Sprint A** (hemen) | SW-1 | Arama → tıkla → sinema; «N oynat» |
| **Sprint B** | SW-2 | Vimeo/TikTok linki panelde |
| **Sprint C** | SW-3 | mp4/m3u8 linkleri |
| **Sprint D** | SW-4 | Panel URL çubuğu |
| **Sprint E** | SW-5 | Sinemadan indir/kes tek tık |

---

## 7. Ortam değişkenleri

| Değişken | Varsayılan | Anlam |
|----------|------------|--------|
| `RUZGAR_YTDLP_STREAM_FORMAT` | `best[ext=mp4][height<=1080]/…` | Sinema kalite tavanı |
| `RUZGAR_YTDLP_COOKIES_BROWSER` | `edge` (Win) | Bot / yaş engeli |
| `RUZGAR_STREAM_TTL_SEC` | `7200` | Proxy oturum ömrü |
| `RUZGAR_VIDEO_FAZ84` | `1` | Arama açık |
| `RUZGAR_YTDLP_PLAYLIST` | `0` | SW-5’te opt-in |

---

## 8. Riskler ve dürüst sınırlar

| Risk | Olasılık | Önlem |
|------|----------|--------|
| YouTube bot / imza değişimi | Yüksek | yt-dlp güncelle; çerez; BrowserView yedek |
| Proxy bant genişliği (uzun 4K) | Orta | 1080p format varsayılan; indir ayrı yol |
| HLS proxy karmaşıklığı | Orta | SW-3 ayrı faz; hls.js fallback |
| DRM platformlar | Kesin | Dokümante «desteklenmez»; SW-4 kısmi |
| Electron / web parity | Orta | Web’de BrowserView yok → akış + iframe |

**Halka açık vaat (dürüst):**

> «Web’de erişilebilen videoların **büyük çoğunluğu** Rüzgar sinema panelinde açılır; korumalı platformlar hariç.»

---

## 9. Başarı ölçütleri

| Milestone | KPI |
|-----------|-----|
| **SW-1 bitti** | 5 YouTube senaryosu smoke geçer; arama tıklama çalışır |
| **SW-2 bitti** | En az 3 farklı site (YouTube + 2) sinema akışı |
| **SW-3 bitti** | Doğrudan mp4 + bir HLS testi geçer |
| **SW-4 bitti** | Electron’da URL çubuğundan sayfa sinema alanında |
| **SW-5 bitti** | Sinemadan «indir ve kes» uçtan uca |
| **Hub tamam** | Ümit abi günlük izleme + kesim işini **dış tarayıcı olmadan** yapar |

---

## 10. Onay checklist (işleme almadan önce)

- [ ] Faz sırası (SW-1 → SW-2 → …) onaylı
- [ ] İlk sprint = **SW-1** (YouTube tam) onaylı
- [ ] DRM / Netflix vb. **kapsam dışı** kabulü
- [ ] SW-2’de «yt-dlp destekli = panelde açılır» tanımı onaylı
- [ ] Commit/push her sprint sonunda isteniyor mu? (evet/hayır)

**Onay sonrası branch önerisi:** `plan/sw-1-youtube-sinema-tam`

---

## 11. Dosya haritası

| Katman | Yol |
|--------|-----|
| Akış motoru (bugün) | `ilim_assistant/motorlar/video_youtube_stream.py` |
| Akış motoru (hedef) | `ilim_assistant/motorlar/video_stream.py` |
| İndirme | `ilim_assistant/motorlar/video_motoru.py` |
| Arama | `ilim_assistant/motorlar/video_faz84.py` |
| API | `ilim-assistant/desktop_server.py` |
| Sinema UI | `ruzgar-desktop/app.js`, `video-atolye.js` |
| Sohbet | `ruzgar-desktop/video-chat-brain.js` |
| Electron | `ruzgar-desktop/main.js`, `preload.js` |
| Smoke | `ruzgar-desktop/docs/VIDEO_MOTOR_SMOKE.md` |

---

*Son güncelleme: 2026-06-03 — Ümit abi vizyonu + mevcut kod tabanı birleşimi.*
