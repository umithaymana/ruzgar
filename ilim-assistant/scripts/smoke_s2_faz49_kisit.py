# -*- coding: utf-8 -*-
"""S2 smoke — Faz49 kısıt: sayı/güncelde kaynaksız hızlı LLM yok."""
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
    from ilim_assistant.ana_motor_fast import should_fast_direct_llm
    from ilim_assistant.ana_motor_plan import looks_like_fast_llm_fact_question
    from ilim_assistant.sohbet_source_router import blocks_faz49_fast
    from ilim_assistant.sohbet_yalan_korpus import list_yalan_cases

    failed = 0
    cases = list_yalan_cases()
    blocked = [c for c in cases if c.get("needs_live") or c.get("needs_number")]
    soft = [
        c
        for c in cases
        if not c.get("needs_live")
        and not c.get("needs_number")
        and c.get("tip") in ("kisa_kavram",)
    ]

    failed += _ok(len(blocked) >= 10, f"blocked pool={len(blocked)}")

    miss_block: list[str] = []
    for c in blocked:
        msg = str(c["message"])
        if not blocks_faz49_fast(msg):
            miss_block.append(f"{c['id']} blocks")
        if looks_like_fast_llm_fact_question(msg):
            miss_block.append(f"{c['id']} fast_fact")
        if should_fast_direct_llm(msg, "genel", None, history=None):
            miss_block.append(f"{c['id']} fast_path")
    failed += _ok(not miss_block, f"sayı/güncel yasak miss={len(miss_block)}")
    for m in miss_block[:10]:
        print("  ·", m)

    # Kısa kavram hâlâ Faz49 adayı olabilir (RAG-first ayrıca açık)
    soft_ok = 0
    for c in soft[:4]:
        if looks_like_fast_llm_fact_question(str(c["message"])) or not blocks_faz49_fast(
            str(c["message"])
        ):
            soft_ok += 1
    failed += _ok(soft_ok >= 2, f"kisa_kavram soft_ok={soft_ok}")

    # Elle örnekler
    failed += _ok(
        blocks_faz49_fast("Türkiye'de kaç üniversite var webten bak"),
        "örnek web+kaç",
    )
    failed += _ok(blocks_faz49_fast("bugün dolar kaç TL"), "örnek dolar")
    failed += _ok(not blocks_faz49_fast("os nedir"), "örnek os nedir serbest")
    failed += _ok(
        not looks_like_fast_llm_fact_question("Osmanlı kaç padişah yönetti"),
        "tarih sayı ≠ fast",
    )
    failed += _ok(
        looks_like_fast_llm_fact_question("uzay nedir")
        or not blocks_faz49_fast("uzay nedir"),
        "uzay nedir aday",
    )

    total = 8
    print(f"result: {total - failed}/{total} pass · blocked={len(blocked)} soft={len(soft)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
