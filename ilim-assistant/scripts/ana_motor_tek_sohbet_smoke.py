# Created by Ümit & Gökçenur
"""Smoke — Ana Motor tek sohbet yüzey→motor niyeti."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ilim_assistant.ana_motor_tek_sohbet import (  # noqa: E402
    enrich_orchestra_tek_sohbet,
    parse_surface_motor_send,
    tek_sohbet_status,
)
from ilim_assistant.ruzgar_orkestrasyon_faz_c import (  # noqa: E402
    build_genel_orchestra_preview,
)


def main() -> int:
    assert tek_sohbet_status()["enabled"] is True
    cases = [
        ("belgeyi tercümeye gönder", "tercume"),
        ("kodu programlamaya gönder", "programlama"),
        ("bunu sese gönder", "ses"),
        ("köprü: video", "video"),
        ("nasılsın", None),
        ("İslamın şartı kaçtır", None),
    ]
    fails = 0
    for msg, want in cases:
        hit = parse_surface_motor_send(msg)
        got = (hit or {}).get("motor")
        ok = got == want
        print(f"  {'OK' if ok else 'FAIL'} parse {msg!r} -> {got!r} (beklenen {want!r})")
        if not ok:
            fails += 1
        if want:
            orch = enrich_orchestra_tek_sohbet({}, msg)
            assert orch.get("quiet") is True
            assert orch.get("ui_action", {}).get("type") == "surface_handoff"
            assert orch.get("ui_action", {}).get("motor") == want
            assert orch.get("active_motor") == want
    orch2, patch = build_genel_orchestra_preview("belgeyi tercümeye gönder")
    assert orch2.get("ui_action", {}).get("motor") == "tercume"
    assert patch.get("tek_sohbet", {}).get("motor") == "tercume"
    print("  OK build_genel_orchestra_preview surface handoff")
    if fails:
        print(f"FAIL {fails}")
        return 1
    print("PASS ana_motor_tek_sohbet_smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
