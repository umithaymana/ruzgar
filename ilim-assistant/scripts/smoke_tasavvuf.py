# -*- coding: utf-8 -*-
"""Tasavvuf anlık cevap duman testi."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ilim_assistant.ruzgar_tasavvuf_kutuphane import try_tasavvuf_reply  # noqa: E402

CASES = [
    ("tasavvuf nedir", ("ahlâk", "kalp")),
    ("ihya nedir", ("gazâlî", "ihyâ")),
    ("mesnevi nedir", ("mevlânâ", "manzum")),
    ("mektubat nedir", ("rabbânî", "mektup")),
    ("fusus nedir", ("ibnü'l-arabî", "hikmet")),
    ("kalbin hastaliklari nelerdir", ("gazâlî", "muhlik")),
    ("futuh gayb nedir", ("geylânî", "gayb")),
    ("ibn arabi kimdir", ("fusûs", "fütûhât")),
]


def main() -> int:
    failed = 0
    for q, needles in CASES:
        ans = try_tasavvuf_reply(q) or ""
        low = ans.lower()
        ok = bool(ans) and any(n.lower() in low or n in ans for n in needles)
        mark = "OK" if ok else "FAIL"
        if not ok:
            failed += 1
        preview = (ans[:130] + "…") if len(ans) > 130 else ans
        print(f"[{mark}] {q} -> {preview}")
    print(f"result: {len(CASES) - failed}/{len(CASES)} pass")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
