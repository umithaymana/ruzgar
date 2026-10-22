# -*- coding: utf-8 -*-
"""D2 — mandate: @@patch yazım sayılır; salt okuma cezası; E2 düzeltme yazım zorunlu."""
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
    from ilim_assistant.motorlar.programlama_faz14 import (
        CodeAgentTask,
        build_agent_turn_user_message,
    )
    from ilim_assistant.motorlar.programlama_faz39 import (
        FAZ39_VERSION,
        _has_write,
        build_write_mandate_message,
        turn_was_read_only,
    )

    failed += _ok("v1.1" in FAZ39_VERSION, f"faz39 {FAZ39_VERSION}")

    patch_body = (
        "@@patch projects/demo/app/util.py\n"
        "```search-replace\n"
        "<<<SEARCH\n"
        'VERSION = "1.0.0-broken"\n'
        "===\n"
        'VERSION = "2.0.0"\n'
        ">>>REPLACE\n"
        "```\n"
    )
    failed += _ok(_has_write(patch_body, []), "@@patch → _has_write")
    failed += _ok(
        not turn_was_read_only(patch_body, [{"tool": "grep", "ok": True}]),
        "patch varken read_only değil",
    )
    failed += _ok(
        turn_was_read_only("plan only", [{"tool": "grep", "ok": True}]),
        "yalnız grep → read_only",
    )

    mandate = build_write_mandate_message(
        goal="app/util.py ve app/service.py VERSION 2.0.0",
        scope_rel="projects/demo",
        tool_block="",
        turn=2,
    )
    failed += _ok("Salt okuma" in mandate or "salt okuma" in mandate.lower(), "mandate salt okuma yasağı")
    failed += _ok("@@patch" in mandate, "mandate @@patch talimatı")

    task = CodeAgentTask(
        goal="app/util.py ve app/service.py version 2.0.0 pytest gecir",
        scope_rel="projects/demo",
        project_slug="demo",
    )
    t2 = build_agent_turn_user_message(
        task, turn=2, max_turns=3, failure_snippet="AssertionError: version"
    )
    failed += _ok(
        "YAZIM ZORUNLU" in t2 or "Salt okuma YASAK" in t2,
        "E2 düzeltme turu yazım zorunlu",
    )

    total = 7
    print(f"result: {total - failed}/{total} pass")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
