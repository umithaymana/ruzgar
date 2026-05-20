# Rüzgar — Cevap Alamama Teşhis Raporu (2026-05-20)

## Özet

Ekrandaki **«Ollama yanıt vermedi»** mesajı yanıltıcıydı: **Gemini bağlı** (`Gemini ✓ gemini-2.0-flash (daemon)`), asıl sorun **zaman aşımı + yanlış yedek model yolu**.

| Bulgu | Durum |
|--------|--------|
| GLOBAL_API_KEY / Gemini API | ✅ Çalışıyor (health + daemon ping 200) |
| Ollama (11434) | ✅ Dinliyor |
| UI hata metni | ❌ 60 sn kesilince «Ollama» sanılıyordu |
| Selam + kısa mesaj | ❌ Plan «bilgi» olunca ağır RAG + LLM (dakikalar) |
| GLOBAL_API_KEY varken zincir | ❌ Bazen Ollama yedeğine düşüp 60–900 sn bekliyordu |

## Kök nedenler

1. **İstemci 60 sn limiti** — `/api/chat/full` RAG indeksi + Gemini + (bazen) Ollama yedeği toplamı 60 sn’yi aşıyor; tarayıcı kesiyor.
2. **Yanlış hata sınıflandırması** — `classifyChatError` her zaman aşımı «Ollama yanıt vermedi» diye gösteriyordu.
3. **Selam mesajları** — «Merhaba, kısa cevap ver» planı `gundelik` olsa bile önce **ağır RAG önbelleği** ve **büyük `ruzgar_genel_hafiza.json` taraması** çalışıyordu.
4. **Ollama yedek zinciri** — Gemini hata/ gecikme sonrası Ollama’ya düşüş; kullanıcı Gemini hazır sanırken Ollama timeout görüyordu.

## Yapılan düzeltmeler

| Dosya | Düzeltme |
|-------|----------|
| `ana_motor_plan.py` | Selam/teşekkür → anında cevap (plan `bilgi` olsa bile) |
| `desktop_server.py` | Selamda RAG prefetch atlama |
| `chat_core.py` | Selamda dev JSON hafıza taraması atlama |
| `llm_brain.py` | `RUZGAR_GEMINI_ONLY=auto` → yalnızca Gemini zinciri |
| `llm_ollama.py` | `ollama_reachable()` — kapalı Ollama yedeğe eklenmez |
| `ruzgar-desktop/app.js` | Timeout **120 sn**; hata metni ayrıştırıldı |
| `.env` | `RUZGAR_GEMINI_ONLY=auto` |

## Sizin yapmanız gereken

1. **Rüzgar’ı tamamen kapatıp `Ruzgar.ps1` ile yeniden başlatın** (API eski kodu bellekte tutuyor olabilir).
2. İlk soru olarak **«Merhaba»** yazın → **1–2 sn** içinde karşılama gelmeli.
3. Bilgi sorusu için **120 sn** bekleyin; şeritte **Gemini ✓ (daemon)** kalmalı.
4. Hâlâ hata varsa: `%TEMP%\ruzgar-api.err` ve sunucu konsolundaki `[RÜZGAR] Gemini hazır` satırına bakın.

## Beklenen davranış (düzeltme sonrası)

- Selam → anında yanıt (LLM/RAG yok).
- Bilgi sorusu → Gemini-2.0-flash, Ollama yedeği yok (`gemini_only`).
- Zaman aşımı → «Yanıt zaman aşımı (120 sn)», «Ollama yanıt vermedi» değil (Gemini yolunda).

*Ümit & Gökçenur — Rüzgar Ana Motor*
