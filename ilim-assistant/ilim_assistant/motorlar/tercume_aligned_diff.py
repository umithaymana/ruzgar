# Created by Ümit & Gökçenur
"""Tercüme Faz 17 — kaynak/hedef hizalı segment karşılaştırma."""

from __future__ import annotations

import re
from typing import Any

ALIGNED_DIFF_VERSION = "tercume-aligned-diff-v17-2026-05-29"
_MAX_SEGMENTS = 120
_SNIP = 2400


def split_segments(text: str) -> list[str]:
    body = (text or "").strip()
    if not body:
        return []
    parts = [p.strip() for p in re.split(r"\n\s*\n+", body) if p.strip()]
    if parts:
        return parts
    lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
    if len(lines) > 1 and all(len(ln) < 400 for ln in lines):
        return lines
    return [body]


def _status(src: str, tgt: str) -> str:
    if src and tgt:
        return "paired"
    if src and not tgt:
        return "missing_target"
    if tgt and not src:
        return "extra_target"
    return "empty"


def build_aligned_diff(
    source_text: str,
    target_text: str,
    *,
    max_segments: int = _MAX_SEGMENTS,
) -> dict[str, Any]:
    src_segs = split_segments(source_text)[:max_segments]
    tgt_segs = split_segments(target_text)[:max_segments]
    n = max(len(src_segs), len(tgt_segs))
    rows: list[dict[str, Any]] = []
    stats = {"paired": 0, "missing_target": 0, "extra_target": 0}
    for i in range(n):
        s = src_segs[i] if i < len(src_segs) else ""
        t = tgt_segs[i] if i < len(tgt_segs) else ""
        if not s and not t:
            continue
        st = _status(s, t)
        stats[st] = stats.get(st, 0) + 1
        rows.append(
            {
                "index": i,
                "source": s[:_SNIP],
                "target": t[:_SNIP],
                "status": st,
                "source_len": len(s),
                "target_len": len(t),
            }
        )
    return {
        "ok": True,
        "version": ALIGNED_DIFF_VERSION,
        "segments": rows,
        "total": len(rows),
        "source_count": len(src_segs),
        "target_count": len(tgt_segs),
        "stats": stats,
        "aligned": stats.get("missing_target", 0) == 0 and stats.get("extra_target", 0) == 0,
    }


def build_aligned_from_pages(
    pages: list[dict[str, Any]],
    target_text: str,
) -> dict[str, Any]:
    if not pages:
        return build_aligned_diff("", target_text)
    tgt_parts = split_segments(target_text)
    rows: list[dict[str, Any]] = []
    stats = {"paired": 0, "missing_target": 0, "extra_target": 0}
    for i, p in enumerate(pages[:_MAX_SEGMENTS]):
        if not isinstance(p, dict):
            continue
        s = str(p.get("text") or "").strip()[:_SNIP]
        label = str(p.get("label") or p.get("page") or f"Sayfa {i + 1}")
        t = tgt_parts[i][: _SNIP] if i < len(tgt_parts) else ""
        st = _status(s, t)
        stats[st] = stats.get(st, 0) + 1
        rows.append(
            {
                "index": int(p.get("index") if p.get("index") is not None else i),
                "page": label,
                "source": s,
                "target": t,
                "status": st,
                "source_len": len(str(p.get("text") or "")),
                "target_len": len(tgt_parts[i]) if i < len(tgt_parts) else 0,
            }
        )
    if len(tgt_parts) > len(pages):
        for j in range(len(pages), min(len(tgt_parts), _MAX_SEGMENTS)):
            t = tgt_parts[j][: _SNIP]
            stats["extra_target"] = stats.get("extra_target", 0) + 1
            rows.append(
                {
                    "index": j,
                    "page": f"+{j + 1}",
                    "source": "",
                    "target": t,
                    "status": "extra_target",
                    "source_len": 0,
                    "target_len": len(tgt_parts[j]),
                }
            )
    return {
        "ok": True,
        "version": ALIGNED_DIFF_VERSION,
        "segments": rows,
        "total": len(rows),
        "source_count": len(pages),
        "target_count": len(tgt_parts),
        "stats": stats,
        "mode": "pages",
        "aligned": stats.get("missing_target", 0) == 0 and stats.get("extra_target", 0) == 0,
    }
