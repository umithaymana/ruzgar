# Tercüme motoru — Faz 14A (arka plan sayfa çevirisi)

**Hedef:** Sayfa sayfa / aralık / tamamı modları tarayıcı döngüsü yerine sunucu işi; sekme kapansa da sürer; canlı önizleme.

| Kod | Konu | Durum |
|-----|------|--------|
| **14A-1** | `batch-start` + `rel` → `start_page_range_job` UI bağlantısı | ✅ |
| **14A-2** | Job durumu: `partial_text`, `outputs`, `ok_count` / `error_count` | ✅ |
| **14A-3** | `GET /api/tercume/batch-jobs` — son işler | ✅ |
| **14A-4** | UI: iş paneli, log, `localStorage` ile yeniden bağlan | ✅ |
| **14A-5** | TXT/DOCX sayfa aralığı dilimleme (`extract_source_pages`) | ✅ |

## Kullanım

1. Sol listeden PDF/TXT/DOCX açın.
2. Mod: **Sayfa sayfa**, **Sayfa aralığı** veya **Tamamı (arka plan)**.
3. **Çevir** — iş sunucuda çalışır; hedef panel canlı güncellenir.
4. **Durdur** — iptal isteği gönderir.
5. Bittiğinde çıktı `ilim-assistant/arsiv/tercume-output/page-range/` altına yazılır; kayıt yolu otomatik dolar.

## Test

```powershell
cd ilim-assistant
python scripts/tercume_faz14a_smoke.py
python scripts/tercume_atolye_smoke.py
node --check ..\ruzgar-desktop\tercume-atolye.js
```

## Sonraki

- **14B** — kalite skoru UI → `TERCUME_FAZ14B_PLANI.md` ✅
- **14C** — kalıcı terim belleği
- **14D** — kaydetme `_v2` versiyonlama
