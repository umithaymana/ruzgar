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

**Kısa cevap:** «Şu programı sıfırdan sen yap» — **evet (Faz 47)** `proje üret:` ile scaffold + pytest Cursor olmadan biter (basit API). Özel özellik (login, CRUD…) için otomatik ajan devreye girer.

## Önerilen kullanım (şimdi — Faz 47)

1. **PROGRAMLAMA MOTORU** sekmesi
2. **Yeni proje (Cursor gerekmez):** `proje üret: fastapi_api benim-api health version pytest`
3. Veya `projects/` altında proje aç / `şablon oluştur: fastapi_api benim-api`
4. Mevcut projede hedef (üç yol):
   - `görev: benim-api health endpointine version ekle ve test geçir`
   - `iş: benim-api …` / `yap: benim-api …`
   - Doğal: `benim-api health endpointine version ekle ve test geçir`
4. Kota için: `RUZGAR_CODE_AGENT_BRAIN=groq,kod` + GROQ_API_KEY
5. Patch gelince **Kabul** → **Uygula** → `commit öner` → `git commit onayla`

Faz 19: max **120 sn** görev süresi; boş/kota turlarda **erken dur** (8 tur boşa gitmez).

## Sıradaki geliştirme (motor sırası)

1. **Toplu canlı deneme** — Programlama modu + görev + Groq (`RUZGAR_PROG_BRAIN_CHAIN=groq,kod`)
2. Ana Motor: tek «iş emri» ile doğru motora yönlendirme + aynı patch/onay modeli
3. Diğer motorlar: ses/okuma/tercüme için ajan döngüsü (programlama Faz 20–28 şablonu)

## CI

- Offline + SLO: `python scripts/programlama_smoke.py --ci`
- Canlı API (GitHub Actions job `smoke-live-api`): `scripts/ci_run_live_smoke.py`
