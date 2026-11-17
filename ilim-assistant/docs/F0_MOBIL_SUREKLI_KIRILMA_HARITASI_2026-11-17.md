# F0.4 — Mobil sürekli sohbet kırılma haritası

**Tarih:** 2026-11-17  
**Amaç:** «Ses gitmiyor / cevap gelmiyor» şikâyetinde hangi halka kırık net olsun.  
**Kod yama yok** — teşhis haritası; F6 bu haritaya göre onarır.

---

## Zincir (sırayla)

```
1) Mic izin + kullanıcı jesti
2) HTTPS 8443 (veya güvenli bağlam) — getUserMedia
3) MediaRecorder / VAD (konuşma sonu)
4) Ses blob → POST STT (/api/… whisper)
5) Metin → sohbet turu (stream/full) — PC beyin 8779
6) Cevap metni UI
7) (isteğe) TTS → hoparlör
8) Wake Lock / sekme arka plan → yeniden dinle
```

---

## Belirti → olası kırılma

| Senin gördüğün | Muhtemel halka | Hızlı kontrol |
|----------------|----------------|---------------|
| «sürekli: HTTPS + mikrofon gerekli» | 1–2 | `8443` açık mı, sertifika kabul edildi mi |
| «kayıt açılamadı» / start hatası | 2–3 | Tarayıcı mic izni, başka app mic kilidi |
| «ses → metin…» uzun / STT hata | 4 | Whisper warmup, `/api` STT log, soğuk ilk tur |
| Metin oluştu, cevap yok | 5 | F0 tur kartı: timeout / miss / Ollama; istemci timeout |
| Cevap yazıda var, ses yok | 6–7 | `with_tts` politikası, TTS pool, hoparlör sessiz |
| Bir tur sonra kesildi | 8 | Wake Lock, sekme arka plan, VAD yeniden bağ |
| ForceRestart sonrası farklı davranış | Working tree / SW cache | PWA SW sürümü, tek canlı yol (F6.1) |

---

## PC vs mobil ortak teşhis

1. `GET /api/tur-teshis/warmup` → `ilik` / `soguk` / `isiniyor`  
2. Bir yazı turu at → `GET /api/tur-teshis/recent` → `miss_class`, `elapsed_sec`, `hits_count`  
3. Mobilde aynı soruyu sesle dene → kırılma 4 mü 5 mi ayır  

**Kural:** STT metni geldiyse kütüphane/F2 suçlanmaz; ses gelmediyse F6/F7.

---

## F6’ya devir notları

- Tek canlı yol: `with_tts` / history / STT fast tutarlı  
- Barge-in mobil (TTS kes)  
- Hata cümleleri F0 miss sınıfıyla aynı dil  
- Checklist: Wi‑Fi + Tailscale + HTTPS mic ayrı satır
