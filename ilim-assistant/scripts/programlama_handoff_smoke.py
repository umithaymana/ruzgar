#!/usr/bin/env python3
"""Blok H — handoff workbench smoke."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
WORKSPACE = _ROOT.parent


def main() -> int:
    from ilim_assistant.motorlar.programlama_handoff_workbench import (
        build_handoff_workbench_payload,
    )

    wb = build_handoff_workbench_payload(
        WORKSPACE,
        message="fastapi projesinde pytest geçir",
    )
    if not wb.get("ok"):
        print("FAIL workbench")
        return 1
    if not wb.get("handoff", {}).get("ok"):
        print("FAIL handoff packet", wb.get("handoff"))
        return 1
    if len(wb.get("motor_chain") or []) < 5:
        print("FAIL motor chain")
        return 1
    if not wb.get("manifest", {}).get("programlama_tag"):
        print("FAIL manifest tag")
        return 1
    print(
        f"OK handoff v4 — scope={wb['handoff'].get('scope_rel')} "
        f"e4={wb['e4'].get('recent_success_rate')} chain={len(wb['motor_chain'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
