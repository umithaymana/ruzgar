#!/usr/bin/env python3
"""Faz 87 — post-verify heal senaryosu (LLM yok)."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
WORKSPACE = ROOT.parent


def main() -> int:
    from ilim_assistant.motorlar.programlama_faz6 import run_scaffold
    from ilim_assistant.motorlar.programlama_motoru import ProgramlamaAraclari
    from ilim_assistant.motorlar.programlama_faz14 import run_project_verify
    from ilim_assistant.motorlar.programlama_faz87 import (
        FAZ87_VERSION,
        try_post_verify_heal,
    )

    stamp = int(time.time())
    scope = f"projects/heal-bat-{stamp}"
    slug = scope.split("/")[-1]
    service = slug.replace("-", "_")
    sc = run_scaffold("fastapi_api", slug, WORKSPACE, force=True)
    if not sc.get("ok"):
        print("scaffold fail", sc.get("error"))
        return 1
    broken = f'''"""Heal test."""
from fastapi import FastAPI
app = FastAPI()
@app.get("/health")
def health() -> dict[str, str]:
    return {{"ok": "false", "service": "wrong"}}
'''
    rel = f"{scope}/app/main.py"
    w = ProgramlamaAraclari(WORKSPACE).write(rel, broken)
    if not w.ok:
        print("write fail", w.detail)
        return 1
    goal = "health duzelt pytest gecir"
    v0 = run_project_verify(WORKSPACE, scope, goal=goal)
    print("before verify ok:", bool(v0 and v0.ok))
    heal = try_post_verify_heal(
        WORKSPACE, scope, goal, verify_output=(v0.output if v0 else "") or ""
    )
    print(FAZ87_VERSION)
    print(json.dumps(heal, ensure_ascii=True, indent=2))
    ok = bool(heal and heal.get("verify_ok"))
    print("RESULT:", "OK" if ok else "FAIL")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
