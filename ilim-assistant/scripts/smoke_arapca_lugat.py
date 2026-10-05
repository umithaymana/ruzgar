# -*- coding: utf-8 -*-
"""Arapça lügat anlık cevap duman testi."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ilim_assistant.ruzgar_arapca_lugat import try_arapca_lugat_reply  # noqa: E402


CASES = [
    ("صبر nedir", ("صبر", "sabret")),
    ("علم kökü", ("علم", "ilim")),
    ("rahman kökü", ("رحم", "rahmet")),
    ("kitab kökü", ("كتب", "yaz")),
    ("takva kökü", ("وقي", "takv")),
    ("nahiv nedir", ("cümle", "i‘râb")),
    ("kök nedir", ("müştak", "ünsüz")),
    ("müştak nedir", ("türet", "kök")),
    ("sarf nedir", ("türet", "vezin")),
]


def main() -> int:
    failed = 0
    for q, needles in CASES:
        ans = try_arapca_lugat_reply(q) or ""
        low = ans.lower()
        ok = bool(ans) and any(n.lower() in low or n in ans for n in needles)
        mark = "OK" if ok else "FAIL"
        if not ok:
            failed += 1
        print(f"[{mark}] {q} -> {(ans[:120] + '…') if len(ans) > 120 else ans}")
    print(f"result: {len(CASES) - failed}/{len(CASES)} pass")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
