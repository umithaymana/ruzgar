# Rüzgar — Büyük plan (Ümit abi · kesin not)

> **Tarih:** 2026-05-26  
> **Hedef kitle (halka açık):** Komut bilen yazar; bilmeyen **konuşarak / yazarak** hayalini gerçeğe döker.  
> **Mimari:** 1 **Ana Motor** + çok **yardımcı motor** · herkes **kendi sayfasında** · **aynı mantık**.

---

## 1. Kesin ilkeler

| # | İlke |
|---|------|
| P1 | **Tek kullanıcı deneyimi:** Sohbet = konuş + yaptır (Cursor gibi). Komutlar isteğe bağlı (uzman). |
| P2 | **Motor izolasyonu:** Bir motorda çalışırken diğer motorların env/ayarları **karışmaz**. |
| P3 | **Ortak çekirdek:** Tüm motorlar aynı tur hattını paylaşır; fark yalnızca **alan araçları**. |
| P4 | **Sırayla olgunlaştır:** Motorlar **tek tek** ele alınır; hepsi hazır olunca **Ana Motor’a bağlanır**. |
| P5 | **Ana Motor = orkestra:** Son aşamada tüm beceriler Ana Motor’dan da tetiklenir; kullanıcı yine istediği sekmede kalabilir. |

---

## 2. Ortak mantık (Rüzgar Ortak Motor Çekirdeği — ROK)

Her motor turunda aynı sıra:

```text
Mesaj → Niyet (sohbet | yap | komut) → [Anlık komut?] → [Ajan döngüsü?] → [LLM sohbet?] → Özet + KPI
```

| Dal | Ne zaman | Örnek |
|-----|----------|--------|
| **Sohbet** | Soru, açıklama, selam | «bu nedir», «nasıl çalışır» |
| **Yap** | İş fiili + alan bağlamı | «şunu yap», «videoyu kes», «çevir» |
| **Komut** | Uzman yazımı (opsiyonel) | `görev:`, `patch onayla`, `shell onay:` |

**Yap** dalı = çok tur ajan + araçlar + doğrulama (programlamada pytest; videoda ffmpeg; tercümede çeviri doğrulama…).

Paylaşılan parçalar (motorlar arası):

- Niyet sınıflandırıcı (Faz 59 benzeri, mode-aware)
- SSE olayları: `plan` · `step` · `tool` · `done` · `error`
- Oturum + Merkezi Zihin Havuzu yazımı
- Ümit cevap emri (hafıza → RAG → Gemini → Groq)
- Görev sonu kısa özet (Türkçe, herkes anlasın)

---

## 3. Motor envanteri ve sıra

| Sıra | Motor | UI modu | Bugün | Pilot / bağlama |
|------|--------|---------|-------|------------------|
| 1 | **Programlama** | `programlama` | En olgun (Faz 2–67) | **ROK pilot** |
| 2 | **Video** | `video` | İndirme, FFmpeg, kurgu | ROK + video araçları |
| 3 | **Ses** | `ses` | STT/TTS, stüdyo | **ROK Faz 72 (v81)** |
| 4 | **Okuma / Bilim** | `okuma` | Arşiv, ilim | **ROK Faz 73 (v82)** |
| 5 | **Tercüme** | `tercume` | Ofis, altyazı | **ROK Faz 74 (v83)** |
| 6 | **Hafıza** | `hafiza` | Kişisel hafıza, görev | **ROK Faz 75 (v84)** |
| 7 | **Hızır** | `hizir` | Ticaret alt sistemi | ROK (kısıtlı domain) |
| 8 | **Ana Motor** | `genel` | Orkestra, delege | **Hub Faz 76 (v85)** |

**Kural:** Sıra dışı motora ROK bağlanmaz; önceki motor bitmeden env çapraz kopyalanmaz.

---

## 4. Ana Motor birleşimi (son dalga)

- Kullanıcı Ana Motor’da yazar → niyet → doğru motora **sessiz delege** veya aynı thread’de sonuç.
- Her yardımcı motor sayfası = **aynı beceri seti** (sohbet + yap + komut), farklı araç kutusu.
- Ana Motor tüm motorları «köprü» olarak görür; patch/özet tek dilde döner.

---

## 5. Başarı ölçütü (halka açık)

| KPI | Hedef |
|-----|--------|
| Doğal cümle → iş başlatma | ≥ **90%** (motor başına) |
| Görev tamamlama (verify) | ≥ **80%** (programlama önce) |
| Kullanıcı «komut öğrenmek zorunda kaldım» | **Hayır** (anket / 4.5+/5) |
| Motorlar arası ayar karışması | **0** (smoke: izolasyon) |

---

## 6. İlgili dosyalar

| Dosya | Rol |
|-------|-----|
| `ilim_assistant/chat_core.py` | Tur hazırlığı, mod normalizasyonu |
| `ilim_assistant/motorlar/ruzgar_cekirdegi.py` | Çoklu motor bağlamı (genişleyecek) |
| `ilim_assistant/motorlar/programlama_motoru.py` | ROK pilot referans |
| `PROGRAMMING_MOTOR_YOL_HARITASI.md` | Programlama faz detayı |
| Bu dosya | **Üst plan — tüm motorlar** |

---

## 7. Şimdi başlangıç

**Dalga U0 — ROK** (`ruzgar_motor_kernel.py`) — **UYGULANDI**  
**Dalga U1 — Faz 68** konuşarak yap — **UYGULANDI**  
**Dalga U1 — Faz 69** otomatik proje — **UYGULANDI (v79)**  
**Dalga U1 — Faz 70** otomatik patch — **UYGULANDI (v79)**

**Dalga U2 — Video Faz 71** ROK — **UYGULANDI (v80)**

**Dalga U3 — Ses Faz 72** ROK — **UYGULANDI (v81)**

**Dalga U4 — Okuma Faz 73** ROK — **UYGULANDI (v82)**

**Dalga U5 — Tercüme Faz 74** ROK — **UYGULANDI (v83)**

**Dalga U6 — Hafıza Faz 75** ROK — **UYGULANDI (v84)**

**Dalga U7 — Ana Motor Hub Faz 76** — **UYGULANDI (v85)**

**Dalga U8 — Cila Faz 77** — **UYGULANDI (v86)**  
Video indirme: sohbet 180sn yerine masaüstü `/api/video/download` · `scripts/rok_smoke.py` KPI.

**Dalga U9 — Faz 84** — **UYGULANDI (v88)**  
Hızır hub · YouTube isimle arama · UI manifest Faz 68–84.

*Son güncelleme: build `faz84-v88` · UI manifest Faz 68–84.*
