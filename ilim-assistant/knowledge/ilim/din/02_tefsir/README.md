# Din / 02 — Tefsir kütüphanesi

İki katman **karıştırılmaz**:

| Katman | Klasör | İçerik |
|--------|--------|--------|
| **Modern** | `kuran_yolu/` | Diyanet Kur’an Yolu (TR meal+tefsir, 5 cilt) |
| **Klasik** | `klasik/{eser_id}/` | İbn Kesîr, Taberî, Kurtubî, Beyzâvî, Râzî (Arapça, ayet hizalı) |

## Modern — Kur’an Yolu

| Dosya | İçerik |
|-------|--------|
| `kuran_yolu/tefsir_bloklari.jsonl` | Ayet aralıklı meal+tefsir |
| `kuran_yolu/tefsir_ayet_indeks.jsonl` | Ayet → blok |
| `manifest.json` | Kur’an Yolu kaynak/QA (yalnız bu eser) |

## Klasik — beşli

Sıra (ingest): `ibn_kesir` → `taberi` → `kurtubi` → `beyzavi` → `razi`  
Katalog: `klasik/catalog.json`  
Her eser kendi `manifest.json` + `tefsir_ayet_indeks.jsonl` tutar.

## Rüzgar tarama

`ilim_assistant/ruzgar_tefsir_kutuphane.py` — tefsir sorusunda **tüm** eserleri tarar (modern+klasik).
