# Rüzgar Onarım — Canlı / Smoke Doğrulama (Faz 7)

**Zaman:** 2026-11-20 (Europe/Istanbul)  
**Dal:** `cursor/ruzgar-onarim-fazlari-9eeb`  
**Ortam:** Cloud agent VM (`ruzgar-work`) — Şamile 13GB tam küme yok

---

## Pytest (regresyon)

| Paket | Sonuç |
|-------|--------|
| `test_anlik_kapi_orkestra` | **GEÇTI** |
| `test_sohbet_tutarlilik` | **GEÇTI** |
| `test_cok_kaynak_sentez` | **GEÇTI** |
| `test_beyin_sure_faz4` | **GEÇTI** |
| `test_motor_routing_faz5` | **GEÇTI** |
| **Toplam** | **37 passed** |

---

## Senaryo smoke (mantık kapıları)

| # | Senaryo | Beklenen | Sonuç |
|---|---------|----------|--------|
| 1 | Niyet hadisi nedir? | Anlık kart yok (`hadis_anlik`+`hadis_kutuphane`+registry None); RAG yolu | **GEÇTI** |
| 2 | Tirmizî ile Buhârî karşılaştır | Anlık yok; `forces_library_rag` | **GEÇTI** |
| 3 | Hicret’i anlat | Anlık yok; RAG | **GEÇTI** |
| 4 | Selam boş oturum | `SELAM_STANDART`; «dün konuştuk» yok | **GEÇTI** |
| 5 | Selam dolu history | `SELAM_WITH_RESUME` | **GEÇTI** |
| 6 | Okuma alias | `normalize(okuma)==okuma` (≠mimar) | **GEÇTI** |
| 7 | İlim cloud-first varsayılan | `False` (local-first tablo) | **GEÇTI** |

---

## İndeks / RAG canlı hit

| Ortam | Durum |
|-------|--------|
| Bu VM | Yerel `knowledge/` jsonl izi var; **tam Şamile indeksi yok** |
| Canlı hit / diversify log (≥3 eser) | **İNDEKSLİ ORTAMDA** ayrıca doğrulanmalı — burada işaret: *indeks sınırlı* |
| Yanlış MISS riski | İndeks yoksa MISS **doğru** olabilir |

---

## Log / beyin sırası notu

- `brain_order_decision_table`: `ilim_rag_cloud_first=False`
- Bu VM’de Ollama yok → genel zincir buluta düşer (`gemini`/`groq`) — local-first bayrağı açık ama Ollama erişilemez; **indeksli+Ollama’lı makinede** zincir `denge/hizli` önce olmalı.

---

## Faz özeti (uygulama)

| Faz | Durum |
|-----|--------|
| 1 Anlık kapı | **yeşil** |
| 2 Selam/oturum | **yeşil** |
| 3 RAG çeşitlilik | **yeşil** (unit); canlı indeks ayrı |
| 4 Beyin+süre | **yeşil** |
| 5 Motor routing | **yeşil** |
| 6 Temizlik P2 | **yeşil** |
| 7 Doğrulama | **bu belge** |

*PR açılmadı — Mimar «al» bekler.*
