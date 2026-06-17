#!/usr/bin/env python3
"""Yazım güvenliği — syntax, boş yazım, patch birleşik kapı smoke."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
WORKSPACE = ROOT.parent
VERSION = "programlama-write-guard-smoke-v1-2026-06-17"


def main() -> int:
    from ilim_assistant.motorlar.programlama_motoru import (
        ProgramlamaAraclari,
        validate_write_syntax,
    )
    from ilim_assistant.motorlar.programlama_patch import apply_search_replace

    checks: list[dict[str, object]] = []
    tools = ProgramlamaAraclari(WORKSPACE)
    rel_py = "projects/.ruzgar_write_guard_smoke/guard_test.py"
    rel_txt = "projects/.ruzgar_write_guard_smoke/note.txt"
    full_py = WORKSPACE / rel_py.replace("/", os.sep)
    full_txt = WORKSPACE / rel_txt.replace("/", os.sep)
    full_py.parent.mkdir(parents=True, exist_ok=True)
    valid_py = '"""guard"""\nx = 1\n'
    full_py.write_text(valid_py, encoding="utf-8")
    full_txt.write_text("hello\n", encoding="utf-8")

    bad_syntax = validate_write_syntax(rel_py, "Dosya icerigi:")
    checks.append(
        {
            "id": "syntax_reject",
            "ok": bad_syntax[0] is False,
            "detail": bad_syntax[1][:80],
        }
    )

    empty_rep = tools.write(rel_py, "   ")
    checks.append(
        {
            "id": "empty_write_reject",
            "ok": empty_rep.ok is False,
            "detail": (empty_rep.detail or "")[:80],
        }
    )

    patch_bad = apply_search_replace(
        WORKSPACE,
        rel_py,
        "x = 1",
        "Dosya icerigi:",
    )
    checks.append(
        {
            "id": "patch_syntax_reject",
            "ok": patch_bad.ok is False,
            "detail": (patch_bad.detail or "")[:80],
        }
    )

    patch_ok = apply_search_replace(WORKSPACE, rel_py, "x = 1", "x = 2")
    checks.append(
        {
            "id": "patch_valid_write",
            "ok": patch_ok.ok is True and "x = 2" in full_py.read_text(encoding="utf-8"),
            "detail": patch_ok.detail,
        }
    )

    try:
        full_py.unlink(missing_ok=True)
        full_txt.unlink(missing_ok=True)
        full_py.parent.rmdir()
    except OSError:
        pass

    ok = all(bool(c.get("ok")) for c in checks)
    report = {"ok": ok, "version": VERSION, "checks": checks}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print("RESULT:", "OK" if ok else "FAIL")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
