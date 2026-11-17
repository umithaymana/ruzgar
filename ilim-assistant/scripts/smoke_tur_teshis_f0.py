# Created by Ümit & Gökçenur
"""F0 smoke — tur teşhis kartı + miss sınıfı + warmup."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from ilim_assistant.ruzgar_tur_teshis_f0 import (
        FAZ_F0_VERSION,
        MISS_FILTERED,
        MISS_KUTUPHANE,
        MISS_NO_HITS,
        MISS_TIMEOUT,
        MISS_WEAK_LLM,
        attach_teshis_to_done,
        build_tur_kart,
        classify_miss,
        mark_warmup,
        recent_cards,
        warmup_snapshot,
    )
    from ilim_assistant.ruzgar_umed_kurallari import MISS_PHRASE

    assert FAZ_F0_VERSION
    mark_warmup("rag", True)
    mark_warmup("boot_bg_done", True)
    w = warmup_snapshot()
    assert w.get("state") in ("ilik", "kismi", "soguk", "isiniyor")
    assert w.get("rag") is True

    assert (
        classify_miss(
            reply=MISS_PHRASE,
            orch={"hits_count": 0},
            hits_count=0,
        )
        == MISS_NO_HITS
    )
    assert (
        classify_miss(
            reply=MISS_PHRASE,
            orch={"hits_count": 0, "hits_raw_count": 5},
            hits_count=0,
        )
        == MISS_FILTERED
    )
    assert (
        classify_miss(
            reply=MISS_PHRASE,
            orch={"kutuphane_usable": False},
            hits_count=2,
        )
        == MISS_KUTUPHANE
    )
    assert (
        classify_miss(
            reply=MISS_PHRASE,
            orch={},
            elapsed_sec=40.0,
            budget_sec=15.0,
            egitim_miss=True,
        )
        == MISS_TIMEOUT
    )
    assert (
        classify_miss(
            reply="Ollama yanıt vermedi",
            orch={},
            egitim_miss=True,
            elapsed_sec=2.0,
            budget_sec=38.0,
        )
        == MISS_WEAK_LLM
    )

    card = build_tur_kart(
        user_message="fotosentez nedir",
        reply=MISS_PHRASE,
        orch={"thin_pipe": False, "hits_count": 0, "hits_raw_count": 3},
        hits=[],
        elapsed_sec=12.5,
        provider=None,
        egitim_miss=False,
    )
    assert card["miss_class"] == MISS_FILTERED
    assert card["hits_count"] == 0
    assert card["thin_pipe"] is False

    done = attach_teshis_to_done(
        {
            "type": "done",
            "user_message": "selam",
            "full_reply": "Merhaba",
            "elapsed_sec": 0.2,
            "orchestra": {"thin_pipe": True, "hits_count": 0},
        },
        mode="genel",
    )
    assert "tur_teshis" in done
    assert done["tur_teshis"].get("thin_pipe") is True
    assert recent_cards(3)
    # F1.1 — Şamile arama tur bütçesini yemesin
    from ilim_assistant.ruzgar_umed_cevap_emri import (
        shamela_search_budget_sec,
        turn_budget_sec,
    )

    tb = turn_budget_sec("fotosentez nedir")
    sb = shamela_search_budget_sec("fotosentez nedir")
    assert sb <= tb * 0.41 + 0.01, (sb, tb)
    assert sb >= 4.0

    # F1.5 — timeout ≠ öğret
    from ilim_assistant.ruzgar_umed_kurallari import TIMEOUT_PHRASE

    assert "öğret" not in TIMEOUT_PHRASE.lower() or "bilmiyorum" in TIMEOUT_PHRASE.lower()
    assert classify_miss(reply=TIMEOUT_PHRASE, egitim_miss=True) == MISS_TIMEOUT

    print("smoke_tur_teshis_f0 OK", FAZ_F0_VERSION, "F1.1/F1.5 ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
