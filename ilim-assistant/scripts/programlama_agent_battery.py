#!/usr/bin/env python3
"""Ajan görev pili (Faz 88) — E1 gerçek döngü ölçümü.

Çalıştırma (ilim-assistant kökünde):
  python scripts/programlama_agent_battery.py
  python scripts/programlama_agent_battery.py --live
  python scripts/programlama_agent_battery.py --combined

API:
  GET /api/programlama/agent-task-battery
  GET /api/programlama/agent-task-battery?live=1
  GET /api/programlama/combined-e1-battery
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
    p = argparse.ArgumentParser(description="Faz 88 ajan görev pili")
    p.add_argument(
        "--live",
        action="store_true",
        help="Ollama/Groq/Gemini ile canlı ajan senaryoları",
    )
    p.add_argument(
        "--combined",
        action="store_true",
        help="Faz 86 + 88 birleşik E1 raporu",
    )
    args = p.parse_args()

    if args.combined:
        from ilim_assistant.motorlar.programlama_faz88 import (
            format_combined_e1_report,
            run_combined_e1_battery,
        )

        print("=== Birleşik E1 pili (Faz 86+88) ===\n")
        bundle = run_combined_e1_battery(WORKSPACE, live_llm=args.live)
        print(format_combined_e1_report(bundle))
        print()
        print(json.dumps(bundle, ensure_ascii=True, indent=2)[:5000])
        if not bundle.get("ok"):
            return 1
        return 0 if bundle.get("combined_meets_target_70") else 2

    from ilim_assistant.motorlar.programlama_faz88 import (
        format_agent_battery_report,
        run_agent_task_battery,
    )

    print("=== Faz 88 — ajan görev pili ===\n")
    report = run_agent_task_battery(WORKSPACE, live_llm=args.live)
    print(format_agent_battery_report(report))
    print()
    print(json.dumps(report, ensure_ascii=True, indent=2)[:5000])
    if not report.get("ok"):
        return 1
    target = report.get("meets_target_70")
    if args.live:
        target = target and report.get("offline_meets_target_70", True)
    else:
        target = report.get("offline_meets_target_70", report.get("meets_target_70"))
    return 0 if target else 2


if __name__ == "__main__":
    raise SystemExit(main())
