#!/usr/bin/env python3
# Created by Ümit & Gökçenur
"""
Rüzgar parity smoke — 8/8 KPI (Faz 54).

Kullanım:
  python scripts/ruzgar_parity_smoke.py
  python scripts/ruzgar_parity_smoke.py --quick
  python scripts/ruzgar_parity_smoke.py --groq-e2e
  python scripts/ruzgar_parity_smoke.py --workspace "D:/CURSOR PROJELER/YAPAY ZEKA"
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _default_workspace() -> str:
    env = (os.environ.get("RUZGAR_WORKSPACE_ROOT") or "").strip()
    if env:
        return env
    return str(_ROOT.parent)


def main() -> int:
    ap = argparse.ArgumentParser(description="Rüzgar parity smoke 8/8 (Faz 54)")
    ap.add_argument(
        "--workspace",
        default=_default_workspace(),
        help="Workspace kökü",
    )
    ap.add_argument(
        "--quick",
        action="store_true",
        help="Hızlı mod (cursor senaryoları atlanır)",
    )
    ap.add_argument(
        "--groq-e2e",
        action="store_true",
        help="Son kontrolde Groq function-calling ping (opsiyonel)",
    )
    args = ap.parse_args()

    from ilim_assistant.motorlar.programlama_faz54 import (
        FAZ54_VERSION,
        run_parity_smoke_and_persist,
        save_parity_smoke_json,
    )

    mode = "quick" if args.quick else "full"
    report = run_parity_smoke_and_persist(
        args.workspace,
        mode=mode,
        groq_e2e=args.groq_e2e,
    )
    path = save_parity_smoke_json(report)
    print(f"=== Rüzgar parity smoke ({FAZ54_VERSION}) ===")
    print(f"Mod: {mode} · geçen: {report.passed}/{report.total} · süre: {report.elapsed_sec:.1f}s")
    for c in report.checks:
        mark = "OK" if c.ok else "FAIL"
        line = f"  [{mark}] {c.label} - {c.detail}"
        try:
            print(line)
        except UnicodeEncodeError:
            print(line.encode("ascii", errors="replace").decode("ascii"))
    if path:
        print(f"JSON: {path}")
    if report.ok:
        print("SONUÇ: 8/8 GEÇTİ")
        return 0
    print("SONUÇ: KIRMIZI")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
