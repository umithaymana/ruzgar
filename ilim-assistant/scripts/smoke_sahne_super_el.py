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
    if int(r_ist["geo"].get("zoom") or 0) < 11:
        fail("istanbul zoom dusuk: " + str(r_ist["geo"].get("zoom")))
    for phrase, tip, zmin in (
        ("Bursa goster", "il", 11),
        ("Uludag goster", "dag", 14),
        ("Mescit Gecidi goster", "gecit", 16),
        ("Bogaz Koprusu goster", "kopru", 17),
        ("Ayasofya goster", "bina", 18),
    ):
        rr = resolve_super_el(phrase, geocode=True)
        g = rr.get("geo") or {}
        if g.get("lat") is None:
            fail(phrase + " geo yok")
        if str(g.get("tip") or "") != tip:
            fail(phrase + " tip=" + str(g.get("tip")) + " != " + tip)
        if int(g.get("zoom") or 0) < zmin:
            fail(phrase + " zoom=" + str(g.get("zoom")) + " < " + str(zmin))
    # H4: Everest varyantları aynı noktaya (Nepal, İstanbul değil)
    everest_pts = []
    for phrase in ("Everest goster", "Mount Everest goster", "Everest Dagi goster"):
        rr = resolve_super_el(phrase, geocode=True)
        g = rr.get("geo") or {}
        if g.get("lat") is None:
            fail(phrase + " geo yok")
        if abs(float(g["lat"]) - 27.9881) > 0.05 or abs(float(g["lon"]) - 86.9250) > 0.05:
            fail(phrase + " yanlis koordinat: " + str(g.get("lat")) + "," + str(g.get("lon")))
        if str(g.get("tip")) != "dag":
            fail(phrase + " tip dag olmali")
        everest_pts.append((round(float(g["lat"]), 4), round(float(g["lon"]), 4)))
    if len(set(everest_pts)) != 1:
        fail("Everest varyantlari farkli nokta: " + str(everest_pts))
    for phrase, tip in (
        ("Agri Dagi goster", "dag"),
        ("Kackar Daglari goster", "dag"),
        ("Uludag goster", "dag"),
        ("Mescit Gecidi goster", "gecit"),
    ):
        rr = resolve_super_el(phrase, geocode=True)
        g = rr.get("geo") or {}
        if g.get("lat") is None or str(g.get("tip")) != tip:
            fail(phrase + " H4 tip/geo")
        if not g.get("hedef_log"):
            fail(phrase + " hedef_log yok")
    viewer_h = (ROOT.parent / "ruzgar-desktop" / "harita-viewer.html").read_text(
        encoding="utf-8"
    )
    if "flyCesiumToLockedTarget" not in viewer_h:
        fail("3d hedef kilit yok")
    if "TARGET" not in viewer_h:
        fail("TARGET tek merkez yok")
    for needle in (
        "cinemaProfileForTarget",
        "flyToBoundingSphere",
        "CUBIC_IN_OUT",
        "3d-cinema-",
        "maximumHeight",
    ):
        if needle not in viewer_h:
            fail("H6 sinema eksik: " + needle)
    for needle in (
        "decodeTerrariumPng",
        "sampleBilinear",
        "heightmapTerrainQuality",
        "MAX_Z = 15",
        "const W = 129",
        "preloadSiblings",
        "baseColor",
    ):
        if needle not in viewer_h:
            fail("H7 terrain kalite eksik: " + needle)
    print("OK: H7 terrain kalite")
    for needle in (
        "H7.5",
        "Y-FLIP YASAK",
        "terrainDebugOn",
        "KUZEY→GÜNEY",
        "terrainExaggeration = 1.0",
        "srcY = v * (srcH - 1)",
    ):
        if needle not in viewer_h:
            fail("H7.5 kök düzeltme eksik: " + needle)
    print("OK: H7.5 terrain kök neden")
    for needle in (
        "createWorldTerrainAsync",
        "fetchCesiumIonConfig",
        "/api/sahne/harita/cesium",
        "Cesium World Terrain",
        "applyTerrariumFallback",
    ):
        if needle not in viewer_h:
            fail("H8 Ion World Terrain eksik: " + needle)
    if "/api/sahne/harita/cesium" not in (
        (ROOT / "desktop_server.py").read_text(encoding="utf-8", errors="ignore")
    ):
        fail("H8 cesium API yok")
    print("OK: H8 Cesium World Terrain")
    for needle in (
        "lpTerrainStatus",
        "Terrain: World Terrain",
        "RUZGAR_HARITA_MODULES",
        "dunyaGezgini",
        "sehirGezgini",
        "kameraKatmani",
        "nasaKatmani",
        "mib-row",
        "syncTerrainStatusLabel",
        "range: 28000",
        "range: 22000",
    ):
        if needle not in viewer_h:
            fail("H8 UI/hazırlık eksik: " + needle)
    masa_js = (ROOT.parent / "ruzgar-desktop" / "ruzgar-masa.js").read_text(
        encoding="utf-8"
    )
    if "toggle_logo" not in masa_js or "ruzgar-harita-logo-off" not in masa_js:
        fail("H8 logo gizle yok")
    masa_css = (ROOT.parent / "ruzgar-desktop" / "ruzgar-masa.css").read_text(
        encoding="utf-8"
    )
    if "ruzgar-harita-logo-off" not in masa_css:
        fail("H8 logo CSS yok")
    print("OK: H8 harita UI + gezgin hazırlık")
    # H9 + H10 + H10.5 Dünya Gezgini (sınıf bazlı)
    from ilim_assistant.sahne_dunya_gezgini import (  # noqa: E402
        H9_VERSION,
        H10_VERSION,
        NATURE_TIPS,
        PHASES,
        build_tour_payload,
        classify_nature_tip,
        looks_like_tour_start,
    )

    if not H9_VERSION.startswith("ruzgar-dunya-gezgini-h9"):
        fail("H9 version")
    if "h10.5" not in H10_VERSION and not H10_VERSION.startswith("ruzgar-dunya-gezgini-h10"):
        fail("H10.5 version")
    if len(PHASES) != 4:
        fail("H10 PHASES != 4")
    for tip_name in (
        "dag",
        "gecit",
        "vadi",
        "kanyon",
        "nehir",
        "gol",
        "volkan",
        "selale",
        "delta",
        "col",
        "ada",
    ):
        if tip_name not in NATURE_TIPS:
            fail("NATURE tip eksik: " + tip_name)
    if classify_nature_tip("Nil Nehri") != "nehir":
        fail("Nil Nehri sinif != nehir")
    if classify_nature_tip("Sahara Colu") != "col":
        fail("col sinif")
    if classify_nature_tip("Amazon Nehri") != "nehir":
        fail("Amazon sinif")
    if classify_nature_tip("Grand Canyon") != "kanyon":
        fail("canyon sinif")
    for phrase, expect_act in (
        ("Everesti gezdir", "tour_start"),
        ("Agri Dagi turu", "tour_start"),
        ("Kackar Daglari turu", "tour_start"),
        ("Mescit Gecidi turu", "tour_start"),
        ("Uludag turu", "tour_start"),
        ("Nil Nehri turu", "tour_start"),
        ("turu durdur", "tour_pause"),
        ("tura devam", "tour_resume"),
        ("turu bitir", "tour_stop"),
        ("sonraki durak", "tour_next"),
        ("onceki durak", "tour_prev"),
        ("durak atla", "tour_skip"),
    ):
        rr = resolve_super_el(phrase, geocode=True)
        if rr.get("action") != expect_act:
            fail(phrase + " action=" + str(rr.get("action")))
        if expect_act == "tour_start":
            tour = rr.get("tour") or {}
            if not tour.get("ok") or len(tour.get("stops") or []) < 4:
                fail(phrase + " tour stops eksik: " + str(tour.get("tour_error") or rr.get("tour_error")))
            if not tour.get("class_based"):
                fail(phrase + " class_based yok")
            if not tour.get("card") or not tour["card"].get("yukseklik"):
                fail(phrase + " bilgi karti yok")
            phases = [s.get("phase") for s in tour.get("stops") or []]
            if phases[:4] != ["baslangic", "kesif", "onemli", "genel"]:
                fail(phrase + " H10 asama sirasi: " + str(phases))
            if not rr.get("geo") or rr["geo"].get("lat") is None:
                fail(phrase + " geo yok")
    nil = resolve_super_el("Nil Nehri turu", geocode=True)
    nil_tour = nil.get("tour") or {}
    if str(nil_tour.get("tip")) != "nehir" or str((nil_tour.get("card") or {}).get("tur")) != "Nehir":
        fail("Nil Nehri tip/kart Dağ olmamalı: " + str(nil_tour.get("tip")) + "/" + str((nil_tour.get("card") or {}).get("tur")))
    if looks_like_tour_start("dunya turu"):
        fail("dunya turu H9 start olmamali (mode_tur)")
    # İsim özel listesi yok — yalnız sınıf + koordinat
    tp = build_tour_payload(
        place="Everest",
        geo={"lat": 27.9881, "lon": 86.925, "tip": "dag", "label": "Everest"},
    )
    if not tp or len(tp.get("stops") or []) < 4:
        fail("build_tour_payload Everest class")
    if not tp.get("smart") or not tp.get("class_based"):
        fail("H10.5 class payload")
    if tp.get("card", {}).get("tur") != "Dağ":
        fail("Everest card tur")
    # Yer adı yokken / coords yokken paket kurulmaz
    if build_tour_payload(place="Everest") is not None:
        fail("coordsuz payload olmamali")
    for needle in (
        "startTourWithPayload",
        "fetchAndStartTour",
        "tourPause",
        "tourResume",
        "tourNext",
        "tourPrev",
        "tourSkip",
        "updateTourProgress",
        "renderTourCard",
        "setTourCinema",
        "tour-cinema-on",
        "h10.5-dunya-gezgini-sinif-v1",
        'id="tourBar"',
        'id="tourCard"',
        'id="tourProgFill"',
        "ruzgar-harita-tour",
        "wantTour",
    ):
        if needle not in viewer_h:
            fail("H10.5 viewer eksik: " + needle)
    if "tour_start" not in masa_js or "ruzgar-harita-tour" not in masa_js:
        fail("H9/H10 masa tour kanca yok")
    if "ruzgar-harita-cinema" not in masa_js:
        fail("H10.5 masa cinema kanca yok")
    if 'data-harita-act="tour_start"' not in masa_js:
        fail("H9 Gezgin menü yok")
    if 'data-harita-act="tour_next"' not in masa_js or 'data-harita-act="tour_skip"' not in masa_js:
        fail("H10 ileri/atla menü yok")
    mobil_js = (ROOT / "static" / "mobil-pwa" / "app.js").read_text(encoding="utf-8")
    for needle in (
        "tour_start",
        "tour_next",
        "tour_skip",
        "ruzgar-harita-tour",
        "ruzgar-harita-cinema",
        "tour=1",
        "mobil-harita-cinema",
    ):
        if needle not in mobil_js:
            fail("H10.5 mobil eksik: " + needle)
    srv = (ROOT / "desktop_server.py").read_text(encoding="utf-8", errors="ignore")
    if "/api/sahne/harita/tur" not in srv or "sahne_dunya_gezgini" not in srv:
        fail("H9 /tur API yok")
    if "H10_VERSION" not in srv:
        fail("H10 API version yok")
    print("OK: H9 Dünya Gezgini")
    print("OK: H10 Akıllı Dünya Gezgini")
    print("OK: H10.5 sınıf + mobil senkron")
    for phrase in ("Zigana Gecidi goster", "Kop Gecidi goster"):
        rr = resolve_super_el(phrase, geocode=True)
        g = rr.get("geo") or {}
        if str(g.get("tip")) != "gecit" or g.get("lat") is None:
            fail(phrase + " gecit geo")
    print("OK: tip+zoom hedefleme")
    print("OK: H4 everest+dag senkron")
    print("OK: H6 sinematik kamera")
    r_z = resolve_super_el("daha yaklastir", geocode=False)
    if int(r_z.get("zoom_delta") or 0) <= 0:
        fail("yaklastir zoom_delta")
    r_so = resolve_super_el("sahneyi ac", geocode=False)
    if r_so.get("action") != "stage_open" or r_so.get("organ") != "yuz":
        fail("sahneyi ac → stage_open")
    r_sc = resolve_super_el("sahneyi kapat", geocode=False)
    if r_sc.get("action") != "stage_close":
        fail("sahneyi kapat → stage_close")
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
    rf = resolve_super_el("f4map yedek", geocode=False)
    if rf.get("action") != "mode_f4":
        fail("f4 yedek mode")
    print("OK: resolve+geo+zoom+3d4d+uydu+tur+f4")
    viewer = ROOT.parent / "ruzgar-desktop" / "harita-viewer.html"
    if not viewer.is_file():
        fail("harita-viewer.html yok")
    leaf = ROOT.parent / "ruzgar-desktop" / "vendor" / "leaflet" / "leaflet.js"
    if not leaf.is_file():
        fail("vendor/leaflet yok")
    cesium = ROOT.parent / "ruzgar-desktop" / "vendor" / "cesium" / "Cesium.js"
    if not cesium.is_file():
        fail("vendor/cesium/Cesium.js yok (Faz 1)")
    viewer_txt = viewer.read_text(encoding="utf-8")
    if "CESIUM_BASE_URL" not in viewer_txt or "vendor/cesium/" not in viewer_txt:
        fail("harita-viewer yerel Cesium tabanı yok")
    if "paintCesium3d" not in viewer_txt and "makeCesiumViewer" not in viewer_txt:
        fail("harita-viewer Cesium 3d ana motor yok")
    if "demo.f4map.com" not in viewer_txt:
        fail("F4map yedek yolu yok")
    if "panoPanel" not in viewer_txt or 'id="pano"' in viewer_txt:
        fail("pano Mapillary iframe kaldırılmalı (X-Frame DENY)")
    if "MODIS z≤9" not in viewer_txt and "z≤9" not in viewer_txt:
        fail("4D GIBS zoom sınırı yok")
    for needle in (
        'id="layerPanel"',
        'id="mapTools"',
        "lpBuildings",
        "lpRoads",
        "measure-line",
        "measure-area",
        "draw-point",
        "draw-line",
        "draw-poly",
        'loadVector("buildings"',
        'loadVector("roads"',
        "ruzgarBase",
        'id="mapInfoBar"',
        'id="mapToast"',
        "Rüzgar Harita Hazır",
        "resolveViewZoom",
        "lp-soon",
        "Parseller",
        "Terrain",
        "updateInfoBar",
        "showToast",
        "applyInitialView",
        "flyTo",
        "TIP_ZOOM",
        "bboxParam",
        "moveend",
        "scheduleReverseGeocode",
        "ruzgar-harita-view",
        "publishView",
        "Merkez:",
        'id="lpTerrain"',
        "makeTerrariumTerrainProvider",
        "hillshadeLayer",
        "elevation-tiles-prod/terrarium",
        "World_Hillshade",
        "applyCesiumSceneQuality",
        "showSkirts",
        "logarithmicDepthBuffer",
        "srcY = v * (srcH - 1)",
        "level > MAX_Z",
        "const W = 129",
        "MAX_Z = 15",
        "Y-FLIP YASAK",
    ):
        if needle not in viewer_txt:
            fail(f"harita-viewer katman/ölçüm eksik: {needle}")
    if 'lp-soon"><input type="checkbox" disabled /> Terrain' in viewer_txt:
        fail("Terrain hâlâ disabled stub")
    print("OK: Cesium yerel + F4map yedek + Faz2 UX")
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
        "harita-tools-menu",
        "harita-tools-more",
        "setHaritaToolsMenuOpen",
        "applyHaritaViewSync",
        "formatHaritaLiveText",
        "ruzgar-harita-view",
        "paintHaritaLiveLabels",
        "sahneOrganState.organ === \"harita\"",
    ):
        if needle not in masa:
            fail(f"masa.js eksik: {needle}")
    mobil = (ROOT / "static" / "mobil-pwa" / "app.js").read_text(encoding="utf-8")
    for needle in ("applyMobilHaritaViewSync", "formatMobilHaritaLive", "ruzgar-harita-view"):
        if needle not in mobil:
            fail(f"mobil app.js sync eksik: {needle}")
    css = (ROOT.parent / "ruzgar-desktop" / "ruzgar-masa.css").read_text(encoding="utf-8")
    if "ruzgar-sahne-organ-on" not in css or "ruzgar-harita-tools" not in css:
        fail("masa.css full/3d yok")
    if "harita-tools-menu" not in css or "harita-tools-more-icon" not in css:
        fail("masa.css harita menü yok")
    mobil = (ROOT / "static" / "mobil-pwa" / "app.js").read_text(encoding="utf-8")
    if "harita-viewer.html" not in mobil or "mode_uydu" not in mobil:
        fail("mobil harita viewer yok")
    if "harita-tools-menu" not in mobil or "setMobilHaritaToolsMenuOpen" not in mobil:
        fail("mobil harita menü yok")
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
    if "/api/sahne/harita/reverse" not in server or "reverse_geocode" not in server:
        fail("desktop_server harita reverse yok")
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
    if "probeApiLanOpen" not in main_js or "killApiListenersOnPort" not in main_js:
        fail("Electron lan_open / bind yeniden başlat yok")
    if "ensureHttpsMicProxy" not in main_js:
        fail("Electron HTTPS 8443 köprüsü yok")
    launch = (ROOT / "ruzgar_launch.py").read_text(encoding="utf-8")
    if "_read_api_host" not in launch or '--host", "127.0.0.1"' in launch:
        fail("ruzgar_launch hâlâ 127.0.0.1 kilitli")
    ps1 = (ROOT.parent / "Ruzgar.ps1").read_text(encoding="utf-8")
    if "Test-ApiBindMatchesDesired" not in ps1 or "Stop-HttpsMicProxy" not in ps1:
        fail("Ruzgar.ps1 mobil bind/HTTPS kilit yok")
    https_fn = ps1.split("function Start-HttpsMicProxy", 1)[-1].split("function ", 1)[0]
    if "ArgumentList $pargs" in https_fn:
        fail("HTTPS proxy hâlâ dizi ArgumentList kullanıyor (bosluklu yol kirar)")
    if 'ArgumentList $argLine' not in https_fn:
        fail("HTTPS proxy quoted argLine yok")
    print("OK: organ+API+CSP+kanca+LAN")
    print("organlar", len(ORGANLAR))
    print("SMOKE_SAHNE_SUPER_EL=PASS")


if __name__ == "__main__":
    main()
