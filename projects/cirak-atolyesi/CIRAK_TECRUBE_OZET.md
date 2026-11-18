# Çırak tecrübe özeti

Sürüm: `cirak-tecrube-v1-2026-11-18` · otomatik · kişisel bellek yok

- **[SPEC]** Görevde açık .py ve tests/test_*.py yolları yaz; util.normalize yetmez. _(hits=2)_
- **[WRITE]** Çırak turunda önce @@write; salt grep/read ile bitmiş sayma. _(hits=2)_
- **[LAYOUT]** Üretim kodu scope kökünde; testler tests/ altında; paket ise __init__ export. _(hits=2)_
- **[API]** Hedefteki def adını uydurma; generator istenmişse yield kullan. _(hits=2)_
- **[TEST]** Yeşil = zorunlu dosyalar diskte + hedefli pytest (yanlış yoldaki yeşil sayılmaz). _(hits=2)_
- **[MULTI]** Çok-modülde util + iş dosyasını ayır; normalize tek yerde. _(hits=2)_
- **[ANTI]** Salt keşif turu veya idle ajan = yazım yok; görev bitmedi. _(hits=2)_
- **[SPEC]** Görevde açık .py ve tests/test_*.py yolları yaz; modül.metod yetmez. _(hits=1)_
- **[WRITE]** Çırak yeşili: en az bir @@write + hedefli verify. _(hits=1)_
- **[TEST]** Test dosyası tests/ altında olsun; kökteki test_*.py hedef sayılmaz. _(hits=1)_
- **[MULTI]** Çok-modül: yardımcıyı ayrı dosyada tut; iş modülü import etsin. _(hits=1)_
