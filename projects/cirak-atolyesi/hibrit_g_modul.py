# Created by Ümit & Gökçenur — Dilim G hibrit
"""Ajan konuşur; yeşil = disk + smoke."""
from pathlib import Path

PASS_LINE = 'PASS cirak-G'


def hibrit_ozet() -> str:
    return PASS_LINE


def main() -> int:
    here = Path(__file__).resolve()
    text = here.read_text(encoding='utf-8')
    if PASS_LINE not in text:
        print('FAIL claim without disk content')
        return 1
    # Scope disiplini: dosya atölyede olmalı
    if 'cirak-atolyesi' not in str(here).replace('\\', '/'):
        print('FAIL wrong scope')
        return 1
    print(PASS_LINE)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
