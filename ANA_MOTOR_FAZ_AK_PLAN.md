# Ana Motor — Faz AK Planı (2026-06-13)

> **Hedef:** Env diff tek tık kopyala + arşiv turunu sohbete hatırlat balonu.

## AK1 — SLO env diff kopyala ✅

| # | Görev | Dosya | Davranış |
|---|--------|-------|----------|
| AK1a | Kopya metin | `ana_motor_faz_ak_slo_env_kopya.py` | eksik/farklı satırlar |
| AK1b | API | `desktop_server.py` | `GET /api/ana-motor/slo-pack/env-copy` |
| AK1c | UI | `app.js` | «Eksik env kopyala» butonu |
| AK1d | Fix | `app.js` | SLO panel kalıcı rapor yükleme |

### Ortam

```env
RUZGAR_SLO_ENV_KOPYA=1
```

## AK2 — Arşiv hatırlat balonu ✅

| # | Görev | Dosya | Davranış |
|---|--------|-------|----------|
| AK2a | Kart | `ana_motor_faz_ak_arsiv_hatirlat.py` | markdown balon gövdesi |
| AK2b | UI | `app.js` | Arşiv satırında «Hatırlat» |

### Ortam

```env
RUZGAR_ARSIV_HATIRLAT=1
```

*Bismillah — Ümit & Gökçenur — Faz AK tamam*
