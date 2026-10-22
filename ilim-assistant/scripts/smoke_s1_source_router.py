# -*- coding: utf-8 -*-
"""S1 smoke — SourceRouter vs S0 yalan korpusu."""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _ok(cond: bool, label: str) -> int:
    print(("OK" if cond else "FAIL"), "-", label)
    return 0 if cond else 1


def main() -> int:
    from ilim_assistant.sohbet_source_router import (
        S1_VERSION,
        classify_source_intent,
        router_enabled,
    )
    from ilim_assistant.sohbet_yalan_korpus import list_yalan_cases

    failed = 0
    failed += _ok("source-router-s1" in S1_VERSION, f"ver {S1_VERSION}")
    failed += _ok(router_enabled(), "RUZGAR_SOURCE_ROUTER açık")

    cases = list_yalan_cases()
    failed += _ok(len(cases) >= 20, f"korpus n={len(cases)}")

    bool_fields = ("needs_live", "needs_number", "library_ok", "allow_parametric")
    mismatches: list[str] = []
    tip_miss = 0
    t0 = time.perf_counter()
    for c in cases:
        d = classify_source_intent(str(c["message"]))
        for f in bool_fields:
            if bool(getattr(d, f)) != bool(c.get(f)):
                mismatches.append(
                    f"{c['id']}.{f}: got={getattr(d, f)} want={c.get(f)}"
                )
        if d.tip != c.get("tip"):
            tip_miss += 1
            mismatches.append(f"{c['id']}.tip: got={d.tip} want={c.get('tip')}")
    elapsed = (time.perf_counter() - t0) * 1000.0
    per = elapsed / max(len(cases), 1)

    failed += _ok(not mismatches, f"alan hizası miss={len(mismatches)}")
    if mismatches:
        for m in mismatches[:12]:
            print("  ·", m)
        if len(mismatches) > 12:
            print(f"  · … +{len(mismatches) - 12}")

    failed += _ok(tip_miss == 0, f"tip exact miss={tip_miss}")
    failed += _ok(per < 50.0, f"ort ms/case={per:.3f} (<50)")
    failed += _ok(elapsed < 1000.0, f"toplam ms={elapsed:.2f} (<1000)")

    # struct zorunlu alanlar
    sample = classify_source_intent("bugün dolar kaç TL")
    keys = set(sample.to_dict())
    need = {
        "tip",
        "needs_live",
        "needs_number",
        "library_ok",
        "allow_parametric",
        "preferred_source",
        "reason",
        "elapsed_ms",
        "version",
    }
    failed += _ok(need <= keys, f"struct keys={sorted(need & keys)}")

    # prepare_turn kancası
    orch: dict = {}
    from ilim_assistant.sohbet_source_router import attach_source_router

    attach_source_router("os nedir", orch)
    failed += _ok(
        isinstance(orch.get("source_router"), dict)
        and orch["source_router"].get("tip") == "kisa_kavram",
        "attach orchestration",
    )

    total = 8
    print(
        f"result: {total - failed}/{total} pass · cases={len(cases)} "
        f"tip_miss={tip_miss} bool_miss={len([m for m in mismatches if '.tip' not in m])}"
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
