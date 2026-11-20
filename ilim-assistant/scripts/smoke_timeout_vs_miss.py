# -*- coding: utf-8 -*-
"""Smoke — süre dolunca TIMEOUT; gerçek boşlukta MISS (öğret)."""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _ok(cond: bool, label: str) -> int:
    print(("OK" if cond else "FAIL"), "-", label)
    return 0 if cond else 1


def main() -> int:
    failed = 0
    from ilim_assistant.ruzgar_umed_kurallari import MISS_PHRASE, TIMEOUT_PHRASE
    from ilim_assistant.ruzgar_umed_cevap_emri import (
        begin_turn_budget,
        set_turn_deadline,
        umed_empty_chain_reply,
        umed_miss_reply,
        umed_timeout_reply,
    )
    from ilim_assistant.ruzgar_tur_teshis_f0 import MISS_NO_HITS, MISS_TIMEOUT, classify_miss
    from ilim_assistant.ruzgar_egitim import should_emit_miss_reply, wrap_miss_if_needed

    failed += _ok("süre yetmedi" in TIMEOUT_PHRASE.lower(), "TIMEOUT metni")
    failed += _ok("öğretir misin" in MISS_PHRASE.lower(), "MISS metni")
    failed += _ok(umed_timeout_reply() == TIMEOUT_PHRASE, "umed_timeout_reply")
    failed += _ok(umed_miss_reply() == MISS_PHRASE, "umed_miss_reply")

    # Süre dolmuş → empty_chain = TIMEOUT
    set_turn_deadline(time.monotonic() - 1.0)
    failed += _ok(umed_empty_chain_reply() == TIMEOUT_PHRASE, "empty_chain timeout")

    # Süre bol → MISS
    set_turn_deadline(time.monotonic() + 60.0)
    failed += _ok(umed_empty_chain_reply() == MISS_PHRASE, "empty_chain miss")
    set_turn_deadline(None)

    # classify: süre önce, hits=0 olsa bile timeout
    mc = classify_miss(
        reply=MISS_PHRASE,
        orch={"hits_count": 0},
        hits_count=0,
        elapsed_sec=20.0,
        budget_sec=15.0,
        egitim_miss=True,
    )
    failed += _ok(mc == MISS_TIMEOUT, f"classify timeout önce ({mc})")

    mc2 = classify_miss(
        reply=TIMEOUT_PHRASE,
        orch={"hits_count": 0},
        hits_count=0,
        elapsed_sec=5.0,
        budget_sec=15.0,
    )
    failed += _ok(mc2 == MISS_TIMEOUT, f"classify TIMEOUT phrase ({mc2})")

    mc3 = classify_miss(
        reply=MISS_PHRASE,
        orch={"hits_count": 0},
        hits_count=0,
        elapsed_sec=2.0,
        budget_sec=15.0,
        egitim_miss=True,
    )
    failed += _ok(mc3 == MISS_NO_HITS, f"classify no_hits kısa süre ({mc3})")

    # wrap: MISS + süre aşımı → TIMEOUT (öğret pending yok)
    q = "Osmanli devletini kim kurdu?"
    r, miss = wrap_miss_if_needed(MISS_PHRASE, q, 120.0)
    failed += _ok(miss and r == TIMEOUT_PHRASE, f"wrap MISS→TIMEOUT ({r[:40]!r})")
    failed += _ok(
        should_emit_miss_reply(MISS_PHRASE, 120.0, user_message=q),
        "should_emit MISS+süre",
    )
    failed += _ok(
        not should_emit_miss_reply(TIMEOUT_PHRASE, 120.0, user_message=q),
        "should_emit TIMEOUT false",
    )

    total = 12
    print(f"result: {total - failed}/{total} pass")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
