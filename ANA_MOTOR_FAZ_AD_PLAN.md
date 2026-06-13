# Ana Motor — Faz AD Planı (2026-06-13)

> **Hedef:** SLO kalıcılığı + gece koşusu + çok kaynak sentez PRO.

## AD1 — SLO gece koşusu ve rapor kalıcılığı ✅

| # | Görev | Dosya | Davranış |
|---|--------|-------|----------|
| AD1a | Kalıcı rapor | `ana_motor_faz_ad_slo_gece.py` | `.ruzgar_slo_last_report.json`, `.ruzgar_slo_reports/` |
| AD1b | Worker hook | `ruzgar_canli_slo_faz_k.py` | Paket bitince `persist_slo_report` |
| AD1c | Startup | `desktop_server.py` | `maybe_schedule_gece_slo_on_startup` (24 saat) |
| AD1d | API | `desktop_server.py` | `GET /api/ana-motor/slo-pack/last-report`, `report-file` |
| AD1e | UI | `index.html`, `app.js` | Gece durumu + son kayıt satırı |

### Ortam

```env
RUZGAR_SLO_GECE_KOSUSU=1
RUZGAR_SLO_GECE_INTERVAL_HOURS=24
```

## AD2 — Sentez PRO (web + yerel + kütüphane) ✅

| # | Görev | Dosya | Davranış |
|---|--------|-------|----------|
| AD2a | PRO kapı | `ana_motor_faz_ad_sentez_pro.py` | `should_synthesize_pro_turn` |
| AD2b | Birleşik özet | `ana_motor_faz_ad_sentez_pro.py` | Kütüphane hint + web PRO + RAG |
| AD2c | Chat | `chat_core.py` | PRO önce, sonra klasik sentez |
| AD2d | API | `desktop_server.py` | `GET /api/ana-motor/sentez-pro/status` |
| AD2e | UI | `index.html`, `app.js` | Durum paneli |

### Ortam

```env
RUZGAR_SENTEZ_PRO=1
RUZGAR_WEB_ARASTIRMA_PRO=1
RUZGAR_KUTUPHANE_ONCE=1
```

### Akış

1. Bilgi/bilim sorusu → web PRO + yerel RAG + BilgiKutuphane
2. Uygun turda → `[ARAŞTIRMA ÖZETİ PRO — Faz AD2]` bağlam bloğu
3. SLO paketi bitince → JSON/MD arşiv; 24 saatten eskiyse startup’ta arka plan koşusu

## Sıradaki (Faz AE — uygulandı)

Detay: `ANA_MOTOR_FAZ_AE_PLAN.md`

*Bismillah — Ümit & Gökçenur — Faz AD tamam*
