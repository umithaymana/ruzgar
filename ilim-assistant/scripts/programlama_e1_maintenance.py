#!/usr/bin/env python3
"""E1 bakım pili (Faz 91) — birleşik pil + temiz KPI."""
from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

WORKSPACE = _ROOT.parent


def main() -> int:
    from ilim_assistant.motorlar.programlama_faz91 import (
        format_e1_maintenance_report,
        run_e1_maintenance,
    )

    print("=== Faz 91 — E1 bakım ===\n")
    report = run_e1_maintenance(WORKSPACE)
    print(format_e1_maintenance_report(report))
    print()
    print(json.dumps(report, ensure_ascii=True, indent=2)[:5000])
    if not report.get("ok"):
        return 1
    aft = report.get("after") or {}
    return 0 if aft.get("meets_target") else 2


if __name__ == "__main__":
    raise SystemExit(main())
