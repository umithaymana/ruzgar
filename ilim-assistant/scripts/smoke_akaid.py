# -*- coding: utf-8 -*-
"""Akaid anlık cevap duman testi."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ilim_assistant.ruzgar_akaid_kutuphane import try_akaid_reply  # noqa: E402

CASES = [
    ("akaid nedir", ("inanç", "mâtürîdî")),
    ("imam maturidi kimdir", ("mâtürîdî", "tevhid")),
    ("eşari kimdir", ("eş'arî", "luma")),
    ("maturidi esari fark", ("ehl-i sünnet", "nüans")),
    ("tevhid nedir", ("birliği", "şirk")),
    ("kader nedir", ("kesb", "takdir")),
    ("kitabü tevhid nedir", ("mâtürîdî", "arapça")),
    ("el luma nedir", ("eş'arî", "kelâm")),
]


def main() -> int:
    failed = 0
    for q, needles in CASES:
        ans = try_akaid_reply(q) or ""
        low = ans.lower()
        ok = bool(ans) and any(n.lower() in low or n in ans for n in needles)
        mark = "OK" if ok else "FAIL"
        if not ok:
            failed += 1
        print(f"[{mark}] {q} -> {(ans[:140] + '…') if len(ans) > 140 else ans}")
    print(f"result: {len(CASES) - failed}/{len(CASES)} pass")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
