# Çırak raporu — Gece 5 tur

Tarih: 2026-11-18

| Tur | Zorluk | Yeşil | Kim yaptı |
|-----|--------|-------|-----------|
| 1 | kolay (`fark`) | EVET | cirak_llm |
| 2 | orta (`bol`) | EVET | cirak_llm (1. deneme kırmızı, 2. yeşil) |
| 3 | zor (`kelime_say`) | EVET | cirak_llm |
| 4 | daha zor (`json_ozet`) | EVET | cirak_llm |
| 5 | en zor (`filtre_*`) | EVET | önce cirak_llm (yanlış API) → usta spec düzeltmesi |

## Çırak notu

Tur 1–4’te dosyaları ben yazdım, hedefli pytest yeşildi.  
Tur 2’de ilk denemede 21 tura kadar çoğu zaman yalnız `grep` yaptım; dosya kapısı kırmızı tuttu, ikinci denemede yazabildim.  
Tur 5’te dosya yazdım ama görevdeki `filtre_satirlar` generator yerine `filtrele_satir` bool yazmışım — usta spec’e çekti. Bunu saklamıyorum.

### Tur tur
- **1:** `fark_is.py` + `tests/test_fark.py` — yeşil
- **2:** `bol_is.py` + `tests/test_bol.py` — 2. deneme yeşil
- **3:** `kelime_say.py` + `tests/test_kelime_say.py` — yeşil
- **4:** `json_ozet.py` + `tests/test_json_ozet.py` — yeşil
- **5:** `filtre_yardim.py` + `filtre_satir.py` + `tests/test_filtre.py` — spec düzeltmeli yeşil
