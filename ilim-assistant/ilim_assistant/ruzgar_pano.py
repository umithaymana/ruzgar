# -*- coding: utf-8 -*-
"""
Sokak / panorama — yalnızca açık erişim.
- Mapillary Graph API: RUZGAR_MAPILLARY_TOKEN varsa
- Token yoksa: Mapillary web uygulaması (açık tarama) gömme URL
Yasal: izinsiz kazıma yok; resmi API veya genel web görünümü.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from ilim_assistant.ruzgar_stac import resolve_place

UA = "RuzgarSehirIkiz/1.0 (local; pano)"
MAPILLARY_GRAPH = "https://graph.mapillary.com"


def _token() -> str:
    return (
        (os.environ.get("RUZGAR_MAPILLARY_TOKEN") or "")
        or (os.environ.get("MAPILLARY_TOKEN") or "")
    ).strip()


def mapillary_embed(lat: float, lon: float, z: int = 17) -> str:
    q = urllib.parse.urlencode({"lat": f"{lat:.6f}", "lng": f"{lon:.6f}", "z": z})
    return f"https://www.mapillary.com/app/?{q}"


def _mapillary_images(lat: float, lon: float, radius_m: int = 80, limit: int = 8) -> dict[str, Any]:
    tok = _token()
    if not tok:
        return {"ok": False, "error": "token_yok", "images": []}
    # close to bbox around point (~radius)
    d = max(0.0003, radius_m / 111320.0)
    west, south, east, north = lon - d, lat - d, lon + d, lat + d
    params = urllib.parse.urlencode(
        {
            "access_token": tok,
            "fields": "id,thumb_256_url,thumb_1024_url,computed_geometry,captured_at,compass_angle,is_pano",
            "bbox": f"{west},{south},{east},{north}",
            "limit": max(1, min(int(limit), 20)),
        }
    )
    url = f"{MAPILLARY_GRAPH}/images?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=40) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"ok": False, "error": f"mapillary HTTP {e.code}", "images": []}
    except Exception as ex:
        return {"ok": False, "error": str(ex), "images": []}

    images = []
    for it in data.get("data") or []:
        geom = it.get("computed_geometry") or {}
        coords = geom.get("coordinates") or [None, None]
        images.append(
            {
                "id": it.get("id"),
                "thumb": it.get("thumb_256_url") or it.get("thumb_1024_url"),
                "thumb_lg": it.get("thumb_1024_url"),
                "lon": coords[0],
                "lat": coords[1],
                "captured_at": it.get("captured_at"),
                "compass": it.get("compass_angle"),
                "is_pano": it.get("is_pano"),
                "viewer": f"https://www.mapillary.com/app/?pKey={it.get('id')}",
            }
        )
    return {"ok": True, "images": images, "provider": "mapillary-graph"}


def pano_nearby(
    *,
    hedef: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    limit: int = 8,
) -> dict[str, Any]:
    place = resolve_place(hedef, lat, lon)
    lat_f, lon_f = float(place["lat"]), float(place["lon"])
    embed = mapillary_embed(lat_f, lon_f)
    api = _mapillary_images(lat_f, lon_f, limit=limit)
    return {
        "ok": True,
        "place": place,
        "provider": "mapillary",
        "token_configured": bool(_token()),
        "embed_url": embed,
        "images": api.get("images") or [],
        "api_ok": bool(api.get("ok")),
        "api_error": api.get("error"),
        "note": (
            "Mapillary Graph API (token) + açık web gömme. "
            "Token: ortam değişkeni RUZGAR_MAPILLARY_TOKEN "
            "(https://www.mapillary.com/dashboard/developers)."
        ),
    }
