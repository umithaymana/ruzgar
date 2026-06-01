# Tercüme motoru — Faz 14B (kalite skoru UI)

**Hedef:** Backend’deki `quality` nesnesini kullanıcıya göstermek; düşük skorda uyarı ve tek parça yeniden çeviri.

| Kod | Konu | Durum |
|-----|------|--------|
| **14B-1** | Kalite şeridi (rozet 0–100, yeşil/sarı/kırmızı) | ✅ |
| **14B-2** | Sorun metni (`issues`) | ✅ |
| **14B-3** | Arka plan iş: `quality_summary` (ortalama, düşük sayfa) | ✅ |
| **14B-4** | İş logunda ⚠ düşük skorlu sayfalar | ✅ |
| **14B-5** | **Yeniden çevir** (Tek parça, son parça) | ✅ |

## Eşikler

- **≥ 75** — iyi (yeşil)
- **55–74** — uyarı (sarı), yeniden çevir önerilir
- **< 55** — düşük (kırmızı)

## Test

```powershell
cd ilim-assistant
python scripts/tercume_faz14b_smoke.py
python scripts/tercume_faz14a_smoke.py
node --check ..\ruzgar-desktop\tercume-atolye.js
```

## Sonraki (14C)

- Kalıcı terim belleği (TM) diske
