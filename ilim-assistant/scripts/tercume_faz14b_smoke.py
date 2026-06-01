#!/usr/bin/env python3
"""Faz 14B — çeviri kalite skoru özeti + workbench config."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))


def main() -> int:
    from ilim_assistant.motorlar.tercume_translate_quality import (
        QUALITY_PASS_SCORE,
        QUALITY_VERSION,
        score_translation,
        summarize_chunk_qualities,
    )

    if "v14b" not in QUALITY_VERSION:
        print("FAIL version", QUALITY_VERSION)
        return 1

    good = score_translation("Merhaba dünya", "Hello world", tgt_lang="en")
    if not good.get("ok") or good.get("score", 0) < 50:
        print("FAIL good sample", good)
        return 1

    bad = score_translation("kaynak paragraf", "[HATA] I cannot translate this", tgt_lang="tr")
    if bad.get("ok") or bad.get("score", 100) >= QUALITY_PASS_SCORE:
        print("FAIL should reject error leak", bad)
        return 1
    short = score_translation("Uzun kaynak metni " * 20, "kısa", tgt_lang="tr")
    if not short.get("issues"):
        print("FAIL short should list issues", short)
        return 1

    outs = [
        {"page": "Sayfa 1", "ok": True, "quality_score": 88},
        {"page": "Sayfa 2", "ok": True, "quality_score": 42},
        {"page": "Sayfa 3", "ok": False, "error": "x"},
    ]
    summ = summarize_chunk_qualities(outs)
    if summ.get("low_count") != 1 or summ.get("pages_scored") != 2:
        print("FAIL summarize", summ)
        return 1
    if summ.get("pass_threshold") != QUALITY_PASS_SCORE:
        print("FAIL threshold", summ)
        return 1

    from ilim_assistant.motorlar.tercume_atolye import workbench_config

    q = workbench_config().get("quality_faz14b") or {}
    if not q.get("ui_strip") or q.get("pass_score") != 55:
        print("FAIL workbench quality_faz14b", q)
        return 1

    print("OK tercume faz14b — quality score + summary + config")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
