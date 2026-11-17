# F6 — Mobil sürekli sohbet checklist

**Tarih:** 2026-11-17  
**Bağ:** `docs/F0_MOBIL_SUREKLI_KIRILMA_HARITASI_2026-11-17.md`

---

## F6.2 — Mic / HTTPS / Wake Lock

| # | Kontrol | Beklenen | Not |
|---|---------|----------|-----|
| 1 | Adres `https://<LAN-IP>:8443/mobil/` | Yeşil kilit / uyarı kabul | HTTP → otomatik 8443 yönlendirme |
| 2 | Mikrofon izni | İzin verildi | «sürekli: HTTPS + mikrofon gerekli» = halka 1–2 |
| 3 | Wake Lock | `sürekli: dinliyorum` (ekran kilidi yoksa uyarı metni) | Sekme arka plan → yeniden bağ |
| 4 | `GET /api/health` → `stt` / `stt_surface` | `ses_stt_pipeline` | F5.5 tek yüzey |
| 5 | Tailscale / Wi‑Fi | Aynı ağ veya TS IP | LAN ACL ayrı konu |

---

## F6.3 — Sürekli VAD (5 dk saha)

| # | Kontrol | Beklenen | Kod / kim |
|---|---------|----------|-----------|
| 1 | Sürekli sohbet açık | `sürekli: dinliyorum` | PWA `livePref` |
| 2 | Konuş → sessizlik | STT → tur → yine dinle | VAD loop `app.js` |
| 3 | 5 dakika kesintisiz | Kopma az; Wake Lock açık | **Mimar telefon** (saha) |
| 4 | Barge-in | Konuşunca TTS kesilir | F6.4 |

Kod smoke: `scripts/smoke_f6_pc_mobil_parity.py` (sözleşme). Canlı 5 dk = Mimar.

---

## F6.6 — `with_tts` politikası (tek canlı yol)

| Yol | `with_tts` | Ses |
|-----|------------|-----|
| Yazı / sürekli sohbet turu | **false** | Metin önce; sonra `/api/tts` veya `speakLocal` |
| Amaç | İlk token hızlı | Ses ayrı; çift bekleme yok |

History: canlıda `trimHistoryForVoice()` (−4 tur, 280 char).

---

## F6.7 — PC ↔ mobil parity

| Yüzey | PC (`ruzgar-desktop`) | Mobil PWA |
|-------|----------------------|-----------|
| STT | `POST /api/stt` | `POST /api/stt` (aynı) |
| Sohbet turu TTS | ayrı `/api/tts` / yerel | `with_tts: false` + ayrı TTS |
| Barge-in | `bargeInStopTtsForMic` | `stopAllSpeech` / barge timer |
| Sahne ACL | varsayılan yüz | varsayılan kapalı (ayrı kalabilir) |

Smoke: `smoke_f6_pc_mobil_parity.py`.

---

## Hızlı teşhis sırası

1. Mic/HTTPS (F6.2)  
2. STT meta: `sürekli: ses → metin…`  
3. Tur: `düşünüyor…` → yazı  
4. TTS / barge-in: konuşunca `kesildi — dinliyorum`  
5. F0 kart: `/api/tur-teshis/recent`  

**Kural:** STT metni geldiyse F2 kütüphane; ses yoksa F6/F7.
