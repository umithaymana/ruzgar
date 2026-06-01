#!/usr/bin/env python3
"""Blok J — tercüme atölye smoke (API'siz mantık + route listesi)."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
REPO = _ROOT.parent


def main() -> int:
    from desktop_server import _tercume_save_rel_allowed

    with tempfile.TemporaryDirectory() as td:
        # Route helper uses REPO_ROOT — test allowed path under real repo
        out = REPO / "ilim-assistant" / "arsiv" / "tercume-output" / "_smoke_test.txt"
        try:
            p = _tercume_save_rel_allowed(out.relative_to(REPO).as_posix())
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("smoke", encoding="utf-8")
            p.unlink(missing_ok=True)
        except Exception as exc:
            print("FAIL save path", exc)
            return 1

    try:
        from fastapi import HTTPException

        try:
            _tercume_save_rel_allowed("projects/evil.txt")
            print("FAIL should reject projects/")
            return 1
        except HTTPException:
            pass
    except ImportError:
        try:
            _tercume_save_rel_allowed("projects/evil.txt")
            print("FAIL should reject projects/")
            return 1
        except Exception:
            pass

    from desktop_server import app

    paths = {getattr(r, "path", "") for r in app.routes}
    needed = {
        "/api/tercume/save-target",
        "/api/tercume/import-url",
        "/api/tercume/translate-chunk",
        "/api/tercume/source-pages",
        "/api/tercume/config",
        "/api/tercume/readiness",
    }
    missing = [p for p in needed if p not in paths]
    if missing:
        print("FAIL routes", missing)
        return 1

    print("OK tercume blok J — save-target + routes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
