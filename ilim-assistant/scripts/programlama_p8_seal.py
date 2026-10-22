# -*- coding: utf-8 -*-
"""P8 — Faz P kapanış mühürü: KPI + P1–P7 smokes + 2 pilot."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SCRIPTS = [
    "smoke_p1_supervised_patterns.py",
    "smoke_p2_ray_siniflandirici.py",
    "smoke_p3_file_verify.py",
    "smoke_p4_boot0_yazim.py",
    "smoke_p5_scaffold_boru.py",
    "smoke_p6_pilot_a_cli.py",
    "smoke_p7_pilot_b_web.py",
    "programlama_e2_seal.py",
]


def main() -> int:
    from ilim_assistant.motorlar.programlama_faz103_e2 import compute_e2_stats

    print("=== Faz P mühür (P8) ===\n")
    fails = 0
    ws = ROOT.parent
    st = compute_e2_stats(ws, window_days=30)
    print(
        f"KPI agent_ok={st.get('agent_ok_rate')} "
        f"recent5={st.get('agent_ok_recent5_rate')} "
        f"boot0={st.get('boot0_agent_ok_rate')} "
        f"heal_r10={st.get('heal_share_recent10')}"
    )
    # Band: ~0.70+ kabul (donanım tavanı)
    agent = float(st.get("agent_ok_rate") or 0)
    if agent < 0.60:
        print("FAIL - agent_ok < %60")
        fails += 1
    else:
        print("OK - agent_ok band")

    for name in SCRIPTS:
        path = ROOT / "scripts" / name
        print(f"\n-- {name}")
        r = subprocess.run(
            [sys.executable, str(path)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=600,
        )
        tail = (r.stdout or r.stderr or "")[-400:]
        if r.returncode == 0:
            print(f"  OK pass")
        else:
            print(f"  FAIL rc={r.returncode}\n{tail}")
            fails += 1

    if fails:
        print(f"\nMÜHÜR KIRMIZI — {fails} hata")
        return 1
    print("\nMÜHÜR YEŞİL — Faz P (P0–P7) OK · sırada Faz S")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
