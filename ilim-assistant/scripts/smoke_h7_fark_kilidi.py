# -*- coding: utf-8 -*-
"""H7 — fark kilidi: ilim + raf anlık (yalnız Rüzgar moatı)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _ok(cond: bool, label: str) -> int:
    print(("OK" if cond else "FAIL"), "-", label)
    return 0 if cond else 1


def main() -> int:
    failed = 0
    from ilim_assistant.ruzgar_cografya_kutuphane import try_cografya_reply
    from ilim_assistant.ruzgar_siyer_kutuphane import try_siyer_reply

    hic = try_siyer_reply("Hicret nedir") or ""
    failed += _ok("medine" in hic.lower() and "622" in hic, "ilim/siyer Hicret")
    kd = try_cografya_reply("Karadeniz nedir") or ""
    failed += _ok("karadeniz" in kd.lower(), "raf/coğrafya Karadeniz")
    haf = ROOT / "ruzgar_genel_hafiza.json"
    failed += _ok(haf.is_file() and haf.stat().st_size > 10, "genel hafıza dosyası var")
    total = 3
    print(f"result: {total - failed}/{total} pass")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
