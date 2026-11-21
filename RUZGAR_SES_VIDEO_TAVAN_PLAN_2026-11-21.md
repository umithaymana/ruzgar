# RÜZGAR — Ses tavanı + Video ses gereksinimleri planı

**Tarih:** 2026-11-21  
**Mimar:** Ümit & Gökçenur  
**Durum:** S0–S4 YEŞİL + XTTS canlı + **FB/iptal/VRAM cila** (2026-11-21) — sırada **V1**  






**Dal:** `cursor/sohbet-akicilik-a-f`  
**Önceki mühür:** Sohbet sahne-kaçma + mobil kilit (`MUHUR_SOHBET_SAHNE_KACMA_MOBIL_2026-11-21.md`)  
**Boot / ana yüz:** dokunulmaz  
**Kim ilerletir:** **Usta (Cursor)** — çırak yalnız dar ödev; Ses tavanı çırağa verilmez  
**S3 not:** BUSENAZ+kuran + **XTTS canlı YEŞİL** (coqui-tts 0.28 · smoke wav) · Edge yedek kalır  
**S4 not:** Raftan kısa pasaj → `/api/okuma/pasaj` + `/api/tts` · masa buton + mobil «raftan oku …» · smoke 26/26  
**Cila not:** FB medyan ~917 ms (S0 1311) · `POST /api/tts/cancel` · VRAM hakemi 8GB · smoke_fb 27/27

---

## 0) Başarı cümlesi

Kur’an’da huşû (imam edası); hadis / tefsirde vakur âlim sohbeti; günlük muhabbette doğal Rüzgar sesi; video’da dublaj ve efekt aynı ses omurgasından beslensin — masaüstü = mobil.

---

## 1) Neden tek plan? (Ses + Video)

Ses motoru yalnız «konuşsun» değil. Video motoru da aynı kaliteyi ister:

| Video ihtiyacı | Ses omurgasına bağı |
|----------------|---------------------|
| Dublaj (çeviri + TTS + mux) | Tilavet / âlim / muhabbet / klon profilleri |
| Anlatıcı / hikâye sesi | Prosodi + karakter |
| Efekt / ambiyans / jingle | Ses kütüphanesi + zaman çizelgesi |
| Altyazı + sesli okuma | Okuma + TTS |
| Videodan referans ses | Klon hattı (`ses_videodan_referans`) |
| İleride dudak senkronu | Yüksek kalite + zaman damgalı TTS |

**Kural:** Ses tavanı önce yükselir; Video bu tavandan **tüketir**. İki ayrı «iyi ses» yapılmaz.

---

## 2) Mevcut zemin (bozma — üzerine ekle)

| Parça | Durum |
|-------|--------|
| Ses V0–V5 · Aşama A–D | Mühürlü arka |
| `ses_tilavet` · `ses_prosody` · `ses_klon_motoru` | İskelet var; tavan düşük |
| `video_dublaj` (S6 MVP, tek anlatıcı) | Prototip; dudak senkronu yok |
| `ses_videodan_referans` · kolon kütüphanesi | Var |
| Edge-TTS | Yedek / hızlı; kalite tavanı sınırlı |
| Okuma → sesle kitap | Askıdaki vizyon; bu plana dilim olarak girer |

---

## 3) Ses tavanı — hedefler (Mimar vizyon)

### 3.1 Kalite
- Robot hissi minimum; ilk ses hızlı; barge-in sağlam  
- Ölçü: ilk-byte ms · robot skoru (kulaktan) · mobil = PC  

### 3.2 Üç (sonra dört) karakter
1. **Muhabbet** — günlük sohbet, sıcak, kısa  
2. **Âlim** — hadis / tefsir / fıkıh: vakur, ağırbaşlı, dinleyen edası  
3. **Tilavet** — Kur’an: Mekke imamı **edası** (tempo, vakıf, huşû, tecvid bilinci)  
4. *(opsiyon)* **Anlatıcı** — kitap / ders okuma  

### 3.3 Klon
- Rüzgar’ın kendi sesi (izinli referans WAV)  
- Tilavet / âlim için ayrı profil (yalnız **izinli** referans)  
- **Etik:** İsimli imamı / telifli tilaveti çalmak yok → eda + kendi kayıt / açık lisans  

### 3.4 Okuma bağ
- Raftan eser → sesle oku; devam / tekrar / daha yavaş / daha huşûlu  

---

## 4) Video — ses gereksinimleri (şimdi + aklıma gelenler)

### 4.1 Dublaj (yükseltilecek)
- Tek anlatıcı MVP → **stabil kalite** (aynı profil sesi)  
- Segment zamanına oturtma (sessizlik / sıkıştırma)  
- İsteğe bağlı: orijinal ses kısık + dublaj üstte (mix)  
- Çok karakterli dublaj = **ikinci tavan** (şimdi yok)  
- Dudak senkronu = **ikinci tavan**  

### 4.2 Efekt / ses tasarımı
- Geçiş jingle, vurgu «ding», soft ambiyans (ders / hikâye)  
- Efekt kütüphanesi: `arsiv/ses-efekt/` + isimle çağır («kapı sesi», «sayfa çevir»)  
- Ses seviyesi normalizasyonu (dublaj boğmasın)  

### 4.3 Altyazı + ses
- Altyazı üret → isteğe bağlı **sesli okut** (erişilebilirlik)  
- Öğretici videoda «satır takip» (okuma motoru ile hizalı düşün)  

### 4.4 Hikâye / storyboard
- Sahne başına anlatıcı cümlesi → TTS  
- Karakter başına ses profili (ileride; şimdi tek anlatıcı)  

### 4.5 Referans / klon köprüsü
- YouTube/yerel videodan temiz konuşma dilimi → klon referansı  
- Tilavet videosundan (izinli) referans çıkarma  

### 4.6 Canlı / yayın (ikinci tavan)
- Ders kaydı mp3/mp4 arşiv  
- Canlı anlatım + ekran (ayrı dilim)  

### 4.7 Bilinçli yapılmayacaklar (bu tavan turunda)
- Hollywood dudak senkronu  
- Telifsiz müzik / imam klonu  
- Boot / ana yüz / sahne yeni dilim  
- %90 serbest ajan  

---

## 5) Ortak omurga (tek sözleşme)

```
İçerik türü → Ses profili (muhabbet|alim|tilavet|anlatıcı)
            → Motor (klon öncelik | Edge yedek)
            → Prosodi / durak
            → Çıktı: sohbet | okuma | dublaj mux | efekt mix
```

- Masaüstü atölye + Mobil PWA **aynı API / aynı profil**  
- Profil değişince Video dublaj da aynı sesi kullanır  

---

## 6) Dilim sırası (yavaş tavan)

| Dilim | İş | Yeşil |
|-------|-----|--------|
| **S0** | Ölçüm kartı: şimdi robot/ilk-byte/mobil | Rapor + smoke tabanı |
| **S1** | Üç profil seçici (muhabbet / âlim / tilavet) Edge üzerinde bile | Sohbette profil doğru |
| **S2** | Prosodi + tilavet/âlim parametre tavanı | Kulak testi + smoke |
| **S3** | Klon yolu: Rüzgar sesi + 1 tilavet/âlim referans (izinli) | Klon yeşil / Edge yedek |
| **S4** | Okuma bağ: raftan kısa pasaj sesle oku | Masa + mobil |
| **V1** | Video dublaj: omurga profili + kalite mux | Tek film deneği yeşil |
| **V2** | Efekt kütüphanesi + seviye normalizasyonu | 3 efekt + dublaj mix |
| **V3** | Altyazı ↔ sesli okut (opsiyon) | 1 video smoke |
| **M** | Mini mühür: başarı cümlesi + mobil eşitlik | Mimar kartı |

**Sonra (ikinci tavan — plana not, şimdi kod yok):** çok karakter, dudak senkronu, duygu tonu, çift dil meal+ayet, ders arşivi.

---

## 7) Her dilimde zorunlu

1. Smoke veya canlı kulak notu  
2. Desktop + mobil aynı davranış (veya bilinçli «mobil sonra» + tarih)  
3. Bir satır ders → bu planın altına  
4. Boot / yüz / hub kırılganına dokunma  

---

## 8) Mimar cevapları (kilit — 2026-11-21)

1. **Klon:** `BUSENAZ ses` — ozel kolon `busenaz-ses` (sohbet/okuma); tilavete bağlı değil.  
2. **Tilavet WAV:** `arsiv/ses-referans/kuran.wav`.  
3. **Başlangıç:** S0→S3 yapı bitti; sırada **S4** veya kulak turu.  

Kulak: S0–S3 birlikte dinlenir. XTTS canlı: `coqui-tts` + `klon_onay` + BUSENAZ; yoksa/hata → Edge yedek.

---

## 9) Ders defteri (doldurulacak)

| Dilim | Ders | Smoke | Yeşil |
|-------|------|-------|-------|
| S0 | Yapı 5/5 · mobil=/api/tts barge OK · gap=muhabbet+tilavet · live first-byte **1311 ms** (V0 1686 / V3 hedef 900) · kulak skoru S1+ | `smoke_s0_ses_tavan` 14/14 + LIVE 16/16 · `docs/S0_SES_TAVAN_OLCUM_2026-11-21.md` | [x] |
| S1 | Üç profil Edge: muhabbet −8% / alim −27% / tilavet −38% · asistan→muhabbet · `BUSENAZ ses` yerinde | `smoke_s1_ses_tavan_profil` 27/27 · `docs/S1_SES_TAVAN_PROFIL_2026-11-21.md` | [x] |
| S2 | Durak 0.88&lt;1.22&lt;1.42 · ayet ~5456 ms · tilavet rate ekstra · API kanca · kulak checklist 3 | `smoke_s2_ses_prosodi_tavan` 19/19 · `docs/S2_SES_PROSODI_TAVAN_2026-11-21.md` | [x] yapı / [ ] kulak |
| S3 | BUSENAZ→muhabbet · kuran→tilavet · klon_onay · **XTTS canlı** (+ Edge yedek) | `smoke_s3` 21/21 · `_s3_busenaz_smoke.wav` · `docs/S3_SES_KLON_YOLU_2026-11-21.md` | [x] yapı+canlı |
| S4 | Raftan kısa pasaj → ses (âlim/tilavet) · devam/tekrar/yavas/husulu · masa+mobil aynı API | `smoke_s4_okuma_ses_bag` 26/26 · `docs/S4_OKUMA_SES_BAG_2026-11-21.md` | [x] yapı / [ ] kulak |
| … | | | |

---

*Ümit & Gökçenur Haymana'nın ortak projesi — Ses + Video tek ses omurgası.*
