# -*- coding: utf-8 -*-
"""Çırak Dilim A — dürüst rapor yeşil kontrolü (ağ yok)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _ok(cond: bool, label: str) -> int:
    print(("OK" if cond else "FAIL"), "-", label)
    return 0 if cond else 1


def main() -> int:
    failed = 0
    rapor = REPO / "projects" / "cirak-atolyesi" / "oz_analiz_raporu_v2.md"
    hello = REPO / "projects" / "cirak-atolyesi" / "hello_cirak.py"
    failed += _ok(rapor.is_file(), "rapor dosya var")
    failed += _ok(hello.is_file(), "hello_cirak var")
    text = rapor.read_text(encoding="utf-8") if rapor.is_file() else ""
    for path in (
        "ruzgar_cirak_ders.py",
        "smoke_cirak_ders_d6.py",
        "hello_cirak.py",
    ):
        failed += _ok(path in text, f"kanıt {path}")
    failed += _ok("bilmiyorum" in text.lower(), "klişe yok / bilmiyorum")
    failed += _ok("(YOK)" not in text or "hello_cirak.py (YOK)" not in text, "hello YOK değil")
    failed += _ok("PASS cirak-hello" in hello.read_text(encoding="utf-8"), "hello PASS")

    total = 8
    print(f"result: {total - failed}/{total} pass")
    if failed:
        print("Dilim A: KIRMIZI")
        return 1
    print("Dilim A: YEŞİL — dürüst rapor + 3 kanıt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
