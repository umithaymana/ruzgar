# Programlama motoru — Blok A→J iş planı (commit + push)

**Oluşturulma:** 2026-05-29  
**Onaylı masaüstü taban:** commit `e2cccb8` (`RUZGAR_MASAUSTU_ONAYLI_DURUM.md`)  
**API hedef rev:** `2026-05-27-ruzgar-faz98-v107`  
**Başlatma:** `Ruzgar_TemizBaslat.bat` · test: Sunucu ✓ + motor geçişi + Gönder

---

## Genel kurallar (her blok öncesi)

1. `git pull` (uzak güncelse).
2. Blok başında: `git checkout -b plan/blok-X-kisa-ad` (main’den).
3. Blok bitiminde checklist geçmeden commit/push yok.
4. **`ruzgar-desktop/`** değişecekse: `e2cccb8` checklist + Ctrl+Shift+R test zorunlu.
5. Commit mesajı: `feat(programlama): blok X — <özet>` veya `chore/docs/chore(ruzgar): …`
6. Push: `git push -u origin HEAD`
7. Blok sonrası: `main`’e merge (PR veya doğrudan merge — tercihinize göre; aşağıda PR önerilir).

### Blok sonu şablonu (kopyala-yapıştır)

```powershell
cd "d:\CURSOR PROJELER\YAPAY ZEKA"
git status
git add <dosyalar>
git commit -m "feat(programlama): blok X — <tek cümle özet>"
git push -u origin HEAD
# İsteğe bağlı: gh pr create --title "..." --body "..."
```

### Ortak test checklist (UI dokunan bloklar)

- [ ] Rüzgar kapat → `Ruzgar_TemizBaslat.bat` → Ctrl+Shift+R
- [ ] Sunucu ✓ · Bağlantı Aktif
- [ ] Programlama sekmesi · Gönder · en az bir motor geçişi

---

## Blok A — Koruma (1–10)

**Branch:** `plan/blok-a-koruma`  
**Süre tahmini:** 0.5 gün  
**Amaç:** Mevcut çalışan hattı kilitle; regresyon önleme.

| # | İş | Dosya / komut |
|---|-----|----------------|
| A1 | Onay doc’a bu plan linki | `RUZGAR_MASAUSTU_ONAYLI_DURUM.md` ✓ |
| A2 | `e2cccb8` geri alma notu README kök | `docs/RUZGAR_HIZLI_GERI_ALMA.md` ✓ |
| A3 | Haftalık bench komutu script | `scripts/Ruzgar_Programlama_Bench.bat` ✓ |
| A4 | E1 izleme: task-stats curl örneği doc | `RUZGAR_PROGRAMLAMA_E1_IZLEME.md` ✓ |
| A5 | `.gitignore` kontrol: `.ruzgar/` geçici | kök `.gitignore` |
| A6 | Launcher tek giriş: `Ruzgar_TemizBaslat.bat` doc | `RUZGAR_MASAUSTU_ONAYLI_DURUM.md` |
| A7 | CI notu: upgrade `--strict` ne zaman | `PROGRAMLAMA_100_ROADMAP.md` 1 satır |
| A8 | Blok checklist bu dosyada (tamam) | — |
| A9 | Tag hazırlığı notu: `ruzgar-desktop-baseline-e2cccb8` | doc only |
| A10 | Boş commit yok — en az A1–A3 dosya | — |

**Blok A test:** Bench bat çalışır (veya py komutu döner); Rüzgar açılır.

**Commit:** `chore(ruzgar): blok A — koruma, bench script, geri alma doc`  
**Push:** `git push -u origin plan/blok-a-koruma`

---

## Blok B — Faz 98 UI paneli (11–20)

**Branch:** `plan/blok-b-faz98-ui`  
**Süre:** 1 gün  
**Amaç:** Kaybedilen Ümit onay kartı + KPI poll; **sadece** programlama UI.

| # | İş | Not |
|---|-----|-----|
| B11 | HTML: `programlama-umit-onay-card` | `index.html` ✓ |
| B12 | `renderProgramlamaUmitOnay()` | `app.js` ✓ |
| B13 | `GET /api/programlama/umit-onay` fetch | KPI dashboard içinde ✓ |
| B14 | Onayla → `tamam yap` (sohbet veya API) | buton → sohbet ✓ |
| B15 | İptal → `yapma` | ✓ |
| B16 | Bekleyen yok durumu | kart + «Bekleyen işlem yok» ✓ |
| B17 | Programlama sekmesi 10 sn poll | `setInterval` 10s ✓ |
| B18 | `programlama-phase-badge` manifest sync | `applyUiManifest` (mevcut) ✓ |
| B19 | Manuel test: kopyala iste → panel → tamam yap | kullanıcı |
| B20 | `app.js?v=` cache buster artır | `20260529-blok-b` ✓ |

**Blok B test:** Onay kartı görünür; `e2cccb8` checklist yeşil.

**Commit:** `feat(ruzgar): blok B — Faz 98 Ümit onay paneli (minimal UI)`  
**Push:** `git push -u origin plan/blok-b-faz98-ui`  
**PR:** `ruzgar-desktop` only · base `main`

---

## Blok C — Canlı E1 (81→90) (21–30)

**Branch:** `plan/blok-c-e1-canli`  
**Süre:** 1–2 hafta (kademeli commit alt-grupları mümkün)

| # | İş | Backend / UI |
|---|-----|--------------|
| C21 | Kök neden etiketi: başarısız görev | `programlama_faz102_e1_live` + faz55 ✓ |
| C22 | Tekrarlayan kök neden → kural önerisi | `.ruzgar/root_cause_rule_hints.jsonl` ✓ |
| C23 | Retry turu footer sohbette net | `format_retry_footer` faz14 ✓ |
| C24 | `task_outcomes` haftalık özet API | `weekly_summary` task-stats ✓ |
| C25 | pytest fail → bonus tur tetik (varsa sertleştir) | Faz 55b/61 (mevcut) ✓ |
| C26 | verify kırmızı kullanıcı mesajı | `format_verify_failure_line` ✓ |
| C27 | scope dışı erken red mesajı | faz78 + write red ✓ |
| C28 | Görev süresi uyarısı (1200 sn) | `RUZGAR_TASK_DURATION_WARN_SEC` ✓ |
| C29 | E1 hedef çizgisi %90 UI | task-stats detail · `RUZGAR_E1_TARGET_RATE` ✓ |
| C30 | 20 görev rolling rapor | `rolling_20` API + UI satırı ✓ |

**Blok C test:** `e1_success_rate` trend; en az 5 görev manuel.

**Commit:** `feat(programlama): blok C — E1 kök neden, retry UX, task-stats`  
**Push:** `git push -u origin plan/blok-c-e1-canli`

---

## Blok D — Komut 100 (31–40)

**Branch:** `plan/blok-d-komut-100`  
**Süre:** 3–5 gün

| # | İş |
|---|-----|
| D31–D35 | `programlama_command_goldens.json` 30→50 ifade | ✓ |
| D36 | CI: `evaluate_command_dataset` + `--strict` runner | ✓ |
| D37 | Başarısız örnekleri altın sete ekle (süreç — aylık) | ✓ not |
| D38 | Upgrade gate komut ≥95 | ✓ 100/50 |
| D39 | Türkçe fiil kalıpları (`şuraya kopyala`) | ✓ |
| D40 | Aylık revizyon notu doc | ✓ `PROGRAMLAMA_100_ROADMAP.md` |

**Blok D test:** `python scripts/programlama_upgrade_runner.py --strict` → command 100.

**Commit:** `feat(programlama): blok D — komut altın seti 50 + CI gate`  
**Push:** `git push -u origin plan/blok-d-komut-100`

---

## Blok E — Bağımsız proje 100 (41–50)

**Branch:** `plan/blok-e-otonomi-100`  
**Süre:** 1 hafta

| # | İş |
|---|-----|
| E41–E43 | `programlama_task_ladder.json` S4/S5 senaryolar | ✓ |
| E44 | Faz 99 iki koşu CI zorunlu (`--strict` + smoke `--upgrade`) | ✓ |
| E45 | Üretim min %95 gate | ✓ |
| E46 | Otonomi rapor arşiv `.ruzgar/autonomy_reports/` | ✓ |
| E47 | smoke-autonomy temizlik | ✓ `cleanup_smoke_autonomy.py` + bat |
| E48 | Görev sonu git commit kanıtı | ✓ `git_branch_commit` ×2 |
| E49 | Bağımsızlık ≥95 gate | ✓ `independence_level` |
| E50 | Parity full 8/8 aylık takvim doc | ✓ `PROGRAMLAMA_PARITY_AYLIK_TAKVIM.md` |

**Blok E test:** upgrade runner ladder 5/5; Faz 99 x2 ok.

**Commit:** `feat(programlama): blok E — merdiven S4/S5, Faz 99 CI gate`  
**Push:** `git push -u origin plan/blok-e-otonomi-100`

---

## Blok F — Profesyonel iş akışı (51–60)

**Branch:** `plan/blok-f-git-pr`  
**Süre:** 3–5 gün

| # | İş |
|---|-----|
| F51 | `pr hazırla:` UI kısayol butonu (programlama atölye) | ✓ `btn-pr-prepare` |
| F52 | gh PR önerisi metni (onaylı, otomatik PR yok) | ✓ `/api/programlama/pr-plan` |
| F53–F55 | branch / commit şablon / diff öncesi UI | ✓ git + PR kartları |
| F56 | git strip otomatik yenile (poll) | ✓ 15s + dosya açılışında |
| F57 | haftalık parity hatırlatıcı doc + script | ✓ bat + aylık takvim |
| F58 | `zayıflık raporu` tek komut doc | ✓ `PROGRAMLAMA_ZAYIFLIK_KOMUT.md` |
| F59 | stale build banner sadeleştir (UI) | ✓ |
| F60 | weekly KPI JSON okuma kartı | ✓ `weekly-kpi` API |

**Commit:** `feat(programlama): blok F — git/PR UX, parity hatırlatıcı`  
**Push:** `git push -u origin plan/blok-f-git-pr`

---

## Blok G — Uzun görev / çok dosya (61–70)

**Branch:** `plan/blok-g-mega-gorev`  
**Süre:** 1–2 hafta

| # | İş |
|---|-----|
| G61–G63 | mega refactor stress; 16 dosya/tur test |
| G64 | patch plan önizleme UI |
| G65 | tur bütçe göstergesi |
| G66 | çok dosyalı parity senaryo |
| G67 | touched_files liste UI |
| G68 | yarım görev devam |
| G69 | birleşik verify rapor |
| G70 | E2 hedef %90 ölçüm doc |

**Commit:** `feat(programlama): blok G — mega görev UX, touched_files, verify`  
**Push:** `git push -u origin plan/blok-g-mega-gorev`

---

## Blok H — Ana Motor ↔ Programlama (71–80)

**Branch:** `plan/blok-h-handoff`  
**Süre:** 1 hafta

| # | İş |
|---|-----|
| H71–H75 | handoff özeti, delege, pytest footer |
| H76–H78 | çok motor sırası, dönüş, bağlam log |
| H79 | E4 hedef doc |
| H80 | manifest programlama tag doğrulama |

**Commit:** `feat(ruzgar): blok H — Ana Motor handoff v4, delege özet`  
**Push:** `git push -u origin plan/blok-h-handoff`

---

## Blok I — Yerel / Groq’suz (81–90)

**Branch:** `plan/blok-i-yerel-zincir`  
**Süre:** 1 hafta

| # | İş |
|---|-----|
| I81–I83 | ollama-only test; Gemini FC stress; text-only <%1 |
| I84–I86 | prog_local_first; API’siz smoke; zincir dokümantasyon |
| I87–I90 | kırsal senaryo; fallback mesaj; E3 hedef; rapor |

**Commit:** `feat(programlama): blok I — yerel öncelik zinciri, ollama-only smoke`  
**Push:** `git push -u origin plan/blok-i-yerel-zincir`

---

## Blok J — Tercüme UI + kapanış (91–100)

**Branch:** `plan/blok-j-tercume-kapanis`  
**Süre:** 1–2 hafta · **programlama dosyalarına dokunma yok**

| # | İş |
|---|-----|
| J91 | tercüme dosya listesi (mini PR 1) |
| J92 | çevir butonu wiring |
| J93 | OCR import |
| J94 | kaydet hedef |
| J95 | ebook akışı |
| J96 | masaüstü checklist otomasyon (opsiyonel) |
| J97 | `RUZGAR_MASAUSTU_ONAYLI_DURUM` rev 2 |
| J98 | memnuniyet anketi taslağı |
| J99 | programlama 100/100 onay doc |
| J100 | Faz 100 hub notu (Ana Motor) |

**Her J91–J95:** ayrı commit mümkün; blok sonunda **tek push** veya alt-commit + son push.

**Blok J test:** Tercüme atölye + `e2cccb8` checklist hâlâ yeşil.

**Commit:** `feat(ruzgar): blok J — tercüme atölye UI (ayrı hat, programlama dokunulmadı)`  
**Push:** `git push -u origin plan/blok-j-tercume-kapanis`

---

## Sıra özeti (gelince uygula)

```
A → push → (merge main)
B → push → test masaüstü
C → push
D → push
E → push
F → push
G → push
H → push
I → push
J → push
```

**Önerilen merge:** Her blok PR ile `main`’e; Blok B ve J’de ekstra UI test.

---

## Hızlı başlangıç (dönüşünüzde ilk komutlar)

```powershell
cd "d:\CURSOR PROJELER\YAPAY ZEKA"
git status
git pull
git checkout main
git checkout -b plan/blok-a-koruma
# A1–A10 işleri
# test
git add .
git commit -m "chore(ruzgar): blok A — koruma, bench script, geri alma doc"
git push -u origin plan/blok-a-koruma
```

---

## İlgili dosyalar

- `ilim-assistant/docs/RUZGAR_MASAUSTU_ONAYLI_DURUM.md` — kesin emir taban
- `ilim-assistant/docs/PROGRAMLAMA_100_ROADMAP.md` — komut/otonomi hedef
- `PROGRAMMING_MOTOR_YOL_HARITASI.md` — Dalga E–H
- `scripts/ruzgar_programlama_upgrade_report.json` — son bench kanıtı

**Durum:** Blok F tamamlandı (2026-05-29) — PR hazırla UI, git strip poll 15s, weekly KPI kartı. Sırada **Blok G** (mega görev).  
Blok B: `programlama-umit-onay-card`, `renderProgramlamaUmitOnay`, 10 sn poll, `app.js?v=20260529-blok-b`.
