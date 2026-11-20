# -*- coding: utf-8 -*-
"""Çırak Dilim B — yazdım = diskte var (ağ yok)."""
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

    target = REPO / "projects" / "cirak-atolyesi" / "verify_yazdim.py"
    wrong = REPO / "ilim-assistant" / "projects" / "cirak-atolyesi" / "verify_yazdim.py"

    hit = try_cirak_supervised_write(
        "görev: projects/cirak-atolyesi cirak verify_yazdim — Dilim B · tam ajan",
        REPO,
    )
    failed += _ok(bool(hit and hit.get("ok") and hit.get("verify_ok")), "supervised OK")
    failed += _ok(bool(hit and hit.get("disk_match")), "disk_match")
    failed += _ok(not bool(hit and hit.get("wrong_root")), "wrong_root false")
    failed += _ok(target.is_file(), "dosya diskte")
    failed += _ok(not wrong.is_file(), "yanlış kök yok")
    text = target.read_text(encoding="utf-8") if target.is_file() else ""
    failed += _ok("PASS cirak-B" in text, "PASS satırı dosyada")

    r = subprocess.run(
        [sys.executable, str(target)],
        cwd=str(target.parent),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    failed += _ok(r.returncode == 0 and "PASS cirak-B" in (r.stdout or ""), "çalıştırınca PASS")

    total = 7
    print(f"result: {total - failed}/{total} pass", flush=True)
    if failed:
        print("Dilim B: KIRMIZI", flush=True)
        return 1
    print("Dilim B: YEŞİL — yazdım=disk", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
