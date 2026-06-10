# Ana Motor — Faz Y Planı (2026-06-10)

> **Hedef:** Bilgi kalite 2.0 — LLM reflection + sohbet içi kaynak/güven rozeti.

## Faz Y — uygulandı

| # | Görev | Dosya | Davranış |
|---|--------|-------|----------|
| Y1 | Opsiyonel LLM reflection | `ana_motor_reflection_llm.py` | Factual soruda ikinci tur (hızlı Ollama) |
| Y2 | Kaynak + güven rozeti | `ana_motor_kaynak_rozet.py` | `source_trust_card` → sohbet balonu altı |

### Boru hattı

`apply_bilgi_kalite_pass` → kural reflection → LLM reflection → rozet kartı

### Ortam

```env
RUZGAR_ANA_LLM_REFLECTION=1
RUZGAR_ANA_LLM_REFLECTION_BUDGET_SEC=8
RUZGAR_ANA_KAYNAK_ROZET=1
```

### Başarı ölçütü

1. Ansiklopedik soru → **Güven** rozeti sohbette görünür
2. Kaynak uyumsuzluğu → LLM reflection notu (Ollama açıksa)
3. Smoke Faz Y yeşil

## Sıradaki (Faz Z — öneri)

- Sohbet paneli sadeleştirme (arşiv kartı katlanır)
- Multi-hop RAG

*Bismillah — Ümit & Gökçenur*
