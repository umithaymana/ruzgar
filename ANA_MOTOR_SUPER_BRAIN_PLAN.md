# Ana Motor — Süper Beyin Planı (2026-05-20)

> **Hedef:** Ümit abi'nin tüm sorularına dürüst, kaynaklı, güncel ve tam cevap — tek beyin: Ana Motor + Süper Beyin zinciri.

## Bugün (Faz A — uygulandı / uygulanıyor)

| # | Görev | Dosya | Etki |
|---|--------|-------|------|
| A1 | Ansiklopedik soruda **RAG atlama kaldırıldı** | `main_engine.py` | «Kim kurdu» vb. yerel arşiv+indeks hızlı tur, sonra Gemini |
| A2 | **Numaralı kaynak blokları** | `ana_motor_kaynak.py`, `chat_core.py` | Model [K1][K2] ile bağlama bağlanır |
| A3 | **Süper beyin talimatı** | `ana_motor_super.py` | Bilgi/ilim/tarih: tam cevap + güven satırı |
| A4 | **Cevap kalite geçidi** | `ana_motor_reflection.py` | Kaynak yoksa dürüst uyarı; kısa cevap uyarısı |
| A5 | Smoke + env | `ana_motor_smoke.py`, `RUZGAR_BRAIN.env.example` | Regresyon koruması |

## Bu hafta (Faz B)

| # | Görev | Açıklama |
|---|--------|----------|
| B1 | Çok kaynaklı sentez turu | Arşiv + indeks + web → tek «araştırma özeti» (hızlı model, 1 tur) |
| B2 | Self-reflection (9.6) | Cevap ↔ kaynak uyumu; çelişkide «emin değilim» |
| B3 | `genel` modda bilgi planı güçlendirme | Kısa sorularda bile `bilgi` + web varsayılan |
| B4 | Programlama → merkezi havuz yazma | Kod turu sonrası `motor_kv` |

## Orta vade (Faz C — Faz 8–12 planı)

- **Faz 8:** 70B yerel veya her zaman Gemini (`RUZGAR_BRAIN_PROFILE=gemini`)
- **Faz 9.1:** Birleşik araştırma raporu
- **Faz 9.4:** «Bugün» / güncellik damgası her web cevabında
- **Faz 10:** Tam otonom debug + çok dosya patch
- **Faz 12:** Latency SLO + `ana_motor_smoke --live` CI

## Ortam (özet)

```env
GOOGLE_GEMINI_API_KEY=...          # Süper beyin için şart (ücretsiz kota)
RUZGAR_SUPER_BRAIN=1
RUZGAR_ANA_MOTOR_PLAN=1
RUZGAR_FAZ9_GEMINI_FIRST_FOR_FACTS=1   # Artık = hızlı yerel merge, RAG atlama yok
RUZGAR_ANA_MOTOR_REFLECTION=1
RUZGAR_ANA_MOTOR_SUPER_DIRECTIVE=1
ENABLE_WEB_SEARCH=1
```

## Başarı ölçütü

1. Ansiklopedik soru → yerel kaynak veya «yerel kaynak bulunamadı» + web/Gemini
2. Cevap sonunda **Güven:** satırı (yüksek/orta/düşük)
3. `python scripts/ana_motor_smoke.py` yeşil
4. Ümit abi: «bilmiyorum» yerine ya kaynaklı cevap ya dürüst sınır

*Bismillah — Ümit & Gökçenur*
