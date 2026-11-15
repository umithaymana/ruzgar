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
    r_ist = resolve_super_el("istanbulu goster", geocode=False)
    if not r_ist.get("ok") or r_ist.get("organ") != "harita":
        fail("istanbulu goster organ")
    # Anayasa: sınıf kamera + hardcode yok; örnekler yalnız test; ağ zorunlu değil
    from ilim_assistant.sahne_harita_geo import (
        CAMERA_BY_TIP,
        TIP_ZOOM,
        _YEREL,
        camera_for_tip,
        geocode_local,
        infer_tip_from_text,
        zoom_for_tip,
        _nominatim_queries,
    )

    if _YEREL:
        fail("Anayasa: uretim _YEREL dolu olamaz")
    if geocode_local("Everest") is not None:
        fail("Anayasa: geocode_local varsayilan kapali olmali")
    geo_src = (ROOT / "ilim_assistant" / "sahne_harita_geo.py").read_text(encoding="utf-8")
    if "GEO_TRUTH" in geo_src:
        fail("Anayasa: GEO_TRUTH uretim kodunda olamaz")
    if "41.1167" in geo_src or "27.98806" in geo_src:
        fail("Anayasa: sabit ornek koordinat uretimde olamaz")
    for tip, zmin in (
        ("il", 11),
        ("dag", 14),
        ("gecit", 16),
        ("kopru", 17),
        ("bina", 18),
        ("nehir", 11),
        ("bogaz", 14),
    ):
        if zoom_for_tip(tip) < zmin:
            fail("zoom_for_tip dusuk: " + tip)
    for phrase, tip in (
        ("Uludag", "dag"),
        ("Mescit Gecidi", "gecit"),
        ("Bogaz Koprusu", "kopru"),
        ("Galata Kulesi", "bina"),
        ("Amazon Nehri", "nehir"),
        ("Grand Canyon", "kanyon"),
        ("Fuji Yanardagi", "volkan"),
        ("Istanbul Bogazi", "bogaz"),
        ("Everest Dagi", "dag"),
        ("Agri Dagi", "dag"),
        ("Kackar Daglari", "dag"),
    ):
        got = infer_tip_from_text(phrase)
        if got != tip:
            fail("sinif tip " + phrase + "=" + str(got) + " != " + tip)
    for tip in ("nehir", "dag", "volkan", "kanyon", "bogaz", "ada", "sehir", "bina"):
        if tip not in CAMERA_BY_TIP and tip not in TIP_ZOOM:
            fail("sinif kamera/zoom eksik: " + tip)
        cam = camera_for_tip(tip, 0.0, 0.0)
        if cam.get("range_m") is None:
            fail("camera_for_tip range yok: " + tip)
    nq = _nominatim_queries("Seine River")
    if not any("river" in str(x).lower() for x in nq):
        fail("evrensel nehir sorgu eki yok")
    if any(", turkiye" in str(x).lower() or ", türkiye" in str(x).lower() for x in nq):
        fail("Anayasa: Turkiye zorlamasi yasak")
    try:
        from ilim_assistant.sahne_harita_geo import geocode as _geo_net

        sample = _geo_net("Mount Everest", allow_network=True)
        if sample and sample.get("lat") is not None and sample.get("camera"):
            # Florida ~28.36 / Avustralya ~-30 — Nepal 27.988,86.925
            if (
                abs(float(sample["lat"]) - 27.988) <= 0.35
                and abs(float(sample["lon"]) - 86.925) <= 0.35
            ):
                print("OK: ag ornek Everest")
            else:
                print(
                    "WARN: ag sapma (ornek, uretim bagimli degil):",
                    sample.get("lat"),
                    sample.get("lon"),
                )
        else:
            print("WARN: Nominatim yok/429 — ag ornek atlandi")
    except Exception as ex:
        print("WARN: ag ornek atlandi:", ex)
    print("OK: Anayasa evrensel geo + sinif kamera")
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
    # H9 + H10.7 Sürekli Dünya Gezgini
    from ilim_assistant.sahne_dunya_gezgini import (  # noqa: E402
        ALT_BANDS,
        FLIGHT_STYLES,
        H9_VERSION,
        H10_VERSION,
        NATURE_TIPS,
        build_tour_payload,
        classify_gezgin_tip,
        classify_nature_tip,
        extend_endless_path,
        looks_like_tour_control,
        looks_like_tour_start,
    )

    if not H9_VERSION.startswith("ruzgar-dunya-gezgini-h9"):
        fail("H9 version")
    if "h10.7" not in H10_VERSION:
        fail("H10.7 version")
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
    if classify_nature_tip("Fuji Yanardagi") != "volkan":
        fail("Fuji volkan sinif")
    if classify_nature_tip("Kibris Adasi") != "ada":
        fail("Kibris ada sinif")
    if classify_gezgin_tip("Istanbul", tip_hint="il") != "sehir":
        fail("Istanbul sehir sinif")
    if FLIGHT_STYLES.get("nehir") != "river_follow":
        fail("nehir flight style")
    if FLIGHT_STYLES.get("dag") != "ridge_wander":
        fail("dag flight style")
    if FLIGHT_STYLES.get("kanyon") != "corridor":
        fail("kanyon flight style")
    if FLIGHT_STYLES.get("ada") != "coast_cruise":
        fail("ada flight style")
    if FLIGHT_STYLES.get("volkan") != "volcano_wander":
        fail("volkan flight style")
    if FLIGHT_STYLES.get("sehir") != "city_cruise":
        fail("sehir flight style")
    if ALT_BANDS["nehir"][1] > 100 or ALT_BANDS["sehir"][1] > 130:
        fail("pilot irtifa bantlari yuksek (cevre gorunmeli)")
    for phrase, expect_act in (
        ("Everesti gezdir", "tour_start"),
        ("Agri Dagi turu", "tour_start"),
        ("Kackar Daglari turu", "tour_start"),
        ("Mescit Gecidi turu", "tour_start"),
        ("Uludag turu", "tour_start"),
        ("Nil Nehri turu", "tour_start"),
        ("Amazon Nehri turu", "tour_start"),
        ("Grand Canyon turu", "tour_start"),
        ("Kibris Adasi turu", "tour_start"),
        ("Fuji Yanardagi turu", "tour_start"),
        ("Istanbulu gezdir", "tour_start"),
        ("turu durdur", "tour_pause"),
        ("tura devam", "tour_resume"),
        ("devam et", "tour_resume"),
        ("turu bitir", "tour_stop"),
        ("dur", "tour_pause"),
        ("hizlandir", "tour_faster"),
        ("hizlan", "tour_faster"),
        ("yavaslat", "tour_slower"),
        ("yere yaklas", "tour_closer"),
        ("yuksel", "tour_farther"),
        ("yukari cik", "tour_farther"),
        ("asagi in", "tour_closer"),
        ("alcal", "tour_closer"),
        ("sola don", "tour_turn_left"),
        ("saga don", "tour_turn_right"),
        ("ileri git", "tour_forward"),
        ("geri don", "tour_back"),
        ("nehri takip et", "tour_follow_river"),
        ("sehre gir", "tour_enter_city"),
        ("kiyiyi takip et", "tour_follow_coast"),
        ("kraterin icine gir", "tour_enter_crater"),
        ("1 metre", "tour_altitude"),
        ("2 metreye in", "tour_altitude"),
        ("kus ucusu", "tour_altitude_reset"),
    ):
        rr = resolve_super_el(phrase, geocode=False)
        if rr.get("action") != expect_act:
            fail(phrase + " action=" + str(rr.get("action")))
    # Tur paketi: test-only koordinat (üretim hardcode değil)
    nil_tour = build_tour_payload(
        place="Nil Nehri",
        geo={"lat": 25.68724, "lon": 32.63964, "tip": "nehir", "label": "Nil Nehri"},
    )
    if str(nil_tour.get("tip")) != "nehir" or str((nil_tour.get("card") or {}).get("tur")) != "Nehir":
        fail("Nil Nehri tip/kart: " + str(nil_tour.get("tip")) + "/" + str((nil_tour.get("card") or {}).get("tur")))
    if (nil_tour.get("flight") or {}).get("style") != "river_follow":
        fail("Nil flight style river_follow olmali")
    if not nil_tour.get("endless") or len(nil_tour.get("waypoints") or []) < 12:
        fail("Nil endless/waypoints")
    ist_tour = build_tour_payload(
        place="Istanbul",
        geo={"lat": 41.0082, "lon": 28.9784, "tip": "sehir", "label": "Istanbul"},
    )
    if str(ist_tour.get("tip")) != "sehir":
        fail("Istanbul tip sehir olmali: " + str(ist_tour.get("tip")))
    if looks_like_tour_start("dunya turu"):
        fail("dunya turu H9 start olmamali (mode_tur)")
    if looks_like_tour_control("dur") != "tour_pause":
        fail("dur = pause olmali")
    if looks_like_tour_control("sola don") != "tour_turn_left":
        fail("sola don")
    if looks_like_tour_control("ileri git") != "tour_forward":
        fail("ileri git")
    if looks_like_tour_control("geri don") != "tour_back":
        fail("geri don")
    if looks_like_tour_control("nehri takip et") != "tour_follow_river":
        fail("nehri takip")
    r_alt = resolve_super_el("2 metreye in", geocode=False)
    if r_alt.get("action") != "tour_altitude" or float(r_alt.get("tour_meters") or 0) != 2.0:
        fail("2 metreye in meters=" + str(r_alt.get("tour_meters")))
    r_zoom = resolve_super_el("uzaklastir", geocode=False)
    if r_zoom.get("action") != "zoom_out":
        fail("uzaklastir zoom bozuldu: " + str(r_zoom.get("action")))
    tp = build_tour_payload(
        place="Everest",
        geo={"lat": 27.9881, "lon": 86.925, "tip": "dag", "label": "Everest"},
    )
    if not tp or not tp.get("endless"):
        fail("build_tour_payload Everest endless")
    if len(tp.get("waypoints") or []) < 20:
        fail("Everest waypoints densite")
    if (tp.get("flight") or {}).get("style") != "ridge_wander":
        fail("Everest ridge_wander")
    # uzatma
    ext = extend_endless_path("nehir", tp["waypoints"][-1], label="Nil", count=16)
    if len(ext) < 8:
        fail("extend_endless_path")
    for place, tip, lat, lon, style in (
        ("Nil", "nehir", 25.68724, 32.63964, "river_follow"),
        ("Amazon", "nehir", -3.1, -60.0, "river_follow"),
        ("Everest", "dag", 27.9881, 86.925, "ridge_wander"),
        ("Agri Dagi", "dag", 39.7016, 44.2983, "ridge_wander"),
        ("Grand Canyon", "kanyon", 36.1069, -112.1129, "corridor"),
        ("Kibris", "ada", 35.1264, 33.4299, "coast_cruise"),
        ("Fuji", "volkan", 35.3606, 138.7274, "volcano_wander"),
        ("Istanbul", "sehir", 41.0082, 28.9784, "city_cruise"),
    ):
        pack = build_tour_payload(
            place=place,
            geo={"lat": lat, "lon": lon, "tip": tip, "label": place},
        )
        if not pack or not pack.get("endless"):
            fail("H10.7 pack: " + place)
        if (pack.get("flight") or {}).get("style") != style:
            fail(place + " style=" + str((pack.get("flight") or {}).get("style")))
        if len(pack.get("waypoints") or []) < 12:
            fail(place + " waypoint az")
        mx = max(float(w.get("range") or 0) for w in pack["waypoints"])
        if mx > 280:
            fail(place + " irtifa yuksek: " + str(mx))
    if build_tour_payload(place="Everest") is not None:
        fail("coordsuz payload olmamali")
    for needle in (
        "startTourWithPayload",
        "fetchAndStartTour",
        "tourPause",
        "tourResume",
        "extendExplorationPath",
        "tourTurn",
        "tourSetSteerMode",
        "tourSlower",
        "tourFaster",
        "tourCloser",
        "tourFarther",
        "tourSetAltitude",
        "effectiveTourRange",
        "startContinuousFlight",
        "tickContinuousFlight",
        "sampleWaypointPair",
        "catmullRom",
        "buildLocalTourPayload",
        "wantTourBoot",
        "requestAnimationFrame",
        "ruzgar-harita-ready",
        "updateTourProgress",
        "setTourCinema",
        "tour-cinema-on",
        "h10.7-dunya-gezgini-surekli-v1",
        "endless",
        "TOUR_BASE_RATE",
        "rebuildPathAhead",
        "tourForward",
        "tourBack",
        "scheduleNarration",
        'id="tourBar"',
        'id="tourProgFill"',
        "ruzgar-harita-tour",
        "wantTour",
    ):
        if needle not in viewer_h:
            fail("H10.7 viewer eksik: " + needle)
    if "tour_start" not in masa_js or "ruzgar-harita-tour" not in masa_js:
        fail("H9/H10 masa tour kanca yok")
    if "ruzgar-harita-cinema" not in masa_js:
        fail("H10.6 masa cinema kanca yok")
    if 'data-harita-act="tour_start"' not in masa_js:
        fail("H9 Gezgin menü yok")
    if 'data-harita-act="tour_faster"' not in masa_js or 'data-harita-act="tour_slower"' not in masa_js:
        fail("H10.7 hız menü yok")
    if 'data-harita-act="tour_closer"' not in masa_js or 'data-harita-act="tour_farther"' not in masa_js:
        fail("H10.7 irtifa menü yok")
    if "scheduleHaritaTourStart" not in masa_js or "ruzgar-harita-ready" not in masa_js:
        fail("H10.7 masa tour retry/ready yok")
    mobil_js = (ROOT / "static" / "mobil-pwa" / "app.js").read_text(encoding="utf-8")
    for needle in (
        "tour_start",
        "tour_faster",
        "tour_slower",
        "tour_closer",
        "tour_farther",
        "tour_turn_left",
        "tour_forward",
        "tour_back",
        "tour_follow_river",
        "tour_enter_city",
        "scheduleMobilHaritaTourStart",
        "ruzgar-harita-ready",
        "ruzgar-harita-tour",
        "ruzgar-harita-cinema",
        "tour=1",
        "mobil-harita-cinema",
    ):
        if needle not in mobil_js:
            fail("H10.7 mobil eksik: " + needle)
    srv = (ROOT / "desktop_server.py").read_text(encoding="utf-8", errors="ignore")
    if "/api/sahne/harita/tur" not in srv or "sahne_dunya_gezgini" not in srv:
        fail("H9 /tur API yok")
    if "H10_VERSION" not in srv:
        fail("H10 API version yok")
    print("OK: H9 Dünya Gezgini")
    print("OK: H10 Akıllı Dünya Gezgini")
    if "tour_forward" not in masa_js or "tour_back" not in masa_js:
        fail("masa pilot forward/back yok")
    if "pilot-gezi-v1" not in masa_js:
        fail("masa cache-bust pilot-gezi yok")
    print("OK: H10.7 pilot gezi (yavaş + steer + anlatım)")
    for phrase in ("Zigana Gecidi", "Kop Gecidi"):
        if infer_tip_from_text(phrase) != "gecit":
            fail(phrase + " gecit sinif")
        if zoom_for_tip("gecit") < 16:
            fail("gecit zoom")
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
    r3g = resolve_super_el("3d goster", geocode=False)
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
