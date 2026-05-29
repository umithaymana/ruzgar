#!/usr/bin/env python3
"""Blok I — yerel zincir workbench smoke (API'siz)."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
WORKSPACE = _ROOT.parent


def main() -> int:
    from ilim_assistant.motorlar.programlama_local_workbench import (
        build_local_workbench_payload,
        e3_text_only_target,
        ollama_only_chain_ids,
    )

    wb = build_local_workbench_payload(WORKSPACE)
    if not wb.get("ok"):
        print("FAIL workbench")
        return 1

    otest = wb.get("ollama_only_test") or {}
    if not otest.get("ok"):
        print("FAIL ollama-only self test", otest)
        return 1

    expected = ollama_only_chain_ids()
    if expected[0] != "kod":
        print("FAIL ollama-only chain head", expected)
        return 1

    chain = wb.get("chain", {}).get("effective") or []
    modes = wb.get("modes") or {}
    if modes.get("prog_local_first") and modes.get("ollama_available"):
        if chain and chain[0] not in ("kod", "denge", "hizli"):
            print("FAIL local-first chain head", chain)
            return 1

    if not wb.get("manifest", {}).get("programlama_tag"):
        print("FAIL manifest tag")
        return 1

    e3 = wb.get("e3") or {}
    if float(e3.get("target_text_only_rate") or 0) > e3_text_only_target() + 0.001:
        print("FAIL e3 target")
        return 1

    fc = wb.get("fc_stress") or {}
    print(
        f"OK local v1 — chain={','.join(chain[:4]) or '?'} "
        f"ollama={modes.get('ollama_available')} "
        f"e3<=%{int(e3_text_only_target()*100)} "
        f"fc={fc.get('provider', '?')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
