# Rüzgar — Çok Kaynaklı Okuma / Özet / Sentez Raporu

**Tarih:** 20 Kasım 2026 (Europe/Istanbul)  
**Dal:** `cursor/genel-cok-kaynak-sentez-9eeb`  
**Hedef:** Dar kalıp sorulara (doğum/vefat, anne/baba vb.) sıkışmayı kırıp genel amaçlı çok kaynaklı mimariye geçiş.

---

## 1) Verdict

Kök sorun “kütüphane yok” değildi; **tek pasaj / tek kart / anlık şablon** yolları bilgi sorularını dar alanlara indirgiyordu. Bu pakette retrieval çeşitlendirme, sentez kapısı, grounding/prompt ve oturum izolasyonu genel amaçlı çok kaynaklı akışa çekildi.

---

## 2) Bulgular (öncelik sırası)

| # | Bulgu | Etki |
|---|--------|------|
| P0 | `format_kutuphane_extractive_reply` yalnızca **tek pasaj** basıyordu | Özet/sentez yerine dar kart |
| P0 | `grounding_directive` çok eser sentezi / karşılaştırma teklifi yoktu | Model tek alana kayabiliyordu |
| P0 | `ana_motor_sentez.should_synthesize_turn` **web şartı** koşuyordu | Şamile-only ≥3 hit sentezlenmiyordu |
| P1 | Hit’ler skor sırasıyla kesiliyor; **eser çeşitliliği** yoktu | Aynı raf/aynı alan tekrarı |
| P1 | `RAG_TOP_K` varsayılanı düşük; kütüphane sorusunda 3–5 kitap zor | Yetersiz bağlam |
| P1 | Hadis anlık (niyet) tek Buhârî kartı; karşılaştırma yolu zayıf | Kullanıcı “diğer kaynak” isteyince kısa kalıyordu |
| P2 | Bilgi izolasyonu kütüphane sorularını her zaman kapsamıyordu | Önceki tur kalıp sızıntısı |
| P2 | `prompts.py` çok kaynak / dar alan yasağı sonda yoktu | Sistem istemi eksik |

---

## 3) Yapılan değişiklikler

| Dosya | Ne değişti |
|-------|------------|
| `ilim_assistant/ruzgar_cok_kaynak_sentez.py` | **Yeni** — eser çeşitlendirme, paketleme, karşılaştırma teklifi, top_k boost, sentez tetik |
| `ruzgar_kutuphane_gorev.py` | Extractive 3–5 pasaj; grounding’e dar alan yasağı + çok kaynak talimatı |
| `chat_core.py` | Hit diversify; çok kaynak paketi blocks’a; grounding’e kitap sayısı |
| `ana_motor_sentez.py` | Web olmadan yerel çok kaynak sentez; çeşitlendirilmiş pack; sistem metni |
| `ana_motor_faz_ad_sentez_pro.py` | `should_force_library_synthesis` köprüsü |
| `ana_motor_plan.py` | Kütüphane sorusunda `library_rag_top_k_boost` |
| `ruzgar_hadis_anlik.py` | Karşılaştırma teklifi; açık karşılaştırma isteğinde RAG’e bırak |
| `ruzgar_tek_beyin_izolasyon.py` | Kütüphane bilgi → izolasyon; dar alan uyarısı |
| `prompts.py` | Kütüphane / çok kaynaklı okuma bloğu |
| `tests/test_cok_kaynak_sentez.py` | 11 birim test (hepsi geçti) |

**Kapatma bayrağı:** `RUZGAR_COK_KAYNAK=0`

---

## 4) Güncellenmiş master prompt (özet — `prompts.py` + grounding)

**Eklendi**
- Önce kütüphane/Şamile/RAG pasajlarını oku; derinliğe göre özetle.
- Dar alan kilidi yok (doğum/vefat/anne-baba tek alanına sıkışma yok).
- 3–5 eser sentezi + kaynak atfı.
- Hadis/rivayette doğal karşılaştırma teklifi.
- Her istekte önceki tur kalıplarını sızdırma.

**Çıkarılan / gevşetilen**
- “Tek pasaj yeter” extractive davranışı.
- Sentez için zorunlu web şartı (yerel ≥3 / ≥2 eser yeter).
- Hadis karşılaştırma isteğinde anlık tek-kart kilidi.

---

## 5) Çözüm planı (kalan iş)

### Faz A — doğrulama (şimdi yapılabilir)
1. Gerçek Şamile shard + RAG index üzerinde: hadis, siyer, genel kültür, matematik soruları.
2. Log: `cok_kaynak_sentez` bloğu, distinct book sayısı, sentez_pro bayrağı.
3. Masaüstü: yeni turda önceki “doğum/vefat” kalıbının sızmadığını kontrol.

### Faz B — anlık kart disiplini
1. Siyer/ilim `try_*_reply` kartlarını “kısa tanım” ile sınırla; uzun anlatımda RAG+sentez’e bırak.
2. `instant_covers_query` eşiğini çok sözcüklü sorularda sıkı tut (zaten var — smoke genişlet).

### Faz C — karşılaştırma stüdyosu
1. Hadis: Buhârî hit → otomatik Tirmizî/Müslim yan arama (aynı konu embedding).
2. UI’da “Kaynakları karşılaştır” aksiyonu (isteğe bağlı).

### Faz D — kuyruk
1. `desktop_server` / hub SSE’de bekleyen eski chat job’larının yeni istek bağlamına karışmadığını assert et.
2. Session id zorunlu; disk geçmişi session süzgeçli (izolasyon zaten kısmen var).

---

## 6) Test logu (bu oturum)

```
OK test_comparison_offer_for_hadis
OK test_diversify_prefers_multiple_books
OK test_extractive_reply_uses_multiple_passages
OK test_grounding_directive_blocks_narrow_field_lock
OK test_hadis_compare_request_defers_to_rag
OK test_hadis_instant_offers_comparison
OK test_isolation_marks_kutuphane_bilgi
OK test_library_rag_top_k_boost
OK test_pack_mentions_multi_source_and_no_narrow_lock
OK test_should_force_library_synthesis
OK test_should_synthesize_without_web_when_multi_local
failed 0
```

Mock hit’lerle doğrulandı; 13 GB Şamile bu ortamda yok — canlı indeks testi yerel makinede Faz A.

---

## 7) Nasıl çalıştırılır

```powershell
cd ilim-assistant
# isteğe bağlı
# $env:RUZGAR_COK_KAYNAK="1"
python desktop_server.py
```

Kontrol soruları:
- «Niyet hadisi nedir» → Buhârî + karşılaştırma teklifi
- «Niyet hadisini Tirmizî ile karşılaştır» → anlık kart yok, RAG/sentez yolu
- «Hicreti anlat» → çok pasaj; yalnız doğum tarihine inmemeli
- «Fotosentez nedir» → kütüphane/RAG özeti; önceki aile kalıbı sızmamalı

---

*Ümit & Gökçenur — Rüzgar Ana Motor*
