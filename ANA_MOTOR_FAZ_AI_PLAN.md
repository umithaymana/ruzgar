# Ana Motor — Faz AI Planı (2026-06-13)

> **Hedef:** Arşivden gelen yanıtları görünür kılmak + arama kutusunda arşiv önizlemesi.

## AI1 — Arşiv rozeti ✅

| # | Görev | Dosya | Davranış |
|---|--------|-------|----------|
| AI1a | Meta köprü | `ana_motor_faz_ai_archive_badge.py` | `resolve_archive_recall_turn` |
| AI1b | SSE | `desktop_server.py` | `done.archive_recall` |
| AI1c | UI | `app.js`, `styles.css` | Balonda «Arşivden» rozeti |

### Ortam

```env
RUZGAR_ARCHIVE_BADGE=1
```

## AI2 — Arşiv arama önizleme ✅

| # | Görev | Dosya | Davranış |
|---|--------|-------|----------|
| AI2a | Önizleme | `ana_motor_faz_ai_arsiv_onizleme.py` | jsonl arama satırları |
| AI2b | API | `desktop_server.py` | `GET /api/ana-motor/chat-memory/search-preview` |
| AI2c | UI | `index.html`, `app.js` | Arama altında önizleme kutusu |

### Ortam

```env
RUZGAR_ARSIV_ONIZLEME=1
```

## Sıradaki (Faz AJ — uygulandı)

Detay: `ANA_MOTOR_FAZ_AJ_PLAN.md`

*Bismillah — Ümit & Gökçenur — Faz AI tamam*
