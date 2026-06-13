# Ana Motor — Faz AC Planı (2026-06-13)

> **Hedef:** Ana Motor güç turları — adım adım.

## AC1 — denge70 otomasyon ✅

RAM kapılı otomatik `ollama pull`, UI panel, `POST /api/ana-motor/denge70/pull`.

## AC2 — Canlı SLO + zayıf nokta raporu ✅ (2026-06-13)

| # | Görev | Dosya | Davranış |
|---|--------|-------|----------|
| AC2a | Zayıf nokta raporu | `ruzgar_canli_slo_faz_k.py` | `build_weak_point_report` + öneriler |
| AC2b | Arka plan SLO | aynı | `POST /api/ana-motor/slo-pack/run-background` |
| AC2c | Job durumu | aynı | `GET /api/ana-motor/slo-pack/job` |
| AC2d | UI panel | `index.html`, `app.js` | SLO koş + rapor listesi |
| AC2e | Smoke | `ana_motor_smoke.py` | Rapor birimi + `--slo-pack` rapor çıktısı |

### Kullanım

```bash
# Tam canlı koşu + terminal raporu (~10 dk, API açık)
python scripts/ana_motor_smoke.py --live http://127.0.0.1:8779 --slo-pack

# UI: Ana Motor → «Canlı SLO testi» → SLO koş
```

## AC3 — Sesli tur VAD paneli (sıradaki)

## AC4 — Otomatik öğrenme → Nebula (sıradaki)

*Bismillah — Ümit & Gökçenur*
