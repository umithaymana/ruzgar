# Created by Ümit & Gökçenur
"""Ana Motor — bekleme sırasında geçen süre / tahmini süre (UI durum satırı)."""

from __future__ import annotations

import os
import time
from typing import Any, Iterator

# Faz bazlı kabaca üst sınır (sn) — kullanıcıya «takılmadı» hissi
_PHASE_ESTIMATE_SEC: dict[str, int] = {
    "retrieval": 20,
    "full_index": 28,
    "encyclopedic": 10,
    "gemini_first": 8,
    "archive": 22,
    "archive_detail": 18,
    "web": 15,
    "web_engine": 12,
    "agent_workspace": 6,
    "bilgi_index": 18,
    "bilim_fast": 12,
    "dilbilgisi": 14,
    "prefetch": 25,
    "ana_agent": 45,
}


def progress_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_PROGRESS_ETA", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def estimate_sec_for_phase(phase: str) -> int:
    p = (phase or "retrieval").strip().lower()
    try:
        base = int(os.environ.get("RUZGAR_ANA_PROGRESS_DEFAULT_SEC", "18"))
    except ValueError:
        base = 18
    return max(5, _PHASE_ESTIMATE_SEC.get(p, base))


def enrich_status_text(
    text: str,
    *,
    phase: str = "",
    started_monotonic: float | None = None,
    extra_estimate: int | None = None,
) -> str:
    """«İndeks taranıyor… (12 sn / ~25 sn)»"""
    raw = (text or "").strip()
    if not raw or not progress_enabled():
        return raw
    t0 = started_monotonic if started_monotonic is not None else time.monotonic()
    elapsed = max(0, int(time.monotonic() - t0))
    est = extra_estimate if extra_estimate is not None else estimate_sec_for_phase(phase)
    if " sn / ~" in raw or "sn geçti" in raw:
        return raw
    return f"{raw} ({elapsed} sn geçti · tahmini ~{est} sn)"


def enrich_status_event(
    ev: dict[str, Any],
    *,
    started_monotonic: float,
) -> dict[str, Any]:
    if str(ev.get("type") or "") != "status":
        return ev
    out = dict(ev)
    out["text"] = enrich_status_text(
        str(ev.get("text") or ""),
        phase=str(ev.get("phase") or ""),
        started_monotonic=started_monotonic,
    )
    out["progress_elapsed_sec"] = max(
        0, int(time.monotonic() - started_monotonic)
    )
    return out


def iter_enriched_status_events(
    events: list[dict[str, Any]],
    *,
    started_monotonic: float | None = None,
) -> Iterator[dict[str, Any]]:
    t0 = started_monotonic if started_monotonic is not None else time.monotonic()
    for ev in events:
        if isinstance(ev, dict) and ev.get("type") == "status":
            yield enrich_status_event(ev, started_monotonic=t0)
        else:
            yield ev
