#!/usr/bin/env python3
"""E2 çok dosya pili (Faz 103).

Çalıştırma (ilim-assistant kökünde):
  python scripts/programlama_e2_battery.py
  python scripts/programlama_e2_battery.py --live
  python scripts/programlama_e2_battery.py --combined

API:
  GET /api/programlama/combined-e2-battery
  GET /api/programlama/combined-e2-battery?live=1
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
    p = argparse.ArgumentParser(description="Faz 103 E2 çok dosya pili")
    p.add_argument(
        "--live",
        action="store_true",
        help="Ollama/Groq/Gemini ile canlı çok dosya ajan",
    )
    p.add_argument(
        "--combined",
        action="store_true",
        help="Offline + canlı birleşik (canlı yoksa offline oranı)",
    )
    args = p.parse_args()

    from ilim_assistant.motorlar.programlama_faz103_e2 import (
        format_e2_battery_report,
        run_combined_e2_battery,
        run_e2_offline_battery,
    )

    if args.live or args.combined:
        print("=== E2 birleşik pil (Faz 103) ===\n")
        bundle = run_combined_e2_battery(WORKSPACE, live_llm=bool(args.live))
        print(format_e2_battery_report(bundle))
        print()
        print(json.dumps(bundle, ensure_ascii=True, indent=2, default=str)[:6000])
        if not bundle.get("ok"):
            return 1
        return 0 if bundle.get("combined_meets_target_90") else 2

    print("=== E2 offline pil (Faz 103) ===\n")
    report = run_e2_offline_battery(WORKSPACE)
    print(format_e2_battery_report(report))
    print()
    print(json.dumps(report, ensure_ascii=True, indent=2, default=str)[:6000])
    if not report.get("ok"):
        return 1
    return 0 if report.get("meets_target_90") else 2


if __name__ == "__main__":
    raise SystemExit(main())
