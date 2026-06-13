# Ana Motor — Faz AE Planı (2026-06-13)

> **Hedef:** AD kalıcılığını trend analizine çevirmek + Sentez PRO → Nebula öğrenme köprüsü.

## AE1 — SLO trend raporu ✅

| # | Görev | Dosya | Davranış |
|---|--------|-------|----------|
| AE1a | Trend motor | `ana_motor_faz_ae_slo_trend.py` | Son N rapor skoru, tekrarlayan zayıf S* |
| AE1b | API | `desktop_server.py` | `GET /api/ana-motor/slo-pack/trend` |
| AE1c | UI | `index.html`, `app.js` | SLO panelinde trend satırı |

### Ortam

```env
RUZGAR_SLO_TREND=1
```

## AE2 — Sentez PRO → öğrenme köprüsü ✅

| # | Görev | Dosya | Davranış |
|---|--------|-------|----------|
| AE2a | PRO boost | `ana_motor_faz_ae_pro_ogrenme.py` | PRO turda Nebula köprüsü güçlendir |
| AE2b | Chat hook | `desktop_server.py` | Yanıt sonrası `maybe_boost_learn_after_pro_turn` |
| AE2c | API | `desktop_server.py` | Health + `pro_ogrenme_faz_ae` |
| AE2d | UI | `app.js` | Öğrenme panelinde PRO notu |

### Ortam

```env
RUZGAR_PRO_OGRENME_BRIDGE=1
RUZGAR_SENTEZ_PRO=1
RUZGAR_OTOMATIK_OGRENME=1
```

### Akış

1. Kalıcı SLO raporları → skor eğilimi + «S3 tekrar kırıldı» uyarısı
2. PRO sentezli bilgi turu → hafıza + learned MD + Nebula (PRO güçlendirme)

## Sıradaki (Faz AF — uygulandı)

Detay: `ANA_MOTOR_FAZ_AF_PLAN.md`

*Bismillah — Ümit & Gökçenur — Faz AE tamam*
