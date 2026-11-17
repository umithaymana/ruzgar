# Created by Ümit & Gökçenur
"""F2.2 — derin Şamile kademe API + fen skip smoke."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from ilim_assistant.shamela_rag_shards import (
        pick_shamela_cats_for_query,
        search_shamela_shards,
    )

    ready = {
        "06_hadis_sunen": {},
        "07_hadis_serh": {},
        "10_hadis_ilimleri": {},
        "24_siyer": {},
        "26_teracim": {},
        "25_tarih": {},
        "01_akaid": {},
    }
    # Fen → boş
    assert pick_shamela_cats_for_query("fotosentez nedir", ready) == []
    # Hadis hızlı
    c1 = pick_shamela_cats_for_query("buhari niyet hadisi", ready)
    assert "06_hadis_sunen" in c1
    # Deep + exclude
    c2 = pick_shamela_cats_for_query(
        "buhari niyet hadisi", ready, deep=True, exclude=c1
    )
    assert not set(c2) & set(c1)
    # deep: boş registry → [] (embedder yüklemeden)
    with patch(
        "ilim_assistant.shamela_rag_shards.load_registry",
        return_value={"ready": {}},
    ):
        out = search_shamela_shards("niyet hadisi", top_k=3, deep=True)
        assert out == []
    print("smoke_f2_2_deep_shamela OK", c1, c2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
