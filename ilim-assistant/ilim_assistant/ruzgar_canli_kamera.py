# -*- coding: utf-8 -*-
"""
Açık lisanslı canlı kamera katalog — scrape yok.
URL'ler env: RUZGAR_WEBCAM_OPEN_JSON_URLS (virgülle)
Beklenen öğe alanları (esnek): lat, lon, id/ad, stream/hls/url, license
"""
from __future__ import annotations

import gzip
import json
import os
import time
import urllib.request
from typing import Any

from ilim_assistant.ruzgar_kamera_rig import CANLI_KAYNAK_ENVANTER

# Digitraffic CDN bazı UA’lara 406 verir; curl benzeri güvenli
UA = "Ruzgar/1.0"
FINTRAFFIC_STATIONS = "https://tie.digitraffic.fi/api/weathercam/v1/stations"
FINTRAFFIC_IMG = "https://weathercam.digitraffic.fi/{preset}.jpg"
_FINTRAFFIC_CACHE: dict[str, Any] = {"t": 0.0, "pack": None}
_FINTRAFFIC_TTL_SEC = 90.0


def _env_urls() -> list[str]:
    raw = (os.environ.get("RUZGAR_WEBCAM_OPEN_JSON_URLS") or "").strip()
    if not raw:
        return []
    return [u.strip() for u in raw.split(",") if u.strip().startswith("http")]


def _fintraffic_enabled() -> bool:
    v = (os.environ.get("RUZGAR_WEBCAM_FINTRAFFIC") or "1").strip().lower()
    return v not in ("0", "false", "off", "no")


def _http_json(url: str, *, headers: dict[str, str] | None = None) -> Any:
    h = {
        "User-Agent": UA,
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
    }
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=25) as resp:
        raw = resp.read()
        enc = (resp.headers.get("Content-Encoding") or "").lower()
        if enc == "gzip" or raw[:2] == b"\x1f\x8b":
            raw = gzip.decompress(raw)
        return json.loads(raw.decode("utf-8"))


def fetch_fintraffic_cameras(*, limit: int = 80) -> dict[str, Any]:
    """Fintraffic Digitraffic weathercam — açık API, hesap yok (CC BY 4.0)."""
    if not _fintraffic_enabled():
        return {
            "ok": True,
            "kameralar": [],
            "count": 0,
            "source": "fintraffic",
            "note": "RUZGAR_WEBCAM_FINTRAFFIC=0",
        }
    now = time.monotonic()
    cached = _FINTRAFFIC_CACHE.get("pack")
    if (
        cached
        and isinstance(cached, dict)
        and cached.get("ok")
        and now - float(_FINTRAFFIC_CACHE.get("t") or 0) < _FINTRAFFIC_TTL_SEC
    ):
        cams = list(cached.get("kameralar") or [])[:limit]
        out = dict(cached)
        out["kameralar"] = cams
        out["count"] = len(cams)
        out["cached"] = True
        return out
    try:
        data = _http_json(
            FINTRAFFIC_STATIONS,
            headers={"Digitraffic-User": "Ruzgar/CanliKamera"},
        )
    except Exception as ex:
        return {
            "ok": False,
            "kameralar": [],
            "count": 0,
            "source": "fintraffic",
            "error": str(ex),
        }
    features = []
    if isinstance(data, dict):
        features = data.get("features") or data.get("data") or []
    elif isinstance(data, list):
        features = data
    cams: list[dict[str, Any]] = []
    for feat in features:
        if not isinstance(feat, dict):
            continue
        props = feat.get("properties") if feat.get("type") == "Feature" else feat
        geom = feat.get("geometry") if feat.get("type") == "Feature" else None
        if not isinstance(props, dict):
            continue
        lat = lon = None
        if isinstance(geom, dict):
            coords = geom.get("coordinates") or []
            if len(coords) >= 2:
                lon, lat = coords[0], coords[1]
        if lat is None:
            lat = props.get("lat") or (props.get("location") or {}).get("latitude")
        if lon is None:
            lon = props.get("lon") or (props.get("location") or {}).get("longitude")
        try:
            lat_f = float(lat)
            lon_f = float(lon)
        except (TypeError, ValueError):
            continue
        presets = props.get("presets") or []
        preset_id = ""
        if isinstance(presets, list) and presets:
            p0 = presets[0]
            if isinstance(p0, dict):
                preset_id = str(p0.get("id") or p0.get("presetId") or "")
            else:
                preset_id = str(p0)
        if not preset_id:
            preset_id = str(props.get("id") or props.get("cameraId") or "")
        if not preset_id:
            continue
        img = FINTRAFFIC_IMG.format(preset=preset_id)
        raw_name = props.get("name") or props.get("names") or preset_id
        if isinstance(raw_name, dict):
            raw_name = (
                raw_name.get("fi")
                or raw_name.get("en")
                or raw_name.get("sv")
                or next(iter(raw_name.values()), preset_id)
            )
        cams.append(
            {
                "id": f"fintraffic-{preset_id}",
                "ad": str(raw_name or preset_id),
                "lat": lat_f,
                "lon": lon_f,
                "hls": "",
                "image": img,
                "license": "CC BY 4.0",
                "source": "fintraffic",
                "attribution": "Fintraffic Digitraffic",
                "tur": "trafik/hava",
                "canli": True,
                "media": "foto",
            }
        )
        # Önbellek için bol tut; dönüşte limit kesilir
        if len(cams) >= max(limit, 400):
            break
    full_cams = cams
    pack = {
        "ok": True,
        "kameralar": full_cams[:limit],
        "count": len(full_cams[:limit]),
        "source": "fintraffic",
        "note": "Fintraffic Digitraffic · CC BY 4.0",
        "cached": False,
    }
    _FINTRAFFIC_CACHE["t"] = now
    _FINTRAFFIC_CACHE["pack"] = {
        "ok": True,
        "kameralar": full_cams,
        "count": len(full_cams),
        "source": "fintraffic",
        "note": pack["note"],
    }
    return pack


def _norm_cam(item: dict[str, Any], source: str) -> dict[str, Any] | None:
    lat = item.get("lat")
    lon = item.get("lon")
    if lat is None:
        lat = (item.get("location") or {}).get("latitude")
    if lon is None:
        lon = (item.get("location") or {}).get("longitude")
    if lat is None and isinstance(item.get("geometry"), dict):
        coords = (item.get("geometry") or {}).get("coordinates") or []
        if len(coords) >= 2:
            lon, lat = coords[0], coords[1]
    try:
        lat_f = float(lat)
        lon_f = float(lon)
    except (TypeError, ValueError):
        return None
    stream = (
        item.get("hls")
        or item.get("stream")
        or item.get("url")
        or item.get("href")
        or item.get("viewUrl")
        or ""
    )
    return {
        "id": str(item.get("id") or item.get("code") or f"{source}-{lat_f:.4f}-{lon_f:.4f}"),
        "ad": str(item.get("ad") or item.get("title") or item.get("name") or "kamera"),
        "lat": lat_f,
        "lon": lon_f,
        "hls": stream if str(stream).startswith("http") else "",
        "license": str(item.get("license") or item.get("licence") or "open"),
        "source": source,
        "attribution": str(item.get("attribution") or source),
    }


def fetch_open_json_cameras(*, limit: int = 80) -> dict[str, Any]:
    urls = _env_urls()
    cams: list[dict[str, Any]] = []
    errors: list[str] = []
    # Yerleşik açık API (hesap yok)
    ft = fetch_fintraffic_cameras(limit=limit)
    if ft.get("error"):
        errors.append(f"fintraffic: {ft['error']}")
    cams.extend(list(ft.get("kameralar") or []))
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as ex:
            errors.append(f"{url}: {ex}")
            continue
        rows = data
        if isinstance(data, dict):
            rows = (
                data.get("kameralar")
                or data.get("cameras")
                or data.get("features")
                or data.get("data")
                or data.get("results")
                or []
            )
        if not isinstance(rows, list):
            continue
        for it in rows:
            if not isinstance(it, dict):
                continue
            # GeoJSON Feature
            if it.get("type") == "Feature":
                props = dict(it.get("properties") or {})
                geom = it.get("geometry") or {}
                props["geometry"] = geom
                it = props
            cam = _norm_cam(it, source=url.split("/")[2] if "://" in url else "open")
            if cam:
                cams.append(cam)
            if len(cams) >= limit:
                break
        if len(cams) >= limit:
            break
    built_in = 1 if _fintraffic_enabled() else 0
    note_parts = []
    if built_in:
        note_parts.append("Fintraffic Digitraffic bağlı (CC BY 4.0).")
    if urls:
        note_parts.append(f"Env JSON: {len(urls)} URL.")
    else:
        note_parts.append("İsteğe bağlı: RUZGAR_WEBCAM_OPEN_JSON_URLS.")
    note_parts.append("Scrape yok. Attribution zorunlu.")
    return {
        "ok": True,
        "kameralar": cams[:limit],
        "count": len(cams[:limit]),
        "sources_configured": len(urls) + built_in,
        "errors": errors,
        "note": " ".join(note_parts),
        "envanter": CANLI_KAYNAK_ENVANTER,
    }


def nearby_open_cameras(
    *,
    lat: float,
    lon: float,
    radius_km: float = 80.0,
    limit: int = 40,
) -> dict[str, Any]:
    import math

    pack = fetch_open_json_cameras(limit=500)
    cams = list(pack.get("kameralar") or [])

    def dist(a: float, b: float, c: float, d: float) -> float:
        r = 6371.0
        p1, p2 = math.radians(a), math.radians(c)
        dp = math.radians(c - a)
        dl = math.radians(d - b)
        x = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
        return 2 * r * math.asin(min(1.0, math.sqrt(x)))

    scored = []
    for cam in cams:
        d = dist(lat, lon, float(cam["lat"]), float(cam["lon"]))
        if d <= max(1.0, radius_km):
            scored.append((d, cam))
    scored.sort(key=lambda t: t[0])
    out = []
    for d, cam in scored[:limit]:
        c = dict(cam)
        c["distance_km"] = round(d, 2)
        out.append(c)
    return {
        "ok": True,
        "lat": lat,
        "lon": lon,
        "radius_km": radius_km,
        "kameralar": out,
        "count": len(out),
        "sources_configured": pack.get("sources_configured"),
        "note": pack.get("note"),
        "envanter": CANLI_KAYNAK_ENVANTER,
    }
