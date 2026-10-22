# -*- coding: utf-8 -*-
"""P6 smoke — Pilot A selam CLI uçtan uca."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WS = ROOT.parent
PILOT = WS / "projects" / "pilot-a-selam-cli"


def _ok(cond: bool, label: str) -> int:
    print(("OK" if cond else "FAIL"), "-", label)
    return 0 if cond else 1


def main() -> int:
    failed = 0
    failed += _ok(PILOT.is_dir(), f"pilot dir {PILOT}")
    failed += _ok((PILOT / "main.py").is_file(), "main.py")
    failed += _ok((PILOT / "tests" / "test_cli.py").is_file(), "tests")

    r = subprocess.run(
        [sys.executable, str(PILOT / "main.py"), "Ümit"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(PILOT),
        timeout=30,
    )
    failed += _ok(r.returncode == 0 and "Merhaba, Ümit!" in (r.stdout or ""), f"run cli out={r.stdout!r}")

    r2 = subprocess.run(
        [sys.executable, str(PILOT / "main.py"), "--upper", "ruzgar"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(PILOT),
        timeout=30,
    )
    failed += _ok(
        r2.returncode == 0 and "MERHABA, RUZGAR!" in (r2.stdout or ""),
        f"run --upper out={r2.stdout!r}",
    )

    pt = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", str(PILOT / "tests")],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(PILOT),
        timeout=120,
    )
    failed += _ok(
        pt.returncode == 0,
        f"pytest rc={pt.returncode} out={(pt.stdout or pt.stderr or '')[:200]!r}",
    )

    total = 6
    print(f"result: {total - failed}/{total} pass")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
