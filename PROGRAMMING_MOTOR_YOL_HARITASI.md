# Rüzgar — Yol haritası (Faz 55+)

> **Temel:** Faz 49–62 · build `faz62-v73`  
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
- [x] Başarısız görevde **otomatik retry turu** (Faz 55b / Faz 61 — v72)

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

### Faz 58 — Git entegrasyonu (read-only+) ← **UYGULANDI (v69)**

- [x] `git status` / `git diff --stat` preset (Faz 15/43 + alias)
- [x] Patch öncesi/sonrası diff özeti LLM’e (tur + patch sonrası)
- [x] UI: «Son değişiklikler» şeridi + `/api/programlama/git-changes`

### Faz 59 — Ana Motor v2 (kod niyeti) ← **UYGULANDI (v70)**

- [x] Kod niyeti sınıflandırıcı (`classify_turn_intent`, ~50ms kural)
- [x] Delege sonrası **kısa özet** (yazım + pytest) — chat `done` + agent footer
- [x] İlim 22 sn; kod delege → `router_budget_sec` + programlama tam bütçe
- [x] API: `/api/ana-motor/delegation-summary`

### Faz 60 — Otomasyon kilidi ← **UYGULANDI (v71)**

- [x] `Ruzgar.ps1` + UI: build uyumsuzluğunda **restart önerisi** (MessageBox + confirm)
- [x] Haftalık KPI JSON — `.ruzgar/weekly_kpi_YYYY-WW.json` + `scripts/ruzgar_weekly_kpi.py`
- [x] `programlama_smoke --ci` + `ruzgar_parity_smoke.py --ci` · parity **full** haftada 1
- [x] API: `/api/programlama/weekly-kpi` · `/api/programlama/ci-run`

---

## Dalga G — İleri (sonraya)

### Faz 61 — Otomatik retry (Faz 55b) ← **UYGULANDI (v72)**

- [x] Normal turlar bittikten sonra verify/yazım kırmızıysa **+1 bonus tur**
- [x] `inject_faz55b_turn_prefix` + KPI kaydında `bonus_retry`
- [x] Kapat: `RUZGAR_FAZ55B=0`

### Faz 62 — Git commit önerisi v2 ← **UYGULANDI (v73)**

- [x] Görev sonrası otomatik commit mesajı (değişiklik varsa)
- [x] git-changes API: `pending_commit` / `commit_suggest`
- [x] Atölye şeridi + `görev:` → Faz 7 rehberi çakışması giderildi

**Sırada (Dalga G devam):**

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

*Build: `faz62-v73` · Faz 62 tamam. Sonraki: canlı KPI ölçümü / Dalga G.*
