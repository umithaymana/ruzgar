# Rüzgar → Cursor seviyesi — Kapanış planı (Faz 39+)

> **Hedef:** Programlama motorunda **~85/100** (Cursor referans 100).  
> **Bugün:** ~**85/100** (build `faz47-v58`, offline kilidi + bağımsız proje üret).  
> **İlke:** Her faz = ölçülebilir çıktı + smoke yeşil + gerçek görevde skor artışı.

**Referans karşılaştırma:** [PROGRAMMING_MOTOR_CURSOR_PLAN.md](PROGRAMMING_MOTOR_CURSOR_PLAN.md) · Üstayol: [PROGRAMMING_MOTOR_USTAYOL.md](PROGRAMMING_MOTOR_USTAYOL.md)

---

## 1. Başarı tanımı («Cursor seviyesi» ne demek?)

| KPI | Bugün | Hedef (seviye planı sonu) |
|-----|-------|---------------------------|
| Parity smoke (offline) | 6/6 ✓ | 8/8 (gerçek Groq E2E opsiyonel) |
| `agent_compliance` skor (gerçek görev) | ~50–60, çoğu tur sadece `read` | **≥85** ortalama |
| Tek cümle → yazım + pytest | Bazen metin only | **%90** görevde yeşil verify |
| Kullanıcı «sen yap» hissi (1–5) | ~3 | **≥4.5** |
| Programlama puan (10 boyut ort.) | ~65 | **≥85** |

%100 = tam VS Code fork + cloud agent + sınırsız frontier — **bilinçli olarak hedef dışı** (ayrı ürün).

---

## 2. Açıklar → faz haritası (özet)

| # | Açık (Cursor’da var, Rüzgar’da zayıf) | Öncelik | Faz | Tahmini etki |
|---|----------------------------------------|---------|-----|----------------|
| A1 | Kota / boş tur → yazım yok | **P0** | **39** | +12 puan «tek sohbet = iş» |
| A2 | Araç protokolü kırılgan (`@@write` metin parse) | **P0** | **40** | +10 araç güvenilirliği |
| A3 | Otonomi sınırı (8 tur, 5 dk) | **P1** | **41** | +8 çok dosya |
| A4 | LSP zayıf (yalnız goto) | **P1** | **42** | +7 proje anlama |
| A5 | Terminal preset, özgür shell yok | **P1** | **43** | +6 terminal |
| A6 | Bağlam ölçeği (repo semantiği) | **P2** | **44** | +6 bağlam |
| A7 | Model zinciri güvenilirliği (Gemini öncelik kalıntısı) | **P0** | **39** (kısmi) + **40** | +8 model |
| A8 | IDE entegrasyonu (refactor, çok dosya editör) | **P2** | **45** | +5 UI |
| A9 | Paralel alt ajan / cloud | **P3** | sonraya | — |

---

## 3. Dört dalga (sprint)

```text
Dalga 1 — «İş bitsin»     Faz 39–40   (2–3 oturum)   P0
Dalga 2 — «Uzun görev»    Faz 41–42   (2 oturum)     P1
Dalga 3 — «Terminal+bağlam» Faz 43–44 (2 oturum)     P2
Dalga 4 — «Cila + ölçüm»  Faz 45–46   (1 oturum)     KPI kilidi
```

---

## 4. Faz detayları

### Faz 39 — Görev tamamlama kilidi (P0) ← **ŞİMDİ**

**Sorun:** Uyum kayıtlarında `read` var, `write`/`verify` yok; kota erken dur.

**Yapılacaklar:**
- Görev modunda beyin: `groq,kod` zorunlu öncelik (Gemini görev turunda ikincil).
- Keşif yapıldı ama yazım yok → Faz 38 döngüsünden sonra **zorunlu yazım mandate** LLM turu.
- `should_abort_loop`: keşif varsa kota/boş turda **+1 tur tolerans**.
- Varsayılan `RUZGAR_CODE_AGENT_MAX_TURNS=12` (env ile 8’e dönülebilir).

**Başarı:** `benim-api health version + pytest` → en az 1 yazım + verify yeşil (3 denemede %80).

**Env:** `RUZGAR_FAZ39=1` · `RUZGAR_FAZ39_MANDATE=1`

---

### Faz 40 — Yapılandırılmış araç API (P0)

**Sorun:** LLM metin içinde `ruzgar-tool` üretmeyi unutuyor.

**Yapılacaklar:**
- `programlama_faz40.py` — OpenAI `tools` / function calling şeması (`read`, `write`, `grep`, `verify`, `run`, `goto`).
- Sunucu tarafı **tool runner döngüsü** (LLM → tool → LLM, max 6, Faz 38 ile birleşik).
- `@@write` yalnızca yedek; birincil yol function call.
- Smoke: mock LLM tool_calls → dosya yazımı.

**Başarı:** Görev turunda araç çağrısı **sunucu zorunlu**; metin-only tur oranı <%10.

**Env:** `RUZGAR_FAZ40=1` · `RUZGAR_TOOL_API=openai`

---

### Faz 41 — Uzun görev bütçesi (P1)

**Yapılacaklar:**
- Varsayılan bütçe **900 sn** (15 dk), max tur **15**.
- Erken dur: yalnızca 3 boş tur **ve** keşif yok.
- UI: kalan süre / tur SSE.

**Başarı:** 5 dosyalı smoke görevi tek oturumda biter.

---

### Faz 42 — LSP v2 (P1)

**Yapılacaklar:**
- `find_references` · `rename_symbol` (tek dosya, güvenli).
- `ruzgar-tool`: `refs`, `rename`.
- Sembol indeks: import grafı (hafif).

**Başarı:** `referanslar health` → en az 2 hit; rename smoke geçer.

---

### Faz 43 — Terminal v3 (P1)

**Yapılacaklar:**
- `projects/` içinde whitelist genişletme (`pip install`, `python -m`, `uv run`).
- Çıktı SSE canlı; LLM’e otomatik özet.
- Tehlikeli komutlar kapalı kalır.

**Başarı:** React projede `npm run build` + çıktı sohbette.

---

### Faz 44 — Bağlam v3 (P2)

**Yapılacaklar:**
- Repo haritası: dizin ağacı + «son değişen dosyalar» görev başında.
- `@dosya` / `@klasör` istemci kısayolu → `read` batch.
- İlgili dosya seçici (anahtar kelime + sembol).

**Başarı:** 50+ dosyalı projede «ana giriş nerede» < 5 sn doğru.

---

### Faz 45 — Editör cila (P2)

**Yapılacaklar:**
- Çok dosya patch sekmesi; satır içi diff v2 (syntax renk).
- Bekleyen patch + görev otomatik uygula birleşik UX.

---

### Faz 46 — Cursor parity kilidi (ölçüm)

**Yapılacaklar:**
- `programlama_cursor_parity.py` — 3 senaryo: API ekle, bugfix+test, 3 dosya refactor.
- CI: skor ≥85 yoksa uyarı (bloklamaz).
- Rapor: `scripts/ruzgar_cursor_seviye_sonuc.json`
- Plan puan tablosu güncelle → hedef 85/100.

---

## 5. Puan projeksiyonu

| Milestone | Build | Tahmini puan |
|-----------|-------|----------------|
| Bugün (Faz 38) | v50 | 65 |
| Faz 39–40 (Dalga 1) | v51–52 | **72–78** |
| Faz 41–42 (Dalga 2) | v53–54 | **78–82** |
| Faz 43–46 (Dalga 3–4) | v55–57 | **82–86** (offline kilidi ≥85) |

---

## 6. Ortam (Ümit abi — önerilen)

```powershell
$env:RUZGAR_PROG_UNIFIED_AGENT = "1"
$env:RUZGAR_CODE_AGENT_BRAIN = "groq,kod"
$env:RUZGAR_PROG_BRAIN_CHAIN = "groq,kod,gemini"
$env:GROQ_API_KEY = "<anahtar>"
$env:RUZGAR_CODE_AGENT_MAX_TURNS = "12"
$env:RUZGAR_CODE_AGENT_BUDGET_SEC = "900"
$env:RUZGAR_FAZ39 = "1"
# Faz 40 sonrası:
# $env:RUZGAR_FAZ40 = "1"
```

---

## 7. Bu oturum — başlangıç

| Adım | Durum |
|------|--------|
| Bu plan dosyası | ✓ |
| **Faz 39** görev tamamlama kilidi | ✓ v51 |
| **Faz 40** yapılandırılmış araç API | ✓ v51 |
| **Faz 41** uzun görev (15 tur / 15 dk) | ✓ v52 |
| **Faz 42** LSP v2 (refs, rename) | ✓ v53 |
| **Faz 43** terminal v3 | ✓ v54 |
| **Faz 44** bağlam v3 | ✓ v55 |
| **Faz 45** editör cila | ✓ v56 |
| **Faz 46** Cursor seviye kilidi | ✓ v57 |
| **Faz 47** Bağımsız proje üret | ✓ v58 |

---

*Ümit & Gökçenur — Cursor seviyesi + bağımsız üretim (Faz 39–47)*
