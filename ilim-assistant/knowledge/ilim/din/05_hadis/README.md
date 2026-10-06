# Din / 05 — Hadis kütüphanesi (Kutüb-i Sitte)

Her eser **ayrı raf**:

| ID | Eser | Klasör |
|----|------|--------|
| `buhari` | Sahîh-i Buhârî | `kutub_i_sitte/buhari/` |
| `muslim` | Sahîh-i Müslim | `kutub_i_sitte/muslim/` |
| `ebu_davud` | Sünen-i Ebû Dâvûd | `kutub_i_sitte/ebu_davud/` |
| `tirmizi` | Câmiu't-Tirmizî | `kutub_i_sitte/tirmizi/` |
| `nesai` | Sünen-i Nesâî | `kutub_i_sitte/nesai/` |
| `ibn_mace` | Sünen-i İbn Mâce | `kutub_i_sitte/ibn_mace/` |

| Katman | İçerik |
|--------|--------|
| **Kavramlar (TR)** | `kavramlar_hadis.jsonl` + `incremental/hadis_kavramlar_tr.md` |
| **Matın (AR)** | her rafta `hadisler.jsonl` + `incremental/*_batch_*.md` |
| **Bölümler** | `bolumler.json` (kitâb adları) |

**Kaynak:** fawazahmed0/hadith-api (Arapça). Anlık sorgu: `ruzgar_hadis_kutuphane`.

**Politika:** Fetva yok. Kaynak numaralı Arapça matın + usûl kavramı.


## Usûl + tarihçe

| Raf | İçerik |
|-----|--------|
| `usul_tarih/ibn_salah/` | Mukaddimetü İbnü's-Salâh (Arapça) |
| `usul_tarih/nukhba/` | Nuhbetü'l-fiker (Arapça OCR) |
| `incremental/hadis_tarihce_tr.md` | Tedvin tarihçesi (TR) |
| `incremental/muhaddisler_tr.md` | Altı imam nasıl topladı (TR) |

İncegest: `python scripts/faz5b_hadis_usul_tarih_ingest.py`
