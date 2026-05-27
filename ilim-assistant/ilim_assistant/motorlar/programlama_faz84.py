# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 84: Kod ajanı tur LLM zaman aşımı (E1).

Tek turda dakikalarca bloklanan LLM çağrılarını keser; sonraki beyin profiline geçilir.
"""

from __future__ import annotations

import os
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Any, Callable, TypeVar

FAZ84_VERSION = "programlama-faz84-v1-2026-05-27"

T = TypeVar("T")


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ84", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz84_enabled() -> bool:
    return _enabled()


def llm_turn_timeout_sec() -> float:
    try:
        return max(
            15.0,
            min(float(os.environ.get("RUZGAR_FAZ84_LLM_TURN_TIMEOUT_SEC", "90")), 300.0),
        )
    except ValueError:
        return 90.0


def run_with_llm_turn_timeout(
    fn: Callable[[], T],
    *,
    timeout_sec: float | None = None,
) -> tuple[T | None, bool, float]:
    """
    fn çalıştır; süre aşımında (None, True, elapsed) döner.
    Kapalıyken zaman aşımı yok.
    """
    t0 = time.perf_counter()
    if not _enabled():
        return fn(), False, time.perf_counter() - t0
    limit = float(timeout_sec if timeout_sec is not None else llm_turn_timeout_sec())
    with ThreadPoolExecutor(max_workers=1) as pool:
        fut = pool.submit(fn)
        try:
            return fut.result(timeout=limit), False, time.perf_counter() - t0
        except FuturesTimeoutError:
            return None, True, time.perf_counter() - t0


def faz84_directive() -> str:
    return (
        "[Faz 84 — tur LLM süresi]\n"
        f"Her kod ajanı turunda LLM üst sınırı ~{int(llm_turn_timeout_sec())} sn; "
        "aşımda sonraki beyin profili denenir.\n"
        f"Kapat: RUZGAR_FAZ84=0 · {FAZ84_VERSION}\n"
    )


def enrich_health_build(build: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(build or {})
    out["programlama_faz84"] = faz84_enabled()
    out["faz84_llm_turn_timeout_sec"] = llm_turn_timeout_sec()
    return out
