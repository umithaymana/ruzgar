# Tercüme motoru — Faz 15 (A–C)

| Faz | Konu | Durum |
|-----|------|--------|
| **15A** | EPUB/FB2 metadata + bölüm başlıkları | ✅ |
| **15B** | Kullanıcı terim tablosu (Terimlerim) | ✅ |
| **15C** | `tercume_live_smoke.py` (Ollama) | ✅ |

## Test

```powershell
cd ilim-assistant
python scripts/tercume_faz15a_smoke.py
python scripts/tercume_faz15b_smoke.py
python scripts/tercume_live_smoke.py
```

Canlı smoke kapalı: `RUZGAR_TERCUME_LIVE_SMOKE=0`
