#!/usr/bin/env python3
"""Smoke — Faz 85 health alanları (status/ok) · «sadece doğrulama» tuzağı kapalı."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_SAMPLE = '''"""FastAPI — health"""
from __future__ import annotations

from fastapi import FastAPI

app = FastAPI(title="health")


@app.get("/health")
def health() -> dict[str, str]:
    return {"ok": "true", "service": "health", "version": "2.1.0"}
'''


def main() -> int:
    from ilim_assistant.motorlar.programlama_faz85 import (
        extract_health_fields,
        patch_main_py_content,
        try_fast_deterministic_task,
        _goal_wants_health_extra_fields,
        _try_verify_only,
    )

    fails = 0

    # 1) çıkarım
    goal = "health endpointine status alanı ekle pytest geçir"
    fields = extract_health_fields(goal)
    ok = _goal_wants_health_extra_fields(goal) and fields.get("status") == "ok"
    print(f"  {'OK' if ok else 'FAIL'} extract status={fields}")
    if not ok:
        fails += 1

    goal_v = "health endpointine status: up ekle version 3.0.0 pytest geçir"
    fields_v = extract_health_fields(goal_v)
    ok2 = fields_v.get("status") == "up" and fields_v.get("version") == "3.0.0"
    print(f"  {'OK' if ok2 else 'FAIL'} extract status+version={fields_v}")
    if not ok2:
        fails += 1

    # 2) bellek içi yama
    patched, changed = patch_main_py_content(
        _SAMPLE, service="health", fields={"status": "ok"}
    )
    ok3 = changed and '"status": "ok"' in patched
    print(f"  {'OK' if ok3 else 'FAIL'} patch_main_py status")
    if not ok3:
        fails += 1

    # 3) verify_only bu hedefi yemesin
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        proj = root / "projects" / "health"
        (proj / "app").mkdir(parents=True)
        (proj / "tests").mkdir(parents=True)
        (proj / "app" / "__init__.py").write_text("", encoding="utf-8")
        (proj / "app" / "main.py").write_text(_SAMPLE, encoding="utf-8")
        (proj / "tests" / "test_health.py").write_text(
            "def test_noop():\n    assert True\n",
            encoding="utf-8",
        )
        vo = _try_verify_only(root, "projects/health", goal)
        ok4 = vo is None
        print(f"  {'OK' if ok4 else 'FAIL'} verify_only skips status goal (got={vo is not None})")
        if not ok4:
            fails += 1

        hit = try_fast_deterministic_task(
            root,
            "projects/health",
            goal,
            allow_agent_fallback=False,
        )
        ok5 = (
            bool(hit)
            and hit.get("source") == "fast_health_fields_faz85"
            and int(hit.get("writes_ok") or 0) >= 1
        )
        main_txt = (proj / "app" / "main.py").read_text(encoding="utf-8")
        ok5 = ok5 and '"status"' in main_txt
        print(
            f"  {'OK' if ok5 else 'FAIL'} fast path writes "
            f"source={(hit or {}).get('source')} writes={(hit or {}).get('writes_ok')}"
        )
        if not ok5:
            fails += 1
            if hit:
                print("   detail:", str(hit.get("detail") or "")[:240])

    if fails:
        print(f"FAIL {fails}")
        return 1
    print("PASS programlama_faz85_fields_smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
