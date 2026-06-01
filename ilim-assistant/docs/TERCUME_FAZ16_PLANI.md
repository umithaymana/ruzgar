# Tercüme Faz 16 — Calibre/DjVu + İnceleme kuyruğu

**Tarih:** 2026-05-29  
**Kapsam:** Sadece tercüme motoru (`tercume_*`, atölye UI, `/api/tercume/*`).

## 16A — Calibre / DjVu okuma

- `tercume_ebook_read.py`: `read_ebook_auto`, `convert_calibre_to_text`, `read_djvu`, `calibre_available`, `djvu_available`
- `tercume_read_pipeline.py`: `.mobi`, `.azw`, `.djvu` uzantıları
- `desktop_server.py`: `read-ebook` → `read_ebook_auto`; preflight Calibre/DjVu satırları

## 16B — İnceleme kuyruğu

- `tercume_review_queue.py`: düşük skor (&lt;55) ve `ok:false` çıktılar
- `tercume_batch_jobs.py`: `outputs[].page_index`
- API: `GET /api/tercume/review-queue?job_id=`
- UI: iş panelinde «İnceleme kuyruğu», **Yeniden çevir** (`output_index` ile hedef parça güncelleme)

## 16C — Preflight

- `tercume_preflight.py`: kaynak `rel` uzantısına göre Calibre / DjVuLibre uyarıları

## Smoke

```bash
cd ilim-assistant
python scripts/tercume_faz16a_smoke.py
python scripts/tercume_faz16b_smoke.py
python scripts/tercume_atolye_smoke.py
python scripts/tercume_faz15a_smoke.py
```

Calibre/DjVu kurulu değilse 16A smoke yine geçer (dosya yok + config kontrolü); canlı dönüşüm manuel test.

## Test (Ümit abi)

1. `Ruzgar_TemizBaslat.bat` → port 8779, Ctrl+F5
2. EPUB veya PDF ile sayfa aralığı işi başlat
3. İş bitince «İnceleme kuyruğu» açılsın; düşük skorlu satırda **Yeniden çevir**
4. `.mobi` / `.djvu` dosyasında preflight’ta araç satırını kontrol et
