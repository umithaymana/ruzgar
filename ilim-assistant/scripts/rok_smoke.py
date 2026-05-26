#!/usr/bin/env python3
# Created by Ümit & Gökçenur
"""ROK + Hub KPI smoke — tüm yardımcı motorlar (offline)."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def main() -> int:
    fails = 0

    def ok(msg: str) -> None:
        print(f"  OK  {msg}")

    def fail(msg: str, detail: str = "") -> None:
        nonlocal fails
        fails += 1
        print(f"  FAIL {msg}" + (f" — {detail}" if detail else ""))

    print("=== ROK KPI smoke (Faz 77) ===")

    from ilim_assistant.motorlar.ruzgar_cila_faz77 import collect_rok_kpi

    kpi = collect_rok_kpi()
    if kpi.get("ok"):
        ok("all ROK motor flags on")
    else:
        fail("ROK flags", str(kpi.get("motors")))

    from ilim_assistant.ruzgar_motor_kernel import classify_motor_intent, kernel_enabled

    if kernel_enabled():
        ok("motor kernel on")
    else:
        fail("kernel off")

    cases = [
        ("video", "bu videoyu indir https://www.youtube.com/watch?v=dQw4w9WgXcQ", "do"),
        ("ses", "alim moduna geç", "do"),
        ("okuma", "arsiv durumu", "command"),
        ("tercume", "dil listesi", "command"),
        ("hafiza", "hafıza durumu", "command"),
    ]
    for mid, msg, expect_kind in cases:
        spec = classify_motor_intent(msg, mid, mode_norm=mid)
        if spec.get("intent") == expect_kind:
            ok(f"{mid} intent {expect_kind}")
        else:
            fail(f"{mid} intent", str(spec))

    from ilim_assistant.motorlar.ana_motor_hub_faz76 import (
        is_video_download_request,
        resolve_hub_target,
    )

    if is_video_download_request(
        "indir https://www.youtube.com/watch?v=abc"
    ):
        ok("hub video download detect")
    else:
        fail("hub video detect")
    tgt, _ = resolve_hub_target(
        "bu videoyu indir https://www.youtube.com/watch?v=abc",
        {"video": True},
    )
    if tgt == "video":
        ok("hub route video")
    else:
        fail("hub route", tgt)

    tgt2, _ = resolve_hub_target("pytest geçir", {"programlama": True})
    if tgt2 == "programlama":
        ok("hub route programlama")
    else:
        fail("hub route prog", tgt2)

    print(f"\n{'PASS' if fails == 0 else 'FAIL'} ({fails} failed)")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
