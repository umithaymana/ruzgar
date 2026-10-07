# -*- coding: utf-8 -*-
"""RAG incremental rebuild — değişen/eklenen knowledge/*.md gömer.

Kullanım (ruzgar venv):
  python scripts/rag_incremental_rebuild.py

Not: embeddings.npy / chunks.jsonl genelde gitignore; yerel indekstir.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ilim_assistant.rag_store import build_index  # noqa: E402


def main() -> int:
    out = build_index(incremental=True)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out.get("status") in ("incremental", "cached", "ok", "built") else 1


if __name__ == "__main__":
    raise SystemExit(main())
