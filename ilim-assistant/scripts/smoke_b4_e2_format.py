# -*- coding: utf-8 -*-
"""B4 — çıplak VERSION / service patch format kurtarma."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ilim_assistant.motorlar.programlama_patch import (  # noqa: E402
    extract_patch_jobs,
    normalize_bare_e2_version_patches,
)


def _ok(cond: bool, label: str) -> int:
    print(("OK" if cond else "FAIL"), "-", label)
    return 0 if cond else 1


def main() -> int:
    failed = 0
    msg = (
        "duzelt projects/e2-bat-1-live/app/util.py\n"
        "<<<SEARCH\n"
        'VERSION = "1.0.0-broken"\n'
        "===\n"
        'VERSION = "2.0.0"\n'
        ">>>REPLACE\n"
        "service.py health_payload version: VERSION\n"
    )
    out = normalize_bare_e2_version_patches(msg)
    jobs = extract_patch_jobs(out)
    failed += _ok("@@patch" in out and "util.py" in out, "util @@patch eklendi")
    failed += _ok(any("util.py" in j[0] for j in jobs), "util job extract")
    failed += _ok(any("service.py" in j[0] for j in jobs), "service job extract")
    failed += _ok(len(jobs) >= 2, f"en az 2 job (got {len(jobs)})")

    # Zaten geçerli blok — dokunma (çift ekleme yok)
    good = (
        "@@patch projects/e2-bat-1-live/app/util.py\n"
        "```search-replace\n"
        "<<<SEARCH\n"
        'VERSION = "1.0.0-broken"\n'
        "===\n"
        'VERSION = "2.0.0"\n'
        ">>>REPLACE\n"
        "```\n"
    )
    out2 = normalize_bare_e2_version_patches(good)
    failed += _ok(out2.count("@@patch") == 1, "mevcut @@patch korunur")

    total = 5
    print(f"result: {total - failed}/{total} pass")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
