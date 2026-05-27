#!/usr/bin/env python3
"""Canlı görev pili (Faz 86) — E1 ölçümü.

Çalıştırma (ilim-assistant kökünde):
  python scripts/programlama_live_tasks.py

API (sunucu ayakta):
  curl "http://127.0.0.1:8779/api/programlama/live-task-battery"
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

WORKSPACE = _ROOT.parent


def main() -> int:
    from ilim_assistant.motorlar.programlama_faz86 import (
        format_live_battery_report,
        run_live_task_battery,
    )

    print("=== Faz 86 — canlı görev pili ===\n")
    report = run_live_task_battery(WORKSPACE)
    print(format_live_battery_report(report))
    print()
    print(json.dumps(report, ensure_ascii=True, indent=2)[:4000])
    if not report.get("ok"):
        return 1
    if not report.get("meets_target_70"):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
