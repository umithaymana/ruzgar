# Created by Ümit & Gökçenur
"""F2.4 Şamile cat + F2.6 ilim provider zinciri smoke."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from ilim_assistant.ruzgar_genel_faz90 import (
        build_ilim_local_first_chain_ids,
        build_ilim_rag_brain_chain_ids,
        ilim_rag_cloud_first_enabled,
    )
    from ilim_assistant.shamela_rag_shards import pick_shamela_cats_for_query

    # F2.4 — fen sorusu Şamile'ye gitmesin
    ready = {
        "06_hadis_sunen": {},
        "01_akaid": {},
        "24_siyer": {},
        "39_genel": {},
    }
    assert pick_shamela_cats_for_query("fotosentez nedir", ready) == []
    assert pick_shamela_cats_for_query("elektron nedir anlat", ready) == []
    # din sorusu hâlâ seçsin
    cats = pick_shamela_cats_for_query("sahih buhari niyet hadisi", ready)
    assert cats, cats
    assert any("hadis" in c for c in cats), cats

    # F2.6 — varsayılan cloud-first kapalı
    os.environ.pop("RUZGAR_ILIM_RAG_CLOUD_FIRST", None)
    assert ilim_rag_cloud_first_enabled() is False
    local = build_ilim_local_first_chain_ids()
    assert local[0] in ("denge", "hizli", "gemini", "groq"), local
    # local-first zincirinde denge/hizli gemini'den önce (ollama varsa)
    rag_chain = build_ilim_rag_brain_chain_ids()
    if "denge" in rag_chain and "gemini" in rag_chain:
        assert rag_chain.index("denge") < rag_chain.index("gemini"), rag_chain

    print("smoke_f2_ilim_provider_cats OK", cats[:3], rag_chain[:4])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
