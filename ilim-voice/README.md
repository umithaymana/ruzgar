# İlim Voice

Çok dilli **metin çevirisi** (NLLB), **konuşmayı yazıya** (Whisper) ve **metni sese** (XTTS + Farsça için MMS-TTS) — bilgisayarında çalışan açık kaynak boru hattı ve Gradio arayüzü.

## Dürüst beklenti

- **“Sıfır hatalı çeviri”** otomatik sistemlerde garanti edilemez; özellikle dinî ve edebî metinlerde insan kontrolü şart sayılmalıdır.
- **İnsan/kopya ses kalitesi** için XTTS’te **30–120 saniye temiz referans `.wav`** ve mümkünse **GPU** gerekir. Farsça hedefte referans gerekmez (MMS-TTS).

## Kurulum

1. Python **3.10+** ve mümkünse **CUDA** kurulu bir makine.
2. Ses dosyaları için **ffmpeg** (Whisper için önerilir).
3. Proje klasöründe:

```bash
pip install -r requirements.txt
python gradio_app.py
```

Tarayıcı: `http://127.0.0.1:7860`

## Ortam değişkenleri (isteğe bağlı)

| Değişken | Anlam |
|----------|--------|
| `NLLB_MODEL` | Örn. `facebook/nllb-200-3.3B` — daha ağır, genelde daha iyi çeviri |
| `WHISPER_MODEL` | `large-v3` (varsayılan), `medium` daha hafif |
| `WHISPER_DEVICE` | `cuda` veya `cpu` |
| `XTTS_MODEL` | Varsayılan Coqui çok dilli XTTS v2 |

## Lisans

Bu repodaki **senaryo kodu** senin projendir; kullandığın modellerin (NLLB, Whisper, Coqui TTS, MMS-TTS) **kendi lisanslarını** ayrıca kontrol et ve ticari kullanımda uyumluluğu doğrula.
