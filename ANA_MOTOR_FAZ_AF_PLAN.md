# Ana Motor — Faz AF Planı (2026-06-13)

> **Hedef:** AE trend verisini aksiyona çevirmek + PRO turda araştırma kartını zenginleştirmek.

## AF1 — SLO aksiyon planı ✅

| # | Görev | Dosya | Davranış |
|---|--------|-------|----------|
| AF1a | Aksiyon motor | `ana_motor_faz_af_slo_aksiyon.py` | Zayıf S* → .env / panel önerileri |
| AF1b | API | `desktop_server.py` | `GET /api/ana-motor/slo-pack/action-plan` |
| AF1c | UI | `index.html`, `app.js` | SLO panelinde aksiyon listesi |

### Ortam

```env
RUZGAR_SLO_AKSIYON=1
```

## AF2 — Araştırma kartı PRO ✅

| # | Görev | Dosya | Davranış |
|---|--------|-------|----------|
| AF2a | Kart zenginleştir | `ana_motor_faz_af_arastirma_pro.py` | PRO rozeti + kaynak sayımı |
| AF2b | Chat | `chat_core.py` | Sentez PRO sonrası kart güncelle |
| AF2c | UI | `app.js` | Araştırma kartında PRO satırı |

### Ortam

```env
RUZGAR_ARASTIRMA_PRO_CARD=1
RUZGAR_SENTEZ_PRO=1
```

*Bismillah — Ümit & Gökçenur — Faz AF tamam*
