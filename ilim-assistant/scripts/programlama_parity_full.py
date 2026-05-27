#!/usr/bin/env python3
"""Haftalık parity full (Faz 89 / E6).

Çalıştırma (ilim-assistant kökünde):
  python scripts/programlama_parity_full.py
  python scripts/programlama_parity_full.py --force

API:
  POST /api/programlama/weekly-parity-full?force=1
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

WORKSPACE = _ROOT.parent


def main() -> int:
    ap = argparse.ArgumentParser(description="Faz 89 haftalık parity full")
    ap.add_argument(
        "--force",
        action="store_true",
        help="Haftalık kilidi atla",
    )
    args = ap.parse_args()

    from ilim_assistant.motorlar.programlama_faz89 import (
        format_weekly_parity_report,
        run_weekly_parity_battery,
    )

    print("=== Faz 89 — haftalık parity full ===\n")
    report = run_weekly_parity_battery(WORKSPACE, force=args.force)
    print(format_weekly_parity_report(report))
    print()
    print(json.dumps(report, ensure_ascii=True, indent=2)[:6000])
    if not report.get("ok"):
        return 1
    if report.get("skipped"):
        return 0
    return 0 if report.get("meets_target_8_8") else 2


if __name__ == "__main__":
    raise SystemExit(main())
