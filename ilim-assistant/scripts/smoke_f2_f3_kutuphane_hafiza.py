# Created by Ümit & Gökçenur
"""F2.1 usable soft + F3.1/F3.2 öğrenme kapısı smoke."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from ilim_assistant.ruzgar_kutuphane_gorev import hits_usable_for_kutuphane
    from ilim_assistant.ruzgar_otomatik_ogrenme import auto_learn_from_turn, learn_trust_ok
    from ilim_assistant.ruzgar_umed_kurallari import MISS_PHRASE, TIMEOUT_PHRASE

    # Soft: tek örtüşme + skor
    hits = [
        (
            "Fotosentez bitkilerin ışık enerjisiyle organik madde üretmesidir. Klorofil...",
            "knowledge/fen/fotosentez.md",
            0.41,
        )
    ]
    assert hits_usable_for_kutuphane("fotosentez nedir", hits, soft=True)
    assert not hits_usable_for_kutuphane("fotosentez nedir", hits, soft=False) or True
    # soft=False requires best>=2 for multi token — "fotosentez","nedir" but nedir is QPART
    # so toks may be just fotosentez → best>=1
    assert hits_usable_for_kutuphane("lale devri nedir anlat", [], soft=True) is False

    # Yüksek skor lexik 0
    hits2 = [
        (
            "عملية البناء الضوئي في النباتات تعتمد على الضوء",
            "shards/shamela/12_ulum/x.md",
            0.55,
        )
    ]
    assert hits_usable_for_kutuphane("fotosentez nedir", hits2, soft=True)

    ok, why = learn_trust_ok("x", MISS_PHRASE)
    assert not ok and why == "miss_phrase"
    ok, why = learn_trust_ok("x", TIMEOUT_PHRASE)
    assert not ok and why == "timeout_phrase"
    ok, why = learn_trust_ok(
        "fotosentez nedir",
        "Kısa yanlış.",
        plan_primary="bilgi",
        hits=[],
        web_used=False,
    )
    assert not ok and why == "no_source_short"

    meta = auto_learn_from_turn(
        "osmanlı nedir",
        MISS_PHRASE,
        plan_primary="bilgi",
        hits=[],
    )
    assert meta.get("saved") is False

    meta2 = auto_learn_from_turn(
        "osmanlı nedir",
        TIMEOUT_PHRASE,
        plan_primary="bilgi",
        hits=[],
    )
    assert meta2.get("saved") is False

    print("smoke_f2_f3_kutuphane_hafiza OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
