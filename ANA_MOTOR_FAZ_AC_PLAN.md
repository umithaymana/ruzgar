# Ana Motor — Faz AC Planı (2026-06-13)

> **Hedef:** Ana Motor güç turları — adım adım.

## AC1 — denge70 otomasyon ✅

## AC2 — Canlı SLO + zayıf nokta raporu ✅

## AC3 — Sesli tur VAD paneli ✅ (2026-06-13)

| # | Görev | Dosya | Davranış |
|---|--------|-------|----------|
| AC3a | Kullanıcı VAD dosyası | `ruzgar_sesli_tur_faz_k.py` | `.ruzgar_vad_ayarlari.json` |
| AC3b | API | `desktop_server.py` | `GET/POST /api/ana-motor/sesli-tur/vad` |
| AC3c | UI kaydırıcılar | `index.html`, `app.js` | 4 eşik + kaydet/sıfırla |
| AC3d | Health birleşik VAD | aynı | `sesli_tur_vad_effective()` |

### Alanlar

- **Sessizlik eşiği (ms)** — konuşma bitince gönder
- **Minimum kayıt (ms)** — kısa gürültüyü yoksay
- **Sessizlik hassasiyeti** — mikrofon ortalaması eşiği
- **TTS sonrası gecikme (ms)** — sesli tur döngüsü

## AC4 — Otomatik öğrenme → Nebula (sıradaki)

*Bismillah — Ümit & Gökçenur*
