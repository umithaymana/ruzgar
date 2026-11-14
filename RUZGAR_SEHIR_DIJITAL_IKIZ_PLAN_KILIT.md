# Rüzgâr — Şehir Dijital İkiz Planı (AKTİF KİLİT)

**Durum:** NEREDEYSE BİTTİ — Faz 10 (UE5) bilinçli ertelendi; PostGIS yönetici kurulumu açık.  
**Başlangıç:** 2026-11-14  
**Kural:** Kullanıcı başka konu açarsa önce bu dosyayı hatırlat; plan bitmeden sapma.

## Paralel hat
Her yeşil dilimde **PC + mobil** birlikte.

## Pilot şehirler (onaylı)
İstanbul · Ankara · Bursa · İzmir

## Fazlar

| Faz | İş | Durum |
|-----|-----|--------|
| 0 | Analiz raporu | ✅ |
| 0b | Harita/ses güvenli liman | ✅ `261b3f598` |
| 1 | Cesium yerel + 3D ana motor; F4map yedek | ✅ `35bc1f767` |
| 2 | Program kayıt defteri | ✅ `7d0f6dd62` |
| 3 | QGIS/GDAL + pilot OSM + GeoPackage | ✅ (PostGIS: yönetici kurulumu başarısız → GPKG yedek) |
| 4 | Bina ayakizi Cesium extrusion | ✅ |
| 5 | Blender + glTF örnek | ✅ |
| 6 | IfcOpenShell örnek IFC | ✅ |
| 7 | Geçmiş/şimdi/gelecek (era) | ✅ |
| 8 | Trafik/ajan iskeleti | ✅ |
| 9 | MediaMTX + kamera pin API | ✅ |
| 10 | UE5 köprüsü | ⏸ bilinçli erteleme (50–150 GB; ayrı oturum) |

## Onay
2026-11-14: Kullanıcı tüm kurulum gerektiren fazları onayladı.

## Açık uçlar (plan içi)
1. **PostgreSQL/PostGIS** — winget yönetici istedi, düştü; GeoPackage aktif yedek. İstersen yöneticiyle yeniden kur.
2. **UE5** — boyut nedeniyle ertelendi; araç kaydında `unreal` satırı bekliyor.
3. **ONVIF gerçek kamera** — yalnızca yazılı izinli pin; demo HLS hazır.

## Veri kökü
`D:\ÜMİT\14-) PROGRAMLAR\RuzgarSehirIkiz\` (osm / cache / models / tools)

## Son güncelleme
- 2026-11-14: Faz 3–9 yeşil; 4 şehir buildings+roads; GPKG 8 katman; smoke PASS.
