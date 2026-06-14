# Ana Motor Faz AL — Hitap ayrıştırma + güncel jeopolitik

> **Mimar:** Ümit & Gökçenur · **2026-06-14**

## Amaç

1. «Rüzgar, …» hitabında asıl soruyu kaybetmemek (self-profile tuzağı).
2. ABD–İran–İsrail gibi **güncel** jeopolitik sorularda web önceliği + 2026 sorgu.

## Uygulandı

| # | Modül | Özet |
|---|--------|------|
| AL1 | `ruzgar_tek_beyin.py` | `strip_assistant_vocative`, `resolve_effective_user_query`, Rüzgar alias kaldırma |
| AL2 | `ana_motor_plan.py` | `looks_like_current_geopolitics_question`, plan + web sorgu 2026 |
| AL3 | `ruzgar_tek_beyin_analiz.py` | Etkili sorgu + jeopolitik niyet |
| AL4 | `desktop_server.py` | SSE erken yol `msg_early` hitap ayrıştırma |
| AL5 | `ana_motor_smoke.py` | Hitap + jeopolitik regression |

## Doğrulama

```bash
python scripts/ana_motor_smoke.py
Ruzgar_TemizBaslat.bat
```

Örnek:
- `Rüzgar abd şuan kimle savaşıyor` → plan: bilgi, web açık
- `Rüzgar kimdir` → hafıza self-profile
