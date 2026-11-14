# -*- coding: utf-8 -*-
from pathlib import Path

p = Path(__file__).resolve().parents[2] / "ruzgar-desktop" / "vendor" / "cesium" / "Cesium.js"
print("exists", p.is_file(), "size", p.stat().st_size if p.is_file() else 0)
full = p.read_text(encoding="utf-8", errors="ignore") if p.is_file() else ""
for k in (
    "CustomHeightmapTerrainProvider",
    "CesiumTerrainProvider",
    "createWorldTerrain",
    "createWorldTerrainAsync",
    "EllipsoidTerrainProvider",
    "Cesium.Ion",
    "VRTheWorldTerrainProvider",
):
    print(k, k in full)
