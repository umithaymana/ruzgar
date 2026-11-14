# -*- coding: utf-8 -*-
"""Sahne harita — yer adı → lat/lon/zoom (yerel sözlük + Nominatim yedek)."""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any

# zoom: 5 ülke · 8 bölge · 11 şehir · 13 ilçe · 15 mahalle/kasaba
_YEREL: dict[str, dict[str, Any]] = {
    "turkiye": {"lat": 39.0, "lon": 35.2, "zoom": 6, "label": "Türkiye"},
    "turkey": {"lat": 39.0, "lon": 35.2, "zoom": 6, "label": "Türkiye"},
    "anadolu": {"lat": 39.2, "lon": 35.5, "zoom": 6, "label": "Anadolu"},
    "istanbul": {"lat": 41.0082, "lon": 28.9784, "zoom": 11, "label": "İstanbul"},
    "ankara": {"lat": 39.9334, "lon": 32.8597, "zoom": 11, "label": "Ankara"},
    "izmir": {"lat": 38.4192, "lon": 27.1287, "zoom": 11, "label": "İzmir"},
    "bursa": {"lat": 40.1885, "lon": 29.0610, "zoom": 11, "label": "Bursa"},
    "antalya": {"lat": 36.8969, "lon": 30.7133, "zoom": 11, "label": "Antalya"},
    "adana": {"lat": 37.0, "lon": 35.3213, "zoom": 11, "label": "Adana"},
    "konya": {"lat": 37.8746, "lon": 32.4932, "zoom": 11, "label": "Konya"},
    "gaziantep": {"lat": 37.0662, "lon": 37.3833, "zoom": 11, "label": "Gaziantep"},
    "kayseri": {"lat": 38.7312, "lon": 35.4787, "zoom": 11, "label": "Kayseri"},
    "mersin": {"lat": 36.8121, "lon": 34.6415, "zoom": 11, "label": "Mersin"},
    "diyarbakir": {"lat": 37.9144, "lon": 40.2306, "zoom": 11, "label": "Diyarbakır"},
    "samsun": {"lat": 41.2867, "lon": 36.33, "zoom": 11, "label": "Samsun"},
    "trabzon": {"lat": 41.0027, "lon": 39.7168, "zoom": 11, "label": "Trabzon"},
    "erzurum": {"lat": 39.9043, "lon": 41.2679, "zoom": 11, "label": "Erzurum"},
    "van": {"lat": 38.4891, "lon": 43.4089, "zoom": 11, "label": "Van"},
    "eskisehir": {"lat": 39.7767, "lon": 30.5206, "zoom": 11, "label": "Eskişehir"},
    "malatya": {"lat": 38.3552, "lon": 38.3095, "zoom": 11, "label": "Malatya"},
    "denizli": {"lat": 37.7765, "lon": 29.0864, "zoom": 11, "label": "Denizli"},
    "sivas": {"lat": 39.7477, "lon": 37.0179, "zoom": 11, "label": "Sivas"},
    "balikesir": {"lat": 39.6484, "lon": 27.8826, "zoom": 11, "label": "Balıkesir"},
    "kahramanmaras": {"lat": 37.5858, "lon": 36.9371, "zoom": 11, "label": "Kahramanmaraş"},
    "hatay": {"lat": 36.4018, "lon": 36.3498, "zoom": 10, "label": "Hatay"},
    "manisa": {"lat": 38.6191, "lon": 27.4289, "zoom": 11, "label": "Manisa"},
    "aydin": {"lat": 37.8560, "lon": 27.8416, "zoom": 11, "label": "Aydın"},
    "tekirdag": {"lat": 40.9833, "lon": 27.5167, "zoom": 11, "label": "Tekirdağ"},
    "sakarya": {"lat": 40.7569, "lon": 30.3781, "zoom": 11, "label": "Sakarya"},
    "kocaeli": {"lat": 40.8533, "lon": 29.8815, "zoom": 11, "label": "Kocaeli"},
    "mugla": {"lat": 37.2153, "lon": 28.3636, "zoom": 10, "label": "Muğla"},
    "canakkale": {"lat": 40.1553, "lon": 26.4142, "zoom": 11, "label": "Çanakkale"},
    "ordu": {"lat": 40.9862, "lon": 37.8797, "zoom": 11, "label": "Ordu"},
    "rize": {"lat": 41.0201, "lon": 40.5234, "zoom": 11, "label": "Rize"},
    "artvin": {"lat": 41.1828, "lon": 41.8183, "zoom": 10, "label": "Artvin"},
    "palandoken": {"lat": 39.8700, "lon": 41.3000, "zoom": 13, "label": "Palandöken"},
    "tortum": {"lat": 40.3000, "lon": 41.5500, "zoom": 12, "label": "Tortum"},
    "oltu": {"lat": 40.5500, "lon": 41.9900, "zoom": 12, "label": "Oltu"},
    "almanya": {"lat": 51.1657, "lon": 10.4515, "zoom": 6, "label": "Almanya"},
    "germany": {"lat": 51.1657, "lon": 10.4515, "zoom": 6, "label": "Almanya"},
    "fransa": {"lat": 46.2276, "lon": 2.2137, "zoom": 6, "label": "Fransa"},
    "france": {"lat": 46.2276, "lon": 2.2137, "zoom": 6, "label": "Fransa"},
    "italya": {"lat": 41.8719, "lon": 12.5674, "zoom": 6, "label": "İtalya"},
    "ispanya": {"lat": 40.4637, "lon": -3.7492, "zoom": 6, "label": "İspanya"},
    "yunanistan": {"lat": 39.0742, "lon": 21.8243, "zoom": 7, "label": "Yunanistan"},
    "suriye": {"lat": 34.8021, "lon": 38.9968, "zoom": 7, "label": "Suriye"},
    "irak": {"lat": 33.2232, "lon": 43.6793, "zoom": 6, "label": "Irak"},
    "iran": {"lat": 32.4279, "lon": 53.6880, "zoom": 5, "label": "İran"},
    "azerbaycan": {"lat": 40.1431, "lon": 47.5769, "zoom": 7, "label": "Azerbaycan"},
    "gurcistan": {"lat": 42.3154, "lon": 43.3569, "zoom": 7, "label": "Gürcistan"},
    "rusya": {"lat": 61.5240, "lon": 105.3188, "zoom": 3, "label": "Rusya"},
    "amerika": {"lat": 37.0902, "lon": -95.7129, "zoom": 4, "label": "ABD"},
    "abd": {"lat": 37.0902, "lon": -95.7129, "zoom": 4, "label": "ABD"},
    "japonya": {"lat": 36.2048, "lon": 138.2529, "zoom": 5, "label": "Japonya"},
    "cin": {"lat": 35.8617, "lon": 104.1954, "zoom": 4, "label": "Çin"},
    "misir": {"lat": 26.8206, "lon": 30.8025, "zoom": 6, "label": "Mısır"},
    "mekke": {"lat": 21.3891, "lon": 39.8579, "zoom": 12, "label": "Mekke"},
    "medine": {"lat": 24.5247, "lon": 39.5692, "zoom": 12, "label": "Medine"},
    "kudus": {"lat": 31.7683, "lon": 35.2137, "zoom": 12, "label": "Kudüs"},
}


def _norm_key(s: str) -> str:
    from ilim_assistant.sahne_super_el import _norm

    t = _norm(s)
    t = t.replace("'", "").replace("'", "").replace("-", " ")
    t = " ".join(t.split())
    return t.replace(" ", "")


def bbox_from_center(lat: float, lon: float, zoom: int) -> list[float]:
    """OSM embed bbox: minLon,minLat,maxLon,maxLat."""
    z = max(2, min(18, int(zoom)))
    # kaba derece span (ekvator yakını)
    span = 360.0 / (2 ** z)
    span_lat = span * 0.55
    span_lon = span * 0.75
    return [
        round(lon - span_lon / 2, 5),
        round(lat - span_lat / 2, 5),
        round(lon + span_lon / 2, 5),
        round(lat + span_lat / 2, 5),
    ]


def geocode_local(hedef: str) -> dict[str, Any] | None:
    if not hedef:
        return None
    key = _norm_key(hedef)
    if not key:
        return None
    hit = _YEREL.get(key)
    if hit:
        out = dict(hit)
        out["source"] = "local"
        out["bbox"] = bbox_from_center(out["lat"], out["lon"], out["zoom"])
        return out
    # kısmi eşleşme (erzuruma, istanbulu)
    for k, v in _YEREL.items():
        if key.startswith(k) or k.startswith(key):
            out = dict(v)
            out["source"] = "local"
            out["bbox"] = bbox_from_center(out["lat"], out["lon"], out["zoom"])
            return out
    return None


def geocode_nominatim(hedef: str, timeout: float = 4.0) -> dict[str, Any] | None:
    q = (hedef or "").strip()
    if len(q) < 2:
        return None
    params = urllib.parse.urlencode(
        {
            "q": q,
            "format": "json",
            "limit": "1",
            "addressdetails": "0",
        }
    )
    url = f"https://nominatim.openstreetmap.org/search?{params}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "RuzgarSahne/1.0 (local desktop; umit-gokcenur)",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        data = json.loads(raw)
        if not data:
            return None
        row = data[0]
        lat = float(row["lat"])
        lon = float(row["lon"])
        # tip → zoom
        kind = (row.get("type") or row.get("class") or "").lower()
        zoom = 11
        if kind in ("country", "nation"):
            zoom = 6
        elif kind in ("state", "province", "region", "county"):
            zoom = 8
        elif kind in ("city", "town"):
            zoom = 11
        elif kind in ("village", "hamlet", "suburb", "neighbourhood"):
            zoom = 14
        elif kind in ("peak", "mountain"):
            zoom = 13
        bb = row.get("boundingbox")
        if bb and len(bb) == 4:
            # nominatim: [south, north, west, east]
            bbox = [float(bb[2]), float(bb[0]), float(bb[3]), float(bb[1])]
        else:
            bbox = bbox_from_center(lat, lon, zoom)
        return {
            "lat": lat,
            "lon": lon,
            "zoom": zoom,
            "label": row.get("display_name") or q,
            "bbox": bbox,
            "source": "nominatim",
        }
    except Exception:
        return None


def geocode(hedef: str, *, allow_network: bool = True) -> dict[str, Any] | None:
    local = geocode_local(hedef)
    if local:
        return local
    if allow_network:
        return geocode_nominatim(hedef)
    return None
