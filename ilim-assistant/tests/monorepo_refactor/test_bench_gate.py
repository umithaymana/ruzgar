"""P5 — üç dosyalı refactor gate doğrulaması."""

from __future__ import annotations

from bench_pkg.api import endpoint
from bench_pkg.core import VERSION
from bench_pkg.service import handler


def test_triple_refactor_gate() -> None:
    assert VERSION == "bench-v2"
    assert handler() == "bench-v2-svc"
    assert endpoint() == "bench-v2-svc-ok"
