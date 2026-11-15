# -*- coding: utf-8 -*-
"""CameraRig smoke — hardcode yer yok; preset + niyet."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ilim_assistant.ruzgar_kamera_rig import (  # noqa: E402
    EARTH_PRESETS,
    SPACE_PRESETS,
    catalog,
    get_preset,
    looks_like_camera_mode,
)
from ilim_assistant.sahne_dunya_gezgini import looks_like_tour_control  # noqa: E402
from ilim_assistant.sahne_super_el import _norm  # noqa: E402


def fail(m: str) -> None:
    print("FAIL:", m)
    raise SystemExit(1)


def main() -> None:
    if len(EARTH_PRESETS) != 6:
        fail("earth presets != 6")
    if len(SPACE_PRESETS) != 6:
        fail("space presets != 6")
    for mid in (
        "yuruyus",
        "bisiklet",
        "arac",
        "drone",
        "serbest",
        "sinematik",
        "yorunge",
        "rover",
    ):
        p = get_preset(mid)
        if not p or "speed_mps" not in p:
            fail("preset eksik: " + mid)
    phrases = [
        ("yuruyus moduna gec", "tour_camera_yuruyus"),
        ("bisiklet moduna gec", "tour_camera_bisiklet"),
        ("arac moduna gec", "tour_camera_arac"),
        ("drone moduna gec", "tour_camera_drone"),
        ("serbest pilot ol", "tour_camera_serbest"),
        ("sinematik mod", "tour_camera_sinematik"),
        ("aya gec", "tour_body_moon"),
        ("marsa gec", "tour_body_mars"),
        ("marsa uzay", "tour_body_space"),
        ("yorunge moduna gec", "tour_camera_yorunge"),
    ]
    for phrase, expect in phrases:
        n = _norm(phrase)
        got = looks_like_tour_control(n) or looks_like_camera_mode(n)
        if got != expect:
            fail(f"{phrase!r} -> {got!r} want {expect!r}")
    cat = catalog()
    if not cat.get("ok") or not cat.get("earth"):
        fail("catalog")
    hv = (ROOT.parent / "ruzgar-desktop" / "harita-viewer.html").read_text(
        encoding="utf-8"
    )
    for token in (
        "CAMERA_PRESETS",
        "setCameraMode",
        "cameraRigTickBlend",
        "walkSyncEyeHeight",
        "cameraRigCloseStreetOverlay",
        "cameraRigAnchorLatLon",
        'act.indexOf("camera_")',
        'act.indexOf("body_")',
    ):
        if token not in hv:
            fail("harita-viewer eksik: " + token)
    masa = (ROOT.parent / "ruzgar-desktop" / "ruzgar-masa.js").read_text(
        encoding="utf-8"
    )
    if "tour_camera_drone" not in masa:
        fail("masa camera actions")
    print("OK: kamera-rig smoke")


if __name__ == "__main__":
    main()
