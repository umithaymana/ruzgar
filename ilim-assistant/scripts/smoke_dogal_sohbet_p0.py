# -*- coding: utf-8 -*-
"""P0 doğal sohbet kapısı — video panel + lookup/sohbet ayrımı."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ilim_assistant.motorlar.video_faz71 import maybe_instant_faz71  # noqa: E402
from ilim_assistant.ruzgar_anlik_niyet_gate import (  # noqa: E402
    collect_library_llm_context,
    library_instant_would_match,
    should_defer_library_instant,
)
from ilim_assistant.ruzgar_siyer_kutuphane import try_siyer_reply  # noqa: E402


def _ok(cond: bool, label: str) -> int:
    print(("OK" if cond else "FAIL"), "-", label)
    return 0 if cond else 1


def main() -> int:
    failed = 0
    # Video: kitap/UI paneli video olmamalı
    failed += _ok(
        maybe_instant_faz71("ihya ülumid din panelde aç") is None,
        "kitap panelde aç → video anlık yok",
    )
    failed += _ok(
        maybe_instant_faz71("kesim panelini aç") is not None,
        "kesim paneli → video anlık var",
    )
    # Lookup korunur
    failed += _ok(
        not should_defer_library_instant("siyer nedir"),
        "siyer nedir → defer yok",
    )
    failed += _ok(
        try_siyer_reply("siyer nedir") is not None,
        "siyer nedir → anlık cevap",
    )
    # Sohbet/anlat → defer
    failed += _ok(
        should_defer_library_instant("hicreti daha açık anlat"),
        "hicreti anlat → defer",
    )
    failed += _ok(
        should_defer_library_instant("siyer hakkında sohbet edelim"),
        "siyer sohbet → defer",
    )
    ctx = collect_library_llm_context("hicreti daha açık anlat")
    failed += _ok(
        bool(ctx) and "KÜTÜPHANE İPUCU" in ctx and "hicret" in ctx.lower(),
        "anlat → LLM kütüphane ipucu",
    )
    failed += _ok(
        library_instant_would_match("siyer nedir"),
        "siyer nedir → library match",
    )
    print(f"result: {8 - failed}/8 pass")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
