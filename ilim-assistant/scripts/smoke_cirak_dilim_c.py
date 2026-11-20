# -*- coding: utf-8 -*-
"""Çırak Dilim C — çok satır / PASS kalıbı dışı (ağ yok)."""
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

    target = REPO / "projects" / "cirak-atolyesi" / "cok_satir_modul.py"
    ana = REPO / "ilim-assistant" / "ilim_assistant" / "cok_satir_modul.py"

    hit = try_cirak_supervised_write(
        "görev: projects/cirak-atolyesi cirak cok_satir — Dilim C · tam ajan",
        REPO,
    )
    failed += _ok(bool(hit and hit.get("ok") and hit.get("verify_ok")), "supervised OK")
    failed += _ok(target.is_file(), "dosya atölyede")
    failed += _ok(not ana.is_file(), "ana pakette yok")
    text = target.read_text(encoding="utf-8") if target.is_file() else ""
    failed += _ok('"""Çok satırlı' in text, "docstring")
    failed += _ok("def ozet_satir" in text, "fonksiyon")
    failed += _ok("MODUL_BASLIK" in text, "başlık sabiti")
    failed += _ok('print("PASS' not in text, "PASS kalıbı yok")

    r = subprocess.run(
        [sys.executable, str(target)],
        cwd=str(target.parent),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    failed += _ok(
        r.returncode == 0 and "docstring+fonksiyon" in (r.stdout or ""),
        "çalıştırınca özet",
    )

    total = 8
    print(f"result: {total - failed}/{total} pass", flush=True)
    if failed:
        print("Dilim C: KIRMIZI", flush=True)
        return 1
    print("Dilim C: YEŞİL — cok_satir_modul", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
