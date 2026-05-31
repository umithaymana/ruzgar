# Rüzgar — halka açılış altyapısı

Ümit abi için özet: **ortak ilim sunucuda**, **kişisel hafıza kullanıcıda** kalır.

## İki katman

| Katman | Ne | Nerede |
|--------|-----|--------|
| **Ortak havuz** | `knowledge/`, RAG indeksi, (isteğe) arşiv alt kümesi | Docker imajı + volume |
| **Kişisel** | `ruzgar_genel_hafiza.json`, kullanıcı profili | `/app/data/users/{kullanici}/` |

Yerel PC'deki Ümit hafızası **halka taşınmaz** — her kullanıcı kendi dosyasını oluşturur.

## Hızlı deploy

1. `ilim-assistant/env.halk.example` → platform env (Railway / Fly / Render)
2. `docker build -f ilim-assistant/Dockerfile ilim-assistant`
3. Volume: `/app/data` (kalıcı kişisel kayıtlar)
4. İsteğe: arşiv için `RUZGAR_SHARED_ARSIV_ROOT=/app/arsiv` + sync script

## Ortam değişkenleri

- `RUZGAR_PUBLIC_MODE=1` — halk API (varsayılan Docker imajında açık)
- `RUZGAR_DATA_ROOT` — kişisel veri kökü
- `RUZGAR_SHARED_ROOT` — salt okunur külliyat (`/app`)
- `X-Ruzgar-User` — istek başlığı; kişisel hafıza yolu

## Arşiv senkron (git dışı)

```bash
cd ilim-assistant
python scripts/ruzgar_arsiv_sync.py --target-dir D:/bulut-arsiv --dry-run
python scripts/ruzgar_arsiv_sync.py --rsync user@sunucu:/app/arsiv/
```

## Test

```bash
python scripts/ruzgar_public_mode_smoke.py
python scripts/tercume_analyst_smoke.py
```

## Kanallar (mevcut altyapı)

- Tarayıcı: `/ui/` + bulut API URL
- Masaüstü: Electron + yerel API (`RUZGAR_PUBLIC_MODE=0`)
- Mobil / mağaza: aynı API + responsive UI (ayrı paketleme sprinti)
