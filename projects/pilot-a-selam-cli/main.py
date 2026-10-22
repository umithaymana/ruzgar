#!/usr/bin/env python3
"""CLI — Pilot A selam aracı (Rüzgar P6).

Ümit & Gökçenur — güvenli scaffold + pytest.
"""
from __future__ import annotations

import argparse


def greet(name: str, *, upper: bool = False) -> str:
    msg = f"Merhaba, {name}!"
    return msg.upper() if upper else msg


def run(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Pilot A — selam CLI")
    p.add_argument("name", nargs="?", default="dünya", help="Selamlanacak isim")
    p.add_argument(
        "--upper",
        action="store_true",
        help="Mesajı büyük harfle yaz",
    )
    args = p.parse_args(argv)
    print(greet(args.name, upper=bool(args.upper)))
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
