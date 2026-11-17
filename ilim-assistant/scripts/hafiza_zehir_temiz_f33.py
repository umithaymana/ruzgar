# Created by Ümit & Gökçenur
"""
F3.3 — genel hafızadan miss/timeout/zehir kartlarını temizle (yazmaz: --apply).

Kullanım:
  python scripts/hafiza_zehir_temiz_f33.py
  python scripts/hafiza_zehir_temiz_f33.py --apply
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "ruzgar_genel_hafiza.json"

_MISS = re.compile(
    r"(?:bulamad[ıi]m|öğretir\s+misin|ogretir\s+misin|süre\s+yetmedi|sure\s+yetmedi|"
    r"net\s+ve\s+güvenilir\s+bir\s+yanıt\s+veremedim|ogrenmedim|öğrenmedim)",
    re.I,
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not PATH.is_file():
        print("yok:", PATH)
        return 1
    data = json.loads(PATH.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        print("beklenen liste değil")
        return 1
    keep = []
    removed = 0
    for it in data:
        if not isinstance(it, dict):
            keep.append(it)
            continue
        cevap = str(it.get("cevap") or "")
        if _MISS.search(cevap):
            removed += 1
            continue
        keep.append(it)
    print(f"adet={len(data)} kalacak={len(keep)} silinecek={removed}")
    if args.apply and removed:
        bak = PATH.with_suffix(
            f".bak_zehir_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        )
        bak.write_text(PATH.read_text(encoding="utf-8"), encoding="utf-8")
        PATH.write_text(json.dumps(keep, ensure_ascii=False, indent=2), encoding="utf-8")
        print("yazıldı; yedek:", bak.name)
    elif not args.apply:
        print("(kuru koşu — yazmak için --apply)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
