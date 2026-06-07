# Tecvid — tilavette kullanılacak özet kurallar (Faz S5 simülasyon)

Tecvid **ses üretimi (TTS)** ile tam karşılanmaz; güzel tilavet için genelde **insan icazeti** veya özel telaffuz modeli gerekir. Rüzgar S5 hattı **durak süreleri** ile tilavet hissini destekler; telaffuz Edge/XTTS sınırlarındadır.

## Vakıf / durak (simülasyon süreleri)

| İşaret / durum | Rüzgar `DurakTuru` | Not |
|----------------|---------------------|-----|
| Ayet sonu (۝, numara) | `ayet` | Uzun nefes |
| Sûre sonu | `sure_sonu` | Daha uzun durak |
| Cümle sonu (. ؟) | `cumle` | Orta |
| Virgül (, ،) | `virgul` | Kısa |
| Besmele sonrası | `besmele` | İlk ayet öncesi nefes |
| Paragraf | `paragraf` | Meal / tefsir arası |

## Okuma üslubu (Alim profili)

- Yavaş taban tempo; acele yok
- Arapça metinde `ar-SA-HamedNeural` (Edge) veya klon referans
- Türkçe meal / hadis / risale: `tr-TR-AhmetNeural`, vakur ton

## Med / ıskal

- TTS med uzunluğunu bilmez; yalnızca kelime arası durak genişletilir
- Kritik tilavet için insan kıraat kaydı + klon (Faz S4) önerilir
