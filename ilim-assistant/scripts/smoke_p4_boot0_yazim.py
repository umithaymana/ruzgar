# -*- coding: utf-8 -*-
"""P4 smoke — BOOT=0 yazım format kurtarma (supervised şişirme yok)."""
from __future__ import annotations

import os
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
    from ilim_assistant.motorlar.programlama_faz103_e2 import (
        _setup_multi_file_broken,
        e2_write_template_nudge,
    )
    from ilim_assistant.motorlar.programlama_patch import (
        PROG_PATCH_VERSION,
        apply_patch_jobs,
        boot0_write_fewshot,
        extract_patch_jobs,
        normalize_diff_lines_under_patch,
        normalize_unfenced_search_replace,
    )

    failed = 0
    failed += _ok("v1.4" in PROG_PATCH_VERSION or "p4" in PROG_PATCH_VERSION, f"ver {PROG_PATCH_VERSION}")

    unfenced = (
        "@@patch projects/demo/app/util.py\n"
        "<<<SEARCH\n"
        'VERSION = "1.0.0-broken"\n'
        "===\n"
        'VERSION = "2.0.0"\n'
        ">>>REPLACE\n"
    )
    st = normalize_unfenced_search_replace(unfenced)
    failed += _ok("```search-replace" in st, "unfenced → fence")
    jobs = extract_patch_jobs(unfenced)
    failed += _ok(len(jobs) >= 1 and "util.py" in jobs[0][0], f"extract unfenced jobs={len(jobs)}")

    diffish = (
        "@@patch projects/demo/app/util.py\n"
        "```diff\n"
        '-VERSION = "1.0.0-broken"\n'
        '+VERSION = "2.0.0"\n'
        "```\n"
    )
    st2 = normalize_diff_lines_under_patch(diffish)
    failed += _ok("<<<SEARCH" in st2 and "2.0.0" in st2, "diff lines → SEARCH")
    jobs2 = extract_patch_jobs(diffish)
    failed += _ok(len(jobs2) >= 1, f"extract diff jobs={len(jobs2)}")

    fs = boot0_write_fewshot("projects/x")
    failed += _ok("P4 BOOT=0" in fs and "@@patch projects/x/app/util.py" in fs, "fewshot")

    nudge = e2_write_template_nudge(
        "projects/demo",
        "app/util.py ve app/service.py VERSION 2.0.0",
    )
    failed += _ok("P4 BOOT=0" in nudge, "nudge includes fewshot")

    # apply on disk — SUPERVISED kapalı; yalnız patch pipeline
    old_boot = os.environ.get("RUZGAR_E2_SUPERVISED_BOOT")
    os.environ["RUZGAR_E2_SUPERVISED_BOOT"] = "0"
    try:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            scope = "projects/p4-boot0"
            ok_setup, _ = _setup_multi_file_broken(root, scope)
            failed += _ok(ok_setup, "setup broken")
            reps = apply_patch_jobs(unfenced.replace("projects/demo", scope), root)
            util = (root / scope.replace("/", os.sep) / "app" / "util.py").read_text(
                encoding="utf-8"
            )
            failed += _ok(
                any(r.ok for r in reps) and 'VERSION = "2.0.0"' in util,
                f"apply unfenced BOOT=0 writes ok={[r.ok for r in reps]}",
            )
            # diff style
            ok_setup2, _ = _setup_multi_file_broken(root, scope + "b")
            failed += _ok(ok_setup2, "setup2")
            reps2 = apply_patch_jobs(
                diffish.replace("projects/demo", scope + "b"), root
            )
            util2 = (
                root / (scope + "b").replace("/", os.sep) / "app" / "util.py"
            ).read_text(encoding="utf-8")
            failed += _ok(
                any(r.ok for r in reps2) and 'VERSION = "2.0.0"' in util2,
                "apply diff-style BOOT=0",
            )
    finally:
        if old_boot is None:
            os.environ.pop("RUZGAR_E2_SUPERVISED_BOOT", None)
        else:
            os.environ["RUZGAR_E2_SUPERVISED_BOOT"] = old_boot

    total = 10
    print(f"result: {total - failed}/{total} pass")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
