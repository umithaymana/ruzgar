# 2026-11-20 — Genel çok kaynaklı kütüphane okuma / sentez

- **tarih:** 2026-11-20 (Europe/Istanbul)
- **branch:** `cursor/genel-cok-kaynak-sentez-9eeb`
- **commit:** `5372ed39f`
- **durum:** hazir (main’e alınmadı; Mimar onayı bekler)
- **benzer_anahtarlar:** cok-kaynak, sentez, kutuphane, RAG, samile, extractive, diversify, grounding, anlik-kart

## is_ozeti

Dar kalıp (doğum/vefat, anne/baba) sıkışmasını kırıp Şamile/RAG için genel amaçlı çok kaynaklı okuma → özet → sentez mimarisi eklendi.

## dosyalar

- `ilim_assistant/ruzgar_cok_kaynak_sentez.py` (yeni)
- `ruzgar_kutuphane_gorev.py`, `chat_core.py`, `ana_motor_sentez.py`
- `ana_motor_faz_ad_sentez_pro.py`, `ana_motor_plan.py`
- `ruzgar_hadis_anlik.py`, `ruzgar_tek_beyin_izolasyon.py`, `prompts.py`
- `tests/test_cok_kaynak_sentez.py` (11 test, geçti)

## tuzaklar

1. Sorun «kütüphane yok» değildi — **tek pasaj extractive** + **tek anlık kart** + **web şartlı sentez** daraltıyordu.
2. Hit’ler skor sırasıyla kesilince aynı eser/raf tekrarı; **eser çeşitliliği** yoktu.
3. `RAG_TOP_K` düşük → 3–5 kitap zor.
4. Hadis anlık (niyet) tek Buhârî kartında kilitleniyordu; açık karşılaştırma isteğinde RAG’e bırakmak gerekiyor.
5. Önceki tur kalıpları kütüphane sorularına sızabiliyordu (izolasyon).
6. Bu cloud ortamında 13 GB Şamile yok — birim test mock; canlı indeks testi yerel makinede.

## cozum

- Yerel ≥3 hit / ≥2 eser → web olmadan sentez tetik.
- Hit diversify + `library_rag_top_k_boost`.
- Extractive 3–5 pasaj; grounding’de dar alan yasağı + karşılaştırma teklifi.
- Kapatma: `RUZGAR_COK_KAYNAK=0`
- Artifact (parent): `/cursor/stores/parent/artifacts/RUZGAR_COK_KAYNAK_SENTEZ_RAPOR.md`

## rehber (sonraki benzer iş)

Kütüphane «yanlış cevap» şikayetinde önce retrieval/kart/sentez kapısını kontrol et; raf yok sanma. Anlık kartı uzun anlatıma genişletme.
