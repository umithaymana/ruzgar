from __future__ import annotations

import hashlib
import time
from typing import Iterable

FAZ95_VERSION = "programlama-faz95-v1-2026-05-27"
_PROMPT_CACHE: dict[str, dict[str, object]] = {}
_PROMPT_CACHE_MAX = 128
_CACHE_STATS = {
    "hits": 0,
    "misses": 0,
    "evictions": 0,
}
_WINDOW_SEC = 300.0
_CACHE_EVENTS: list[tuple[float, int]] = []


def _clean_block(text: str, *, max_chars: int) -> str:
    t = " ".join((text or "").split()) if "\n" not in (text or "") else str(text or "").strip()
    if len(t) <= max_chars:
        return t
    return t[: max(0, max_chars - 3)].rstrip() + "..."


def optimize_prompt_blocks(
    blocks: Iterable[str],
    *,
    per_block_limit: int = 1800,
    total_limit: int = 5200,
) -> str:
    """P8: Programlama promptunu sınırlı bütçede tutar."""
    cleaned: list[str] = []
    seen: set[str] = set()
    total = 0
    for raw in blocks:
        b = _clean_block(str(raw or ""), max_chars=per_block_limit).strip()
        if not b:
            continue
        if b in seen:
            continue
        next_len = len(b) + (2 if cleaned else 0)
        if total + next_len > total_limit:
            break
        cleaned.append(b)
        seen.add(b)
        total += next_len
    return "\n\n".join(cleaned)


def build_prompt_cache_key(
    *,
    workspace_root: str | None,
    scope_rel: str,
    user_message: str,
    blocks: Iterable[str],
) -> str:
    raw = "\n||\n".join(str(b or "").strip() for b in blocks if str(b or "").strip())
    sig = hashlib.sha1(raw.encode("utf-8", errors="ignore")).hexdigest()[:16]
    ws = (workspace_root or "").strip().lower()
    scope = (scope_rel or "").strip().lower()
    msg = " ".join((user_message or "").split()).strip().lower()[:220]
    return f"{ws}|{scope}|{msg}|{sig}"


def get_prompt_cache(key: str, *, ttl_sec: int = 75) -> str:
    if not key:
        return ""
    now = time.time()
    row = _PROMPT_CACHE.get(key) or {}
    ts = float(row.get("ts") or 0.0)
    val = str(row.get("value") or "")
    if not val:
        _CACHE_STATS["misses"] = int(_CACHE_STATS.get("misses") or 0) + 1
        _record_cache_event(is_hit=False)
        return ""
    if now - ts > max(5, ttl_sec):
        _PROMPT_CACHE.pop(key, None)
        _CACHE_STATS["misses"] = int(_CACHE_STATS.get("misses") or 0) + 1
        _record_cache_event(is_hit=False)
        return ""
    _CACHE_STATS["hits"] = int(_CACHE_STATS.get("hits") or 0) + 1
    _record_cache_event(is_hit=True)
    return val


def set_prompt_cache(key: str, value: str) -> None:
    if not key or not value:
        return
    if len(_PROMPT_CACHE) >= _PROMPT_CACHE_MAX:
        oldest_key = min(_PROMPT_CACHE.items(), key=lambda kv: float(kv[1].get("ts") or 0.0))[0]
        _PROMPT_CACHE.pop(oldest_key, None)
        _CACHE_STATS["evictions"] = int(_CACHE_STATS.get("evictions") or 0) + 1
    _PROMPT_CACHE[key] = {"ts": time.time(), "value": value}


def prompt_cache_metrics() -> dict[str, object]:
    hits = int(_CACHE_STATS.get("hits") or 0)
    misses = int(_CACHE_STATS.get("misses") or 0)
    evictions = int(_CACHE_STATS.get("evictions") or 0)
    total = hits + misses
    hit_rate = (hits / total) if total > 0 else 0.0
    win_hits, win_misses = _window_counts()
    win_total = win_hits + win_misses
    win_hit_rate = (win_hits / win_total) if win_total > 0 else 0.0
    return {
        "version": FAZ95_VERSION,
        "entries": len(_PROMPT_CACHE),
        "max_entries": _PROMPT_CACHE_MAX,
        "hits": hits,
        "misses": misses,
        "hit_rate": round(hit_rate, 4),
        "evictions": evictions,
        "window_sec": int(_WINDOW_SEC),
        "window_hits": win_hits,
        "window_misses": win_misses,
        "window_hit_rate": round(win_hit_rate, 4),
    }


def _record_cache_event(*, is_hit: bool) -> None:
    now = time.time()
    _CACHE_EVENTS.append((now, 1 if is_hit else 0))
    _prune_cache_events(now)


def _prune_cache_events(now: float | None = None) -> None:
    cur = now if now is not None else time.time()
    cutoff = cur - _WINDOW_SEC
    while _CACHE_EVENTS and _CACHE_EVENTS[0][0] < cutoff:
        _CACHE_EVENTS.pop(0)
    if len(_CACHE_EVENTS) > 4000:
        del _CACHE_EVENTS[:-3000]


def _window_counts() -> tuple[int, int]:
    _prune_cache_events()
    hits = sum(v for _, v in _CACHE_EVENTS)
    misses = len(_CACHE_EVENTS) - hits
    return hits, misses

