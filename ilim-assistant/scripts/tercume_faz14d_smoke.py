#!/usr/bin/env python3
"""Faz 14D — kayıt klasörü hafızası ve _v2 çakışma sürümleme."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
REPO = _ROOT.parent
sys.path.insert(0, str(_ROOT))


def main() -> int:
    from ilim_assistant.motorlar import tercume_save_prefs as mod
    from ilim_assistant.motorlar.tercume_save_prefs import (
        SAVE_PREFS_VERSION,
        get_save_prefs,
        prepare_save_path,
        remember_save_rel,
    )

    if "v14d" not in SAVE_PREFS_VERSION:
        print("FAIL version", SAVE_PREFS_VERSION)
        return 1

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        out_dir = root / "ilim-assistant" / "arsiv" / "tercume-output"
        out_dir.mkdir(parents=True)
        existing = out_dir / "eser_tr.txt"
        existing.write_text("ilk", encoding="utf-8")

        prefs_dir = root / ".ruzgar"
        prefs_dir.mkdir()
        orig_prefs = mod._prefs_path
        orig_repo = mod._repo_root
        mod._prefs_path = lambda: prefs_dir / "tercume_save_prefs.json"  # type: ignore[method-assign]
        mod._repo_root = lambda: root  # type: ignore[method-assign]

        rel = "ilim-assistant/arsiv/tercume-output/eser_tr.txt"
        prep = prepare_save_path(rel, root=root)
        if not prep.get("versioned") or not str(prep["rel"]).endswith("_v2.txt"):
            print("FAIL versioned path", prep)
            return 1

        target = prep["path"]
        target.write_text("ikinci", encoding="utf-8")
        remember_save_rel(prep["rel"])
        prefs = get_save_prefs()
        if prefs.get("last_save_dir") != "ilim-assistant/arsiv/tercume-output":
            print("FAIL last_save_dir", prefs)
            return 1

        prep3 = prepare_save_path(rel, root=root)
        if not str(prep3["rel"]).endswith("_v3.txt"):
            print("FAIL v3", prep3)
            return 1

        mod._prefs_path = orig_prefs  # type: ignore[method-assign]
        mod._repo_root = orig_repo  # type: ignore[method-assign]

    from desktop_server import _tercume_save_rel_allowed, app

    paths = {getattr(r, "path", "") for r in app.routes}
    if "/api/tercume/save-prefs" not in paths:
        print("FAIL save-prefs route")
        return 1

    try:
        p = _tercume_save_rel_allowed("ilim-assistant/arsiv/tercume-output/_smoke14d.txt")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x", encoding="utf-8")
        p.unlink(missing_ok=True)
    except Exception as exc:
        print("FAIL save allowed", exc)
        return 1

    from ilim_assistant.motorlar.tercume_atolye import workbench_config

    sf = workbench_config().get("save_faz14d") or {}
    if not sf.get("collision_suffix"):
        print("FAIL save_faz14d", sf)
        return 1

    print("OK tercume faz14d — save prefs + _v2 versioning")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
