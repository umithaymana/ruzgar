# -*- coding: utf-8 -*-
"""Smoke — Arapça Şamile gövdesi Türkçe sorgu lexik süzgecinde elenmesin."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _ok(cond: bool, label: str) -> int:
    print(("OK" if cond else "FAIL"), "-", label)
    return 0 if cond else 1


def main() -> int:
    failed = 0
    from ilim_assistant.ruzgar_anlam_koruma import (
        arabic_letter_ratio,
        chunk_fits_query,
        chunk_is_arabic_heavy,
        filter_rag_hits,
        fold_ascii,
    )

    ar = (
        "أخبرنا الشيخ الإمام الحافظ أبو عبد الله محمد بن إسماعيل البخاري "
        "قال إنما الأعمال بالنيات وإنما لكل امرئ ما نوى"
    )
    q = "Buhari niyet hadisi nedir"
    src = "ilim/din/shamela/06_hadis_sunen/sahih_buhari/kitab.md"

    failed += _ok(fold_ascii(ar) == "", "fold_ascii Arapça boşaltır (tuzak)")
    failed += _ok(arabic_letter_ratio(ar) >= 0.4, "arabic_letter_ratio")
    failed += _ok(chunk_is_arabic_heavy(ar), "chunk_is_arabic_heavy")

    # Bypass açık (varsayılan)
    os.environ.pop("RUZGAR_RAG_ARABIC_LEX_BYPASS", None)
    failed += _ok(
        chunk_fits_query(q, ar, source=src) is True,
        "chunk_fits Arapça+kaynak True",
    )
    failed += _ok(
        chunk_fits_query(q, ar, source="") is True,
        "chunk_fits Arapça bypass True",
    )

    # Bypass kapalı: kaynak yolunda buhari varsa hâlâ True
    os.environ["RUZGAR_RAG_ARABIC_LEX_BYPASS"] = "0"
    failed += _ok(
        chunk_fits_query(q, ar, source=src) is True,
        "bypass kapalı + kaynak yolu True",
    )
    failed += _ok(
        chunk_fits_query(q, ar, source="") is False,
        "bypass kapalı + boş kaynak False",
    )
    os.environ.pop("RUZGAR_RAG_ARABIC_LEX_BYPASS", None)

    hits = [(ar, src, 0.55), ("tamamen alakasiz latin metin xyz", "other/x.md", 0.55)]
    kept = filter_rag_hits(q, hits, min_score=0.32, soft=False)
    failed += _ok(len(kept) >= 1 and kept[0][1] == src, "filter_rag_hits Arapça tutar")

    # Eski tuzak: skorlu Arapça hit soft=False ile [] olmamalı
    only_ar = [(ar, src, 0.48)]
    kept2 = filter_rag_hits(q, only_ar, min_score=0.32, soft=False)
    failed += _ok(len(kept2) == 1, "tek Arapça hit soft=False kalır")

    from ilim_assistant.ruzgar_kutuphane_gorev import (
        filter_hits_lexically,
        hits_usable_for_kutuphane,
    )

    lex = filter_hits_lexically(q, [(ar, src, 0.48)])
    failed += _ok(len(lex) >= 1, "kutuphane lex Arapça tutar")

    # Usable: Arapça skor 0.28+ soft kabul (lexik 0 olsa bile)
    usable = hits_usable_for_kutuphane(q, [(ar, src, 0.30)], soft=True)
    failed += _ok(usable is True, "usable Arapça skor 0.30")

    total = 12
    print(f"result: {total - failed}/{total} pass")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
