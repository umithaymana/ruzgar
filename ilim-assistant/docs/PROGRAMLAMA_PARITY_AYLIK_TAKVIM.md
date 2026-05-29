# Parity full 8/8 — aylık takvim (Blok E50)

**Başlangıç:** 2026-05-29 · **Hedef:** Cursor parity full senaryoları ayda en az bir kez yeşil.

## Haftalık / aylık ritim

| Ne zaman | Komut / aksiyon | Beklenen |
|----------|-----------------|----------|
| **Her PR / push** (CI) | `programlama_smoke.py --ci --upgrade` | Komut ≥95, Faz99 x2, ladder 5/5, parity quick 8/8 |
| **Her Pazartesi** (yerel) | `scripts\Ruzgar_Programlama_Bench.bat strict` | Upgrade raporu `ruzgar_programlama_upgrade_report.json` |
| **Ayın 1–7’si** | Parity **full** (3 cursor senaryo) | `python scripts/ruzgar_parity_smoke.py` veya API `POST /api/programlama/weekly-parity-full` |
| **Ay sonu** | Bench artığı temizlik | `scripts\Ruzgar_Cleanup_Smoke_Autonomy.bat` |

## 2026 takvim (parity full önerilen hafta)

| Ay | Önerilen hafta | Not |
|----|----------------|-----|
| Mayıs | 26–31 May | Blok E kapanış smoke |
| Haziran | 2–8 Haz | İlk tam ay full |
| Temmuz | 1–7 Tem | |
| Ağustos | 1–7 Ağu | |
| Eylül | 1–7 Eyl | |
| Ekim | 1–7 Eki | |
| Kasım | 1–7 Kas | |
| Aralık | 1–7 Ara | |

## Doğrulama checklist

- [ ] `ruzgar_parity_smoke_sonuc.json` → `passed: 8`, `total: 8`, `ok: true`
- [ ] `ruzgar_programlama_upgrade_report.json` → `ladder` 5 satır, hepsi `pass: true`
- [ ] `checks.faz99_run1_ok` ve `faz99_run2_ok` → `true`
- [ ] `.ruzgar/autonomy_reports/` son rapor mevcut

## İlgili dosyalar

- `scripts/programlama_task_ladder.json` — S1–S5 merdiven
- `scripts/programlama_upgrade_runner.py` — strict gate
- `ilim-assistant/ilim_assistant/motorlar/programlama_faz89.py` — haftalık full API
