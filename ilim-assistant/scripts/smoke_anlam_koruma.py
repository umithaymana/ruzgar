# -*- coding: utf-8 -*-
"""Smoke — anlam kilidi / RAG süzgeç / cevap koruması."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def main() -> int:
    from ilim_assistant.ruzgar_anlam_koruma import (
        answer_fits_question,
        filter_rag_hits,
        fuzzy_pair_allowed,
        guard_assistant_reply,
    )

    fails = 0

    def ok(name: str, cond: bool) -> None:
        nonlocal fails
        print(("OK" if cond else "FAIL"), name)
        if not cond:
            fails += 1

    ok("pair_tefsir_foto", not fuzzy_pair_allowed("tefsir nedir", "fotosentez nedir"))
    ok("pair_mat_esari", not fuzzy_pair_allowed("maturidi kimdir", "esari kimdir"))
    ok("pair_adin_anne", not fuzzy_pair_allowed("senin adin ne", "annemin adi ne"))
    ok(
        "fit_tefsir_good",
        answer_fits_question("tefsir nedir", "Tefsir ayetlerin açıklanmasıdır."),
    )
    ok(
        "fit_tefsir_bad",
        not answer_fits_question(
            "tefsir nedir", "Bitkilerin ışık enerjisiyle karbondioksit"
        ),
    )
    guarded = guard_assistant_reply(
        "tefsir nedir", "Bitkilerin ışık enerjisiyle karbondioksit ve sudan besin"
    )
    ok("guard_blocks", guarded is not None and "güven: düşük" in guarded.casefold())

    hits = [
        ("Fotosentez bitkilerde olur", "biyoloji.md", 0.55),
        ("Tefsir ayetlerin yorumudur", "kuran.md", 0.40),
    ]
    filtered = filter_rag_hits("tefsir nedir", hits, min_score=0.30)
    ok("rag_keeps_tefsir", len(filtered) == 1 and "Tefsir" in filtered[0][0])
    ok(
        "rag_drops_all_wrong",
        filter_rag_hits("tefsir nedir", [hits[0]], min_score=0.30) == [],
    )

    print(f"result: {8 - fails}/8")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
