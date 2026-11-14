#!/usr/bin/env python3
"""Süper-el + organ iskelet smoke. Çıkış 0 = yeşil."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ilim_assistant.sahne_super_el import FILLER, ORGANLAR, resolve_super_el, smoke_super_el  # noqa: E402


def fail(msg: str) -> None:
    print("FAIL:", msg)
    sys.exit(1)


def main() -> None:
    if len(FILLER) != 8:
        fail("8 fiil şart")
    fails = smoke_super_el()
    if fails:
        fail("; ".join(fails))
    print("OK: super_el cases")
    r = resolve_super_el("haritayi goster", geocode=False)
    if not r.get("ok") or r.get("organ") != "harita":
        fail("harita goster")
    r_ist = resolve_super_el("istanbulu goster", geocode=True)
    if not r_ist.get("geo") or r_ist["geo"].get("lat") is None:
        fail("istanbul geo yok")
    r_z = resolve_super_el("daha yaklastir", geocode=False)
    if int(r_z.get("zoom_delta") or 0) <= 0:
        fail("yaklastir zoom_delta")
    r3 = resolve_super_el("3d goster", geocode=False)
    if r3.get("action") != "mode_3d" or r3.get("organ") != "harita":
        fail("3d mode")
    if r3.get("hedef"):
        fail("3d hedef olmamali: " + str(r3.get("hedef")))
    r3g = resolve_super_el("3d goster", geocode=True)
    if r3g.get("geo"):
        fail("3d geo olmamali")
    r4 = resolve_super_el("4d ye gec", geocode=False)
    if r4.get("action") != "mode_4d":
        fail("4d mode")
    if r4.get("hedef"):
        fail("4d hedef olmamali")
    ru = resolve_super_el("uydu goster", geocode=False)
    if ru.get("action") != "mode_uydu" or ru.get("organ") != "harita":
        fail("uydu mode")
    rt = resolve_super_el("dunya turu", geocode=False)
    if rt.get("action") != "mode_tur":
        fail("tur mode")
    print("OK: resolve+geo+zoom+3d4d+uydu+tur")
    viewer = ROOT.parent / "ruzgar-desktop" / "harita-viewer.html"
    if not viewer.is_file():
        fail("harita-viewer.html yok")
    leaf = ROOT.parent / "ruzgar-desktop" / "vendor" / "leaflet" / "leaflet.js"
    if not leaf.is_file():
        fail("vendor/leaflet yok")
    masa = (ROOT.parent / "ruzgar-desktop" / "ruzgar-masa.js").read_text(encoding="utf-8")
    for needle in (
        "applySahneOrgan",
        "runSuperEl",
        "ruzgar-sahne-organ",
        "ruzgar-sahne-mini",
        "/api/sahne/super-el",
        "clearSahneOrgan",
        "dispatchSahneOrganCommand",
        "applyHaritaCommand",
        "zoom_delta",
        "mode_3d",
        "mode_uydu",
        "mode_tur",
        "harita-viewer.html",
        "ruzgar-harita-tools",
        "ruzgar-sahne-organ-on",
    ):
        if needle not in masa:
            fail(f"masa.js eksik: {needle}")
    css = (ROOT.parent / "ruzgar-desktop" / "ruzgar-masa.css").read_text(encoding="utf-8")
    if "ruzgar-sahne-organ-on" not in css or "ruzgar-harita-tools" not in css:
        fail("masa.css full/3d yok")
    mobil = (ROOT / "static" / "mobil-pwa" / "app.js").read_text(encoding="utf-8")
    if "harita-viewer.html" not in mobil or "mode_uydu" not in mobil:
        fail("mobil harita viewer yok")
    idx = (ROOT.parent / "ruzgar-desktop" / "index.html").read_text(encoding="utf-8")
    if "f4map.com" not in idx:
        fail("CSP 3d frame-src yok")
    css = (ROOT.parent / "ruzgar-desktop" / "ruzgar-masa.css").read_text(encoding="utf-8")
    for needle in ("ruzgar-sahne-organ", "ruzgar-sahne-mini #ruzgar-sahne", "is-organ-dim"):
        if needle not in css:
            fail(f"masa.css eksik: {needle}")
    server = (ROOT / "desktop_server.py").read_text(encoding="utf-8")
    if "/api/sahne/super-el" not in server or "resolve_super_el" not in server:
        fail("desktop_server super-el yok")
    if "/api/mobil/erisim" not in server:
        fail("mobil erisim API yok")
    app_js = (ROOT.parent / "ruzgar-desktop" / "app.js").read_text(encoding="utf-8")
    if "ruzgarSahneSuperEl" not in app_js:
        fail("app.js süper-el sohbet kancası yok")
    idx = (ROOT.parent / "ruzgar-desktop" / "index.html").read_text(encoding="utf-8")
    if "openstreetmap.org" not in idx:
        fail("CSP OSM frame-src yok — harita engellenir")
    main_js = (ROOT.parent / "ruzgar-desktop" / "main.js").read_text(encoding="utf-8")
    if "readApiHostForSpawn" not in main_js:
        fail("Electron API host .env okumuyor")
    print("OK: organ+API+CSP+kanca+LAN")
    print("organlar", len(ORGANLAR))
    print("SMOKE_SAHNE_SUPER_EL=PASS")


if __name__ == "__main__":
    main()
