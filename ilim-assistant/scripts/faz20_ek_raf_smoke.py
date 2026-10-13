# -*- coding: utf-8 -*-
"""Ek raflar anlık dumanı — her raf vurur, komşu rafların sözü çalınmaz."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ilim_assistant.ruzgar_bilim_kutuphane import try_bilim_reply
from ilim_assistant.ruzgar_cografya_kutuphane import try_cografya_reply
from ilim_assistant.ruzgar_ek_raflar import try_ek_raf_reply
from ilim_assistant.ruzgar_felsefe_kutuphane import try_felsefe_reply

HITS = [
    "turev nedir",
    "olasilik nedir",
    "kirchhoff kanunu",
    "paralaks",
    "levha tektonigi",
    "sera etkisi",
    "dolasim sistemi",
    "sesbilim",
    "makam",
    "tabakalasma",
    "kuvvetler ayriligi",
    "firsat maliyeti",
    "hukuk devleti",
    "mufredat",
]

MISSES = [
    "fotosentez nedir",
    "atom nedir",
    "hucre nedir",
    "ekosistem nedir",
    "iklim nedir",
    "mantik nedir",
    "isletim sistemi nedir",
    "dosya nedir",
]


def main() -> int:
    fail = 0
    for q in HITS:
        hit = try_ek_raf_reply(q if q.endswith("nedir") or " " in q else q + " nedir")
        ok = bool(hit) and len(hit) >= 400
        fail += int(not ok)
        print(("OK" if ok else "FAIL"), "HIT", q, "len", len(hit or ""))
    for q in MISSES:
        hit = try_ek_raf_reply(q)
        ok = hit is None
        fail += int(not ok)
        print(("OK" if ok else "FAIL"), "MISS", q)
    others = [
        ("fotosentez nedir", try_bilim_reply),
        ("hucre nedir", try_bilim_reply),
        ("iklim nedir", try_cografya_reply),
        ("mantik nedir", try_felsefe_reply),
    ]
    for q, fn in others:
        hit = fn(q)
        ok = bool(hit)
        fail += int(not ok)
        print(("OK" if ok else "FAIL"), "OTHER", q)
    print(f"smoke fail={fail}")
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
