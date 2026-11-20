# -*- coding: utf-8 -*-
"""Çırak Dilim D — üç dar patch ayrı yeşil (ağ yok)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _ok(cond: bool, label: str) -> int:
    print(("OK" if cond else "FAIL"), "-", label, flush=True)
    return 0 if cond else 1


def main() -> int:
    failed = 0
    from ilim_assistant.ruzgar_cirak_ders import try_cirak_supervised_write

    def run(adim: str, msg: str) -> dict:
        return try_cirak_supervised_write(msg, REPO) or {}

    h1 = run(
        "d1",
        "görev: projects/cirak-atolyesi cirak dar_patch Dilim D d1 yeni · tam ajan",
    )
    failed += _ok(bool(h1.get("ok") and h1.get("adim") == "d1"), "d1 yeşil")

    h2 = run(
        "d2",
        "görev: projects/cirak-atolyesi cirak dar_patch Dilim D d2 düzelt · tam ajan",
    )
    failed += _ok(bool(h2.get("ok") and h2.get("adim") == "d2"), "d2 yeşil")

    h3 = run(
        "d3",
        "görev: projects/cirak-atolyesi cirak dar_patch Dilim D d3 smoke · tam ajan",
    )
    failed += _ok(bool(h3.get("ok") and h3.get("adim") == "d3"), "d3 yeşil")

    d1 = REPO / "projects" / "cirak-atolyesi" / "dar_patch_d1.py"
    sm = REPO / "projects" / "cirak-atolyesi" / "smoke_dar_patch_d3.py"
    ana = REPO / "ilim-assistant" / "ilim_assistant" / "dar_patch_d1.py"
    text = d1.read_text(encoding="utf-8") if d1.is_file() else ""
    failed += _ok("def carp" in text, "d1 carp var")
    failed += _ok("return int(a) * int(b)" in text, "d2 int güvenli")
    failed += _ok(sm.is_file(), "d3 smoke dosya")
    failed += _ok(not ana.is_file(), "ana paket yok")

    r = subprocess.run(
        [sys.executable, str(sm)],
        cwd=str(sm.parent),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    failed += _ok(r.returncode == 0 and "PASS cirak-D3" in (r.stdout or ""), "d3 PASS")

    total = 8
    print(f"result: {total - failed}/{total} pass", flush=True)
    if failed:
        print("Dilim D: KIRMIZI", flush=True)
        return 1
    print("Dilim D: YEŞİL — d1+d2+d3", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
