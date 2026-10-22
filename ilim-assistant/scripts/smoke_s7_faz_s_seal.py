# -*- coding: utf-8 -*-
"""S7 — Faz S kapanış mühürü: S0–S6 smokes + korpus batarya (S4 askıda)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SCRIPTS = [
    "smoke_s0_yalan_korpus.py",
    "smoke_s1_source_router.py",
    "smoke_s2_faz49_kisit.py",
    "smoke_s3_sayi_hard_gate.py",
    "smoke_s5_fuzzy_sentez.py",
    "smoke_s6_anlik_harman.py",
]


def _battery() -> tuple[int, str]:
    """S0 korpus üzerinden router→faz49→hard-gate bataryası (LLM yok)."""
    from ilim_assistant.ana_motor_plan import looks_like_fast_llm_fact_question
    from ilim_assistant.sohbet_sayi_hard_gate import should_force_sayi_miss
    from ilim_assistant.sohbet_source_router import (
        blocks_faz49_fast,
        classify_source_intent,
    )
    from ilim_assistant.sohbet_yalan_korpus import list_yalan_cases

    cases = list_yalan_cases()
    fail = 0
    for c in cases:
        msg = str(c["message"])
        d = classify_source_intent(msg)
        for f in ("needs_live", "needs_number", "library_ok", "allow_parametric"):
            if bool(getattr(d, f)) != bool(c.get(f)):
                fail += 1
                break
        if c.get("needs_live") or c.get("needs_number"):
            if not blocks_faz49_fast(msg):
                fail += 1
            if looks_like_fast_llm_fact_question(msg):
                fail += 1
            if not should_force_sayi_miss(msg, web_extra="", blocks="", hits=[]):
                fail += 1
    return fail, f"battery cases={len(cases)} field/gate_fail={fail}"


def main() -> int:
    print("=== Faz S mühür (S7) ===\n")
    print("Not: S4 (Ümit web sırası) Mimar `evet` bekler — bu mühürde uygulanmadı.\n")
    fails = 0

    for name in SCRIPTS:
        path = ROOT / "scripts" / name
        print(f"-- {name}")
        r = subprocess.run(
            [sys.executable, str(path)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=300,
        )
        if r.returncode == 0:
            print("  OK pass")
        else:
            tail = (r.stdout or r.stderr or "")[-500:]
            print(f"  FAIL rc={r.returncode}\n{tail}")
            fails += 1

    print("\n-- korpus batarya (offline)")
    bfail, blabel = _battery()
    if bfail:
        print(f"  FAIL {blabel}")
        fails += 1
    else:
        print(f"  OK {blabel}")

    if fails:
        print(f"\nMÜHÜR KIRMIZI — {fails} hata")
        return 1
    print(
        "\nMÜHÜR YEŞİL — Faz S (S0–S3·S5–S6) OK · S4 askıda · sırada Faz V"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
