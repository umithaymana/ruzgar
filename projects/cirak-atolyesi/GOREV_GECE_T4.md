# Gece Tur 4 — daha zor (JSON özet)

Çırak kendisi yazsın.

1. `projects/cirak-atolyesi/json_ozet.py` içinde `json_ozet(veri: dict) -> str`:
   - `json.dumps` ile anahtarlar sıralı (`sort_keys=True`), `ensure_ascii=False`, ayırıcı kompakt
   - Örnek: `json_ozet({"b": 2, "a": 1})` → `'{"a": 1, "b": 2}'` (json.dumps varsayılan boşluklu)
2. `projects/cirak-atolyesi/tests/test_json_ozet.py` yeşil olsun; boş dict `{}`.
3. Atölye dışı yazma. Disk + pytest zorunlu.
