# Ana Motor — Faz AC Planı (2026-06-13)

> **Hedef:** Ana Motor güç turları — tamamlandı.

## AC1 — denge70 otomasyon ✅

## AC2 — Canlı SLO + zayıf nokta raporu ✅

## AC3 — Sesli tur VAD paneli ✅

## AC4 — Otomatik öğrenme → Nebula ✅ (2026-06-13)

| # | Görev | Dosya | Davranış |
|---|--------|-------|----------|
| AC4a | QA Nebula paketi | `ana_motor_nebula_apply.py` | `write_nebula_qa_batch` |
| AC4b | Köprü | `ruzgar_otomatik_ogrenme.py` | Öğrenme sonrası incremental + indeks |
| AC4c | API | `desktop_server.py` | `GET /api/ana-motor/otomatik-ogrenme/status` |
| AC4d | UI | `index.html`, `app.js` | Durum paneli |

### Ortam

```env
RUZGAR_OTOMATIK_OGRENME=1
RUZGAR_KUTUPHANE_ONCE=1
RUZGAR_OGRENME_NEBULA_BRIDGE=1
RUZGAR_OGRENME_NEBULA_COLLECTION=tarih_kaynak
```

### Akış

1. Bilgi/bilim sorusu → web/hafıza → yanıt
2. `auto_learn_from_turn` → `ruzgar_genel_hafiza.json` + `knowledge/learned/`
3. Uygun turda → `knowledge/nebula/<koleksiyon>/incremental/nebula_batch_*.md` + arka plan indeks

*Bismillah — Ümit & Gökçenur — Faz AC tamam*
