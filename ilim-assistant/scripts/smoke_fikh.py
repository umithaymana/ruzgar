# -*- coding: utf-8 -*-
"""Fıkıh anlık cevap duman testi."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ilim_assistant.ruzgar_fikh_kutuphane import try_fikh_reply  # noqa: E402

CASES = [
    ("fıkıh nedir", ("hüküm", "mezhep")),
    ("hanefi mezhebi", ("hanefî", "kudûrî")),
    ("şafii nedir", ("şâfiî", "minhâc")),
    ("maliki kimdir", ("mâlik", "muvatta")),
    ("hanbeli ilmihal", ("hanbelî", "ravzü")),
    ("ilmihal nedir", ("matın", "fetva")),
    ("minhac nedir", ("nevevî", "şâfiî")),
    ("kuduri nedir", ("hanefî", "matın")),
]


def main() -> int:
    failed = 0
    for q, needles in CASES:
        ans = try_fikh_reply(q) or ""
        low = ans.lower()
        ok = bool(ans) and any(n.lower() in low or n in ans for n in needles)
        mark = "OK" if ok else "FAIL"
        if not ok:
            failed += 1
        preview = (ans[:140] + "…") if len(ans) > 140 else ans
        print(f"[{mark}] {q} -> {preview}")
    print(f"result: {len(CASES) - failed}/{len(CASES)} pass")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
