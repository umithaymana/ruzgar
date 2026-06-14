# Ana Motor — Faz AJ Planı (2026-06-13)

> **Hedef:** Arşiv önizlemeden tek tıkla soru yapıştırma + SLO env rehber vs canlı ortam diff.

## AJ1 — Arşiv yapıştır ✅

| # | Görev | Dosya | Davranış |
|---|--------|-------|----------|
| AJ1a | Insert köprü | `ana_motor_faz_aj_arsiv_yapistir.py` | Arşiv satırı → yazı alanı |
| AJ1b | UI | `index.html`, `app.js` | Tıklanabilir arşiv listesi |

### Ortam

```env
RUZGAR_ARSIV_YAPISTIR=1
```

## AJ2 — SLO env diff ✅

| # | Görev | Dosya | Davranış |
|---|--------|-------|----------|
| AJ2a | Diff motor | `ana_motor_faz_aj_slo_env_diff.py` | eksik / farklı / uyumlu |
| AJ2b | API | `desktop_server.py` | `GET /api/ana-motor/slo-pack/env-diff` |
| AJ2c | UI | `app.js` | SLO panelinde diff satırı |

### Ortam

```env
RUZGAR_SLO_ENV_DIFF=1
```

*Bismillah — Ümit & Gökçenur — Faz AJ tamam*
