# Rüzgâr Sistem Analizi — 2026-11-14

**Kural uygulandı:** Analiz tamamlanmadan kurulum başlatılmadı.  
**İlke:** Aynı işi yapan ikinci yazılım yok.

### Bu turda kurulan (yalnızca çakışmayan eksikler)
Rüzgâr venv: `shapely` `pyproj` `pyogrio` `geopandas` `rasterio` `psycopg` `ifcopenshell` — smoke OK (PostGIS `bursa_buildings` 24278).  
**Kurulmayan:** GeoServer, MapServer, DEM indirme, Sentinel masaüstü, Bonsai, UE5 editör.

---

## 1) Kurulu ve kullanılabilir bileşenler

| Bileşen | Durum | Yol / not |
|---------|--------|-----------|
| CesiumJS 1.114 | Kurulu | `ruzgar-desktop/vendor/cesium` (yerel) |
| Leaflet | Kurulu | `vendor/leaflet` |
| QGIS LTR 3.44.15 | Kurulu | `C:\Program Files\QGIS 3.44.15` |
| GDAL (CLI) | Kurulu | QGIS `ogr2ogr` / `gdalinfo` |
| Blender 4.5 LTS | Kurulu | `Blender Foundation\Blender 4.5` |
| PostgreSQL 17.5 | Kurulu + çalışıyor | `D:\RuzgarSehirIkiz\pgsql` · port **5432** |
| PostGIS 3.6.2 | Kurulu + aktif | DB `sehir_ikiz` · 4 şehir tabloları |
| OpenStreetMap | Kullanılıyor | 2D karo + yerel GeoJSON/PostGIS |
| Esri World Imagery | Kullanılıyor | Uydu (ağ) |
| NASA GIBS MODIS | Kullanılıyor | 4D zamanlı uydu |
| F4map | Yedek | 3D iframe (Cesium ana) |
| IfcOpenShell | Kurulu (sistem Py) | v0.9 — **venv’de YOK** |
| MediaMTX | Kurulu | `RuzgarSehirIkiz\tools\mediamtx.exe` (servis kapalı) |
| FFmpeg / FFprobe | Kurulu | winget |
| Ollama | Kurulu + çalışıyor | port **11434** |
| Electron 33 | Kurulu | `ruzgar-desktop` |
| FastAPI API | Çalışıyor | port **8779** |
| Epic Games Launcher | Kurulu | UE5 editörü henüz yok |
| Rüzgâr araç kaydı | 14/14 | `RUZGAR_ARAC_KAYIT.json` |
| NetworkX, NumPy, Pandas, SciPy, sklearn, Torch, ST | Kurulu (venv) | coğrafi AI omurgası kısmen |

---

## 2) Eksik bileşenler

| Bileşen | Durum | “Başka bileşen sağlıyor mu?” |
|---------|--------|------------------------------|
| Gerçek DEM / arazi (SRTM, Copernicus) | Eksik | **Hayır** — Cesium `EllipsoidTerrain` (düz elipsoid) |
| Sentinel-2 / Landsat STAC borusu | Eksik | **Kısmen** — Esri+GIBS görüntü verir; analiz-grade band yok |
| GeoServer / MapServer | Yok | **Evet — kurma** · FastAPI+PostGIS+Cesium yayınlıyor |
| GeoPandas / Rasterio / PyProj / Fiona | Eksik (venv) | **Hayır** — CLI GDAL var; Python analiz yok |
| Shapely / IfcOpenShell | Sistem Py’de var, venv’de yok | Rüzgâr venv’e hizala |
| psycopg | Eksik | **Hayır** — PostGIS’e Python bağ yok |
| Bonsai (Blender BIM) | Yok | **Kısmen** — IfcOpenShell+Blender glTF yeterli (opsiyonel) |
| UnrealEditor 5 | Yok | Launcher var; editör Epic hesabı ile |
| ONVIF istemci | Yok | MediaMTX HLS/WebRTC iskeleti var (ileri) |
| Mapillary / KartaView entegrasyonu | Yok | Yasal API entegrasyonu (yazılım paketi değil) |
| WebRTC/HLS ayrı SDK | Yok | **Evet** — MediaMTX + tarayıcı |

---

## 3) Önerilen kurulumlar (gerekçeli)

### A) Python coğrafi analiz yığını → **venv’e kur (öneri + bu turda uygulanır)**
- **Paketler:** `shapely` `pyproj` `pyogrio` `geopandas` `rasterio` `psycopg[binary]` (+ gerekirse `ifcopenshell` venv’e)
- **Kazanım:** “Paris’i aç” sonrası buffer/intersect, yol ağı, raster maske, PostGIS sorgu
- **Disk:** ~150–400 MB  
- **Performans:** Sadece analiz anında CPU/RAM; sahne motoruna yük yok  
- **Çakışma:** Yok (QGIS CLI ile tamamlayıcı)

### B) DEM / yükseklik → **yeni program değil, veri + Cesium sağlayıcı**
- **Seçenek 1:** Ücretsiz Cesium Ion token → `CesiumTerrainProvider` / World Terrain  
- **Seçenek 2:** Copernicus DEM / SRTM yerel karo (D:) + quantized-mesh veya heightmap  
- **Kazanım:** Dağ/vadi gerçek 3D  
- **Disk:** Ülke DEM 1–20 GB; Ion ~0  
- **Çakışma:** EllipsoidTerrain yerine geçer (bilinçli)

### C) Sentinel/Landsat → **STAC/Copernicus API + rasterio (sonra)**
- Yeni masaüstü yazılımı **kurma**  
- Gerekçe: Uydu gösterme zaten Esri/GIBS’te; analiz için API yeterli

### D) Mapillary/KartaView → **sonra, yalnızca açık API**
- Yeni program yok; `harita-viewer` katmanı

### E) Bonsai / UE5 editör / ONVIF → **ileri, isteğe bağlı**
- Bonsai: IfcOpenShell yeterliyse kurma  
- UE5: Epic Library (50–150 GB) — bilinçli  
- ONVIF: izinli kamera gelince

---

## 4) Gereksiz kurulumlar (YAPMA)

| Aday | Neden gereksiz |
|------|----------------|
| GeoServer | FastAPI `/api/sehir-ikiz/*` + Cesium/Leaflet yayınlıyor |
| MapServer | Aynı |
| İkinci PostgreSQL | `D:\RuzgarSehirIkiz` zaten ayakta |
| Docker (zorunlu) | Yerel PG/MediaMTX yeterli |
| İkinci Cesium CDN | Yerel vendor var |
| Ayrı WebRTC SDK | MediaMTX + tarayıcı |

---

## 5) Çakışan / dikkat

| Konu | Not |
|------|-----|
| İki Python | Sistem Py312 ≠ `venvs\ruzgar` — paketler dağınık; Rüzgâr **venv** kullanmalı |
| İki psql | PATH’te QGIS `psql`; PostGIS `D:\RuzgarSehirIkiz\pgsql\bin\psql` — araç kaydı hedefi net |
| F4map vs Cesium | Cesium ana; F4 yedek — bilinçli |

---

## 6) Disk kullanımı (özet)

| Konum | ~Boyut |
|-------|--------|
| `D:\RuzgarSehirIkiz` (PG+PostGIS) | ~2.1 GB |
| `…\RuzgarSehirIkiz` (OSM/models/tools) | ~2.3 GB |
| Cesium+Leaflet vendor | ~19 MB |
| C: boş / D: boş | ~73 GB / ~3239 GB |

---

## 7) Performans etkisi (mevcut)

| Servis | Port | Etki |
|--------|------|------|
| Rüzgâr API | 8779 | Ana |
| PostgreSQL | 5432 | Orta (sorguda) |
| Ollama | 11434 | Yüksek (VRAM/RAM) — harita oturumunda dikkat |
| MediaMTX | kapalı | 0 |

16 GB RAM + RTX 4060: Cesium + hafif LLM uygun; DEM+büyük Sentinel + büyük LLM aynı anda riskli.

---

## 8) Rüzgâr’ın mevcut yetenekleri

- Ülke/şehir açma (süper-el + geocode; pilot 4 şehir bina/yol kalın)
- 2D OSM, 3D Cesium, uydu Esri, 4D GIBS, tur Cesium
- Bina ayakizi ekstrüzyonu (yerel OSM)
- PostGIS’te 4 şehir vektör
- Sesli/yazılı sahne komutları
- glTF/IFC örnek, kamera pin iskeleti, MediaMTX hazır

**Zayıf:** Gerçek arazi DEM, dünya çapı bina 3D Tiles, Sentinel analizi, sokak panoraması, Python↔PostGIS köprüsü.

---

## 9) Önerilen kurulumlar sonrası yeni yetenekler

- Coğrafi buffer/intersect/yol ağı analizi (GeoPandas…)
- PostGIS’ten doğrudan sorgu (psycopg)
- DEM ile gerçek dağ/vadi (veri aşaması)
- İleride Sentinel ile yangın/arazi kullanımı (API)

---

## 10) Nihai mimari (özet)

```
Ses/yazı → süper-el → sahne organı harita
                         ↓
              harita-viewer (Leaflet 2D / Cesium 3D)
                         ↓
         FastAPI :8779  ←→  PostGIS sehir_ikiz
                         ↓
         OSM/GeoJSON · Esri/GIBS · (ileride DEM/STAC)
                         ↓
         MediaMTX (izinli kamera) · Blender/IFC (model)
```

**Yayın katmanı = FastAPI + Cesium. GeoServer yok.**
