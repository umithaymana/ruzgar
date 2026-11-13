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
    r = resolve_super_el("haritayi goster")
    if not r.get("ok") or r.get("organ") != "harita":
        fail("harita goster")
    print("OK: resolve")
    masa = (ROOT.parent / "ruzgar-desktop" / "ruzgar-masa.js").read_text(encoding="utf-8")
    for needle in (
        "applySahneOrgan",
        "runSuperEl",
        "ruzgar-sahne-organ",
        "ruzgar-sahne-mini",
        "/api/sahne/super-el",
        "clearSahneOrgan",
    ):
        if needle not in masa:
            fail(f"masa.js eksik: {needle}")
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
