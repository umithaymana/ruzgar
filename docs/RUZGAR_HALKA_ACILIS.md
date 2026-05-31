# Rüzgar — halka açılış altyapısı

Ümit abi için özet: **ortak ilim sunucuda**, **kişisel hafıza kullanıcıda** kalır.

## İki katman

| Katman | Ne | Nerede |
|--------|-----|--------|
| **Ortak havuz** | `knowledge/`, RAG indeksi, (isteğe) arşiv alt kümesi | Docker imajı + volume |
| **Kişisel** | `ruzgar_genel_hafiza.json`, kullanıcı profili | `/app/data/users/{kullanici}/` |

Yerel PC'deki Ümit hafızası **halka taşınmaz** — her kullanıcı kendi dosyasını oluşturur.

## Deploy öncesi kontrol

```bash
cd ilim-assistant
python scripts/ruzgar_cloud_deploy_check.py
```

## Railway (önerilen ilk deneme)

1. [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub**
2. Repo: `umithaymana/ruzgar` — **kök dizin** (ilim-assistant değil)
3. Railway `railway.json` okur → `ilim-assistant/Dockerfile` derler
4. **Variables** → `env.halk.example` satırlarını yapıştır
5. **Zorunlu:** `GEMINI_API_KEY` veya `GROQ_API_KEY`
6. **Volume** ekle: mount `/app/data` (kişisel hafıza kalıcı kalsın)
7. Deploy bitince: `https://SIZIN-URL.railway.app/api/health` → `"ok": true`
8. Tarayıcı: `https://SIZIN-URL.railway.app/ui/`

## Fly.io (alternatif)

```bash
fly launch --dockerfile ilim-assistant/Dockerfile --copy-config
fly secrets set GEMINI_API_KEY=...
fly volumes create ruzgar_data --size 1
fly deploy
```

`fly.toml` repo kökünde hazır.

## Yerel Docker denemesi

```bash
docker build -f ilim-assistant/Dockerfile -t ruzgar-halk .
docker run --rm -p 8777:8777 -e PORT=8777 -e GEMINI_API_KEY=... ruzgar-halk
# http://127.0.0.1:8777/ui/
```

## Ortam değişkenleri

- `RUZGAR_PUBLIC_MODE=1` — halk API (Docker varsayılan)
- `RUZGAR_DATA_ROOT` — kişisel veri kökü (`/app/data`)
- `RUZGAR_SHARED_ROOT` — salt okunur külliyat (`/app/ilim-assistant`)
- `X-Ruzgar-User` — istek başlığı; kişisel hafıza yolu
- `RUZGAR_SKIP_RAG_WARMUP=1` — ilk açılış hızlandırma

## Arşiv senkron (git dışı)

```bash
cd ilim-assistant
python scripts/ruzgar_arsiv_sync.py --target-dir D:/bulut-arsiv --dry-run
python scripts/ruzgar_arsiv_sync.py --rsync user@sunucu:/app/arsiv/
```

Sonra env: `RUZGAR_SHARED_ARSIV_ROOT=/app/arsiv`

## Test

```bash
python scripts/ruzgar_public_mode_smoke.py
python scripts/tercume_analyst_smoke.py
python scripts/ruzgar_cloud_deploy_check.py
```

## Kanallar

- **Web:** `/ui/` aynı sunucuda (API otomatik aynı origin)
- **Masaüstü:** Electron + yerel API (`RUZGAR_PUBLIC_MODE=0`)
- **Mobil:** responsive `/ui/` veya ileride mağaza kabuğu
