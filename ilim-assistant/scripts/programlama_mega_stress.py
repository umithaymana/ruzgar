#!/usr/bin/env python3
"""Blok G61–G63 — mega refactor limit smoke (16 dosya/tur)."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

WORKSPACE = _ROOT.parent


def main() -> int:
    from ilim_assistant.motorlar.programlama_faz80 import (
        effective_agent_limits,
        max_files_per_turn_mega,
        wants_mega_refactor,
    )
    from ilim_assistant.motorlar.programlama_mega_workbench import build_mega_workbench_payload

    msg = "mega refactor 10+ dosya tüm repoyu düzenle"
    if not wants_mega_refactor(msg):
        print("FAIL wants_mega_refactor")
        return 1
    lim = effective_agent_limits(msg)
    if not lim.get("mega") or int(lim.get("max_files_per_turn") or 0) < 16:
        print("FAIL mega limits", lim)
        return 1
    cap = max_files_per_turn_mega()
    if cap < 16:
        print("FAIL files per turn", cap)
        return 1
    wb = build_mega_workbench_payload(WORKSPACE)
    if not wb.get("ok"):
        print("FAIL workbench")
        return 1
    print(
        f"OK mega stress — {lim['max_turns']} tur, {cap} dosya/tur, "
        f"e2 hedef {wb.get('e2', {}).get('target_rate')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
