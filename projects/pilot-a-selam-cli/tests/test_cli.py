# -*- coding: utf-8 -*-
"""Pilot A — selam CLI pytest."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from main import greet, run  # noqa: E402


def test_greet_default() -> None:
    assert greet("Ümit") == "Merhaba, Ümit!"


def test_greet_upper() -> None:
    assert greet("ruzgar", upper=True) == "MERHABA, RUZGAR!"


def test_run_ok(capsys) -> None:
    assert run(["Gökçenur"]) == 0
    assert "Merhaba, Gökçenur!" in capsys.readouterr().out


def test_run_upper(capsys) -> None:
    assert run(["--upper", "pilot"]) == 0
    out = capsys.readouterr().out
    assert "MERHABA, PILOT!" in out
