#!/usr/bin/env python3
"""Smoke — Faz 39 E2 yazım mandate (keşif yokken de çok dosyada zorla)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from ilim_assistant.motorlar.programlama_faz39 import (
        build_write_mandate_message,
        turn_had_discovery,
    )

    msg = build_write_mandate_message(
        goal="app/util.py ve app/service.py VERSION 2.0.0 pytest gecir",
        scope_rel="projects/demo",
        tool_block="",
        turn=2,
    )
    if "ZORUNLU YAZIM" not in msg:
        print("FAIL mandate header")
        return 1
    if "E2" not in msg and "çok dosya" not in msg and "cok dosya" not in msg.lower():
        # ascii fold in message uses E2/çok
        if "çok dosya" not in msg and "E2" not in msg:
            print("FAIL multi hint", msg[:200])
            return 1
    assert not turn_had_discovery([])
    # Keşif yok + çok dosya → run_write_mandate_followup giriş kapısı force_e2
    # (tam LLM çağrısı yok — yalnız metin + kapı mantığı)
    force = False
    goal = "app/a.py ve app/b.py duzelt"
    try:
        from ilim_assistant.motorlar.programlama_faz56 import looks_like_multi_file_task
        from ilim_assistant.motorlar.programlama_faz85 import goal_wants_agent_path

        force = looks_like_multi_file_task(goal) or goal_wants_agent_path(goal)
    except Exception as exc:
        print("FAIL import", exc)
        return 1
    if not force:
        print("FAIL force_e2 gate")
        return 1
    print("PASS programlama_faz39_mandate_smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
