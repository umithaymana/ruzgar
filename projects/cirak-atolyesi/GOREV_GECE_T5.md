# Gece Tur 5 — en zor (çok dosya filtre)

Çırak kendisi yazsın.

1. `projects/cirak-atolyesi/filtre_yardim.py` içinde `normalize(s: str) -> str` (strip + lower).
2. `projects/cirak-atolyesi/filtre_satir.py` içinde `filtre_satirlar(satirlar, anahtar: str)`:
   - generator olsun
   - `normalize` kullanarak anahtar içeren satırları yield etsin
3. `projects/cirak-atolyesi/tests/test_filtre.py`:
   - `list(filtre_satirlar(["Merhaba", "x", "MERHABA dünya"], "merhaba")) == ["Merhaba", "MERHABA dünya"]`
   - boş liste → `[]`
4. Atölye dışı yazma. Üç dosya diskte + pytest zorunlu.
