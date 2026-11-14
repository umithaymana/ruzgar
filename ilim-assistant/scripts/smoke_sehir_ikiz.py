#!/usr/bin/env python3
"""Şehir ikiz smoke (Faz 3–9 iskelet). Çıkış 0 = yeşil."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ilim_assistant.ruzgar_sehir_ikiz import liste_pilot, geojson_oku  # noqa: E402
from ilim_assistant.ruzgar_arac_kayit import tara, sec  # noqa: E402
from ilim_assistant.sahne_super_el import resolve_super_el  # noqa: E402


def fail(m: str) -> None:
    print("FAIL:", m)
    sys.exit(1)


def main() -> None:
    doc = liste_pilot()
    if not doc.get("ok"):
        fail("pilot liste")
    for k in ("istanbul", "ankara", "bursa", "izmir"):
        if k not in doc.get("pilot", []):
            fail(f"pilot eksik {k}")
    # En az 2 şehirde buildings dosyası
    ready = sum(1 for k, v in (doc.get("sehirler") or {}).items() if v.get("buildings"))
    if ready < 2:
        fail(f"buildings dosyası az: {ready}")
    print("OK: pilot", ready, "şehir buildings")

    g = geojson_oku("bursa", "buildings", limit=50)
    if not g or not g.get("features"):
        fail("bursa geojson")
    print("OK: bursa geojson", len(g["features"]))

    tools = tara()
    for tid in ("gdal", "blender", "cesium", "mediamtx", "ifcopenshell"):
        a = next((x for x in tools["araclar"] if x["id"] == tid), None)
        if not a or not a.get("kurulu"):
            fail(f"araç {tid} kurulu değil")
    print("OK: araçlar gdal/blender/cesium/mediamtx/ifc")

    if not sec("gis"):
        fail("sec(gis)")
    if not sec("3d"):
        fail("sec(3d)")

    r = resolve_super_el("binalari goster", geocode=False)
    if r.get("action") != "show_buildings":
        fail("show_buildings")
    r2 = resolve_super_el("gelecek sehir goster", geocode=False)
    if r2.get("action") != "era_gelecek":
        fail("era_gelecek")

    server = (ROOT / "desktop_server.py").read_text(encoding="utf-8")
    for n in (
        "/api/sehir-ikiz/pilot",
        "/api/sehir-ikiz/geojson",
        "/api/sehir-ikiz/gpkg",
        "/api/sehir-ikiz/kameralar",
        "/api/sehir-ikiz/mediamtx",
        "/api/sehir-ikiz/model/",
    ):
        if n not in server:
            fail(f"API {n}")
    viewer = (ROOT.parent / "ruzgar-desktop" / "harita-viewer.html").read_text(encoding="utf-8")
    for n in ("loadBuildings", "spawnAgents", "loadCameraPins", "era"):
        if n not in viewer:
            fail(f"viewer {n}")
    glb = Path(r"D:\ÜMİT\14-) PROGRAMLAR\RuzgarSehirIkiz\models\ornek_bina.glb")
    ifc = Path(r"D:\ÜMİT\14-) PROGRAMLAR\RuzgarSehirIkiz\models\ornek_bina.ifc")
    if not glb.is_file() or not ifc.is_file():
        fail("örnek glb/ifc yok")
    print("OK: modeller + API + viewer")
    print("SMOKE_SEHIR_IKIZ=PASS")


if __name__ == "__main__":
    main()
