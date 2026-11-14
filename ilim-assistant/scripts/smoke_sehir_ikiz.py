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
    r3 = resolve_super_el("sentinel goster", geocode=False)
    if r3.get("action") != "mode_sentinel":
        fail("mode_sentinel")
    r4 = resolve_super_el("mapillary sokak goruntu", geocode=False)
    if r4.get("action") != "mode_pano":
        fail("mode_pano")

    from ilim_assistant.ruzgar_stac import search_sentinel  # noqa: E402
    from ilim_assistant.ruzgar_pano import pano_nearby  # noqa: E402

    st = search_sentinel(hedef="Bursa", limit=2)
    if not st.get("ok") or not st.get("best"):
        fail(f"STAC arama: {st.get('error') or 'best yok'}")
    print("OK: STAC", (st.get("best") or {}).get("id", "")[:40])
    pn = pano_nearby(hedef="İstanbul", lat=41.0082, lon=28.9784)
    if not pn.get("ok") or not pn.get("embed_url"):
        fail("pano embed")
    print("OK: pano embed", "token" if pn.get("token_configured") else "web")

    server = (ROOT / "desktop_server.py").read_text(encoding="utf-8")
    for n in (
        "/api/sehir-ikiz/pilot",
        "/api/sehir-ikiz/geojson",
        "/api/sehir-ikiz/gpkg",
        "/api/sehir-ikiz/kameralar",
        "/api/sehir-ikiz/mediamtx",
        "/api/sehir-ikiz/model/",
        "/api/sehir-ikiz/stac",
        "/api/sehir-ikiz/pano",
    ):
        if n not in server:
            fail(f"API {n}")
    viewer = (ROOT.parent / "ruzgar-desktop" / "harita-viewer.html").read_text(encoding="utf-8")
    for n in ("loadBuildings", "spawnAgents", "loadCameraPins", "era", "paintSentinel", "paintPano"):
        if n not in viewer:
            fail(f"viewer {n}")
    masa = (ROOT.parent / "ruzgar-desktop" / "ruzgar-masa.js").read_text(encoding="utf-8")
    if "mode_sentinel" not in masa or "mode_pano" not in masa:
        fail("masa mode_sentinel/pano")
    mobil = (ROOT / "static" / "mobil-pwa" / "app.js").read_text(encoding="utf-8")
    if "mode_sentinel" not in mobil or "mode_pano" not in mobil:
        fail("mobil mode_sentinel/pano")
    glb = Path(r"D:\ÜMİT\14-) PROGRAMLAR\RuzgarSehirIkiz\models\ornek_bina.glb")
    ifc = Path(r"D:\ÜMİT\14-) PROGRAMLAR\RuzgarSehirIkiz\models\ornek_bina.ifc")
    if not glb.is_file() or not ifc.is_file():
        fail("örnek glb/ifc yok")
    print("OK: modeller + API + viewer")
    print("SMOKE_SEHIR_IKIZ=PASS")


if __name__ == "__main__":
    main()
