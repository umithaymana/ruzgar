# -*- coding: utf-8 -*-
"""
Sahne Y1 sıra 4–17: eksik meslek rafları KALIN (RAG yok).
Zaten bilgisayar_eserleri / tools içinde olanlar ATLANIR.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _ileri_i_madde_kalin as i

REPORT = i.RAF / "SAHNE_Y1_MESLEK_RAFLARI_RAPOR.json"
MIN = 40


def pack(key: str, dal: str, baslik: str, seed: str, urls: list[str], expected: int = 22) -> dict:
    # zaten yeterince parça varsa atla
    existing = list((i.RAF / dal).rglob(f"*{key}*")) if (i.RAF / dal).exists() else []
    md_existing = [p for p in (i.RAF / dal).rglob("*.md")] if (i.RAF / dal).exists() else []
    # kaynak klasörü convention: dal / metin / {key} veya incremental
    meta_hint = i.RAF / dal / "metin" / key
    if meta_hint.exists():
        n = len(list(meta_hint.rglob("*.md")))
        if n >= MIN:
            print(f"SKIP {key} already {n} md", flush=True)
            return {
                "kaynak_id": f"{dal}_{key}",
                "baslik": baslik,
                "url": seed,
                "dal": dal,
                "parca": n,
                "ok": True,
                "skipped": True,
                "durum": "zaten_var",
            }
    urls = i.uniq(urls, cap=i.URL_CAP)
    print(f"=== {key} urls={len(urls)}", flush=True)
    return i.thick(dal, key, baslik, seed, urls, expected)


def main() -> int:
    try:
        sys.stdout.reconfigure(line_buffering=True)  # type: ignore[attr-defined]
    except Exception:
        pass
    i.BODY_TARGET = MIN * 12000
    items: dict = {}

    # 4) Mimar / müteahhit
    items["mimar_bina_3d"] = pack(
        "mimar_bina_3d",
        "08_yazilim_mi_mari_leri_",
        "Mimar/müteahhit — çizim, gabari, glTF/Three, fotogrametri, 4D düşünce (kalın)",
        "https://www.khronos.org/gltf/",
        [
            "https://www.khronos.org/gltf/",
            "https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html",
            "https://github.com/KhronosGroup/glTF",
            "https://threejs.org/docs/",
            "https://threejs.org/manual/",
            "https://threejs.org/examples/",
            "https://raw.githubusercontent.com/mrdoob/three.js/dev/README.md",
            "https://www.blender.org/manual/en/index.html",
            "https://docs.blender.org/manual/en/latest/",
            "https://wiki.osgeo.org/wiki/Main_Page",
            "https://gdal.org/",
            "https://gdal.org/en/latest/",
            "https://proj.org/",
            "https://en.wikipedia.org/wiki/Building_information_modeling",
            "https://en.wikipedia.org/wiki/Architectural_drawing",
            "https://en.wikipedia.org/wiki/4D_BIM",
            "https://en.wikipedia.org/wiki/Photogrammetry",
            "https://opensfm.org/",
            "https://www.opendronemap.org/",
            "https://docs.opendronemap.org/",
            "https://wiki.openstreetmap.org/wiki/Buildings",
            "https://wiki.openstreetmap.org/wiki/Simple_3D_buildings",
            "https://3d.bk.tudelft.nl/opendata/citygml/",
            "https://www.citygml.org/",
            "https://en.wikipedia.org/wiki/Urban_planning",
            "https://en.wikipedia.org/wiki/Zoning",
            "https://en.wikipedia.org/wiki/Floor_area_ratio",
            "https://developer.mozilla.org/en-US/docs/Web/API/WebGL_API",
            "https://raw.githubusercontent.com/KhronosGroup/glTF/main/README.md",
        ]
        + i.bfs(
            ["https://threejs.org/docs/", "https://docs.opendronemap.org/"],
            lambda u: "threejs.org" in u or "opendronemap.org" in u or "khronos.org" in u,
            limit=40,
            max_depth=1,
        ),
        expected=24,
    )

    # 5) Yönetmen / editör
    items["yonetmen_kurgu"] = pack(
        "yonetmen_kurgu",
        "08_yazilim_mi_mari_leri_",
        "Yönetmen/editör — kurgu dili, OTIO, altyazı, ses post (kalın)",
        "https://opentimelineio.readthedocs.io/",
        [
            "https://opentimelineio.readthedocs.io/",
            "https://opentimelineio.readthedocs.io/en/latest/",
            "https://github.com/AcademySoftwareFoundation/OpenTimelineIO",
            "https://www.w3.org/TR/webvtt1/",
            "https://www.w3.org/TR/media-frags/",
            "https://developer.mozilla.org/en-US/docs/Web/API/WebVTT_API",
            "https://ffmpeg.org/ffmpeg-filters.html",
            "https://trac.ffmpeg.org/wiki/Concatenate",
            "https://trac.ffmpeg.org/wiki/AudioChannelManipulation",
            "https://en.wikipedia.org/wiki/Film_editing",
            "https://en.wikipedia.org/wiki/Continuity_editing",
            "https://en.wikipedia.org/wiki/Montage_(filmmaking)",
            "https://en.wikipedia.org/wiki/Storyboard",
            "https://en.wikipedia.org/wiki/Subtitle_(captioning)",
            "https://en.wikipedia.org/wiki/Loudness_war",
            "https://en.wikipedia.org/wiki/Dialog_normalization",
            "https://www.itu.int/rec/R-REC-BS.1770",
            "https://raw.githubusercontent.com/AcademySoftwareFoundation/OpenTimelineIO/main/README.md",
        ]
        + i.bfs(
            ["https://opentimelineio.readthedocs.io/en/latest/"],
            lambda u: "opentimelineio.readthedocs.io" in u,
            limit=35,
            max_depth=1,
        ),
        expected=22,
    )

    # 9) Doktor / eğitmen (teşhis iddiası YOK)
    items["egitim_anatomi"] = pack(
        "egitim_anatomi",
        "18_bi_li_msel_ara_tirma_y_ntemleri_",
        "Eğitmen/anatomi — açık eğitim atlası+pedagoji (teşhis yok etiketi)",
        "https://openstax.org/details/books/anatomy-and-physiology-2e",
        [
            "https://openstax.org/details/books/anatomy-and-physiology-2e",
            "https://openstax.org/books/anatomy-and-physiology-2e/pages/1-introduction",
            "https://openstax.org/books/anatomy-and-physiology-2e/pages/1-1-overview-of-anatomy-and-physiology",
            "https://openstax.org/details/books/introduction-intellectual-property",
            "https://en.wikipedia.org/wiki/Anatomy",
            "https://en.wikipedia.org/wiki/Physiology",
            "https://en.wikipedia.org/wiki/Medical_education",
            "https://en.wikipedia.org/wiki/Pedagogy",
            "https://en.wikipedia.org/wiki/Instructional_design",
            "https://en.wikipedia.org/wiki/Active_learning",
            "https://en.wikipedia.org/wiki/Bloom%27s_taxonomy",
            "https://www.w3.org/WAI/fundamentals/accessibility-intro/",
            "https://developer.mozilla.org/en-US/docs/Web/Accessibility",
            "https://openstax.org/subjects",
        ]
        + i.bfs(
            ["https://openstax.org/books/anatomy-and-physiology-2e/pages/1-introduction"],
            lambda u: "openstax.org" in u and "anatomy" in u.lower(),
            limit=40,
            max_depth=1,
        ),
        expected=24,
    )

    # 10) Avukat / noter dosya masası (tavsiye değil)
    items["hukuk_dosya_masa"] = pack(
        "hukuk_dosya_masa",
        "18_bi_li_msel_ara_tirma_y_ntemleri_",
        "Hukuk dosya masası — diff, kronoloji, arşiv (tavsiye değil)",
        "https://www.w3.org/TR/annotation-model/",
        [
            "https://www.w3.org/TR/annotation-model/",
            "https://www.w3.org/TR/prov-overview/",
            "https://www.w3.org/TR/prov-dm/",
            "https://www.rfc-editor.org/rfc/rfc6902",
            "https://en.wikipedia.org/wiki/Diff",
            "https://en.wikipedia.org/wiki/Chronology",
            "https://en.wikipedia.org/wiki/Records_management",
            "https://en.wikipedia.org/wiki/Document_management_system",
            "https://en.wikipedia.org/wiki/Version_control",
            "https://git-scm.com/docs/git-diff",
            "https://www.ietf.org/archive/id/draft-ietf-httpapi-linkset-10.html",
            "https://schema.org/Legislation",
            "https://schema.org/DigitalDocument",
        ]
        + i.bfs(
            ["https://www.w3.org/TR/prov-overview/", "https://www.w3.org/TR/annotation-model/"],
            lambda u: "w3.org" in u,
            limit=30,
            max_depth=1,
        ),
        expected=20,
    )

    # 14) Müzisyen
    items["muzik_partisyon"] = pack(
        "muzik_partisyon",
        "08_yazilim_mi_mari_leri_",
        "Müzisyen — teori, MusicXML, Web Audio, dalga (kalın)",
        "https://www.w3.org/2021/03/smufl13/",
        [
            "https://www.musicxml.com/",
            "https://www.w3.org/2021/03/smufl13/",
            "https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API",
            "https://developer.mozilla.org/en-US/docs/Web/API/OscillatorNode",
            "https://en.wikipedia.org/wiki/Music_theory",
            "https://en.wikipedia.org/wiki/Musical_notation",
            "https://en.wikipedia.org/wiki/Sheet_music",
            "https://en.wikipedia.org/wiki/MIDI",
            "https://en.wikipedia.org/wiki/Audio_bit_depth",
            "https://musescore.org/",
            "https://musescore.org/en/handbook",
            "https://w3c.github.io/mnx/overview/",
        ]
        + i.bfs(
            ["https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API"],
            lambda u: "developer.mozilla.org" in u and "Audio" in u,
            limit=30,
            max_depth=1,
        ),
        expected=20,
    )

    # 13) Gazeteci
    items["gazeteci_acik_veri"] = pack(
        "gazeteci_acik_veri",
        "18_bi_li_msel_ara_tirma_y_ntemleri_",
        "Gazeteci — açık veri, kaynak doğrulama, harita haber (kalın)",
        "https://opendatahandbook.org/",
        [
            "https://opendatahandbook.org/",
            "https://opendatahandbook.org/guide/en/",
            "https://en.wikipedia.org/wiki/Open_data",
            "https://en.wikipedia.org/wiki/Data_journalism",
            "https://en.wikipedia.org/wiki/Fact-checking",
            "https://en.wikipedia.org/wiki/Source_criticism",
            "https://schema.org/NewsArticle",
            "https://www.w3.org/TR/annotation-model/",
            "https://geojson.org/",
            "https://datatracker.ietf.org/doc/html/rfc7946",
        ]
        + i.bfs(
            ["https://opendatahandbook.org/guide/en/"],
            lambda u: "opendatahandbook.org" in u,
            limit=30,
            max_depth=1,
        ),
        expected=18,
    )

    # 15) Çiftçi / saha
    items["ciftci_saha"] = pack(
        "ciftci_saha",
        "08_yazilim_mi_mari_leri_",
        "Çiftçi/saha — GeoJSON, açık hava, tarla haritası (kalın)",
        "https://openweathermap.org/api",
        [
            "https://geojson.org/",
            "https://datatracker.ietf.org/doc/html/rfc7946",
            "https://open-meteo.com/",
            "https://open-meteo.com/en/docs",
            "https://www.openstreetmap.org/about",
            "https://wiki.openstreetmap.org/wiki/Tag:landuse%3Dfarmland",
            "https://en.wikipedia.org/wiki/Precision_agriculture",
            "https://en.wikipedia.org/wiki/Geographic_information_system",
            "https://gdal.org/en/latest/",
            "https://proj.org/",
        ]
        + i.bfs(
            ["https://open-meteo.com/en/docs", "https://geojson.org/"],
            lambda u: "open-meteo.com" in u or "geojson.org" in u,
            limit=25,
            max_depth=1,
        ),
        expected=18,
    )

    # 16) Öğrenci
    items["ogrenci_quiz"] = pack(
        "ogrenci_quiz",
        "18_bi_li_msel_ara_tirma_y_ntemleri_",
        "Öğrenci — spaced repetition, quiz, ders yöntemi (kalın)",
        "https://en.wikipedia.org/wiki/Spaced_repetition",
        [
            "https://en.wikipedia.org/wiki/Spaced_repetition",
            "https://en.wikipedia.org/wiki/Active_recall",
            "https://en.wikipedia.org/wiki/Testing_effect",
            "https://en.wikipedia.org/wiki/Feynman_technique",
            "https://en.wikipedia.org/wiki/Cornell_Notes",
            "https://en.wikipedia.org/wiki/Bloom%27s_taxonomy",
            "https://apps.ankiweb.net/",
            "https://docs.ankiweb.net/",
            "https://openstax.org/subjects",
        ]
        + i.bfs(
            ["https://docs.ankiweb.net/"],
            lambda u: "docs.ankiweb.net" in u or "ankiweb.net" in u,
            limit=25,
            max_depth=1,
        ),
        expected=18,
    )

    # 17) Aile / cihaz defteri
    items["aile_cihaz"] = pack(
        "aile_cihaz",
        "07_si_ber_g_venli_k",
        "Aile — cihaz defteri, gizlilik, ev camı izin modeli (kalın)",
        "https://www.home-assistant.io/docs/",
        [
            "https://www.home-assistant.io/docs/",
            "https://www.home-assistant.io/docs/authentication/",
            "https://www.home-assistant.io/docs/organizing/",
            "https://en.wikipedia.org/wiki/Home_automation",
            "https://en.wikipedia.org/wiki/Privacy",
            "https://en.wikipedia.org/wiki/Principle_of_least_privilege",
            "https://owasp.org/www-project-internet-of-things/",
            "https://www.w3.org/TR/permissions/",
            "https://developer.mozilla.org/en-US/docs/Web/API/Permissions_API",
        ]
        + i.bfs(
            ["https://www.home-assistant.io/docs/"],
            lambda u: "home-assistant.io" in u,
            limit=30,
            max_depth=1,
        ),
        expected=20,
    )

    # 12) Mühendis simülasyon
    items["muhendis_sim"] = pack(
        "muhendis_sim",
        "14_fi_zi_k",
        "Mühendis — şema/simülasyon (sarkaç, yörünge, akış) kalın",
        "https://openstax.org/details/books/university-physics-volume-1",
        [
            "https://openstax.org/details/books/university-physics-volume-1",
            "https://openstax.org/books/university-physics-volume-1/pages/1-introduction",
            "https://en.wikipedia.org/wiki/Pendulum_(mechanics)",
            "https://en.wikipedia.org/wiki/Orbital_mechanics",
            "https://en.wikipedia.org/wiki/Fluid_dynamics",
            "https://en.wikipedia.org/wiki/Circuit_diagram",
            "https://en.wikipedia.org/wiki/Finite_element_method",
            "https://scipy.org/",
            "https://docs.scipy.org/doc/scipy/tutorial/",
            "https://matplotlib.org/stable/tutorials/index.html",
        ]
        + i.bfs(
            ["https://docs.scipy.org/doc/scipy/tutorial/"],
            lambda u: "scipy.org" in u or "matplotlib.org" in u,
            limit=30,
            max_depth=1,
        ),
        expected=20,
    )

    # 8/11 gezgin + tarihçi (nebula var; ek atlas/rehber)
    items["gezgin_rehber"] = pack(
        "gezgin_rehber",
        "08_yazilim_mi_mari_leri_",
        "Gezgin/tarihçi rehber — OSM, Geo, seyahat coğrafyası (kalın)",
        "https://wiki.openstreetmap.org/wiki/Main_Page",
        [
            "https://wiki.openstreetmap.org/wiki/Main_Page",
            "https://wiki.openstreetmap.org/wiki/Map_features",
            "https://www.openstreetmap.org/about",
            "https://nominatim.org/release-docs/latest/",
            "https://en.wikipedia.org/wiki/Travel_literature",
            "https://en.wikipedia.org/wiki/Historical_geography",
            "https://en.wikipedia.org/wiki/Chorography",
            "https://maplibre.org/",
            "https://maplibre.org/maplibre-gl-js/docs/",
            "https://www.naturalearthdata.com/",
        ]
        + i.bfs(
            ["https://maplibre.org/maplibre-gl-js/docs/", "https://wiki.openstreetmap.org/wiki/Map_features"],
            lambda u: "maplibre.org" in u or "openstreetmap.org" in u,
            limit=35,
            max_depth=1,
        ),
        expected=22,
    )

    kalin = sum(1 for v in items.values() if v.get("ok") and (v.get("parca") or v.get("parca_sayisi") or 0) >= MIN)
    report = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "plan_adim": "4-17 meslek rafları (RAG yok)",
        "items": items,
        "kalin": kalin,
        "n": len(items),
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("REPORT", REPORT, "kalin", kalin, "/", len(items), flush=True)
    return 0 if kalin >= max(1, len(items) // 2) else 1


if __name__ == "__main__":
    raise SystemExit(main())
