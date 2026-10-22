# -*- coding: utf-8 -*-
"""D6 — hub niyet: görüş/bilgi/programlama tuzağı → yanlış motor yok."""
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
    from ilim_assistant.ana_motor_plan import looks_like_opinion_request
    from ilim_assistant.motorlar.ses_faz72 import classify_ses_intent, maybe_instant_faz72

    traps = [
        ("Yapay zeka hakkinda ne dusunuyorsun?", True),
        ("Ses nedir anlat biraz", False),
        ("Profil fotoğrafı nedir", False),
        ("kodda version duzelt pytest gecir", False),
        ("asistan sence nasil bir yapay zekasin", True),
    ]
    for q, want_op in traps:
        op = looks_like_opinion_request(q)
        failed += _ok(op == want_op, f"opinion({want_op}): {q[:40]}")
        inst = maybe_instant_faz72(q)
        failed += _ok(inst is None, f"ses anlık yok: {q[:40]}")
        ses = classify_ses_intent(q, mode_norm="ses")
        failed += _ok(
            ses.get("reason") != "set_profile",
            f"set_profile yok: {q[:40]} got={ses.get('reason')}",
        )

    switch = classify_ses_intent("asistan moduna geç", mode_norm="ses")
    failed += _ok(switch.get("reason") == "set_profile", "açık geçiş korunur")
    # inceleme: «asistan yap» / «yapay» profil değil
    yap = classify_ses_intent("asistan yap", mode_norm="ses")
    failed += _ok(yap.get("reason") != "set_profile", f"asistan yap ≠ profil (got {yap.get('reason')})")
    yapay = classify_ses_intent("asistan sence nasil bir yapay zekasin", mode_norm="ses")
    failed += _ok(yapay.get("reason") != "set_profile", "yapay ≠ profil")

    total = len(traps) * 3 + 3
    print(f"result: {total - failed}/{total} pass")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
