# Rüzgar — Motor vizyonu (Ümit abi)

## Hedef (Cursor gibi)

Sohbete yaz → **işi Rüzgar yapsın**: plan, dosya okuma/yazma, test, düzeltme, (projede) git.

- **Aktif motor önce:** Hangi sekmede/moddaysanız o motorun talimatları ve araçları yüklenir; diğer motorlar karışmaz.
- **Sırayla genişleme:** Programlama motoru en olgun; diğer motorlara aynı «ajan» modeli kademeli taşınır.

## Bugün ne var?

| Alan | Durum | Not |
|------|--------|-----|
| Programlama — tek tur patch | Var | `@@write`, onay şeridi (Faz 16) |
| Programlama — çok tur görev | Var | `görev: proje hedef` (Faz 14), LLM kotasına bağlı |
| Programlama — şablon / scaffold | Var | CLI, FastAPI, React, site |
| Programlama — test / terminal / git | Var | pytest, npm, `git durum`, `commit öner` |
| Ana Motor → programlama delege | Var | Kod isteği programlama moduna yönlenir |
| Genel sohbet (Gemini/Groq) | Var | Ümit cevap emri; kod işi için yeterli değil |
| Tüm motorlarda tam otonom ürün | **Hayır** | Video/okuma/tercüme ayrı iş akışları |

**Kısa cevap:** «Şu programı sıfırdan sen yap» — **kısmen evet** (programlama modu + `görev:` + şablonlar). **Tam Cursor seviyesi** (uzun oturum, her motor, sıfır müdahale) — **henüz hayır**; Faz 14 kotası ve çok dosyalı uzun işler sınırlı.

## Önerilen kullanım (şimdi — Faz 19)

1. **PROGRAMLAMA MOTORU** sekmesi
2. `projects/` altında proje aç veya `şablon: fastapi_api benim-api`
3. Hedef (üç yol):
   - `görev: benim-api health endpointine version ekle ve test geçir`
   - `iş: benim-api …` / `yap: benim-api …`
   - Doğal: `benim-api health endpointine version ekle ve test geçir`
4. Kota için: `RUZGAR_CODE_AGENT_BRAIN=groq,kod` + GROQ_API_KEY
5. Patch gelince **Kabul** → **Uygula** → `commit öner` → `git commit onayla`

Faz 19: max **120 sn** görev süresi; boş/kota turlarda **erken dur** (8 tur boşa gitmez).

## Sıradaki geliştirme (motor sırası)

1. Programlama: görev motoru sağlamlaştırma (kotada Groq, erken dur, 2 dk SLO)
2. Ana Motor: tek «iş emri» ile doğru motora yönlendirme + aynı patch/onay modeli
3. Diğer motorlar: ses/okuma/tercüme için «motor önce yükle» zaten var; ajan döngüsü kopyalanır

## CI

- Offline + SLO: `python scripts/programlama_smoke.py --ci`
- Canlı API (GitHub Actions job `smoke-live-api`): `scripts/ci_run_live_smoke.py`
