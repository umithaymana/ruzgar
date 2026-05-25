# Rüzgar Programlama Motoru — Üstayol (2026-05-24)

> **Hedef:** Ümit abi için Rüzgar, senin (Cursor/Claude) seviyesinde **projede iş yapan** bir kod ajanı olsun — plan okur, çok dosya yazar, test eder, hata düzeltir, dürüstçe sınır koyar.

> **İlke:** Plan → oku → yaz → doğrula → tekrarla. Her fazda **ölçülebilir** çıktı; smoke test yeşil kalsın.

---

## Şu ana kadar (commit edildi — `main`)

| Commit | Ne |
|--------|-----|
| `0724b7c` | Faz 8–11: patch, delege, web şablonları, orkestra, scaffold odak |
| `ddc57b7` | Faz 12: diff önizleme, `programlama_smoke.py`, hızlı şablon düğmeleri |
| `98d554f` | Manifest Faz 12 etiketi |

**Build:** `2026-05-25-programlama-faz22-v36`

### Bugün çalışan kabiliyetler

- `projects/` altında güvenli okuma/yazma (`@@write`, `.bak`)
- Şablonlar: CLI, FastAPI, paket, bot, **statik site**, **React+Vite**
- `proje çalıştır`, `api başlat`, workspace indeks, `@@read` / `@@glob`
- Ana Motor → programlama **otomatik delege**
- Tur sonu **otomatik patch** + diff önizleme
- Otonom **pytest döngüsü** (sınırlı tur)
- Atölye: ağaç, patch şeridi, orkestra adımları, +API/+Site/+React

### Henüz Cursor kadar değil (dürüst sınır)

- Tek komutla **uzun otonom görev** (10+ dosya, 5+ tur) yok
- Proje genelinde **semantik arama** / tam indeks yok
- **Git** (status, commit, branch) entegre değil
- **npm/git** terminali `projects/` kapsamında sınırlı
- **Mobil uygulama** (Android/iOS) üretimi yok — web/API/CLI var

---

## Güç için 5 sütun

| Sütun | Açıklama | Durum |
|-------|----------|--------|
| **1. Zeka** | Güçlü model zinciri (kod turunda Gemini/API), uzun proje özeti | Kısmen (`llm_brain`, Faz 8) |
| **2. Araçlar** | Okuma, çok dosya yazma, terminal, test | Kısmen (Faz 10, 7) |
| **3. Otonom döngü** | Plan → act → verify → retry (insan müdahalesi az) | Kısmen (Faz 10.4) |
| **4. UI** | Atölye, diff, onay, adım şeridi | Kısmen (Faz 11–12) |
| **5. Kalite** | Smoke, regresyon, süre SLO | Başlangıç (`programlama_smoke.py`) |

---

## Uygulama planı (sıradaki fazlar)

### Faz 13 — Proje zekâsı v2 ✓ (2026-05-24)

**Amaç:** Model proje içinde kaybolmasın.

- Tüm `projects/<ad>/` için dosya listesi + boyut + dil (py/js/html)
- `proje özeti` komutu: LLM’e 1 sayfalık bağlam özeti
- Sembol çıkarma: fonksiyon/sınıf isimleri (hafif AST, Python + JS)
- `@@find <desen>` — proje içi metin arama

**Başarı:** «Bu projede kaç dosya var, ana giriş nerede?» → 3 sn, doğru yol.

---

### Faz 14 — Otonom görev motoru ✓ (2026-05-24)

**Amaç:** Tek cümle → bitene kadar çalış.

- Komut: `görev: <proje> <ne yapılacak>` veya doğal dil + delege
- İç döngü (max N tur, env: `RUZGAR_CODE_AGENT_MAX_TURNS=8`):
  1. Plan (kısa madde)
  2. İlgili dosyaları oku (`@@read` otomatik)
  3. `@@write` patch(ler)
  4. `pytest` / `npm run build`
  5. Kırmızıysa traceback → tekrar
- Tur sonu rapor: yazılan dosyalar, test, süre
- Durdurma: `görev durdur`

**Başarı:** «benim-api’de health’e versiyon ekle ve test geçir» → insan sadece sonucu okur.

---

### Faz 15 — Terminal v2 (`projects/` kapsamı) ✓ (2026-05-25)

**Amaç:** Web ve Python projelerinde gerçek komutlar.

- Onaylı preset’ler: `npm install`, `npm run build`, `npm test`, `git status`, `git diff`
- Çalışma dizini **yalnızca** `projects/<ad>/`
- Çıktı LLM bağlamına otomatik eklenir
- Tehlikeli komutlar kapalı (rm -rf, push --force)

**Başarı:** React şablonunda `npm run build` yeşil, çıktı sohbette.

---

### Faz 16 — Çok dosya patch + onay UI ✓ (2026-05-25)

**Amaç:** Cursor’daki gibi «şu dosyalar değişecek» ekranı.

- Bekleyen patch: dosya listesi + diff + **Kabul / Red** (dosya bazlı)
- `RUZGAR_FAZ10_AUTO_PATCH=0` varsayılan bu fazda → güvenli onay
- Toplu uygula / geri al (son `.bak`)

**Başarı:** 3 dosyalı değişiklik önce ekranda, tek tık uygula.

---

### Faz 17 — Git köprüsü ✓ (2026-05-25)

**Amaç:** Değişiklikleri kayda al.

- `git durum`, `git diff --stat` (proje kökü)
- Önerilen commit mesajı (LLM, kısa)
- İsteğe bağlı: `git commit` **yalnızca** onaylı + boş `--no-verify` yok

**Başarı:** Patch sonrası «commit öner» → anlamlı mesaj + diff özeti.

---

### Faz 18 — Kalite ve SLO (Faz 12 planı) ✓ (2026-05-25)

- `programlama_smoke.py --live` CI’da
- Senaryolar: scaffold → patch → test → delege
- Süre: basit görev &lt; 2 dk, scaffold &lt; 30 sn
- `RUZGAR_USTA_PLAN` Faz 11 orkestra ile birleşik rapor

---

## Model / donanım (paralel, Ümit abi ortamı)

| Profil | Programlama | Not |
|--------|-------------|-----|
| **Hibrit (önerilen)** | Kod turunda **Gemini** + yerel 8B hızlı | `RUZGAR_BRAIN_PROFILE=auto`, API anahtarı |
| **Yerel güçlü** | 70B / Qwen-Coder | 32GB+ RAM/VRAM |
| **Yalnızca yerel** | 8B + araçlar | Yavaş ama gizlilik |

Kod kalitesi için **Faz 14–16 (araç + döngü)** API’den önce bile büyük fark yaratır.

---

## Bilinçli olarak sonraya

- Android/iOS mağaza uygulaması (Flutter/RN ayrı şablon + toolchain)
- Uzantı botları (arbitraj vb.) — ayrı onay
- Tam IDE (LSP, breakpoint) — Electron dışı kapsam

---

## Sıradaki uygulama oturumu

### Faz 19 — Otonom görev v2 ✓ (2026-05-25)

- `iş:` / `yap:` / doğal cümle → görev
- `RUZGAR_CODE_AGENT_BRAIN=groq,kod` öncelik
- `RUZGAR_CODE_AGENT_BUDGET_SEC=120` · boş tur erken dur

### Faz 20 — Cursor yolu ✓ (2026-05-25)

- Birleşik ajan · `ruzgar-tool` · `RUZGAR_PROG_UNIFIED_AGENT=1`

### Faz 21 — Hafif bağlam ✓ (2026-05-25)

- `programlama_faz21.py` · `RUZGAR_PROG_LIGHT_CONTEXT=1` (varsayılan)
- Programlama turunda: RAG/süper beyin/idrak katmanı atlanır; kompakt proje özeti + araçlar
- `build_motor_context` ve otonom ajan Faz 21 yolunu kullanır

### Faz 22 — Sembol indeks v2 ✓ (2026-05-25)

- `programlama_faz22.py` · AST (Python) + satırlı JS tanımları
- Önbellek: `.ruzgar/symbol_index.json` · `RUZGAR_SYMBOL_INDEX_TTL_SEC=300`
- Komutlar: `sembol health` · `@@symbol health` · `sembol indeks yenile`
- `ruzgar-tool` → `symbol` · hafif bağlamda sembol ipucu

**Üstayol Faz 8–22 tamam** — sırada Faz 23 (5 dk görev + otomatik apply).  
Build: `faz22-v36` · smoke: `python scripts/programlama_smoke.py --ci`

*Ümit & Gökçenur — Rüzgar Programlama Üstayol*
