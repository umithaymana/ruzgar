# -*- coding: utf-8 -*-
"""
Sokak / panorama — yalnızca açık erişim.
- Mapillary Graph API: RUZGAR_MAPILLARY_TOKEN varsa
- Dilim C+: hedefe bağlı SEQUENCE (yol boyunca sıralı kareler)
- Token yoksa: dürüst yedek + web gömme URL (site iframe değil)
Yasal: izinsiz kazıma yok; resmi API veya genel web görünümü.
"""
from __future__ import annotations

import json
import math
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from ilim_assistant.ruzgar_stac import resolve_place

UA = "RuzgarSehirIkiz/1.0 (local; pano)"
MAPILLARY_GRAPH = "https://graph.mapillary.com"
_IMG_FIELDS = (
    "id,thumb_256_url,thumb_1024_url,thumb_2048_url,"
    "computed_geometry,geometry,captured_at,compass_angle,"
    "computed_compass_angle,is_pano,sequence"
)


def _token() -> str:
    return (
        (os.environ.get("RUZGAR_MAPILLARY_TOKEN") or "")
        or (os.environ.get("MAPILLARY_TOKEN") or "")
    ).strip()


def mapillary_embed(lat: float, lon: float, z: int = 17) -> str:
    q = urllib.parse.urlencode({"lat": f"{lat:.6f}", "lng": f"{lon:.6f}", "z": z})
    return f"https://www.mapillary.com/app/?{q}"


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


def _http_json(url: str, timeout: int = 40) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _norm_image(it: dict[str, Any]) -> dict[str, Any] | None:
    geom = it.get("computed_geometry") or it.get("geometry") or {}
    coords = geom.get("coordinates") or [None, None]
    lon, lat = coords[0], coords[1]
    if lat is None or lon is None:
        return None
    compass = it.get("computed_compass_angle")
    if compass is None:
        compass = it.get("compass_angle")
    return {
        "id": it.get("id"),
        "thumb": it.get("thumb_256_url") or it.get("thumb_1024_url"),
        "thumb_lg": it.get("thumb_2048_url")
        or it.get("thumb_1024_url")
        or it.get("thumb_256_url"),
        "lon": lon,
        "lat": lat,
        "captured_at": it.get("captured_at"),
        "compass": compass,
        "is_pano": it.get("is_pano"),
        "sequence": it.get("sequence"),
        "viewer": f"https://www.mapillary.com/app/?pKey={it.get('id')}",
    }


def _mapillary_images_bbox(
    lat: float,
    lon: float,
    *,
    radius_m: int = 80,
    limit: int = 8,
) -> dict[str, Any]:
    tok = _token()
    if not tok:
        return {"ok": False, "error": "token_yok", "images": []}
    # Mapillary: bbox alanı < 0.01 derece²
    d = max(0.0003, min(radius_m / 111320.0, 0.09))
    west, south, east, north = lon - d, lat - d, lon + d, lat + d
    # kare alanı sınırı
    while (east - west) * (north - south) >= 0.0095 and d > 0.0004:
        d *= 0.85
        west, south, east, north = lon - d, lat - d, lon + d, lat + d
    params = urllib.parse.urlencode(
        {
            "access_token": tok,
            "fields": _IMG_FIELDS,
            "bbox": f"{west},{south},{east},{north}",
            "limit": max(1, min(int(limit), 50)),
        }
    )
    url = f"{MAPILLARY_GRAPH}/images?{params}"
    try:
        data = _http_json(url)
    except urllib.error.HTTPError as e:
        return {"ok": False, "error": f"mapillary HTTP {e.code}", "images": []}
    except Exception as ex:
        return {"ok": False, "error": str(ex), "images": []}

    images: list[dict[str, Any]] = []
    for it in data.get("data") or []:
        im = _norm_image(it)
        if im:
            images.append(im)
    return {
        "ok": True,
        "images": images,
        "provider": "mapillary-graph",
        "bbox": [west, south, east, north],
    }


def _mapillary_images_sequence(sequence_id: str, *, limit: int = 80) -> dict[str, Any]:
    tok = _token()
    if not tok or not sequence_id:
        return {"ok": False, "error": "sequence_yok", "images": []}
    params = urllib.parse.urlencode(
        {
            "access_token": tok,
            "fields": _IMG_FIELDS,
            "sequence_ids": sequence_id,
            "limit": max(1, min(int(limit), 100)),
        }
    )
    url = f"{MAPILLARY_GRAPH}/images?{params}"
    try:
        data = _http_json(url)
    except urllib.error.HTTPError as e:
        return {"ok": False, "error": f"mapillary seq HTTP {e.code}", "images": []}
    except Exception as ex:
        return {"ok": False, "error": str(ex), "images": []}

    images: list[dict[str, Any]] = []
    for it in data.get("data") or []:
        im = _norm_image(it)
        if im:
            images.append(im)
    images.sort(key=lambda im: (im.get("captured_at") is None, im.get("captured_at") or 0))
    return {
        "ok": True,
        "images": images,
        "provider": "mapillary-sequence",
        "sequence_id": sequence_id,
    }


def _pick_best_sequence(
    images: list[dict[str, Any]],
    *,
    lat: float,
    lon: float,
) -> str | None:
    """En uzun / hedefe en yakın sequence kimliği."""
    buckets: dict[str, list[dict[str, Any]]] = {}
    for im in images:
        sid = str(im.get("sequence") or "").strip()
        if not sid:
            continue
        buckets.setdefault(sid, []).append(im)
    if not buckets:
        return None

    def score(sid: str) -> tuple[int, float]:
        arr = buckets[sid]
        n = len(arr)
        dist = min(
            (
                _haversine_m(lat, lon, float(im["lat"]), float(im["lon"]))
                for im in arr
                if im.get("lat") is not None and im.get("lon") is not None
            ),
            default=1e9,
        )
        return (n, -dist)

    best = max(buckets.keys(), key=score)
    return best


def _order_path_nearest(
    images: list[dict[str, Any]],
    *,
    lat: float,
    lon: float,
) -> list[dict[str, Any]]:
    """Sequence yoksa: merkeze en yakından greedy yol (zevk için sıra)."""
    left = [
        im
        for im in images
        if im.get("lat") is not None and im.get("lon") is not None
    ]
    if not left:
        return []
    ordered: list[dict[str, Any]] = []
    cur_lat, cur_lon = lat, lon
    while left:
        left.sort(
            key=lambda im: _haversine_m(
                cur_lat, cur_lon, float(im["lat"]), float(im["lon"])
            )
        )
        nxt = left.pop(0)
        ordered.append(nxt)
        cur_lat, cur_lon = float(nxt["lat"]), float(nxt["lon"])
    return ordered


def _downsample(images: list[dict[str, Any]], max_n: int) -> list[dict[str, Any]]:
    max_n = max(3, min(int(max_n), 80))
    if len(images) <= max_n:
        return images
    step = len(images) / float(max_n)
    out: list[dict[str, Any]] = []
    i = 0.0
    while len(out) < max_n and int(i) < len(images):
        out.append(images[int(i)])
        i += step
    if out and images and out[-1].get("id") != images[-1].get("id"):
        out[-1] = images[-1]
    return out


def pano_nearby(
    *,
    hedef: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    limit: int = 8,
    radius_m: int = 120,
    mode: str | None = None,
) -> dict[str, Any]:
    """
    Dilim C+: mode=seri|sequence → hedefe bağlı sıralı yol kareleri.
    Varsayılan (yakın): geriye uyumlu nearest listesi.
    """
    place = resolve_place(hedef, lat, lon)
    lat_f, lon_f = float(place["lat"]), float(place["lon"])
    label = str(place.get("label") or hedef or "konum")
    embed = mapillary_embed(lat_f, lon_f)
    mode_l = str(mode or "").strip().lower()
    seri = mode_l in ("seri", "sequence", "seq", "walk", "yuru", "1", "true")
    tok = bool(_token())

    if seri:
        rad = max(120, min(int(radius_m or 450), 900))
        want = max(12, min(int(limit or 40), 60))
        images: list[dict[str, Any]] = []
        api: dict[str, Any] = {"ok": False}
        how = "nearest_path"
        seq_id: str | None = None

        # 1) istenen yarıçap  2) geniş yedek  3) yakın klasik — boş bırakma
        for try_rad, try_lim in (
            (rad, 50),
            (min(900, max(rad * 2, 700)), 50),
            (min(900, 850), 50),
        ):
            scan = _mapillary_images_bbox(
                lat_f, lon_f, radius_m=int(try_rad), limit=try_lim
            )
            seed = list(scan.get("images") or [])
            if not seed:
                api = scan
                continue
            sid = _pick_best_sequence(seed, lat=lat_f, lon=lon_f)
            cand: list[dict[str, Any]] = []
            if sid:
                full = _mapillary_images_sequence(sid, limit=100)
                if full.get("ok") and full.get("images"):
                    cand = list(full["images"])
                    api = full
                    how = "sequence"
                    seq_id = sid
                else:
                    cand = [
                        im
                        for im in seed
                        if str(im.get("sequence") or "") == sid
                    ]
                    cand.sort(
                        key=lambda im: (
                            im.get("captured_at") is None,
                            im.get("captured_at") or 0,
                        )
                    )
                    api = scan
                    how = "sequence_seed"
                    seq_id = sid
            if not cand:
                cand = _order_path_nearest(seed, lat=lat_f, lon=lon_f)
                api = scan
                how = "nearest_path"
                seq_id = None
            if cand:
                images = cand
                rad = int(try_rad)
                break

        images = _downsample(images, want)
        # merkeze en yakın kareden başla (seri içinde)
        start_i = 0
        if images:
            start_i = min(
                range(len(images)),
                key=lambda i: _haversine_m(
                    lat_f,
                    lon_f,
                    float(images[i]["lat"]),
                    float(images[i]["lon"]),
                ),
            )
            # yürüyüşü start’tan başlat: öne al
            images = images[start_i:] + images[:start_i]

        latest = images[0] if images else None
        if not tok:
            note = (
                f"{label}: sokak serisi için token yok. "
                "Token: RUZGAR_MAPILLARY_TOKEN."
            )
        elif not images:
            note = (
                f"{label}: bu alanda sıralı sokak karesi yok (dürüst yedek). "
                "Yakın yolda tekrar dene."
            )
        else:
            note = (
                f"{label} · seri {len(images)} kare"
                + (f" · yol {seq_id[:8]}…" if seq_id else " · yakın yol")
                + " · İleri/Geri ile yürü · Canlı değil"
            )
        return {
            "ok": True,
            "mode": "seri",
            "place": place,
            "place_label": label,
            "provider": "mapillary",
            "token_configured": tok,
            "embed_url": embed,
            "images": images,
            "latest": latest,
            "sequence_id": seq_id,
            "sequence_how": how,
            "series_count": len(images),
            "series_index": 0,
            "radius_m": rad,
            "api_ok": bool(api.get("ok")),
            "api_error": api.get("error"),
            "note": note,
        }

    # --- klasik yakın (geriye uyumlu) ---
    rad = max(40, min(int(radius_m or 120), 250))
    api = _mapillary_images_bbox(lat_f, lon_f, radius_m=rad, limit=limit)
    images = list(api.get("images") or [])
    try:
        images.sort(
            key=lambda im: str(im.get("captured_at") or ""),
            reverse=True,
        )
    except Exception:
        pass
    latest = images[0] if images else None
    if not tok:
        note = (
            "Sokak karesi API’si kapalı (token yok). "
            "Yürü ile şehirde gezinmeye devam et. "
            "Token: RUZGAR_MAPILLARY_TOKEN."
        )
    elif not images:
        note = (
            "Bu noktada sokak karesi yok (dürüst yedek). "
            "Yakın sokakta Yürü ile tekrar dene — site açılmaz."
        )
    else:
        note = (
            "En son kare sahneyi doldurur. Canlı yayın değil. "
            "Kapat = 3D yürüyüşe dön."
        )
    return {
        "ok": True,
        "mode": "yakin",
        "place": place,
        "place_label": label,
        "provider": "mapillary",
        "token_configured": tok,
        "embed_url": embed,
        "images": images,
        "latest": latest,
        "radius_m": rad,
        "api_ok": bool(api.get("ok")),
        "api_error": api.get("error"),
        "note": note,
    }
