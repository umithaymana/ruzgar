# Rüzgar — Yol haritası (Faz 55+)

> **Temel:** Faz 49–57 · build `faz57-v68`  
> **Hedef:** Offline KPI değil — **gerçek görevde** Cursor’a yaklaşmak  
> **Ölçü:** Görev başarı oranı **≥80%** · parity **full 8/8** · kullanıcı memnuniyeti **≥4.5/5**

---

## Eksikler özeti (Cursor / bu sohbet ajanına göre)

| # | Eksik | Etki |
|---|--------|------|
| E1 | Offline 8/8 ≠ canlı görev her zaman yeşil | Güven kaybı |
| E2 | Uzun çok dosyalı görev (10+ dosya) | Büyük refactor zor |
| E3 | Groq yokken araç zayıf | Kırsal / API’siz ortam |
| E4 | Ana Motor ↔ Programlama bağlam kopuk | «Site yap» sonrası kayıp |
| E5 | Git yok (status, diff, commit öneri) | Profesyonel iş akışı yarım |
| E6 | Parity sadece `--quick` rutinde | 3 ağır senaryo seyrek |
| E7 | Build/restart kullanıcıda | Eski API uyarısı |

---

## Dalga E — «Gerçek iş bitsin» (Faz 55–57)

### Faz 55 — Görev başarı KPI + delege paketi ← **UYGULANDI (v66)**

- [x] `.ruzgar/task_outcomes.json` — her görev sonucu (başarı, tur, pytest, süre)
- [x] Başarı oranı 30 gün · Atölye kartı + API (`/api/programlama/task-stats`)
- [x] Ana Motor → Programlama **handoff paketi** (scope, hedef, sembol özeti)
- [ ] Başarısız görevde **otomatik retry turu** (Faz 55b — sırada)

**Başarı:** Son 20 görevde **≥70%** verify yeşil (ölçülür).

### Faz 56 — Uzun görev + çok dosya ← **UYGULANDI (v67)**

- [x] `RUZGAR_FAZ56`: 20 tur / 1200 sn (env: `RUZGAR_FAZ56_MAX_TURNS`, `RUZGAR_FAZ56_BUDGET_SEC`)
- [x] Çok dosya patch planı: max 8 dosya/tur (`infer_target_files`, tur plan bloğu)
- [x] Görev sonu **birleşik verify** (pytest + bekleyen patch sayısı)
- [x] `touched_files` agent state · tur başına cap nudge

**Başarı:** 3 dosyalı refactor senaryosu **%80** (parity full — ölçüm sırada).

### Faz 57 — Model yedek zinciri (Groq’suz) ← **UYGULANDI (v68)**

- [x] Gemini function calling yedek (`route_fc_completion` — Faz 40 üzerinden)
- [x] Metin-only oranı **<%3** hedef — `.ruzgar/text_only_stats.json` + KPI dashboard
- [x] `ruzgar_parity_smoke.py --groq-e2e` → Groq veya Gemini FC E2E
- [x] Groq yokken görev zinciri: `gemini` öncelik (Faz 39)

---

## Dalga F — «Profesyonel iş akışı» (Faz 58–60)

### Faz 58 — Git entegrasyonu (read-only+)

- [ ] `git status` / `git diff --stat` preset (Faz 43)
- [ ] Patch öncesi/sonrası diff özeti LLM’e
- [ ] UI: «Son değişiklikler» şeridi

### Faz 59 — Ana Motor v2 (kod niyeti)

- [ ] Kod niyeti sınıflandırıcı (hafif, 50ms)
- [ ] Delege sonrası Ana Motor’da **kısa özet** (ne yazıldı, test sonucu)
- [ ] İlim sorularında 22 sn; kod delege **programlama bütçesine** aktarım

### Faz 60 — Otomasyon kilidi

- [ ] `Ruzgar.ps1` build uyumsuzluğunda **otomatik restart önerisi** (modal)
- [ ] Haftalık KPI e-posta/JSON raporu (opsiyonel)
- [ ] `programlama_smoke --ci` + parity **full** haftada 1

---

## Dalga G — İleri (sonraya)

- Paralel alt ajan (Best-of-N worktree)
- Tam repo sembol rename (LSP tam)
- Özgür shell (güvenlik politikası onayı ile)
- Mobil native (Expo dışı store build)

---

## Öncelik sırası (uygulama)

1. **Faz 55** — ölç, göster, delege paketi  
2. **Faz 56** — uzun görev  
3. **Faz 57** — Groq yedek  
4. **Faz 58–59** — git + Ana Motor özet  
5. **Faz 60** — otomasyon  

---

## Hızlı komutlar

```bash
# Parity
python ilim-assistant/scripts/ruzgar_parity_smoke.py --quick
python ilim-assistant/scripts/ruzgar_parity_smoke.py

# Smoke
python ilim-assistant/scripts/programlama_smoke.py --ci

# Görev istatistik API (Faz 55+)
# GET /api/programlama/task-stats?workspace_root=...
```

---

*Build: `faz57-v68` · Sonraki: Faz 58 Git entegrasyonu.*
