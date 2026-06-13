# Ana Motor — Faz AC Planı (2026-06-13)

> **Hedef:** Ana Motor güç turları — adım adım, yanlış yapmadan.

## AC1 — denge70 otomasyon ✅ (2026-06-13)

| # | Görev | Dosya | Davranış |
|---|--------|-------|----------|
| AC1a | RAM kapılı otomatik pull | `ruzgar_denge70_faz_k.py` | API açılışında ≥14 GB boş RAM → arka plan `ollama pull` |
| AC1b | Pull API | `desktop_server.py` | `POST /api/ana-motor/denge70/pull` |
| AC1c | Durum genişletme | `denge70_faz_k_status` | `pull_job`, `ram_available_gb`, `auto_pull` |
| AC1d | UI panel | `index.html`, `app.js` | Ana Motor sayfasında 70B kartı |
| AC1e | Smoke | `ana_motor_smoke.py` | Faz AC1 kontrolleri |

### Ortam

```env
RUZGAR_DENGE70_AUTO_PULL=1
RUZGAR_DENGE70_AUTO_CHAIN=1
RUZGAR_DENGE70_MIN_RAM_GB=14
RUZGAR_DENGE70_PULL_TIMEOUT_SEC=7200
RUZGAR_BRAIN_DENGE70_MODEL=llama3.1:70b
```

### Başarı ölçütü

1. Health → `denge70_faz_k.auto_chain_ready: true` (model indirildiyse + RAM yeterliyse)
2. Bilgi/bilim sorusunda zincirde `denge70` görünür
3. UI panel «70B hazır» veya «indiriliyor» durumunu gösterir

## AC2 — Canlı SLO gece koşusu (sıradaki)

- `python scripts/ana_motor_smoke.py --live http://127.0.0.1:8779 --slo-pack`
- Zayıf senaryo raporu

## AC3 — Sesli tur VAD paneli (sıradaki)

- Health VAD eşikleri → kullanıcı ayar paneli

## AC4 — Otomatik öğrenme → Nebula (sıradaki)

- `ruzgar_otomatik_ogrenme.py` köprüsü

*Bismillah — Ümit & Gökçenur*
