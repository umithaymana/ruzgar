# Tercüme motoru — Faz 14C (kalıcı terim belleği)

**Hedef:** Oturum belleğini diske yazmak; aynı eser + hedef dil için sunucu yeniden başlasa da terim tutarlılığı.

| Kod | Konu | Durum |
|-----|------|--------|
| **14C-1** | `.ruzgar/tercume_tm/` JSON depolama | ✅ |
| **14C-2** | Anahtar: `dosya + hedef dil` | ✅ |
| **14C-3** | Sözlük + satır hizalı terim çıkarma | ✅ |
| **14C-4** | `GET /api/tercume/memory-status` | ✅ |
| **14C-5** | UI: `TM: N terim · diskte` | ✅ |

## Env

```env
RUZGAR_TERCUME_MEMORY=1
RUZGAR_TERCUME_MEMORY_PERSIST=1
```

Kapatmak: `RUZGAR_TERCUME_MEMORY_PERSIST=0` (yalnızca RAM).

## Test

```powershell
cd ilim-assistant
python scripts/tercume_faz14c_smoke.py
python scripts/tercume_faz14a_smoke.py
```

## Sonraki

- **14D** — kayıt hafızası + `_v2` → `TERCUME_FAZ14D_PLANI.md` ✅
