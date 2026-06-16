#!/usr/bin/env python3
"""Çok dilli verify smoke — Adım 10."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

WORKSPACE = Path((os.environ.get("RUZGAR_WORKSPACE_ROOT") or "").strip() or str(_ROOT.parent))


def main() -> int:
    from ilim_assistant.motorlar.programlama_multilingual_verify import (
        run_multilingual_verify_smoke,
    )

    rep = run_multilingual_verify_smoke(WORKSPACE)
    print(json.dumps(rep, ensure_ascii=True, indent=2))
    return 0 if rep.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
