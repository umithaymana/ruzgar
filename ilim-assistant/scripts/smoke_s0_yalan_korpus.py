# -*- coding: utf-8 -*-
"""S0 smoke — yalan/uydurma korpusu."""
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
    from ilim_assistant.sohbet_yalan_korpus import (
        S0_VERSION,
        cases_needing_live,
        cases_needing_number,
        list_yalan_cases,
        validate_korpus,
    )

    failed = 0
    failed += _ok("s0-v1" in S0_VERSION or "korpus-s0" in S0_VERSION, f"ver {S0_VERSION}")
    errs = validate_korpus()
    failed += _ok(not errs, f"validate {errs[:3] if errs else 'ok'}")
    cases = list_yalan_cases()
    n = len(cases)
    failed += _ok(20 <= n <= 40, f"count={n}")
    live = cases_needing_live()
    num = cases_needing_number()
    failed += _ok(len(live) >= 5, f"live>={len(live)}")
    failed += _ok(len(num) >= 8, f"number>={len(num)}")
    tips = {c.get("tip") for c in cases}
    failed += _ok(len(tips) >= 8, f"tip çeşit={len(tips)}")
    # örnek id’ler
    ids = {c["id"] for c in cases}
    failed += _ok("S0-01" in ids and "S0-28" in ids, "uç id’ler")
    failed += _ok(
        any(c.get("forbid") and "uydurma_sayi" in c["forbid"] for c in cases),
        "forbid uydurma_sayi var",
    )

    total = 8
    print(f"result: {total - failed}/{total} pass · cases={n} live={len(live)} number={len(num)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
