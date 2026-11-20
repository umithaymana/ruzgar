# Created by Ümit & Gökçenur — Dilim D3
"""Smoke: dar_patch_d1.carp."""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from dar_patch_d1 import carp


def main() -> int:
    if carp(3, 4) != 12:
        print('FAIL carp')
        return 1
    print('PASS cirak-D3')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
