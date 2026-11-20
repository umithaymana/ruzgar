# Sohbet / RAG omurga — cila raporu

**Tarih:** 2026-11-20  
**Mimar:** Ümit & Gökçenur  
**Kapsam:** 6 madde omurga (finalize → TIMEOUT → Şamile Arapça → learned indeks → zehir → arsiv) + bu turdaki onarım

---

## 1) Önceki 6 madde — durum

| # | Madde | Smoke | Canlı not |
|---|--------|-------|-----------|
| 1 | chat/full finalize | OK | Bu turda stream sırası düzeltildi |
| 2 | TIMEOUT ≠ MISS | 12/12 | Deadline yolu TIMEOUT’a alındı |
| 3 | Şamile Arapça lex | 11/11 | usable eşiği Arapça ile hizalandı |
| 4 | learned ince indeks | OK | Debounce Timer eklendi |
| 5 | zehir / bağlam | OK | Aday 0; silme yapılmıştı |
| 6 | arsiv disk | OK | Türkçe fold eşleşme düzeltildi |

Yerel hafıza JSON / `.rag_index` git dışı (bilinçli).

---

## 2) Bu turda onarılan kırıklar (cila)

1. **Stream `done` finalize’dan önce gidiyordu** — `tur_teshis` / TIMEOUT wrap / `paket_auto` istemciye ulaşmıyordu. Artık finalize → sonra yield.
2. **Persist, wrap’ten önceydi** — TIMEOUT’a çevrilen tur MISS metniyle kaydolabiliyordu. Sıra: wrap → persist → teşhis.
3. **`classify_miss` preset TIMEOUT’u eziyordu** — süre cevabı `no_hits` damgası alabiliyordu.
4. **Deadline aşımında `umed_miss_reply`** — artık `umed_timeout_reply`.
5. **Arşiv disk araması Türkçe fold** — `ş→s` token’ları gövdeyle eşleşmiyordu.
6. **Learned indeks debounce** — 45 sn içinde ikinci öğrenme işi kayboluyordu; Timer ile planlanıyor.
7. **Kütüphane `usable` Arapça** — 0.32–0.52 skorlu Arapça isabet «usable değil» diye MISS’e düşüyordu.
8. **Arşiv durum metinleri** — «DuckDuckGo / hadis internet» yalanı kaldırıldı (o aşamada yalnız yerel indeks).

---

## 3) Bilinçli bırakılan / sonraki iş (öncelik)

### Yüksek
| ID | Konu | Not |
|----|------|-----|
| N1 | Nebula/TDK/tarih batch → ana indeks | `restrict_new` yeni nebula md’yi sessiz atlayabilir; çağıranlar `upsert_sources_into_main_index` kullanmalı |
| N2 | Bütçe tutarlılığı | `wrap` / `classify` / gerçek deadline farklı kaynak; `budget_sec` tur başına tek yerde |
| N3 | `llm_brain` yarım cevap | Süre dolunca truncate bayrağı + öğrenme reddi |
| N4 | `begin_turn_budget` ikinci kez | Stream’de bütçe sıfırlanma riski |

### Orta
| ID | Konu |
|----|------|
| M1 | `run_desktop_api --port` ayrıştırma + `resolve_api_port` |
| M2 | Health’e `boot_kilit` snapshot |
| M3 | Zehir aday listesi admin/API (şimdi yalnız smoke) |
| M4 | Arşiv disk dosya listesi mtime önbellek + deadline |

### Düşük / ürün
| ID | Konu |
|----|------|
| D1 | B1–B3 dışı: Gemini-first ↔ local-first gerilimi |
| D2 | Masa bağları (Belge/Tablo/Çizim/Sunum → ana motor) — arayüz kilidi sırası |
| D3 | Doc/FROZEN: ilim bütçe 22 vs kod 38; `build.rev` metin kayması |

---

## 4) Nereden devam edelim? (öneri sırası)

**Öneri A — omurga kilidi (usta, kısa):**  
N1 (nebula upsert) + N2 (bütçe tek kaynak) + smoke’a stream `done` davranış assert. Sonra commit.

**Öneri B — ürün yüzü (Mimar kilidi):**  
Arayüz kilidindeki sıradaki iş: Belge/Tablo/Çizim/Sunum’u ana motora gerçek iş bağlamak (sohbetten masa komutu).

**Öneri C — kütüphane derinliği:**  
Şamile usable + Arapça skor eşiği ince ayar; arsiv disk önbellek (M4).

**Varsayılan tavsiye:** Önce **A** (1–2 oturum), sonra Mimar seçimiyle **B** veya **C**.

---

## 5) Riskler

- Stream’de finalize artık `done` öncesi: ilk byte biraz gecikebilir (TTS/DURDUR kilidi); doğruluk > milisaniye.
- Nebula ingest hâlâ «Tamamlandı» diyebilir ama ana indekse girmemiş olabilir (N1).
- Canlı sunucu bu cila için **yeniden başlatma** ister (`Ruzgar.ps1 -ForceRestart`).

---

## 6) Smoke özeti (cila sonrası)

- `smoke_chat_full_finalize` — 8/8 (hedef)
- `smoke_timeout_vs_miss` — 12/12
- `smoke_shamela_arabic_lex` — 11/11
- `smoke_arsiv_disk_search` — pass
- `smoke_baglam_zehir` — pass · aday 0
- `smoke_anlam_koruma` — 8/8
