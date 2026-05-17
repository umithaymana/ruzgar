# Rüzgar Ustası — Yol Haritası (Faz 8–12)

> **Kayıt:** 2026-05-17 · Ümit & Gökçenur  
> **Hedef:** Bilgi açısından Gemini/Cem seviyesi; programlamada Cursor benzeri ajan.  
> **Durum:** Plan onaylandı — uygulama bekliyor.

---

## Hedef profili

| Alan | Hedef | Bugünkü Rüzgar (özet) |
|------|--------|------------------------|
| Genel bilgi | Güncel, kaynaklı, derin özet | Yerel RAG + web + Ollama (8B/3B) |
| Programlama | Proje okur, çok dosya düzenler, test/debug döngüsü | Atölye Faz 1.3, `@@dosya`, mini ajan |
| Birlikte | Ana Motor doğru motoru seçer, kalite kontrol | Plan + motorlar; reflection/kod döngüsü eksik |

**“Her şeyi bilen”** = sonsuz bilgi değil; doğru kaynak + doğru derinlik + dürüst “bilmiyorum” + kabul edilebilir hız.

---

## Gerçekçi sınır

- Yerel **8B** → iyi asistan; üst bilgi/kod için sınırlı.
- **70B+ veya bulut API** (Gemini/OpenAI/Claude) → ciddi sıçrama.
- **Programlama** → model + **workspace araçları** (dosya, terminal, diff, test).

Plan **iki katmanlı:** (A) mimari/ürün, (B) donanım veya bulut model.

---

## Mevcut durum (Faz 0–7)

| Faz | Ad | Durum |
|-----|-----|--------|
| 0 | UI iskeleti | tamam |
| 1 | Programlama (1.3) | tamam |
| 2 | Okuma | tamam |
| 3 | Tercüme | tamam |
| 4 | Ses | tamam |
| 5 | Video | devam (v2) |
| 6 | Ana Motor akıl (plan, RAG, web, ajan) | tamam |
| 7 | Cila (UX, hata, yardım) | tamam |

**Son teknik commit (sohbet hızı):** `2be7ed2` — gündelik anında yanıt, RAG atlama.

---

## Faz 8 — Zeka altyapısı

**Amaç:** Seçilebilir “beyin gücü”.

- Model profilleri: `hizli` (3B), `denge` (8B), `bilgi` (70B/API), `kod` (code model / API)
- Mod başına model eşlemesi
- İsteğe bağlı API köprüsü (Gemini/OpenAI/Claude, `.env`)
- Sağlık paneli: model, gecikme, VRAM

**Çıktı:** Bilgi sorularında 8B tavanına takılmama.

---

## Faz 9 — Bilgi motoru v2 (“Cem” hattı)

**Amaç:** Geniş, güncel, kaynaklı cevap.

| # | Görev |
|---|--------|
| 9.1 | Çok kaynaklı araştırma (indeks + arşiv + web → tek rapor) |
| 9.2 | Kaynak zorunluluğu / güven satırı |
| 9.3 | Bilim/tarih derin mod (arşiv öncelik, uzun bağlam) |
| 9.4 | Güncellik (haber, hava, “bugün” + tarih damgası) |
| 9.5 | Hafıza + öğrenme katmanı (`ruzgar_genel_hafiza`, Hafıza Motoru) |
| 9.6 | Self-reflection (bilgi): cevap → mini kontrol turu → temiz yanıt |

**Başarı ölçütü:** “X nedir?”, tarih/ilim soruları → ~30 sn içinde kaynaklı, tutarlı cevap.

---

## Faz 10 — Programlama motoru v2 (“Cursor” hattı)

**Amaç:** Projede iş yapan ajan.

| # | Görev |
|---|--------|
| 10.1 | Workspace haritası (proje indeksi, `@@` genişletme) |
| 10.2 | Çok dosya düzenleme (plan → oku → patch → onay → yaz) |
| 10.3 | Terminal / test (`pytest`, `npm test`, script çalıştır) |
| 10.4 | Hata ayıklama döngüsü (traceback → düzelt → tekrar, max N tur) |
| 10.5 | Ana Motor → Programlama delege |
| 10.6 | Kod self-reflection (derleme/test kontrolü) |

**Başarı ölçütü:** “X dosyasında Y düzelt” → bulur, patch, smoke test.

---

## Faz 11 — Orkestra şefi v3

- Otonom araştırma v2 (çok adım, durdurulabilir)
- Netleştirme + hız (sohbet anında; bilgi/kod ağır)
- Uzun oturum özeti
- Güven modu (tehlikeli komut onayı)

```
Soru → Plan → Motor delege → Araçlar → Reflection → Yanıt
```

---

## Faz 12 — Cila ve güven

- Regresyon: `ana_motor_smoke` + bilgi + kod senaryoları
- Latency: sohbet &lt;3 sn, bilgi &lt;45 sn, kod turu &lt;2 dk
- Kullanıcı kılavuzu
- Video Faz 5 paralel kalabilir

---

## Uygulama önceliği

1. **Faz 8** — Model profili + API köprüsü  
2. **Faz 9** — Bilgi + reflection  
3. **Faz 10** — Kod ajanı  
4. **Faz 11** — Birleştirme  
5. **Faz 5 Video** — paralel isteğe bağlı  

---

## Donanım / maliyet

| Profil | Bilgi | Kod | Not |
|--------|--------|-----|-----|
| A Yerel güçlü | llama3.1:70b / qwen2.5:72b | deepseek-coder / qwen-coder | 32GB+ RAM/VRAM |
| B Hibrit (önerilen) | Gemini API | Yerel veya API kod | En iyi fiyat/performans |
| C Mevcut PC | 8B + RAG/web | Atölye + küçük patch | Tam Cem/Cursor olmaz; Faz 9–10 yine değerli |

---

## İlk sprint (dönüş oturumu)

1. Sohbet gecikmesi canlı test (`2be7ed2`, API yeniden başlat)  
2. `.env` şablonu: `OLLAMA_CHAT_MODEL`, `GEMINI_API_KEY`, profiller  
3. Faz 8.1: mod → model eşlemesi tasarımı  
4. Backlog: Faz 9.6 + Faz 10.2  

---

## Devam komutu (yeni sohbette)

Şunu yazman yeterli:

> `RUZGAR_USTA_PLAN_FAZ8-12.md` dosyasındaki planı uygulamaya başla — Faz 8’den.

Veya: *“Rüzgar Ustası planına devam”*
