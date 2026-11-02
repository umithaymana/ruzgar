# -*- coding: utf-8 -*-
"""M2 smoke — Tercüme baseline (dil çifti + SRT mock + hub)."""
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
    from ilim_assistant.ses_m2_tercume_baseline import M2_VERSION, run_m2_baseline

    failed = 0
    failed += _ok("m2-tercume" in M2_VERSION, f"ver {M2_VERSION}")
    r = run_m2_baseline()
    st = r.get("stages") or {}
    for name in ("lang_pair", "srt_mock", "hub", "api_routes", "workbench"):
        s = st.get(name) or {}
        failed += _ok(bool(s.get("ok")), f"{name} detail={ {k:s.get(k) for k in s if k!='cases'} }")

    failed += _ok(bool(r.get("ok")), "baseline ok")

    doc = ROOT / "docs" / "M2_TERCUME_BASELINE_2026-11-03.md"
    failed += _ok(doc.is_file() and doc.stat().st_size > 80, f"doc {doc.name}")

    total = 8
    print(f"result: {total - failed}/{total} pass")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
