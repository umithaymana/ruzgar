#!/usr/bin/env python3
"""Faz 14C — kalıcı terim belleği (TM) diske."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))


def main() -> int:
    from ilim_assistant.motorlar import tercume_translate_memory as mod
    from ilim_assistant.motorlar.tercume_translate_memory import (
        TERCUME_MEMORY_VERSION,
        clear_session,
        consistency_block,
        memory_status,
        mine_line_pairs,
        record_translation,
        seed_pairs_from_glossary,
    )

    if "v14c" not in TERCUME_MEMORY_VERSION:
        print("FAIL version", TERCUME_MEMORY_VERSION)
        return 1

    mined = mine_line_pairs("Satır bir\nSatır iki", "Line one\nLine two")
    if len(mined) != 2:
        print("FAIL mine_line_pairs", mined)
        return 1

    with tempfile.TemporaryDirectory() as td:
        tm_dir = Path(td) / "tercume_tm"
        tm_dir.mkdir()
        orig = mod._tm_dir
        mod._tm_dir = lambda: tm_dir  # type: ignore[method-assign]
        mod._sessions.clear()

        rel = "ilim-assistant/arsiv/test_kitap.pdf"
        seed_pairs_from_glossary(rel, "Mecdüddîn halvet", tgt_lang="tr")
        record_translation(
            rel,
            source_text="Satır A\nSatır B",
            translated="Satır A tr\nSatır B tr",
            tgt_lang="tr",
        )
        st = memory_status(rel, tgt_lang="tr")
        if not st.get("ok") or st.get("pairs", 0) < 1:
            print("FAIL memory_status", st)
            return 1
        if not st.get("persisted_on_disk"):
            print("FAIL not on disk", st)
            return 1

        mod._sessions.clear()
        block = consistency_block(rel, tgt_lang="tr")
        if "TERİM" not in block and "Satır" not in block and "Mecdüddîn" not in block:
            print("FAIL reload block", block[:160])
            return 1

        clear_session(rel, tgt_lang="tr")
        st2 = memory_status(rel, tgt_lang="tr")
        if st2.get("pairs", 1) != 0:
            print("FAIL after clear", st2)
            return 1

        mod._tm_dir = orig  # type: ignore[method-assign]

    from desktop_server import app

    paths = {getattr(r, "path", "") for r in app.routes}
    if "/api/tercume/memory-status" not in paths:
        print("FAIL memory-status route")
        return 1

    from ilim_assistant.motorlar.tercume_atolye import workbench_config

    tm = workbench_config().get("tm_faz14c") or {}
    if not tm.get("persist_dir"):
        print("FAIL tm_faz14c config", tm)
        return 1

    print("OK tercume faz14c — persistent TM + memory-status")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
