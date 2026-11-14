# -*- coding: utf-8 -*-
"""
Sentinel-2 STAC arama (Element84 earth-search) — masaüstü yazılım yok.
Açık/ücretsiz STAC; Rüzgâr harita organına önizleme + meta verir.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from ilim_assistant.sahne_harita_geo import geocode_local, geocode_nominatim

STAC_SEARCH = "https://earth-search.aws.element84.com/v1/search"
COLLECTION = "sentinel-2-l2a"
UA = "RuzgarSehirIkiz/1.0 (local; STAC)"


def _bbox_from_center(lat: float, lon: float, span: float = 0.12) -> list[float]:
    return [
        round(lon - span / 2, 5),
        round(lat - span / 2, 5),
        round(lon + span / 2, 5),
        round(lat + span / 2, 5),
    ]


def resolve_place(hedef: str | None, lat: float | None, lon: float | None) -> dict[str, Any]:
    if lat is not None and lon is not None:
        return {"lat": float(lat), "lon": float(lon), "label": hedef or "konum", "source": "coords"}
    if hedef:
        g = geocode_local(hedef) or geocode_nominatim(hedef)
        if g:
            return {
                "lat": float(g["lat"]),
                "lon": float(g["lon"]),
                "label": g.get("label") or hedef,
                "source": g.get("source") or "geo",
            }
    # varsayılan: İstanbul
    return {"lat": 41.0082, "lon": 28.9784, "label": "İstanbul", "source": "default"}


def search_sentinel(
    *,
    hedef: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    limit: int = 5,
    max_cloud: float = 40.0,
    datetime: str = "2024-01-01T00:00:00Z/2025-12-31T23:59:59Z",
) -> dict[str, Any]:
    place = resolve_place(hedef, lat, lon)
    bbox = _bbox_from_center(place["lat"], place["lon"])
    body = {
        "collections": [COLLECTION],
        "bbox": bbox,
        "datetime": datetime,
        "limit": max(1, min(int(limit or 5), 20)),
        "query": {"eo:cloud_cover": {"lt": float(max_cloud)}},
    }
    req = urllib.request.Request(
        STAC_SEARCH,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": UA},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"ok": False, "error": f"STAC HTTP {e.code}", "place": place, "bbox": bbox}
    except Exception as ex:
        return {"ok": False, "error": str(ex), "place": place, "bbox": bbox}

    items = []
    for f in data.get("features") or []:
        props = f.get("properties") or {}
        assets = f.get("assets") or {}
        thumb = None
        for key in ("thumbnail", "rendered_preview", "overview"):
            if key in assets and assets[key].get("href"):
                thumb = assets[key]["href"]
                break
        visual = (assets.get("visual") or {}).get("href")
        items.append(
            {
                "id": f.get("id"),
                "datetime": props.get("datetime"),
                "cloud_cover": props.get("eo:cloud_cover"),
                "platform": props.get("platform"),
                "thumbnail": thumb,
                "visual_cog": visual,
                "bbox": f.get("bbox"),
                "self": next(
                    (L.get("href") for L in (f.get("links") or []) if L.get("rel") == "self"),
                    None,
                ),
            }
        )

    best = items[0] if items else None
    return {
        "ok": True,
        "provider": "element84-earth-search",
        "collection": COLLECTION,
        "place": place,
        "bbox": bbox,
        "count": len(items),
        "items": items,
        "best": best,
        "preview": (best or {}).get("thumbnail"),
        "note": "Sentinel-2 L2A — açık STAC; görsel önizleme + COG bağlantısı",
    }
