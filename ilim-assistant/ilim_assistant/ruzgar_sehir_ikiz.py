# -*- coding: utf-8 -*-
"""
Rüzgâr Şehir Dijital İkiz — pilot veri + GeoPackage (Faz 3–4).
PostGIS yoksa GDAL GeoPackage yedek; aynı API.
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

DATA = Path(r"D:\ÜMİT\14-) PROGRAMLAR\RuzgarSehirIkiz")
OSM = DATA / "osm"
GPKG = DATA / "cache" / "pilot_sehirler.gpkg"
MANIFEST = OSM / "PILOT_MANIFEST.json"
# ASCII-only PG/PostGIS (Türkçe yol initdb kırıyordu)
PG_BIN = Path(r"D:\RuzgarSehirIkiz\pgsql\bin")
PG_DATA = Path(r"D:\RuzgarSehirIkiz\pgdata")
PG_DB = "sehir_ikiz"
PG_USER = "postgres"
PG_HOST = "127.0.0.1"
PG_PORT = 5432

PILOT = {
    "istanbul": {"label": "İstanbul", "lat": 41.0082, "lon": 28.9784, "zoom": 11},
    "ankara": {"label": "Ankara", "lat": 39.9334, "lon": 32.8597, "zoom": 11},
    "bursa": {"label": "Bursa", "lat": 40.1885, "lon": 29.0610, "zoom": 11},
    "izmir": {"label": "İzmir", "lat": 38.4192, "lon": 27.1287, "zoom": 11},
}


def _ogr2ogr() -> str | None:
    env = (os.environ.get("RUZGAR_OGR2OGR") or "").strip()
    if env and Path(env).is_file():
        return env
    candidates = [
        Path(r"C:\Program Files\QGIS 3.44.15\bin\ogr2ogr.exe"),
        Path(r"C:\Program Files\QGIS 3.40.0\bin\ogr2ogr.exe"),
    ]
    for c in candidates:
        if c.is_file():
            return str(c)
    import shutil

    return shutil.which("ogr2ogr")


def postgis_durum() -> dict[str, Any]:
    """Yerel PostGIS ayakta mı? (şifre env: PGPASSWORD veya RUZGAR_PGPASSWORD)."""
    psql = PG_BIN / "psql.exe"
    if not psql.is_file():
        return {"ok": False, "error": "psql yok", "bin": str(PG_BIN)}
    import subprocess

    env = os.environ.copy()
    if not env.get("PGPASSWORD"):
        env["PGPASSWORD"] = env.get("RUZGAR_PGPASSWORD") or "RuzgarSehir17"
    try:
        r = subprocess.run(
            [
                str(psql),
                "-U",
                PG_USER,
                "-h",
                PG_HOST,
                "-p",
                str(PG_PORT),
                "-d",
                PG_DB,
                "-tAc",
                "SELECT PostGIS_Version();",
            ],
            capture_output=True,
            text=True,
            timeout=15,
            env=env,
        )
        ver = (r.stdout or "").strip()
        return {
            "ok": r.returncode == 0 and bool(ver),
            "postgis": ver or None,
            "db": PG_DB,
            "host": PG_HOST,
            "port": PG_PORT,
            "bin": str(PG_BIN),
            "data": str(PG_DATA),
            "stderr": (r.stderr or "")[-300] if r.returncode else None,
        }
    except Exception as ex:
        return {"ok": False, "error": str(ex), "bin": str(PG_BIN)}


def liste_pilot() -> dict[str, Any]:
    dosyalar: dict[str, Any] = {}
    for k, meta in PILOT.items():
        b = OSM / f"{k}_buildings.geojson"
        r = OSM / f"{k}_roads.geojson"
        dosyalar[k] = {
            **meta,
            "buildings": str(b) if b.is_file() else None,
            "roads": str(r) if r.is_file() else None,
            "buildings_bytes": b.stat().st_size if b.is_file() else 0,
            "roads_bytes": r.stat().st_size if r.is_file() else 0,
        }
    return {
        "ok": True,
        "pilot": list(PILOT.keys()),
        "sehirler": dosyalar,
        "gpkg": str(GPKG) if GPKG.is_file() else None,
        "ogr2ogr": _ogr2ogr(),
        "postgis": postgis_durum(),
    }


def geojson_yolu(sehir: str, kind: str = "buildings") -> Path | None:
    key = (sehir or "").strip().lower()
    # Türkçe karakter sadeleştir
    key = (
        key.replace("ı", "i")
        .replace("İ", "i")
        .replace("ş", "s")
        .replace("ğ", "g")
        .replace("ü", "u")
        .replace("ö", "o")
        .replace("ç", "c")
    )
    aliases = {
        "istanbul": "istanbul",
        "ankara": "ankara",
        "bursa": "bursa",
        "izmir": "izmir",
    }
    k = aliases.get(key)
    if not k:
        return None
    p = OSM / f"{k}_{kind}.geojson"
    return p if p.is_file() else None


def _feat_lon_lat(feat: dict[str, Any]) -> tuple[float, float] | None:
    """GeoJSON feature → kabaca lon/lat (çokgen ilk halka merkezi)."""
    try:
        geom = feat.get("geometry") or {}
        gtype = str(geom.get("type") or "")
        coords = geom.get("coordinates")
        if not coords:
            return None
        if gtype == "Point":
            return float(coords[0]), float(coords[1])
        # Polygon / MultiPolygon — ilk halkadan ortalama
        ring = coords
        if gtype == "Polygon":
            ring = coords[0]
        elif gtype == "MultiPolygon":
            ring = coords[0][0]
        if not ring:
            return None
        sx = sy = 0.0
        n = 0
        for pt in ring:
            if not pt or len(pt) < 2:
                continue
            sx += float(pt[0])
            sy += float(pt[1])
            n += 1
            if n >= 24:
                break
        if n <= 0:
            return None
        return sx / n, sy / n
    except Exception:
        return None


def geojson_oku(
    sehir: str,
    kind: str = "buildings",
    limit: int = 0,
    *,
    lat: float | None = None,
    lon: float | None = None,
    radius_deg: float = 0.045,
) -> dict[str, Any] | None:
    """Bina/yol GeoJSON. lat/lon verilirse kameraya yakın dilim (Dilim B)."""
    p = geojson_yolu(sehir, kind)
    if not p:
        return None
    data = json.loads(p.read_text(encoding="utf-8"))
    feats = list(data.get("features") or [])
    total = len(feats)
    lim = int(limit or 0)
    near = lat is not None and lon is not None and isfinite_lat_lon(lat, lon)
    if near:
        md = max(0.008, min(0.12, float(radius_deg or 0.045)))
        md2 = md * md
        scored: list[tuple[float, dict[str, Any]]] = []
        for f in feats:
            ll = _feat_lon_lat(f)
            if not ll:
                continue
            flo, fla = ll
            d2 = (fla - float(lat)) ** 2 + (flo - float(lon)) ** 2
            if d2 <= md2:
                scored.append((d2, f))
        scored.sort(key=lambda x: x[0])
        take = lim if lim > 0 else 8000
        feats = [f for _, f in scored[:take]]
        data = {
            "type": "FeatureCollection",
            "features": feats,
            "truncated": total > len(feats),
            "total": total,
            "near": True,
            "lat": float(lat),
            "lon": float(lon),
            "radius_deg": md,
        }
    elif lim > 0 and total > lim:
        data = {
            "type": "FeatureCollection",
            "features": feats[:lim],
            "truncated": True,
            "total": total,
        }
    return data


def isfinite_lat_lon(lat: float, lon: float) -> bool:
    try:
        return -90.0 <= float(lat) <= 90.0 and -180.0 <= float(lon) <= 180.0
    except Exception:
        return False


def gpkg_olustur() -> dict[str, Any]:
    """Tüm mevcut GeoJSON'ları tek GeoPackage'e yaz (GDAL)."""
    ogr = _ogr2ogr()
    if not ogr:
        return {"ok": False, "error": "ogr2ogr yok — QGIS kurulu mu?"}
    GPKG.parent.mkdir(parents=True, exist_ok=True)
    if GPKG.is_file():
        GPKG.unlink()
    layers = []
    for k in PILOT:
        for kind in ("buildings", "roads"):
            src = OSM / f"{k}_{kind}.geojson"
            if not src.is_file() or src.stat().st_size < 100:
                continue
            layer = f"{k}_{kind}"
            # ilk katman -t_srs EPSG:4326, sonrakiler -append
            cmd = [
                ogr,
                "-f",
                "GPKG",
                "-t_srs",
                "EPSG:4326",
                str(GPKG),
                str(src),
                "-nln",
                layer,
            ]
            if layers:
                cmd.insert(1, "-append")
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
                if r.returncode != 0:
                    layers.append({"layer": layer, "ok": False, "err": (r.stderr or "")[-400]})
                else:
                    layers.append({"layer": layer, "ok": True})
            except Exception as ex:
                layers.append({"layer": layer, "ok": False, "err": str(ex)})
    return {
        "ok": any(x.get("ok") for x in layers),
        "gpkg": str(GPKG),
        "layers": layers,
        "ogr2ogr": ogr,
    }
