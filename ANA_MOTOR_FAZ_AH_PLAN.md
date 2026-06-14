# Ana Motor — Faz AH Planı (2026-06-13)

> **Hedef:** Sohbet arşivi hafıza görünürlüğü + SLO aksiyonlarından güvenli .env rehberi.

## AH1 — Hafıza arşiv durumu ✅

| # | Görev | Dosya | Davranış |
|---|--------|-------|----------|
| AH1a | Arşiv istatistik | `ana_motor_sohbet_gecmis.py` | `chat_history_stats` |
| AH1b | AH köprü | `ana_motor_faz_ah_hafiza_recall.py` | Durum + arama önizleme |
| AH1c | API | `desktop_server.py` | `GET /api/ana-motor/chat-memory/status` |
| AH1d | UI | `index.html`, `app.js` | Sohbet panelinde arşiv satırı |

### Ortam

```env
RUZGAR_HAFIZA_RECALL=1
RUZGAR_ANA_CHAT_HISTORY=1
```

## AH2 — SLO .env rehberi ✅

| # | Görev | Dosya | Davranış |
|---|--------|-------|----------|
| AH2a | Rehber motor | `ana_motor_faz_ah_slo_env_rehber.py` | AF aksiyon → kopyalanabilir env |
| AH2b | API | `desktop_server.py` | `GET /api/ana-motor/slo-pack/env-rehber` |
| AH2c | UI | `index.html`, `app.js` | SLO panelinde kopyala butonu |

### Ortam

```env
RUZGAR_SLO_ENV_REHBER=1
RUZGAR_SLO_AKSIYON=1
```

*Not: Rehber yalnızca öneri üretir — .env otomatik değiştirilmez.*

## Sıradaki (Faz AI — uygulandı)

Detay: `ANA_MOTOR_FAZ_AI_PLAN.md`

*Bismillah — Ümit & Gökçenur — Faz AH tamam*
