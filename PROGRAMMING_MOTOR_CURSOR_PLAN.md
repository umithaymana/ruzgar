# Rüzgar Programlama Motoru → Cursor seviyesi

> **Tek hedef:** Ümit abi sohbete yazar — Rüzgar projede okur, yazar, çalıştırır, test eder, düzeltir.  
> **Kapsam:** Yalnızca programlama motoru (Ana Motor / diğer motorlar şimdilik dışarıda).

**Referans (Cursor / bu sohbet):** Plan → araçlarla oku → çok dosya değiştir → terminal/test → hata oku → tekrarla → kullanıcıya özet.

**Mevcut build:** `2026-05-25-programlama-faz19-v33` (Faz 8–19 üstayol tamamlandı)

---

## 1. Seviye analizi (dürüst puan)

| Boyut | Cursor (~100) | Rüzgar bugün (~) | Eksik öz |
|--------|----------------|------------------|----------|
| **Tek sohbet = iş** | 95 | 45 | Görev ayrı komut; normal sohbet çoğu zaman «sadece metin» |
| **Araç kullanımı** | 95 | 50 | `@@write` metin içi parse; yapılandırılmış tool yok |
| **Çok dosya / çok tur** | 90 | 55 | Faz 14 var; kota/süre/ boş tur kesiyor |
| **Proje anlama** | 85 | 60 | Faz 13 tarama/@@find; semantik/LSP yok |
| **Terminal + test** | 90 | 70 | Faz 15/7/14 pytest; tam özgür terminal yok |
| **Git** | 80 | 55 | Faz 17 durum/commit; branch/PR yok |
| **UI (diff, onay)** | 90 | 65 | Patch şeridi var; editör içi diff zayıf |
| **Model güvenilirliği** | 90 | 50 | Gemini kota; Groq ikincil |
| **Bağlam yönetimi** | 85 | 40 | `prepare_turn` ağır RAG; kod turunda indeks atlama kısmen |
| **Hız algısı** | 85 | 55 | Uzun «düşünüyor»; 120 sn görev sınırı |

**Genel:** ~**52/100** — güçlü iskelet, **henüz Cursor değil**. Ana boşluk: **tek birleşik ajan döngüsü + yapılandırılmış araçlar**.

---

## 2. Cursor’da olan, bizde olmayan (öncelik sırası)

### P0 — Olmadan «sen yap» hissi gelmez

1. **Birleşik kod ajanı** — Programlama modunda «şunu yap» = otomatik çok tur (görev: şart değil).
2. **Yapılandırılmış araçlar** — `read` / `write` / `grep` / `verify` / `run` (JSON), `@@write` yedek.
3. **Hafif bağlam** — Kod turunda RAG/ansiklopedi kapalı; yalnızca proje özeti + seçili dosyalar.
4. **Güvenilir beyin** — Görevde Groq/kod öncelik (Faz 19); tüm programlama turuna yayılacak.

### P1 — Cursor’a yaklaşma

5. **Sembol/indeks v2** — Tanımlar, import grafı, «şu fonksiyon nerede» (ripgrep+AST hafif).
6. **Otomatik patch uygulama (görevde)** — Görev döngüsünde Faz 16 onay atlama (`RUZGAR_AGENT_AUTO_APPLY=1`).
7. **Plan görünürlüğü** — 3–5 maddelik plan SSE + orkestra (Faz 11 genişletme).
8. **Daha uzun görev bütçesi** — Yapılandırılmış: 5 dk üst sınır, erken dur korunur.

### P2 — Cila

9. Editör satır içi diff  
10. Git branch / PR  
11. Çoklu proje workspace  
12. Mobil şablon  

---

## 3. Hedef mimari (Cursor benzeri)

```text
Kullanıcı (programlama modu)
    │
    ▼
[Niyet: kod/iş mi?] ──hayır──► Kısa sohbet / komut (git durum, şablon…)
    │
   evet
    ▼
[Birleşik Kod Ajanı — Faz 20+]
    │  sistem: proje özeti + araç listesi + aktif dosya
    ▼
 tur 1..N (bütçe + erken dur)
    │  LLM → ruzgar-tool çağrıları
    │  sunucu araçları çalıştırır → sonuç LLM'e
    │  verify (pytest/npm)
    ▼
[Başarı / kırmızı özet] + isteğe bağlı patch onay (normal sohbet)
```

---

## 4. Uygulama programı (Faz 20–25)

| Faz | Ad | Başarı ölçütü | Durum |
|-----|-----|----------------|--------|
| **20** | Birleşik ajan + araç protokolü | «benim-api version ekle» → otomatik tur + tool | ✓ v34 |
| **21** | Hafif bağlam (RAG kapalı) | Kod turu < 5 sn hazırlık | ✓ v35 |
| **22** | Sembol indeks v2 | `sembol health` → tanım listesi | ✓ v36 |
| **23** | Görev otomatik uygula + 5 dk bütçe | Patch onaysız görev; 3 dosya test geçer |
| **24** | Plan SSE + UI adım şeridi | Kullanıcı tur tur görür |
| **25** | Cursor parity smoke | Senaryo: sıfırdan API + test < 5 dk (Groq) |

---

## 5. Hemen başlanan (Faz 20)

- `programlama_faz20.py` — araç çalıştırıcı + birleşik ajan girişi  
- Programlama modunda **iş/niyet** mesajları → Faz 14 döngüsü (normalize)  
- LLM prompt: `ruzgar-tool` JSON blokları  
- Tur sonunda araç çıktıları bir sonraki tura beslenir  
- Env: `RUZGAR_PROG_UNIFIED_AGENT=1` (varsayılan açık)

---

## 6. Sizin kullanım (Faz 20 sonrası)

1. **PROGRAMLAMA MOTORU**  
2. `projects/<proje>` odak  
3. Doğal: **«benim-api health'e version ekle ve pytest geçir»**  
4. `RUZGAR_CODE_AGENT_BRAIN=groq,kod` + GROQ_API_KEY  
5. İzleyin: tur / araç / doğrulama — patch şeridi (isteğe bağlı onay)

---

*Ümit & Gökçenur — Cursor seviyesi yol haritası*
