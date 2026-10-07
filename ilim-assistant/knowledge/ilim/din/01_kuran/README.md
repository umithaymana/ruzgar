# Din / 01 — Kur'an-ı Kerim

**Kaynak:** Diyanet İşleri Başkanlığı (`kuran.diyanet.gov.tr` / `dijital.diyanet.gov.tr`)  
**Yükleme:** `scripts/faz1_kuran_diyanet_ingest.py`

## İçerik

| Dosya | Açıklama |
|-------|----------|
| `ayetler.jsonl` | 6236 ayet — Arapça + meal |
| `manifest.json` | Kaynak URL, SHA256, QA |
| `metadata/sureler.json` | 114 sure metadata |

## Alanlar (her satır)

- `text_ar` — Diyanet Word mushaf
- `meal_tr` / `meal_tr_kuran_yolu` — **Kur’an Yolu** meal (birincil)
- `meal_tr_diyanet` — DİB Cep Meal (boş surelerde Kur’an Yolu yedeği)

## Staging (ham indirme)

`arsiv/_ilim_staging/01_kuran/`

## Temel kavramlar (Faz 1 ek)

| Dosya | Açıklama |
|-------|----------|
| `metadata/sureler.json` | 114 sure — ad TR/AR, ayet, Mekkî/Medenî, nüzûl sırası |
| `metadata/nuzul_sirasi.json` | İniş kronolojisi |
| `metadata/cuz_hizb.json` | 30 cüz başlangıçları |
| `temel_kavramlar.jsonl` | Sûre, âyet, meal, tefsir, tecvid… tanımları |
| `tecvid_giris.jsonl` | Kısa tecvid usulü |
| `incremental/*.md` | RAG için düz metin |

## RAG ayet batch

| Dosya | Açıklama |
|-------|----------|
| `incremental/ayetler/kuran_ayet_batch_*.md` | 6236 ayet — AR + meal (RAG `*.md` indeksi) |
| Script | `scripts/faz1_kuran_ayet_rag_ingest.py` |
