# -*- coding: utf-8 -*-
"""Motor C smoke — çift dilli ilim vitrini + atölye mutlu yolu."""
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
    from ilim_assistant.ruzgar_tercume_ilim_vitrin import (
        VERSION,
        atolye_mutlu_yol,
        measure_vitrin,
    )

    failed = 0
    failed += _ok("ilim-vitrin" in VERSION, f"ver {VERSION}")

    vit = measure_vitrin()
    failed += _ok(bool(vit.get("ok")), f"vitrin score={vit.get('score_pct')} hit={vit.get('hit')}/{vit.get('total')}")
    for c in vit.get("cards") or []:
        if not c.get("ok"):
            failed += _ok(False, f"miss {c.get('query')}")

    mut = atolye_mutlu_yol()
    for s in mut.get("steps") or []:
        failed += _ok(bool(s.get("ok")), f"step {s.get('id')} {s.get('detail')}")
    failed += _ok(bool(mut.get("ok")), "mutlu_yol")

    # API yüzey satırı
    ds = ROOT / "desktop_server.py"
    txt = ds.read_text(encoding="utf-8") if ds.is_file() else ""
    failed += _ok("/api/tercume/ilim-vitrin" in txt, "route ilim-vitrin")

    total = 3 + len(vit.get("cards") or []) + len(mut.get("steps") or []) + 2
    # recount simpler
    print(f"failed_count={failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
