#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Faz 3 — Pilot şehir OSM/Overpass indirme (İstanbul, Ankara, Bursa, İzmir).
Büyük şehirler için bbox kiremitleri + yedek Overpass aynaları.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

OUT = Path(r"D:\ÜMİT\14-) PROGRAMLAR\RuzgarSehirIkiz\osm")
OUT.mkdir(parents=True, exist_ok=True)

ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]

SEHIRLER = {
    "istanbul": {
        "label": "İstanbul",
        # Avrupa yakası merkez (tam metropol çok büyük — kiremitlerle genişler)
        "bbox": (40.95, 28.85, 41.15, 29.15),
        "center": {"lat": 41.0082, "lon": 28.9784, "zoom": 11},
        "tiles": 2,
    },
    "ankara": {
        "label": "Ankara",
        "bbox": (39.85, 32.70, 40.00, 32.95),
        "center": {"lat": 39.9334, "lon": 32.8597, "zoom": 11},
        "tiles": 2,
    },
    "bursa": {
        "label": "Bursa",
        "bbox": (40.15, 28.95, 40.25, 29.15),
        "center": {"lat": 40.1885, "lon": 29.0610, "zoom": 11},
        "tiles": 1,
    },
    "izmir": {
        "label": "İzmir",
        "bbox": (38.38, 27.05, 38.48, 27.22),
        "center": {"lat": 38.4192, "lon": 27.1287, "zoom": 11},
        "tiles": 1,
    },
}


def _tiles(bbox: tuple[float, float, float, float], n: int) -> list[tuple[float, float, float, float]]:
    s, w, n_, e = bbox
    if n <= 1:
        return [bbox]
    out = []
    for i in range(n):
        for j in range(n):
            ss = s + (n_ - s) * i / n
            nn = s + (n_ - s) * (i + 1) / n
            ww = w + (e - w) * j / n
            ee = w + (e - w) * (j + 1) / n
            out.append((ss, ww, nn, ee))
    return out


def _query_buildings(s: float, w: float, n: float, e: float) -> str:
    return f"""
[out:json][timeout:120];
(
  way["building"]({s},{w},{n},{e});
);
out body;
>;
out skel qt;
"""


def _query_roads(s: float, w: float, n: float, e: float) -> str:
    return f"""
[out:json][timeout:120];
(
  way["highway"~"^(primary|secondary|tertiary|residential|trunk|motorway)$"]({s},{w},{n},{e});
);
out body;
>;
out skel qt;
"""


def _fetch(ql: str) -> dict:
    data = urllib.parse.urlencode({"data": ql}).encode("utf-8")
    last_err: Exception | None = None
    for ep in ENDPOINTS:
        try:
            req = urllib.request.Request(
                ep,
                data=data,
                headers={"User-Agent": "RuzgarSehirIkiz/1.0 (local pilot)"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=180) as resp:
                raw = resp.read()
            return json.loads(raw.decode("utf-8"))
        except Exception as ex:
            last_err = ex
            time.sleep(1.5)
    raise RuntimeError(str(last_err))


def osm_to_geojson(osm: dict) -> dict:
    nodes = {
        el["id"]: (el["lon"], el["lat"])
        for el in osm.get("elements", [])
        if el.get("type") == "node" and "lon" in el
    }
    features = []
    seen = set()
    for el in osm.get("elements", []):
        if el.get("type") != "way" or "nodes" not in el:
            continue
        oid = el.get("id")
        if oid in seen:
            continue
        seen.add(oid)
        coords = [nodes[nid] for nid in el["nodes"] if nid in nodes]
        if len(coords) < 2:
            continue
        tags = el.get("tags") or {}
        closed = len(coords) >= 4 and coords[0] == coords[-1]
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "osm_id": oid,
                    "building": tags.get("building"),
                    "highway": tags.get("highway"),
                    "name": tags.get("name"),
                    "levels": tags.get("building:levels"),
                    "height": tags.get("height"),
                },
                "geometry": {
                    "type": "Polygon" if closed else "LineString",
                    "coordinates": [coords] if closed else coords,
                },
            }
        )
    return {"type": "FeatureCollection", "features": features}


def _merge(a: dict, b: dict) -> dict:
    seen = {f["properties"].get("osm_id") for f in a.get("features", [])}
    feats = list(a.get("features", []))
    for f in b.get("features", []):
        oid = f.get("properties", {}).get("osm_id")
        if oid in seen:
            continue
        seen.add(oid)
        feats.append(f)
    return {"type": "FeatureCollection", "features": feats}


def indir_kind(key: str, kind: str) -> dict:
    meta = SEHIRLER[key]
    out = OUT / f"{key}_{kind}.geojson"
    if out.is_file() and out.stat().st_size > 2000:
        return {"path": str(out), "cached": True, "bytes": out.stat().st_size}
    tiles = _tiles(meta["bbox"], int(meta.get("tiles") or 1))
    merged: dict = {"type": "FeatureCollection", "features": []}
    qfn = _query_buildings if kind == "buildings" else _query_roads
    for i, bb in enumerate(tiles):
        print(f"[{key}] {kind} tile {i+1}/{len(tiles)} {bb}", flush=True)
        try:
            osm = _fetch(qfn(*bb))
            merged = _merge(merged, osm_to_geojson(osm))
            print(f"  -> features so far {len(merged['features'])}", flush=True)
        except Exception as ex:
            print(f"  -> HATA tile: {ex}", flush=True)
        time.sleep(2.0)
    if not merged["features"]:
        return {"error": "no features"}
    out.write_text(json.dumps(merged, ensure_ascii=False), encoding="utf-8")
    return {
        "path": str(out),
        "cached": False,
        "features": len(merged["features"]),
        "bytes": out.stat().st_size,
    }


def main() -> None:
    tum = []
    for k in SEHIRLER:
        rapor = {"sehir": k, "label": SEHIRLER[k]["label"], "dosyalar": {}}
        for kind in ("buildings", "roads"):
            rapor["dosyalar"][kind] = indir_kind(k, kind)
        tum.append(rapor)
    manifesto = {
        "pilot_sehirler": list(SEHIRLER.keys()),
        "centers": {k: v["center"] | {"label": v["label"]} for k, v in SEHIRLER.items()},
        "raporlar": tum,
    }
    mp = OUT / "PILOT_MANIFEST.json"
    mp.write_text(json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8")
    print("MANIFEST", mp)


if __name__ == "__main__":
    main()
