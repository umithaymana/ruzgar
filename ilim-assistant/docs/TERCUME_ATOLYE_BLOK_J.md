# Tercüme atölye — Blok J (91–100)

**Kural:** Programlama motor dosyalarına dokunulmaz.

## UI (ruzgar-desktop)

| # | Özellik |
|---|---------|
| J91 | Sol arşiv ağacı + EPUB/görsel açılış |
| J92 | **Çevir** → sohbet; yanıt otomatik hedef panel |
| J93 | **OCR** butonu + görsel açılışta `read-image-ocr` |
| J94 | **Hedefi kaydet** + yol alanı |
| J95 | EPUB/MOBI/DJVU → `read-ebook` |
| — | URL indir → `POST /api/tercume/import-url` |

## API

- `GET /api/workspace/read-ebook`
- `GET /api/workspace/read-image-ocr`
- `POST /api/tercume/import-url`
- `POST /api/tercume/save-target` (yalnızca `ilim-assistant/arsiv/` altı)

## Test

```powershell
cd ilim-assistant
python scripts/tercume_atolye_smoke.py
node --check ..\ruzgar-desktop\app.js
```

Masaüstü: `Ruzgar_TemizBaslat.bat` → Tercüme modu → dosya aç → Çevir → Hedefi kaydet.
