# Ana Motor Faz AM — Eksik kapatma + build senkron

> **Mimar:** Ümit & Gökçenur · **2026-06-14**

## Amaç

Faz AK (SLO env kopyala, arşiv hatırlat) ve AL (hitap ayrıştırma, jeopolitik web) sonrası kalan **operasyonel ve regresyon** boşluklarını kapatmak.

## Öncelik tablosu

| Öncelik | Eksik | Çözüm | Durum |
|---------|--------|--------|-------|
| P0 | Smoke `bu?` → hafıza hijack | `looks_like_clarification_short_query` + tek beyin skip | ✅ AM1 |
| P0 | Health build eski (Faz L) | `2026-06-14-ruzgar-ana-motor-faz-am` | ✅ AM2 |
| P1 | PROJE_DURUMU port/build | 8779 + AM build rev | ✅ AM3 |
| P1 | AK+AL yerel commit | Tek commit/push turu | ✅ `d656679` |
| P1 | SLO panel canlı doğrulama | TemizBaslat + dashboard | ⏳ PID 9844 — yönetici restart gerekli |
| P2 | denge70 model indir | Operasyonel (Ollama pull) | — |
| P2 | Motor boot 5 vs 7 dokümantasyon | `.cursorrules` uyum notu | ⏳ AM6 |

## Uygulanan modüller

| # | Modül | Özet |
|---|--------|------|
| AM1 | `ana_motor_plan.py` | `looks_like_clarification_short_query`; plan override skip |
| AM1 | `ruzgar_tek_beyin.py` | chat_history / blocks / plan_override kısa soru koruması |
| AM2 | `programlama_faz60.py`, `desktop_server.py` | Build rev senkron |
| AM3 | `PROJE_DURUMU.md` | Port 8779, build AM, Faz AK–AL özeti |
| AM5 | `scripts/ana_motor_smoke.py` | Regression: clarify + aile + jeopolitik |

## Doğrulama

```bash
cd ilim-assistant
python scripts/ana_motor_smoke.py
```

Beklenen: **0 hata** (özellikle `bu?` netleştirme).

Canlı:

```bat
Ruzgar_TemizBaslat.bat
```

- Dashboard build: `2026-06-14-ruzgar-ana-motor-faz-am`
- `emine haymana kimdir` → eş profili
- `Rüzgar abd şuan kimle savaşıyor` → bilgi + web (self-profile değil)
- `bu?` → netleştirme balonu (hafıza değil)

## Sıradaki (Faz AN adayı)

1. Commit + push (AK + AL + AM)
2. SLO «Henüz rapor yok» canlı smoke
3. Motor sayısı dokümantasyon hizası
4. denge70 Ollama pull rehberi dashboard’a

*Bismillah — Faz AM*
