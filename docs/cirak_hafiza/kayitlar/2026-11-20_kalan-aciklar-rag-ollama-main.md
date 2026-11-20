# Kalan açıklar: RAG canlı + Ollama + main

## Ne yapıldı
- TR→AR kütüphane köprüsü (`chunk_fits_query`) — niyet/hadis Arapça metne oturuyor
- Canlı mühür scripti: ≥3 eser diversify + Ollama local-first
- Feature onarımlar main'e alınacak

## Tuzak
- `fold_ascii` Arapçayı siler; köprü olmadan filtre tüm hit'leri öldürür
- `hadisi` token'ı `hadis` köprüsüne bağlanmalı
- Ollama systemd yoksa `ollama serve` elle

## Bir daha yapma
- İndeks yokken «canlı RAG yeşil» deme
- Ollama yokken local-first mühür iddia etme
