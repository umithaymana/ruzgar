# -*- coding: utf-8 -*-
"""V5 — Faz V kapanış mühürü: V0–V5 smokes zinciri."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SCRIPTS = [
    "smoke_v0_stt_tts_baseline.py",
    "smoke_v1_ses_isinma.py",
    "smoke_v2_stt_decode.py",
    "smoke_v3_tts_ilk_byte.py",
    "smoke_v4_barge_in.py",
    "smoke_v5_sesli_tur.py",
]


def main() -> int:
    print("=== Faz V mühür (V5) ===\n")
    # V0 smoke hızlı kalsın
    os.environ.setdefault("RUZGAR_V0_STT_LOAD", "0")
    fails = 0
    for name in SCRIPTS:
        path = ROOT / "scripts" / name
        print(f"-- {name}")
        r = subprocess.run(
            [sys.executable, str(path)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=600,
            env={**os.environ},
        )
        if r.returncode == 0:
            # son satır özeti
            lines = [ln for ln in (r.stdout or "").splitlines() if ln.strip()]
            tail = lines[-1] if lines else "pass"
            print(f"  OK {tail}")
        else:
            tail = (r.stdout or r.stderr or "")[-600:]
            print(f"  FAIL rc={r.returncode}\n{tail}")
            fails += 1

    if fails:
        print(f"\nMÜHÜR KIRMIZI — {fails} hata · Faz V açık")
        return 1
    print("\nMÜHÜR YEŞİL — Faz V (V0–V5) OK · sırada Faz M (Video→Tercüme→Okuma→Mimar)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
