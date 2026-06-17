#!/usr/bin/env python3
"""Tek seferlik E1 teşhis — smoke kayıtlarını ayırır."""
from __future__ import annotations

import json
import time
from collections import Counter
from pathlib import Path

import sys

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from ilim_assistant.motorlar.programlama_faz55 import _load_store, _outcomes_path
from ilim_assistant.motorlar.programlama_faz91 import compute_e1_stats, is_kpi_eligible_outcome


def is_smoke_noise(o: dict) -> bool:
    g = (o.get("goal") or "").lower()
    d = (o.get("detail") or "").lower()
    if "smoke" in g:
        return True
    if (
        int(o.get("turns_used") or 0) == 0
        and float(o.get("elapsed_sec") or 0) == 0
        and "pytest assert failed in test_health" in d
    ):
        return True
    return False


def main() -> int:
    ws = Path(__file__).resolve().parents[2]
    op = _outcomes_path(ws)
    print("workspace", ws)
    print("outcomes_path", op)
    if not op or not op.is_file():
        print(json.dumps({"ok": False, "error": "no task_outcomes.json"}))
        return 1

    store = _load_store(op)
    outcomes = [o for o in store.get("outcomes") or [] if isinstance(o, dict)]
    smoke = [o for o in outcomes if is_smoke_noise(o)]
    real = [o for o in outcomes if not is_smoke_noise(o)]

    cutoff7 = time.time() - 7 * 86400
    cutoff30 = time.time() - 30 * 86400

    def rate(rows: list) -> dict:
        n = len(rows)
        ok = sum(1 for o in rows if o.get("success"))
        return {"total": n, "success": ok, "pct": round(100 * ok / n, 1) if n else 0.0}

    e1_api = compute_e1_stats(ws, window_days=7)
    fails = [o for o in real if not o.get("success")]
    rc = Counter(str(o.get("root_cause") or "unknown") for o in fails)

    rep = {
        "ok": True,
        "total_records": len(outcomes),
        "smoke_noise": len(smoke),
        "real_records": len(real),
        "rates": {
            "7g_all": rate([o for o in outcomes if float(o.get("ts", 0)) >= cutoff7]),
            "7g_real_no_smoke": rate([o for o in real if float(o.get("ts", 0)) >= cutoff7]),
            "30g_real": rate([o for o in real if float(o.get("ts", 0)) >= cutoff30]),
        },
        "e1_api_filtered": e1_api,
        "root_cause_real_fails": rc.most_common(10),
        "last_real_failures": [
            {
                "scope": o.get("scope_rel"),
                "goal": (o.get("goal") or "")[:60],
                "root_cause": o.get("root_cause"),
                "detail": (o.get("detail") or "")[:80],
                "turns": o.get("turns_used"),
                "writes_ok": o.get("writes_ok"),
            }
            for o in fails[-10:]
        ],
        "kpi_ineligible_in_7g": sum(
            1
            for o in outcomes
            if float(o.get("ts", 0)) >= cutoff7 and not is_kpi_eligible_outcome(o)
        ),
    }
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
