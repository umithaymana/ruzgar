# Tercüme motoru — Faz 13 (eksik kapatma)

**Hedef:** Ollama-only güvenilir çeviri, net hazırlık raporu, arama/OCR bağımlılık şeffaflığı.

| Kod | Konu | Durum |
|-----|------|--------|
| **13A** | `tercume_llm.py` — çeviri LLM zinciri + Türkçe hata | ✅ |
| **13B** | `tercume_readiness.py` + preflight Ollama-only | ✅ |
| **13C** | `translate-chunk` → `error_code`, `hint_tr` | ✅ |
| **13D** | Eser arama: ddgs yoksa anlaşılır mesaj | ✅ |
| **13E** | UI: açılış hazırlık şeridi + çeviri hata metni | ✅ |

## Test

```powershell
python ilim-assistant/scripts/tercume_faz13_smoke.py
python ilim-assistant/scripts/tercume_atolye_smoke.py
python ilim-assistant/scripts/tercume_analyst_smoke.py
```

## Env (Ollama-only öneri)

```env
RUZGAR_OLLAMA_ONLY=1
RUZGAR_DISABLE_GEMINI=1
RUZGAR_DISABLE_GROQ=1
RUZGAR_DISABLE_LOCAL_OLLAMA=0
OLLAMA_CHAT_MODEL=llama3.1:8b
```
