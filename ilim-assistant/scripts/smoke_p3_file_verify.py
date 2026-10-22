# -*- coding: utf-8 -*-
"""P3 smoke — dosya-dosya verify + heal→pattern."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _ok(cond: bool, label: str) -> int:
    print(("OK" if cond else "FAIL"), "-", label)
    return 0 if cond else 1


def main() -> int:
    from ilim_assistant.motorlar.programlama_faz56 import (
        build_multi_file_plan_block,
        multi_file_cap_nudge,
    )
    from ilim_assistant.motorlar.programlama_p3_file_verify import (
        P3_VERSION,
        classify_heal_root,
        file_verify_policy,
        lessons_nudge_block,
        recent_heal_lessons,
        record_heal_lesson,
        try_pattern_heal_from_verify,
    )

    failed = 0
    failed += _ok("p3-file-verify" in P3_VERSION, f"version {P3_VERSION}")

    pol = file_verify_policy(
        "app/util.py ve app/service.py düzelt",
        writes_this_turn=0,
    )
    failed += _ok(pol.prefer_one_file and "1 dosya" in pol.nudge, f"policy multi nudge={pol.nudge[:40]!r}")

    pol2 = file_verify_policy("pytest geçir", writes_this_turn=0)
    failed += _ok(not pol2.prefer_one_file, "policy non-multi")

    nudge = multi_file_cap_nudge(3)
    failed += _ok(bool(nudge) and "P3" in (nudge or ""), f"cap nudge={nudge!r}")

    failed += _ok(classify_heal_root("NameError: name 'greet' is not defined") == "import_fix", "root import")
    failed += _ok(classify_heal_root("assert 'uptime' in payload") == "dict_field", "root dict")
    failed += _ok(classify_heal_root("VERSION == 2.0.0 failed; 1.0.0-broken") == "e2_version", "root version")

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        scope = "projects/p3"
        app = root / "projects" / "p3" / "app"
        app.mkdir(parents=True)
        (app / "__init__.py").write_text("", encoding="utf-8")
        (app / "util.py").write_text(
            'VERSION = "2.0.0"\ndef greet(n: str) -> str:\n    return n\n',
            encoding="utf-8",
        )
        (app / "service.py").write_text(
            'from app.util import VERSION\n\ndef health_payload():\n'
            '    return {"ok": "true", "msg": greet("x")}\n',
            encoding="utf-8",
        )
        heal = try_pattern_heal_from_verify(
            root,
            scope,
            "düzelt",
            verify_output="NameError: name 'greet' is not defined",
        )
        txt = (app / "service.py").read_text(encoding="utf-8")
        failed += _ok(
            bool(heal.get("writes_ok")) and "greet" in txt and heal.get("healed"),
            f"pattern heal import detail={heal.get('detail')!r}",
        )
        failed += _ok(len(recent_heal_lessons()) >= 1, "lesson recorded")

    record_heal_lesson(root_cause="dict_field", pattern_id="dict_field", detail="uptime")
    block = lessons_nudge_block("projects/p3")
    failed += _ok("heal dersi" in block and "dict_field" in block, "lessons nudge")

    plan = build_multi_file_plan_block(
        None,
        scope_rel="projects/demo",
        message="iki dosyada düzelt",
        goal="app/a.py ve app/b.py refactor",
        turn=1,
        touched_files=[],
    )
    failed += _ok("P3" in plan and "1 dosya" in plan, f"plan block has P3")

    total = 12
    print(f"result: {total - failed}/{total} pass")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
