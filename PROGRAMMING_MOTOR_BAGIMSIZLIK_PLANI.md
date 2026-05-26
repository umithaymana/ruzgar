# Programlama Motoru — Tam Bağımsızlık Planı (Faz 49+)

> **Kayıt tarihi:** 2026-05-26  
> **Durum:** Yarın devam — Ümit & Gökçenur  
> **Mevcut build:** `2026-05-25-programlama-faz49-v60`  
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

**Faz 50 — Doğal dil → proje üret köprüsü**

- [ ] «Şu özelliklere sahip …» cümlesini `proje üret:` + şablon + `features[]` parse
- [ ] Ana Motor «site yap» deyince otomatik Programlama delege (Faz 10 genişletme)
- [ ] UI: Proje Üret modalında özellik listesi alanı

**Faz 51 — Offline görev genişletme**

- [ ] Offline bootstrap: `crud_api`, `auth_jwt`, `dashboard_static` şablonları
- [ ] Her şablonda: README + pytest + `requirements.txt` + tek komut çalıştır
- [ ] Smoke: 4 şablon × offline verify

**Başarı:** Cursor’sız 4 proje tipi tek komutla yeşil.

---

### Dalga C — Otonom ajan (2 oturum) · Faz 52–53

**Faz 52 — Function calling birincil (Faz 40 sertleştirme)**

- [ ] Görev modunda metin-only tur <%5
- [ ] `write` + `verify` mandate (Faz 39) function-call ile zorunlu
- [ ] Kota: keşif sonrası +1 tur toleransı

**Faz 53 — Bağlam + sembol**

- [ ] Workspace sembol indeksi (Faz 44 lite): sınıf/fonksiyon özeti LLM’e
- [ ] Çok dosya patch önizleme (Faz 45) Atölye’de varsayılan

**Başarı:** `benim-api health + pytest` görevi 3 denemede %80 yeşil.

---

### Dalga D — Ölçüm ve KPI (1 oturum) · Faz 54

- [ ] `ruzgar_parity_smoke.py` → 8/8 (Groq E2E opsiyonel bayrak)
- [ ] `agent_compliance` v3: hedef ≥85, rapor JSON + UI kart
- [ ] Üstayol dokümanı güncelle; build `faz54-v60`

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

## 4. Bilinçli olarak sonraya

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
