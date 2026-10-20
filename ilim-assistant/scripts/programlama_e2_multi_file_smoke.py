# Created by Ümit & Gökçenur
"""Smoke — Programlama E2 çok dosya niyeti → ajan yolu."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from ilim_assistant.motorlar.programlama_faz56 import (
        extract_named_paths,
        looks_like_multi_file_task,
    )
    from ilim_assistant.motorlar.programlama_faz80 import wants_mega_refactor
    from ilim_assistant.motorlar.programlama_faz85 import goal_wants_agent_path
    from ilim_assistant.motorlar.programlama_yuzey_bridge import (
        build_surface_handoff_payload,
    )

    cases = [
        ("health endpointine version 2.0.0 ekle pytest gecir", False, "faz85_fast"),
        ("app/main.py ve app/api.py refactor et", True, "agent_multi"),
        ("iki dosyada auth ekle", True, "agent_multi"),
        ("mega refactor 10+ dosya", True, "agent_mega"),
        ("cok dosyali monorepo duzenle", True, "agent_multi"),
    ]
    fails = 0
    for goal, want_agent, hint in cases:
        got_agent = goal_wants_agent_path(goal)
        payload = build_surface_handoff_payload(f"gorev: {goal}")
        got_hint = payload.get("path_hint")
        if goal.startswith("health"):
            ok = (not got_agent) and got_hint == "faz85_fast"
        else:
            ok = bool(got_agent) is bool(want_agent) and got_hint == hint
        print(
            f"  {'OK' if ok else 'FAIL'} {goal!r} agent={got_agent} "
            f"hint={got_hint!r} (beklenen {hint!r})"
        )
        if not ok:
            fails += 1

    paths = extract_named_paths("duzelt app/main.py ile tests/test_health.py")
    assert "app/main.py" in paths and "tests/test_health.py" in paths
    assert looks_like_multi_file_task("app/a.py ve app/b.py guncelle")
    assert wants_mega_refactor("mega refactor tum repoyu")
    print("OK named paths + mega")
    if fails:
        print(f"FAIL {fails}")
        return 1
    print("PASS programlama_e2_multi_file_smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
