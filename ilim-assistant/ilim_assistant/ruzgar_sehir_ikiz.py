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


def geojson_oku(sehir: str, kind: str = "buildings", limit: int = 0) -> dict[str, Any] | None:
    p = geojson_yolu(sehir, kind)
    if not p:
        return None
    data = json.loads(p.read_text(encoding="utf-8"))
    feats = data.get("features") or []
    if limit and limit > 0 and len(feats) > limit:
        data = {"type": "FeatureCollection", "features": feats[:limit], "truncated": True, "total": len(feats)}
    return data


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
