# -*- coding: utf-8 -*-
"""Incremental RAG rebuild after Kimya expand."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ilim_assistant.rag_store import build_index  # noqa: E402

if __name__ == "__main__":
    out = build_index(incremental=True)
    print(json.dumps(out, ensure_ascii=False, indent=2))
