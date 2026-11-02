# -*- coding: utf-8 -*-
"""M4 smoke — Mimar baseline (atölye + hub + API)."""
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
    from ilim_assistant.ses_m4_mimar_baseline import M4_VERSION, run_m4_baseline

    failed = 0
    failed += _ok("m4-mimar" in M4_VERSION, f"ver {M4_VERSION}")
    r = run_m4_baseline()
    st = r.get("stages") or {}
    for name in ("atolye_parse", "instant", "hub", "modules", "api_routes", "context"):
        s = st.get(name) or {}
        brief = {k: s.get(k) for k in s if k != "cases"}
        failed += _ok(bool(s.get("ok")), f"{name} {brief}")

    failed += _ok(bool(r.get("ok")), "baseline ok")
    doc = ROOT / "docs" / "M4_MIMAR_BASELINE_2026-11-03.md"
    failed += _ok(doc.is_file() and doc.stat().st_size > 80, f"doc {doc.name}")

    total = 9
    print(f"result: {total - failed}/{total} pass")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
