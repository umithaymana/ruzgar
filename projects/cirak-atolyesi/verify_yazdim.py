# Created by Ümit & Gökçenur — Dilim B
"""Yazdım = diskte var — self-check."""
from pathlib import Path

PASS_LINE = 'PASS cirak-B'


def main() -> int:
    here = Path(__file__).resolve()
    text = here.read_text(encoding='utf-8')
    if PASS_LINE not in text:
        print('FAIL missing PASS')
        return 1
    print(PASS_LINE)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
