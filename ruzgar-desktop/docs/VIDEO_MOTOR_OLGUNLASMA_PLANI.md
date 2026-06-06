# Rüzgar Video Motoru — Olgunlaştırma Planı

> **Kuzey yıldızı:** Ümit abi dosyayı açar, keser, indirir, altyazı gömer, kurgular — sohbet veya panel; çıktı `.ruzgar-video-export/` altında, tek ekranda sinema deneyimi.  
> **Referans seviye:** CapCut / DaVinci Resolve “hobi+” — tam Hollywood değil; yerel, gizlilik, Rüzgar ekosistemi (tercüme, havuz, virüs kalkanı).  
> **Durum raporu:** Haziran 2026 — sinema UI + dock + FFmpeg backend çalışır; sohbet FFmpeg, AI sahne, pipeline birleşimi eksik.

**Mevcut build:** `aadde30` — sinema düzeni, dock panelleri, motor kabuğu düzeltmeleri

---

## 1. Dürüst seviye analizi

| Boyut | Profesyonel editör (~100) | Rüzgar bugün (~) | Not |
|--------|---------------------------|------------------|-----|
| **Önizleme + timeline** | 95 | 62 | Oynatıcı, in/out, sürükleme var; dalga formu / çok iz yok |
| **Kes · dönüştür · birleştir** | 90 | 75 | FFmpeg API + panel tam; göreli yoldan probe yok |
| **İndirme (yt-dlp)** | 85 | 68 | Çalışır; kurulum pip dışı, virüs kalkanı zorunlu |
| **Altyazı göm + tercüme** | 80 | 55 | Ayrı paneller; tek tık pipeline yok |
| **Çok parçalı kurgu** | 85 | 58 | Mix var (≤5 dk/parça); görsel timeline zayıf |
| **Sohbetten iş** | 70 | 35 | İndir + arama; kes/kurgu/altyazı yok |
| **UI / sinema deneyimi** | 90 | 72 | Yeni layout; küçük UX boşlukları |
| **AI sahne / plan** | 75 | 15 | `ilim-video/` CLI — API bağlı değil |
| **Performans / büyük dosya** | 85 | 50 | 600 MB upload; ilerleme çubuğu yok |
| **Yardım + keşfedilebilirlik** | 80 | 25 | `?` rehberi yazılmadı |

**Genel:** ~**52/100** — güçlü FFmpeg omurga, **henüz süper editör değil**. Ana boşluk: **birleşik iş akışları + sohbet niyeti + timeline zenginliği**.

---

## 2. Eksiklik → faz eşlemesi

| # | Eksiklik (rapordan) | Faz |
|---|---------------------|-----|
| E1 | Son indirmelere tıklayınca form doldurma | V1 |
| E2 | Kurgu bin boş mesajı toggle | V1 |
| E3 | Göreli yoldan probe (upload şart değil) | V1 |
| E4 | yt-dlp requirements + kurulum rehberi | V1 |
| E5 | Yardım (`?`) Video motor bölümü | V1 |
| E6 | Tüm dock paneller smoke test listesi | V1 |
| E7 | Sohbetten kes / kurgu / altyazı niyeti | V2 |
| E8 | İş bitince oynatıcıda çıktı önizleme | V2 |
| E9 | Uzun FFmpeg işlerinde ilerleme + iptal | V2 |
| E10 | Altyazı → çevir → göm pipeline | V3 |
| E11 | Timeline klavye kısayolları | V3 |
| E12 | Sürükle-bırak dosya → timeline / bin | V3 |
| E13 | Çok iz / basit waveform | V4 |
| E14 | Kurgu parça limiti UX (5 dk uyarı + bölme) | V4 |
| E15 | `ilim-video` plan → montaj API | V5 |
| E16 | Şablon preset (intro, sosyal 9:16) | V5 |
| E17 | Web/Electron export klasörü tutarlılığı | V1–V2 |
| E18 | Playlist / toplu indirme (bilinçli kapalı → opt-in) | V6 |

---

## 3. Hedef mimari (süper editör)

```text
┌─────────────────────────────────────────────────────────────┐
│  Üst şerit: hızlı işlemler + iş kuyruğu rozeti              │
├──────────┬──────────────────────────────────────────────────┤
│  Sohbet  │  SİNEMA SAHNESİ                                   │
│  (niyet  │  ┌─────────────────────────────────────────────┐ │
│   + ROK) │  │  Oynatıcı (letterbox)                        │ │
│          │  └─────────────────────────────────────────────┘ │
│          │  ┌─────────────────────────────────────────────┐ │
│          │  │  Timeline: playhead · range · (waveform)     │ │
│          │  └─────────────────────────────────────────────┘ │
│          │  Dock overlay: indir · kes · altyazı · kurgu…   │
└──────────┴──────────────────────────────────────────────────┘
         │
         ▼
   Yerel API (8779) ──► FFmpeg / yt-dlp / havuz / virüs kalkanı
         │
         ▼
   .ruzgar-video-export/  +  hafiza/video_indirilen/
```

**Prensipler (kilitli):**
- Sinema sahnesi asla kalabalıklaşmaz; ağır paneller yalnızca dock.
- Her iş sonunda: **durum mesajı + isteğe çıktıyı oynat**.
- Sohbet panel işlemini tekrarlamaz; niyet → API veya panel aç.
- Virüs kalkanı indirmede varsayılan kalır.

---

## 4. Uygulama programı (V1–V6)

### V1 — Temel sağlam (1–2 oturum) · **ŞİMDİ**

**Hedef:** Mevcut özellikler güvenilir, keşfedilebilir, boş UX delikleri kapalı.

| Adım | İş | Dosyalar | Bitti say |
|------|-----|----------|-----------|
| V1.1 | Son indirmeler: tıkla → URL / rel alanlarını doldur | `app.js` | ✓ |
| V1.2 | Kurgu bin: `#video-edit-bin-empty` toggle | `app.js` | ✓ |
| V1.3 | Probe: repo `rel` yolu ile (upload alternatifi) | `app.js`, `desktop_server.py` | ✓ |
| V1.4 | FFmpeg/yt-dlp sağlık: `#video-engine-hint` net mesaj | `app.js`, `/api/health` | ✓ |
| V1.5 | `?` yardım: Video motoru bölümü (madde madde) | `index.html` | ✓ |
| V1.6 | Smoke checklist dokümanı + manuel test | `docs/VIDEO_MOTOR_SMOKE.md` | ✓ |
| V1.7 | yt-dlp `requirements.txt` | `ilim-assistant/requirements.txt` | ✓ |

**Çıktı:** “Panel açıyorum, iş bitiyor, ne oldu anlıyorum.”

---

### V2 — Akıllı iş akışı (2–3 oturum)

**Hedef:** İş bitince editör hissi; sohbet basit FFmpeg emirlerini anlar.

| Adım | İş | Katman |
|------|-----|--------|
| V2.1 | İş sonrası: çıktı dosyasını oynatıcıya yükle + flash | UI | ✓ |
| V2.2 | FFmpeg job SSE veya poll ile **ilerleme çubuğu** | API + UI | ✓ (belirsiz çubuk; SSE sonraki) |
| V2.3 | Sohbet ROK: «kes 0:30–1:00», «medya bilgisi», «çıktı klasörü» | `video_faz71.py` | ✓ |
| V2.4 | Sohbet: panel açma («kesim panelini aç») | `video-atolye.js` + Faz 71 | ✓ |
| V2.5 | Hata mesajları Türkçe, eylem önerili (ffmpeg yok → link) | API + UI | ✓ |

**Çıktı:** “Sohbetten de basit iş; uzun işte bekliyorum ama görüyorum.”

---

### V2.5+ — Sohbet süper beyin (2026-06-07)

**Hedef:** Düğme yerine konuşarak sinema paneli; tercüme motoru `tryAtolyeFromMessage` deseni.

| Bileşen | Dosya |
|---------|--------|
| Niyet yönlendirici | `video-chat-brain.js` |
| Bağlantı | `app.js` → `sendMessageWithText` (tercüme gibi erken yakalama) |
| Genel mod hub | `ana_motor_hub_faz76.py` → `is_video_workflow_request` |
| Sunucu ROK | `video_faz71.py` genişletildi |

**Sohbet komutları (örnek):** yardım · link indir/oynat · arama · son indirmeler · kes · medya bilgisi · timeline işaretle · kurgu · dönüştür · panel aç · sıfırla

---

### V3 — Profesyonel timeline (3–4 oturum)

**Hedef:** Klavye + sürükle-bırak; altyazı pipeline.

| Adım | İş |
|------|-----|
| V3.1 | Klavye: Space play/pause, I/O in/out, Enter kesime yaz |
| V3.2 | Dosyayı sinema sahnesine sürükle → seç + probe |
| V3.3 | **Altyazı pipeline sihirbazı:** dosya seç → tercüme → geri dön → burn (3 adım UI) |
| V3.4 | Kesim panelinde «son çıktıyı birleştir» kısayolu |
| V3.5 | Dock: panel boyutu hatırla (localStorage) |

**Çıktı:** “Mouse + klavye ile hızlı kesim; altyazı işi tek akış.”

---

### V4 — Görsel zenginlik (4+ oturum)

**Hedef:** Timeline editör seviyesine yaklaşma (hobi+).

| Adım | İş |
|------|-----|
| V4.1 | Basit waveform (ffprobe + canvas veya statik thumb strip) |
| V4.2 | Kurgu bin: thumbnail + süre etiketi |
| V4.3 | 5 dk limit UX: aşımda otomatik böl veya uyarı |
| V4.4 | Çoklu seçim export listesi (son 10 iş) |
| V4.5 | Sinema modda mini «iş geçmişi» şeridi |

**Çıktı:** “Nereyi kestiğimi görüyorum; kurgu listesi okunaklı.”

---

### V5 — AI plan + şablon (ileri)

**Hedef:** `ilim-video` entegrasyonu; hızlı sosyal format.

| Adım | İş |
|------|-----|
| V5.1 | `POST /api/video/plan` — sahne JSON (Ollama) |
| V5.2 | Plan → görsel kurgu bin’e aktar |
| V5.3 | Preset: 9:16, 16:9, «konuşma khead» crop |
| V5.4 | Basit intro/outro metin kartı (FFmpeg drawtext) |

**Not:** Sinema kalitesi AI video üretimi kapsam dışı; plan + montaj birleşimi kapsam içi.

---

### V6 — İsteğe bağlı güç (uzun vade)

- Playlist indirme (`RUZGAR_YTDLP_PLAYLIST=1` + UI onay)
- Proje dosyası `.ruzgar-video` (timeline + bin kaydet/yükle)
- Ses seviyesi normalize (EBU R128 basit)
- Video motor ↔ Programlama motor handoff («bu kesimi scriptle»)

---

## 5. İlk sprint — sıradaki 7 adım (V1)

Ümit abi onayı ile **bu sırayla** kodlayalım:

1. **V1.1** — Son indirmeler tıklanabilir  
2. **V1.2** — Kurgu bin boş mesajı  
3. **V1.4** — Engine hint (ffmpeg / yt-dlp / sunucu)  
4. **V1.3** — Rel yoldan probe  
5. **V1.5** — Yardım metni Video bölümü  
6. **V1.6** — Smoke checklist  
7. **V1.7** — yt-dlp kurulum notu  

Her adım: küçük PR/commit, Ctrl+Shift+R test, smoke maddesini işaretle.

---

## 6. Başarı ölçütleri (V1→V3)

| Milestone | Kriter |
|-----------|--------|
| **V1 bitti** | 8 dock paneli smoke’tan geçer; yardım metni var; hint doğru |
| **V2 bitti** | Sohbetten en az 3 FFmpeg niyeti çalışır; trim sonrası oynatıcıda çıktı |
| **V3 bitti** | Altyazı pipeline uçtan uca; 5 klavye kısayolu dokümante |
| **Süper editör (V4+)** | Genel puan ≥75; Ümit abi günlük kesim işini panel + sohbet karışık yapar |

---

## 7. Riskler

| Risk | Önlem |
|------|--------|
| FFmpeg/libass Windows PATH | V1.4 hint + kurulum linki |
| yt-dlp güncel değil | requirements + sürüm pin notu |
| Büyük dosya | rel yol + upload limit mesajı |
| Dock/CSS cache | `?v=` bump kuralı (video-atolye) |
| Virüs kalkanı sürtünme | Panelde «onay bekliyor» banner (V2) |

---

## 8. İlgili dosyalar

| Alan | Yol |
|------|-----|
| UI dock | `ruzgar-desktop/video-atolye.js`, `video-atolye.css` |
| İş mantığı | `ruzgar-desktop/app.js` (video bloğu) |
| Sidebar | `ruzgar-desktop/modules/video/manifest.json` |
| API | `ilim-assistant/desktop_server.py` |
| FFmpeg | `ilim_assistant/video_ffmpeg.py` |
| Motor | `ilim_assistant/motorlar/video_motoru.py` |
| Sohbet ROK | `video_faz71.py`, `video_faz84.py` |
| AI plan (ileri) | `ilim-video/` |

---

*Son güncelleme: 2026-06-08 — V6 storyboard yol haritası eklendi.*

---

## 9. V6–V9 — Hikâye canlandırma

> **Hedef:** Sohbetten hikâye (+ isteğe fotoğraf) → Rüzgar kahramanları canlandırır, sinemada video oynatır.

| Faz | Ne | Durum |
|-----|-----|--------|
| V5 | Ses + fotoğraf/zoom montajı | Aktif |
| V6 | Storyboard: kahraman, mekân, asset eşlemesi | Aktif |
| V7.1 | Yerel sinematik hareket (pan/zoom/drift) | Aktif |
| V7.2 | Konuşan portre (SadTalker / RUZGAR_SADTALKER_ROOT) | Aktif (kurulum gerekir) |
| V8 | AI sahne klibi (Runway API) | Aktif (API anahtarı gerekir) |
| V9 | Dudak senkronu + tam pipeline | Plan |

V5 «slayt»dır; V7.1 yerel hareket. V7.2/V8 harici model veya API ister — yoksa otomatik hareket yedeği.
Kurulum notları: `ilim-assistant/env.video.example`
