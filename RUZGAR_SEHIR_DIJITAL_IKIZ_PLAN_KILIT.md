# Rüzgâr — Şehir Dijital İkiz Planı

**Durum:** PLAN KAPANDI (Faz 0–10) — 2026-11-14  
**Kural:** Yeni büyük işe geçmeden önce bu dosyaya bak; açık uç yoksa serbest.

## Pilot şehirler
İstanbul · Ankara · Bursa · İzmir

## Fazlar

| Faz | Durum |
|-----|--------|
| 0–2 | ✅ |
| 3 | ✅ QGIS/GDAL + **PostGIS 3.6** (`D:\RuzgarSehirIkiz`) + 4 şehir tabloları |
| 4–9 | ✅ Cesium bina, Blender/IFC, era, ajan, MediaMTX |
| 10 | ✅ Epic Games Launcher kurulu (UE5 editör Epic’ten indirilir — hesap/login gerekir) |
| STAC | ✅ Element84 Sentinel-2 (masaüstü yazılım yok) — `/api/sehir-ikiz/stac` + harita S2 |
| Mapillary | ✅ Açık API/web gömme — `/api/sehir-ikiz/pano` (+ isteğe bağlı `RUZGAR_MAPILLARY_TOKEN`) |

## PostGIS
- Bin: `D:\RuzgarSehirIkiz\pgsql\bin`
- Data: `D:\RuzgarSehirIkiz\pgdata`
- DB: `sehir_ikiz` · user: `postgres` · şifre env: `RUZGAR_PGPASSWORD` (kurulum: `RuzgarSehir17`)
- Başlat: `pg_ctl -D D:\RuzgarSehirIkiz\pgdata -l D:\RuzgarSehirIkiz\logs\pg.log start`
- Tablolar: `istanbul_*` `ankara_*` `bursa_*` `izmir_*` (buildings+roads)

## UE5 notu
Launcher: `C:\Program Files\Epic Games\Launcher\...\EpicGamesLauncher.exe`  
Asıl Unreal Engine 5 editörü Epic hesabıyla Library’den kurulur (büyük indirme).

## Son commit hattı
`94cffc469` + bu kapanış commit’i
