#!/usr/bin/env python3
"""Smoke — E2 yazım şablonunda @@patch yolu var mı (saf yazım dilimi 1)."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from ilim_assistant.motorlar.programlama_faz103_e2 import e2_write_template_nudge
    from ilim_assistant.motorlar.programlama_faz14 import (
        CodeAgentTask,
        build_agent_turn_user_message,
    )

    scope = "projects/e2-nudge-demo"
    goal = "app/util.py ve app/service.py VERSION 2.0.0 pytest gecir"
    nudge = e2_write_template_nudge(scope, goal)
    fails: list[str] = []
    if f"@@patch {scope}/app/util.py" not in nudge:
        fails.append("nudge missing @@patch util.py")
    if f"@@patch {scope}/app/service.py" not in nudge:
        fails.append("nudge missing @@patch service.py")
    if "```search-replace" not in nudge:
        fails.append("nudge missing search-replace fence")
    if 'VERSION = "2.0.0"' not in nudge:
        fails.append("nudge missing VERSION 2.0.0")

    task = CodeAgentTask(
        goal=goal,
        scope_rel=scope,
        project_slug="e2-nudge-demo",
    )
    turn1 = build_agent_turn_user_message(task, turn=1, max_turns=3)
    if "YAZIM ÖNCE" not in turn1:
        fails.append("turn1 missing YAZIM ÖNCE")
    if f"@@patch {scope}/app/util.py" not in turn1:
        fails.append("turn1 missing @@patch util")
    if "Kısa plan" in turn1:
        fails.append("turn1 still asks for short plan (E2 should be write-first)")

    # Canlı kök: @@patch python fence içinde + search-replace ayrı → birleşmeli
    from ilim_assistant.motorlar.programlama_patch import (
        extract_patch_jobs,
        normalize_split_patch_fences,
    )

    malformed = (
        "7. dosyayı değiştireceğim:\n\n"
        "```python\n"
        f"@@patch {scope}/app/util.py\n"
        "```\n\n"
        "```search-replace\n"
        "<<<SEARCH\n"
        'VERSION = "1.0.0-broken"\n'
        "===\n"
        'VERSION = "2.0.0"\n'
        ">>>REPLACE\n"
        "```\n"
    )
    fixed = normalize_split_patch_fences(malformed)
    if f"@@patch {scope}/app/util.py\n```search-replace" not in fixed.replace(
        "\r\n", "\n"
    ):
        fails.append("normalize_split_patch_fences did not stitch")
    jobs = extract_patch_jobs(malformed)
    if not any(j[0].endswith("app/util.py") and "2.0.0" in j[2] for j in jobs):
        fails.append(f"extract_patch_jobs missed split fence jobs={jobs!r}")

    # Disk: bölünmüş fence gerçekten yazılmalı (canlı BOOT=0 kökü)
    try:
        from ilim_assistant.motorlar.programlama_faz103_e2 import _setup_multi_file_broken
        from ilim_assistant.motorlar.programlama_patch import apply_patch_jobs

        with tempfile.TemporaryDirectory() as td:
            scope2 = "projects/split-rescue"
            ok_s, msg_s = _setup_multi_file_broken(td, scope2)
            if not ok_s:
                fails.append(f"setup broken: {msg_s}")
            else:
                body = (
                    "```python\n"
                    f"@@patch {scope2}/app/util.py\n"
                    "```\n\n"
                    "```search-replace\n"
                    "<<<SEARCH\n"
                    'VERSION = "1.0.0-broken"\n'
                    "===\n"
                    'VERSION = "2.0.0"\n'
                    ">>>REPLACE\n"
                    "```\n"
                )
                reps = apply_patch_jobs(body, td)
                util = Path(td) / "projects" / "split-rescue" / "app" / "util.py"
                txt = util.read_text(encoding="utf-8") if util.is_file() else ""
                if not any(getattr(r, "ok", False) for r in reps) or 'VERSION = "2.0.0"' not in txt:
                    fails.append(
                        f"disk apply failed reps={[(r.path, r.ok, r.detail) for r in reps]}"
                    )
    except Exception as exc:
        fails.append(f"disk apply exc: {exc}")

    if fails:
        for f in fails:
            print(f"FAIL {f}")
        print("--- nudge preview ---")
        print(nudge[:800])
        return 1
    print("PASS programlama_e2_write_nudge_smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
