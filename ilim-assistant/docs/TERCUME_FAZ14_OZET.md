# Tercüme motoru — Faz 14 özeti (A–E)

| Faz | Konu | Doküman |
|-----|------|---------|
| **14A** | Arka plan sayfa çevirisi, job, yeniden bağlan | `TERCUME_FAZ14A_PLANI.md` |
| **14B** | Kalite skoru UI | `TERCUME_FAZ14B_PLANI.md` |
| **14C** | Kalıcı terim belleği (TM) | `TERCUME_FAZ14C_PLANI.md` |
| **14D** | Kayıt klasörü + `_v2` sürüm | `TERCUME_FAZ14D_PLANI.md` |
| **14E** | md/html çıktı şablonu | `TERCUME_FAZ14E_PLANI.md` |

## Smoke (hepsi)

```powershell
cd ilim-assistant
python scripts/tercume_faz14a_smoke.py
python scripts/tercume_faz14b_smoke.py
python scripts/tercume_faz14c_smoke.py
python scripts/tercume_faz14d_smoke.py
python scripts/tercume_faz14e_smoke.py
```

## Sonraki (15+)

- EPUB bölüm/metadata okuma
- Kullanıcı terim tablosu düzenleme
- Canlı Ollama regresyon smoke
