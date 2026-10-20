#!/usr/bin/env python3
"""E2 kapanış mühürü — dilim 1–4 + 6c + mandate yeşil mi?"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = [
    ("e2_multi", "programlama_e2_multi_file_smoke.py"),
    ("e2_workbench", "programlama_e2_workbench_smoke.py"),
    ("mega_stress", "programlama_mega_stress.py"),
    ("faz39_mandate", "programlama_faz39_mandate_smoke.py"),
    ("faz6c", "ana_motor_faz6c_smoke.py"),
    ("tek_sohbet", "ana_motor_tek_sohbet_smoke.py"),
    ("e2_offline", "programlama_e2_battery.py"),
]


def main() -> int:
    py = sys.executable
    fails = 0
    print("=== E2 kapanış mühürü ===\n")
    for name, script in _SCRIPTS:
        path = _ROOT / "scripts" / script
        env = None
        cmd = [py, str(path)]
        print(f"-- {name}")
        r = subprocess.run(
            cmd,
            cwd=str(_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
        )
        tail = (r.stdout or "")[-400:] + (r.stderr or "")[-200:]
        if r.returncode != 0:
            print(f"  FAIL exit={r.returncode}")
            print(tail)
            fails += 1
        else:
            last = [ln for ln in (r.stdout or "").splitlines() if ln.strip()]
            print(f"  OK {last[-1] if last else 'pass'}")
    # Heal yedek (LLM yok)
    import os

    env2 = os.environ.copy()
    env2["RUZGAR_E2_LIVE_FORCE_HEAL"] = "1"
    print("-- e2_live_heal")
    r = subprocess.run(
        [py, "-u", str(_ROOT / "scripts" / "programlama_e2_battery.py"), "--live-only"],
        cwd=str(_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env2,
    )
    if r.returncode != 0:
        print(f"  FAIL heal exit={r.returncode}")
        print((r.stdout or "")[-500:])
        fails += 1
    else:
        print("  OK heal fallback %100")

    if fails:
        print(f"\nMÜHÜR KIRIK — {fails} başarısız")
        return 1
    print("\nMÜHÜR YEŞİL — E2 + 6c + mandate OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
