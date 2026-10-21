#!/usr/bin/env python3
"""Smoke — E2 supervised boot: health status alan yedek (0 write → yama)."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_SAMPLE = '''"""FastAPI — health"""
from fastapi import FastAPI
app = FastAPI(title="health")

@app.get("/health")
def health() -> dict[str, str]:
    return {"ok": "true", "service": "health", "version": "2.1.0"}
'''


def main() -> int:
    from ilim_assistant.motorlar.programlama_faz103_e2 import (
        e2_write_template_nudge,
        try_e2_supervised_write_boot,
        try_supervised_health_fields_boot,
    )
    from ilim_assistant.motorlar.programlama_faz39 import build_write_mandate_message

    fails = 0
    goal = "health endpointine status alanı ekle pytest geçir"

    nudge = e2_write_template_nudge("projects/health", goal)
    ok_n = "status" in nudge.lower() and "main.py" in nudge
    print(f"  {'OK' if ok_n else 'FAIL'} e2_write_template_nudge health")
    if not ok_n:
        fails += 1

    mandate = build_write_mandate_message(
        goal=goal, scope_rel="projects/health", tool_block="", turn=1
    )
    ok_m = "status" in mandate.lower()
    print(f"  {'OK' if ok_m else 'FAIL'} write_mandate health hint")
    if not ok_m:
        fails += 1

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        proj = root / "projects" / "health"
        (proj / "app").mkdir(parents=True)
        (proj / "app" / "__init__.py").write_text("", encoding="utf-8")
        (proj / "app" / "main.py").write_text(_SAMPLE, encoding="utf-8")

        boot = try_supervised_health_fields_boot(root, "projects/health", goal)
        ok_b = bool(boot.get("writes_ok")) and boot.get("source") == "e2_supervised_health_fields"
        main_txt = (proj / "app" / "main.py").read_text(encoding="utf-8")
        ok_b = ok_b and '"status"' in main_txt
        print(f"  {'OK' if ok_b else 'FAIL'} supervised health fields boot detail={boot.get('detail')!r}")
        if not ok_b:
            fails += 1

        # Unified entry: VERSION yok → health yedek
        (proj / "app" / "main.py").write_text(_SAMPLE, encoding="utf-8")
        unified = try_e2_supervised_write_boot(root, "projects/health", goal)
        ok_u = bool(unified.get("writes_ok")) and "status" in (
            (proj / "app" / "main.py").read_text(encoding="utf-8")
        )
        print(
            f"  {'OK' if ok_u else 'FAIL'} try_e2_supervised_write_boot "
            f"source={unified.get('source')!r}"
        )
        if not ok_u:
            fails += 1

    if fails:
        print(f"FAIL {fails}")
        return 1
    print("PASS programlama_supervised_health_smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
