#!/usr/bin/env python3
"""Çekirdek paket registry smoke — Adım 11."""
from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def main() -> int:
    from ilim_assistant.motorlar.programlama_cekirdek_paketleri import (
        run_cekirdek_smoke,
    )

    rep = run_cekirdek_smoke()
    print(json.dumps(rep, ensure_ascii=True, indent=2))
    return 0 if rep.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
