# Tercüme Faz 17 — Plan boşluklarının kapanması (14F / 14G / P3)

**Tarih:** 2026-05-29

| ID | Konu | Durum |
|----|------|--------|
| **14F** | Kullanıcı sözlüğü CSV/JSON import | ✅ |
| **14G** | DOCX kayıt (`.docx` çıktı seçeneği) | ✅ (`python-docx` gerekir) |
| **P3-TMX** | TMX dışa aktar / içe aktar | ✅ |
| **P3-diff** | Hizalı kaynak–hedef segment tablosu | ✅ |
| **P3-review** | İnceleme kuyruğu | ✅ (Faz 16B) |

## API

- `POST /api/tercume/user-glossary/import` — `text`, `fmt` (csv/json), `merge`
- `POST /api/tercume/tmx/export` — `rel`, `src_lang`, `tgt_lang`
- `POST /api/tercume/tmx/import` — `text` (TMX XML)
- `POST /api/tercume/aligned-diff` — `source_text`, `target_text`, isteğe `rel` (sayfa hizalı)

## UI

- Terimlerim: **CSV/JSON**, **TMX indir**, **TMX yükle**
- Çıktı: **.docx**
- Araç çubuğu: **Hizalı diff** + tablo paneli

## Smoke

```powershell
cd ilim-assistant
python scripts/tercume_faz17_smoke.py
python scripts/tercume_atolye_smoke.py
```

## CSV örnek

```csv
kaynak,tr,en,scope
Merhaba,Merhaba,Hello,kitap.pdf
```

## JSON örnek

```json
{"entries":[{"src":"kitap","tr":"book","scope":""}]}
```
