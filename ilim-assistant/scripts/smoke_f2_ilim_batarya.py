# Created by Ümit & Gökçenur
"""F2.5 — kısa ilim batarya (yazım + usable + cat + provider; canlı LLM yok)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from ilim_assistant.ruzgar_kutuphane_gorev import hits_usable_for_kutuphane
    from ilim_assistant.ruzgar_soru_yazim import resolve_user_niyet
    from ilim_assistant.shamela_rag_shards import pick_shamela_cats_for_query

    ready = {"06_hadis_sunen": {}, "24_siyer": {}, "01_akaid": {}, "03_tefsir": {}}

    # Yazım
    f, m = resolve_user_niyet("foto senrez nedir")
    assert "fotosentez" in f.lower() and m.get("changed")

    # Usable soft
    hits = [
        (
            "Fotosentez bitkilerde ışıkla organik madde üretimidir.",
            "knowledge/fen.md",
            0.4,
        )
    ]
    assert hits_usable_for_kutuphane("fotosentez nedir", hits, soft=True)

    # Cat: fen boş, hadis dolu
    assert pick_shamela_cats_for_query("fotosentez nedir", ready) == []
    assert pick_shamela_cats_for_query("buhari niyet hadisi nedir", ready)

    print("smoke_f2_ilim_batarya OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
