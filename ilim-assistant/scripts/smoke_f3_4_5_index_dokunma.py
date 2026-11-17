# Created by Ümit & Gökçenur
"""F3.4 indeks bekliyor + F3.5 dokunma etiketi smoke."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from ilim_assistant.rag_store import _is_dokunma_markdown, nebula_dokunma_inventory
    from ilim_assistant.ruzgar_otomatik_ogrenme import (
        otomatik_ogrenme_status,
        rag_index_pending_status,
    )

    st = rag_index_pending_status()
    assert "index_pending" in st and "hint" in st

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        good = root / "ok.md"
        good.write_text("# normal\nmerhaba\n", encoding="utf-8")
        tagged = root / "skip.md"
        tagged.write_text("dokunma: true\n# gizli\n", encoding="utf-8")
        named = root / "_DOKUNMA_eski.md"
        named.write_text("# eski\n", encoding="utf-8")
        side = root / "yan.md"
        side.write_text("# yan\n", encoding="utf-8")
        (root / "yan.md.dokunma").write_text("1", encoding="utf-8")

        assert not _is_dokunma_markdown(good, good.read_text(encoding="utf-8"))
        assert _is_dokunma_markdown(tagged, tagged.read_text(encoding="utf-8"))
        assert _is_dokunma_markdown(named, named.read_text(encoding="utf-8"))
        assert _is_dokunma_markdown(side, side.read_text(encoding="utf-8"))

        inv = nebula_dokunma_inventory(root)
        assert inv["dokunma"] == 3
        assert inv["aday"] == 1
        assert inv["policy"] == "dokunma_etiketi_veya_ingest"

    ost = otomatik_ogrenme_status()
    assert "index_status" in ost
    assert "nebula_dokunma" in ost
    print("smoke_f3_4_5_index_dokunma OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
