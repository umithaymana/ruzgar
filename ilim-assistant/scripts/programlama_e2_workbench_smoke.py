#!/usr/bin/env python3
"""E2 dilim 4 — mega/E2 workbench ürün kartı smoke."""
from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
WORKSPACE = _ROOT.parent


def main() -> int:
    from ilim_assistant.motorlar.programlama_faz14 import save_agent_state
    from ilim_assistant.motorlar.programlama_mega_workbench import (
        MEGA_WORKBENCH_VERSION,
        build_mega_workbench_payload,
    )

    # Sentetik yarım görev — UI alanlarının dolu geldiğini doğrula
    save_agent_state(
        WORKSPACE,
        {
            "status": "running",
            "scope_rel": "projects/e2-wb-smoke",
            "goal": "app/main.py ve app/api.py refactor et pytest gecir",
            "turn": 2,
            "max_turns": 8,
            "touched_files": [
                "projects/e2-wb-smoke/app/main.py",
                "projects/e2-wb-smoke/app/api.py",
            ],
            "last_verify_ok": False,
            "last_verify_detail": "pytest kirmizi (smoke)",
            "stop_requested": False,
        },
    )
    wb = build_mega_workbench_payload(WORKSPACE)
    fails: list[str] = []
    if not wb.get("ok"):
        fails.append("ok")
    if not wb.get("product"):
        fails.append("product")
    if "v1.1" not in str(wb.get("version") or MEGA_WORKBENCH_VERSION):
        fails.append(f"version={wb.get('version')}")
    ag = wb.get("agent") or {}
    if not ag.get("can_resume"):
        fails.append("can_resume")
    if "görev:" not in str(ag.get("resume_hint") or "") and "gorev:" not in str(
        ag.get("resume_hint") or ""
    ):
        fails.append("resume_hint")
    if ag.get("path_hint") not in ("agent_multi", "agent", "agent_mega"):
        fails.append(f"path_hint={ag.get('path_hint')}")
    if not (wb.get("multi_file_plan") or "").strip():
        fails.append("multi_file_plan")
    if int(wb.get("touched_count") or 0) < 2:
        fails.append("touched_count")
    ver = wb.get("verify") or {}
    if ver.get("ok") is not False:
        fails.append("verify.ok")
    e2 = wb.get("e2") or {}
    if "target_rate" not in e2 or "current_rate" not in e2:
        fails.append("e2")

    # Temizlik: idle'a çek (sonraki UI'yi kirletme)
    save_agent_state(
        WORKSPACE,
        {
            "status": "idle",
            "scope_rel": "",
            "goal": "",
            "turn": 0,
            "max_turns": 8,
            "touched_files": [],
            "stop_requested": False,
        },
    )

    if fails:
        print("FAIL", fails)
        print(json.dumps(wb, ensure_ascii=True, indent=2)[:2500])
        return 1
    print(
        f"PASS e2 workbench — status={ag.get('status_label')} "
        f"hint={ag.get('path_hint')} e2_n={e2.get('sample_total')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
