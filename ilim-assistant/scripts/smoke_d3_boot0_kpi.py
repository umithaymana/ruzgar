# -*- coding: utf-8 -*-
"""D3 — BOOT=0 / recent5 KPI alanları compute_e2_stats'ta."""
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
    failed = 0
    from ilim_assistant.motorlar.programlama_faz103_e2 import compute_e2_stats

    st = compute_e2_stats(ROOT.parent)
    for key in (
        "agent_ok_recent5_rate",
        "agent_ok_recent5_total",
        "agent_ok_meets_70_recent5",
        "boot0_agent_ok_rate",
        "boot0_agent_ok_total",
    ):
        failed += _ok(key in st, f"kpi alan {key}")
    print(
        "recent5",
        st.get("agent_ok_recent5_count"),
        "/",
        st.get("agent_ok_recent5_total"),
        "=",
        st.get("agent_ok_recent5_rate"),
        "meets70",
        st.get("agent_ok_meets_70_recent5"),
    )
    print(
        "boot0",
        st.get("boot0_agent_ok_count"),
        "/",
        st.get("boot0_agent_ok_total"),
        "=",
        st.get("boot0_agent_ok_rate"),
    )
    total = 5
    print(f"result: {total - failed}/{total} pass")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
