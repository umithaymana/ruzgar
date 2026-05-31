# Tercüme motoru — eksik kapatma planı (Faz 9–12)

**Amaç:** Atölyeyi «çırak»tan «güvenilir usta yardımcısı» seviyesine taşımak.  
**Kapsam:** Yalnızca `tercume_*` + atölye UI + ilgili API.

---

## Eksik → Faz eşlemesi

| Analizdeki eksik | Faz | Çözüm |
|------------------|-----|--------|
| Taranmış PDF / zayıf OCR | **9** | OCR cascade (çoklu dil dene, en iyisini seç) |
| Uzun iş patlaması | **9** | Kapı kontrol (preflight) — OCR, beyin, arşiv |
| Çeviri kalitesi belirsiz | **9** | Çeviri skoru + sızıntı uyarısı |
| Çok cilt / sayfa aralığı | **10** | Sayfa aralığı + boş sayfa atla |
| Terim tutarsızlığı | **10** | Genişletilmiş sözlük setleri |
| Her siteden indirme yok | **11** | Archive mirror + yerel eşleşme önceliği |
| Tam analist kontrolsüz | **12** | Checkpoint modu (oku → onay → çevir) |

---

## Faz 9 — Kapı kontrol + OCR cascade + çeviri skoru ✅

- `tercume_preflight.py` — hazırlık raporu
- `tercume_ocr_cascade.py` — görsel / zayıf PDF sayfası
- `tercume_translate_quality.py` — çıktı puanı
- API: `GET /api/tercume/preflight`
- UI: **Hazırlık** butonu
- Tam analist başında preflight

**Env:** `RUZGAR_TERCUME_PDF_OCR=1` (pdf2image kuruluysa taranmış PDF)

---

## Faz 10 — Sayfa aralığı + sözlük ✅

- `source-pages?page_from=&page_to=` sayfa penceresi
- Batch: `POST /api/tercume/batch-start` + `rel` + `page_from` / `page_to` / `skip_empty`
- `start_page_range_job` — arka planda sayfa aralığı çevir + kaydet
- Sözlük: Gazzali, Nakşibendi, Osmanlıca yaygın terimler
- UI: «Sayfa X–Y» girişi + **Sayfa aralığı** modu

---

## Faz 11 — İndirme + arşiv ✅

- `tercume_download_v2.py` — Archive.org details → PDF URL
- Yerel arşiv fuzzy skor (`local_score`, `why_local`)
- İndirme hata mesajları (403, 404, timeout, telif)

---

## Faz 12 — İnsan onaylı sihirbaz ✅

- `RUZGAR_TERCUME_SUPER_CHECKPOINT=1` — rapor sonrası dur
- API: `POST /api/tercume/super-resume` (`continue` / `skip` / `cancel`)
- UI: checkpoint’te onay penceresi (Devam / Atla)

---

## Test disiplini

Her faz sonu: `python scripts/tercume_analyst_smoke.py`  
Manuel: arşivden 1 PDF, adım adım (preflight → aç → 2 sayfa çevir → hafızaya)
