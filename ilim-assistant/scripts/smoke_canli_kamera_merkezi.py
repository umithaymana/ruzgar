# -*- coding: utf-8 -*-
"""Canlı Kamera Merkezi smoke."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ilim_assistant.ruzgar_canli_kamera_merkezi import (  # noqa: E402
    UZAY_KAMERALAR,
    execute_canli_intent,
    looks_like_canli_kamera,
)
from ilim_assistant.sahne_super_el import _norm, resolve_super_el  # noqa: E402


def fail(m: str) -> None:
    print("FAIL:", m)
    raise SystemExit(1)


def main() -> None:
    phrases = [
        ("yakinimdaki canli kameralari listele", "cam_list"),
        ("en yakin canli kameralar", "cam_list"),
        ("trafik kameralari", "cam_list"),
        ("hava durumu kameralari", "cam_list"),
        ("paris canli kameralar", "cam_list"),
        ("uzay kameralari", "cam_list_space"),
        ("nasa canli yayinlarini ac", "cam_open_nasa"),
        ("iss kamerasini ac", "cam_open_iss"),
        ("dunya kamerasini ac", "cam_open_earth_view"),
        ("tam ekran ac", "cam_layout_full"),
        ("dort kamera ac", "cam_layout_4"),
        ("sekiz kamera ac", "cam_layout_8"),
        ("ac", "cam_open"),
    ]
    for phrase, expect in phrases:
        n = _norm(phrase)
        got = looks_like_canli_kamera(n)
        if not got or got.get("action") != expect:
            # cam_open_earth_view maps via execute to mode_4d
            if expect == "cam_open_earth_view" and got and got.get("action") == expect:
                continue
            fail(f"{phrase!r} -> {got} want action={expect}")

    se = resolve_super_el("uzay kameralari")
    if not se.get("ok") or not se.get("canli_kamera"):
        fail("super-el uzay")
    if "NASA TV" not in str(se.get("reply") or ""):
        fail("uzay reply")

    se2 = resolve_super_el("trafik kameralari")
    if not se2.get("ok") or se2.get("action") != "cam_list":
        fail("trafik super-el")

    pack = execute_canli_intent({"action": "cam_list", "kategori": "trafik", "nearby": False})
    if not pack.get("ok"):
        fail("trafik pack")
    # Fintraffic bağlıysa count>0 beklenir (ağ)
    print("trafik_count", pack.get("count"), "note", (pack.get("note") or "")[:60])

    if len(UZAY_KAMERALAR) < 3:
        fail("uzay katalog")

    masa = (ROOT.parent / "ruzgar-desktop" / "ruzgar-masa.js").read_text(encoding="utf-8")
    if "paintCanliKameraMosaic" not in masa:
        fail("masa mosaic")
    app = (ROOT.parent / "ruzgar-desktop" / "app.js").read_text(encoding="utf-8")
    if "canli_kamera" not in app:
        fail("app canli")

    print("OK: canli-kamera-merkezi smoke")


if __name__ == "__main__":
    main()
