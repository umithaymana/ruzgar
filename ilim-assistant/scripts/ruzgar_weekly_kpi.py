#!/usr/bin/env python3
# Created by Ümit & Gökçenur
"""Haftalık KPI raporu (Faz 60)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def main() -> int:
    ws = (os.environ.get("RUZGAR_WORKSPACE_ROOT") or "").strip() or str(_ROOT.parent)
    from ilim_assistant.motorlar.programlama_faz60 import (
        format_weekly_kpi_report_text,
        generate_weekly_kpi_report,
    )

    report = generate_weekly_kpi_report(ws)
    print(format_weekly_kpi_report_text(report))
    if report.get("saved_path"):
        print(f"JSON: {report['saved_path']}")
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
