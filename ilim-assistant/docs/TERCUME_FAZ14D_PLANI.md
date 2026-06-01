# Tercüme motoru — Faz 14D (güvenli kaydetme)

**Hedef:** Son kayıt klasörünü hatırlamak; aynı dosya adı varsa üzerine yazmadan `_v2`, `_v3` … oluşturmak.

| Kod | Konu | Durum |
|-----|------|--------|
| **14D-1** | `.ruzgar/tercume_save_prefs.json` — `last_save_dir` | ✅ |
| **14D-2** | `GET /api/tercume/save-prefs` | ✅ |
| **14D-3** | `save-target` çakışmada `_v2` … | ✅ |
| **14D-4** | UI: son klasör + yerel `localStorage` | ✅ |
| **14D-5** | İkinci kopya (`copy_rel`) için de sürümleme | ✅ |

## Davranış

- `kitap_tr.txt` varsa → `kitap_tr_v2.txt`, sonra `_v3` …
- Kayıt sonrası yol alanı güncellenir; flash’ta sürüm uyarısı
- Varsayılan yol: son kullanılan `ilim-assistant/arsiv/...` klasörü

## Env

```env
RUZGAR_TERCUME_SAVE_PREFS=1
RUZGAR_TERCUME_SAVE_VERSION=1
```

## Test

```powershell
cd ilim-assistant
python scripts/tercume_faz14d_smoke.py
python scripts/tercume_atolye_smoke.py
node --check ..\ruzgar-desktop\tercume-atolye.js
```
