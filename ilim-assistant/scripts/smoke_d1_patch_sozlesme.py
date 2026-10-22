# -*- coding: utf-8 -*-
"""D1 — araç sözleşmesi: backtick / backslash / aynı-fence patch kurtarma."""
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
    failed = 0
    from ilim_assistant.motorlar.programlama_faz103_e2 import _setup_multi_file_broken
    from ilim_assistant.motorlar.programlama_patch import (
        PROG_PATCH_VERSION,
        apply_patch_jobs,
        clean_patch_path,
        normalize_patch_path_lines,
        normalize_split_patch_fences,
    )

    failed += _ok(
        "v1.3" in PROG_PATCH_VERSION or "v1.4" in PROG_PATCH_VERSION,
        f"version {PROG_PATCH_VERSION}",
    )
    failed += _ok(
        clean_patch_path("`projects/demo/app/util.py`") == "projects/demo/app/util.py",
        "clean backtick path",
    )
    failed += _ok(
        clean_patch_path(r"projects\demo\app\util.py") == "projects/demo/app/util.py",
        "clean backslash path",
    )
    failed += _ok(
        clean_patch_path("projects/projects/demo/app/util.py")
        == "projects/demo/app/util.py",
        "clean double projects/",
    )

    same = (
        "```python\n"
        "@@patch projects/demo/app/util.py\n"
        "<<<SEARCH\n"
        'VERSION = "1.0.0-broken"\n'
        "===\n"
        'VERSION = "2.0.0"\n'
        ">>>REPLACE\n"
        "```\n"
    )
    stitched = normalize_split_patch_fences(same)
    failed += _ok(
        "```search-replace" in stitched and stitched.strip().startswith("@@patch"),
        "same-fence → search-replace stitch",
    )

    td = tempfile.mkdtemp()
    scope = "projects/demo"
    ok, msg = _setup_multi_file_broken(td, scope)
    failed += _ok(ok, f"setup ({msg})")

    bodies = {
        "backtick": (
            "@@patch `projects/demo/app/util.py`\n"
            "```search-replace\n"
            "<<<SEARCH\n"
            'VERSION = "1.0.0-broken"\n'
            "===\n"
            'VERSION = "2.0.0"\n'
            ">>>REPLACE\n"
            "```\n"
        ),
        "backslash": (
            "@@patch "
            + "projects"
            + chr(92)
            + "demo"
            + chr(92)
            + "app"
            + chr(92)
            + "util.py\n"
            "```search-replace\n"
            "<<<SEARCH\n"
            'VERSION = "1.0.0-broken"\n'
            "===\n"
            'VERSION = "2.0.0"\n'
            ">>>REPLACE\n"
            "```\n"
        ),
        "same_fence": same,
    }
    for name, body in bodies.items():
        _setup_multi_file_broken(td, scope)
        # path line normalize first (as extract_patch_jobs does)
        body2 = normalize_patch_path_lines(body)
        reps = apply_patch_jobs(body2, td)
        util = Path(td) / "projects" / "demo" / "app" / "util.py"
        text = util.read_text(encoding="utf-8") if util.is_file() else ""
        wrote = 'VERSION = "2.0.0"' in text and "1.0.0-broken" not in text
        failed += _ok(wrote and any(r.ok for r in reps), f"apply {name}")

    total = 3 + 1 + 1 + 1 + 1 + len(bodies)
    print(f"result: {total - failed}/{total} pass")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
