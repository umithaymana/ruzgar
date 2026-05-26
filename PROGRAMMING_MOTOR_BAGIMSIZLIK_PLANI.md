# Programlama Motoru — Tam Bağımsızlık Planı (Faz 49+)

> **Kayıt tarihi:** 2026-05-26  
> **Durum:** Yarın devam — Ümit & Gökçenur  
> **Mevcut build:** `2026-05-26-programlama-faz57-v68`  
> **Yol haritası:** [PROGRAMMING_MOTOR_YOL_HARITASI.md](PROGRAMMING_MOTOR_YOL_HARITASI.md)  
> **Referans:** [PROGRAMMING_MOTOR_CURSOR_SEVIYE_PLAN.md](PROGRAMMING_MOTOR_CURSOR_SEVIYE_PLAN.md) · [PROGRAMMING_MOTOR_USTAYOL.md](PROGRAMMING_MOTOR_USTAYOL.md)

---

## 1. «Tam bağımsız» ne demek?

Cursor IDE olmadan, yalnızca Rüzgar Atölyesi ile:

| Yetenek | Bugün (Faz 47–48) | Hedef |
|---------|-------------------|--------|
| `proje üret:` / Proje Üret UI | ✓ fastapi, static, react, cli + offline bootstrap | + özellik listesi → çok dosya |
| Tek cümle görev → patch + pytest | Kısmen (Groq/Gemini gerekir) | %80 görevde yeşil verify |
| Site / API / React iskelet | ✓ şablon | + CRUD/login şablonları |
| Doğal dil «şu özelliklerle uygulama yap» | Zayıf (genel sohbet karışır) | Programlama modunda otomatik yönlendirme |
| Uzun otonom görev (çok dosya) | 8–12 tur, kota sınırı | 12+ tur, mandate write |
| Bağımsız çalışma (API restart) | Kullanıcı `Ruzgar_YenidenBaslat.bat` | Otomatik build uyumu |

**Ölçü:** Parity smoke yeşil + `agent_compliance` ortalama **≥85** + kullanıcı «Cursor’sız yaptı» hissi **≥4.5/5**.

---

## 2. Dört dalga (yarın ve sonrası)

### Dalga A — Stabilite (1 oturum) · Faz 49 ✓

- [x] Restart sonrası build kilidi: UI + `Ruzgar.ps1` → `faz49-v60`
- [x] Ana Motor: gündelik (`nasılsın`) **eğitim katmanından önce** hızlı yol
- [x] Karşılaştırma / ansiklopedik soruda gereksiz web atlama (`looks_like_fast_llm_fact_question`)
- [x] UI varsayılan «Sayfa oku» = 0; `chat_core` hızlı bilgi turunda web kapalı

**Çıktı:** Canlı sohbet tutarlı; Faz 38 uyarısı tekrarlamaz.

---

### Dalga B — «İş bitsin» (2 oturum) · Faz 50–51

**Faz 50 — Doğal dil → proje üret köprüsü** ✓

- [x] «Şu özelliklere sahip …» cümlesini `proje üret:` + şablon + `features[]` parse
- [x] Ana Motor «site yap» deyince otomatik Programlama delege (Faz 10 genişletme)
- [x] UI: Proje Üret modalında özellik listesi alanı

**Faz 51 — Offline görev genişletme** ✓

- [x] Offline bootstrap: `crud_api`, `auth_jwt`, `dashboard_static` şablonları
- [x] Her şablonda: README + pytest + `requirements.txt` (API) / statik smoke
- [x] Smoke: faz51 şablonları × offline verify (`programlama_smoke.py`)

**Başarı:** Cursor’sız 4 proje tipi tek komutla yeşil.

---

### Dalga C — Otonom ajan (2 oturum) · Faz 52–53

**Faz 52 — Function calling birincil (Faz 40 sertleştirme)** ✓

- [x] Görev modunda metin-only tur → zorunlu araç kurtarma (`run_structured_recovery_turn`)
- [x] `write` + `verify` mandate → function-call (`tool_choice=required`, Faz 52 FC)
- [x] Kota: keşif sonrası +1 tur toleransı (`effective_max_turns` / `discovery_bonus_turns`)

**Faz 53 — Bağlam + sembol** ✓

- [x] Workspace sembol indeksi (Faz 22 + Faz 53 lite): sınıf/fonksiyon özeti LLM’e
- [x] Çok dosya patch önizleme (Faz 45) Atölye’de varsayılan

**Başarı:** `benim-api health + pytest` görevi 3 denemede %80 yeşil.

---

### Dalga D — Ölçüm ve KPI (1 oturum) · Faz 54 ✓

- [x] `ruzgar_parity_smoke.py` → 8/8 (`--quick` / `--groq-e2e` opsiyonel)
- [x] `agent_compliance` v3: hedef ≥85, JSON + Atölye KPI kartı (`/api/programlama/kpi-dashboard`)
- [x] Üstayol dokümanı güncelle; build `faz54-v65`

---

## 3. Öncelik matrisi (P0 → P2)

| P | İş | Faz | Etki |
|---|-----|-----|------|
| P0 | Restart/build uyumu otomatik | 49 | Kullanıcı güveni |
| P0 | Doğal dil → proje üret | 50 | «Tam bağımsız üretim» |
| P0 | Offline şablon çoğaltma | 51 | Cursor’sız HTML/API |
| P1 | Function call mandate | 52 | Görev bitirme |
| P1 | Sembol/bağlam | 53 | Büyük repo |
| P2 | KPI kilidi + dokümantasyon | 54 | Ölçülebilir 85 puan |

---

## 4. Dalga E — Devam (Faz 55+) · [YOL HARİTASI](PROGRAMMING_MOTOR_YOL_HARITASI.md)

**Faz 55 — Canlı görev KPI** (uygulanıyor)

- [x] `task_outcomes.json` kayıt
- [x] API `/api/programlama/task-stats` + KPI dashboard entegrasyonu
- [x] Ana Motor handoff paketi (delege)
- [ ] Otomatik retry turu (Faz 55b)

**Sırada:** Faz 56 uzun görev · Faz 57 Groq yedek · Faz 58 git

---

## 5. Bilinçli olarak sonraya

- Cloud alt ajan / paralel worktree (Cursor Best-of-N)
- Tam LSP (rename symbol tüm repo)
- Özgür shell (güvenlik politikası ayrı tasarım)
- %100 frontier model garantisi

---

## 5. Yarın ilk 30 dakika kontrol listesi

1. `Ruzgar_YenidenBaslat.bat` → build `faz48-v59` doğrula  
2. `py -3 ilim-assistant/scripts/programlama_smoke.py --ci`  
3. Programlama: `proje üret: static_site test-vitrin smoke`  
4. Ana Motor: «nasılsın» + «Neptün mü Dünya mı büyük» (web kapalı/açık)  
5. Bu dosyadan **Faz 49** ile kodlamaya başla  

---

## 6. İlgili dosyalar (geliştirme)

| Alan | Dosya |
|------|--------|
| Proje üret | `programlama_faz47.py` |
| Uyum skoru | `programlama_faz48.py` |
| Ajan döngüsü | `programlama_faz14.py`, `programlama_faz38.py`, `programlama_faz40.py` |
| API / UI | `desktop_server.py`, `ruzgar-desktop/app.js`, `index.html` |
| Başlatma | `Ruzgar.ps1`, `Ruzgar_YenidenBaslat.bat` |
| Ana Motor sohbet | `desktop_server.py`, `ruzgar_egitim.py`, `ruzgar_umed_cevap_emri.py` |

---

*Plan onaylı — yarın bu sırayla devam.*
