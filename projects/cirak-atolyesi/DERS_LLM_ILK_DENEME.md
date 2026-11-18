# Ders — İlk LLM el denemesi (dürüst)

**Sonuç:** Ajan `tam ajan` yoluna girdi (supervised handoff OK) ama **3+ tur yazım bırakmadı** (`carp_is` / `test_carp` diskte yokken turn ilerliyordu).

**Ne öğrendik:**
1. Handoff kapısı çalışıyor (şablon ezmedi).
2. LLM çırak henüz güvenilir yazıcı değil — okuma/timeout döngüsü riski.
3. Usta kurtardı: `carp_is.py` + `tests/test_carp.py`; G kapısı (disk+pytest) zorunlu.

**Sonraki:** Daha kısa hedef + yazım-önce sertleştirme; abartı yok.
