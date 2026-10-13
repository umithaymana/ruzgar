# -*- coding: utf-8 -*-
"""Bilgisayar mühendisliği anlık cevap — çakışma dumanı.

Beklenen vuruşlar bu rafta kalır. Teknoloji, felsefe ve bilim sözleri çalınmaz.
"""
from __future__ import annotations

import json
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ilim_assistant.ruzgar_bilgisayar_kutuphane import (
    programlama_kavram_notu,
    try_bilgisayar_reply,
)
from ilim_assistant.ruzgar_bilim_kutuphane import try_bilim_reply
from ilim_assistant.ruzgar_felsefe_kutuphane import try_felsefe_reply
from ilim_assistant.ruzgar_teknoloji_kutuphane import try_teknoloji_reply


def fold(s: str) -> str:
    t = unicodedata.normalize("NFKD", s or "")
    t = "".join(c for c in t if not unicodedata.combining(c))
    return t.lower().strip()


HITS = [
    "islemci nedir",
    "von neumann nedir",
    "saat darbesi nedir",
    "kati hal diski nedir",
    "cevre birimi nedir",
    "kernel nedir",
    "sanal bellek nedir",
    "dosya sistemi nedir",
    "derleyici nedir",
    "ag yigini nedir",
    "veri yapisi nedir",
    "yigin nedir",
    "hash tablosu nedir",
    "birim testi nedir",
    "ayrik matematik nedir",
    "hata ayiklama nedir",
]

MISSES = [
    "fotosentez nedir",
    "isletim sistemi nedir",
    "dosya nedir",
    "internet nedir",
    "mantik nedir",
    "atom nedir",
    "bilgisayar nedir",
    "os nedir",
    "algoritma nedir",
]

OTHERS = [
    ("isletim sistemi nedir", try_teknoloji_reply),
    ("bilgisayar nedir", try_teknoloji_reply),
    ("dosya nedir", try_teknoloji_reply),
    ("mantik nedir", try_felsefe_reply),
    ("fotosentez nedir", try_bilim_reply),
    ("atom nedir", try_bilim_reply),
]


def _aliases(path: Path) -> set[str]:
    out: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        out.add(fold(row.get("baslik") or ""))
        for a in row.get("aliases") or []:
            out.add(fold(a))
    out.discard("")
    return out


def main() -> int:
    fail = 0
    for q in HITS:
        hit = try_bilgisayar_reply(q)
        ok = bool(hit) and len(hit) >= 400
        fail += int(not ok)
        print(("OK" if ok else "FAIL"), "HIT", q, "len", len(hit or ""))
    for q in MISSES:
        hit = try_bilgisayar_reply(q)
        ok = hit is None
        fail += int(not ok)
        print(("OK" if ok else "FAIL"), "MISS", q, "->" , (hit or "")[:60])
    for q, fn in OTHERS:
        hit = fn(q)
        ok = bool(hit)
        fail += int(not ok)
        print(("OK" if ok else "FAIL"), "OTHER", q)

    bm = ROOT / "knowledge" / "ortak_kaynak" / "alanlar" / "bilgisayar_muhendisligi" / "kavramlar_bilgisayar.jsonl"
    tk = ROOT / "knowledge" / "ortak_kaynak" / "alanlar" / "teknoloji" / "kavramlar_teknoloji.jsonl"
    overlap = sorted(_aliases(bm) & _aliases(tk))
    if overlap:
        fail += 1
        print("FAIL alias overlap", overlap)
    else:
        print("OK alias overlap yok")
    note_cases = [
        ("sanal bellek nasil calisir", True),
        ("birim testini anlat", True),
        ("pytest calistir", False),
        ("@@write main.py", False),
        ("fotosentez nedir", False),
    ]
    for q, expect in note_cases:
        note = programlama_kavram_notu(q)
        ok = bool(note) == expect
        fail += int(not ok)
        print(("OK" if ok else "FAIL"), "NOTE", q, "->", "VAR" if note else "YOK")
    print(f"smoke fail={fail}")
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
