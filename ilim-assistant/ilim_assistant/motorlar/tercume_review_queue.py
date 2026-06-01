# Created by Ümit & Gökçenur
"""Tercüme Faz 16B — düşük kalite / hatalı sayfa inceleme kuyruğu."""

from __future__ import annotations

from typing import Any

REVIEW_QUEUE_VERSION = "tercume-review-queue-v16b-2026-05-29"
_DEFAULT_PASS = 55.0


def review_items_from_outputs(
    outputs: list[dict[str, Any]],
    *,
    pass_score: float = _DEFAULT_PASS,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for i, o in enumerate(outputs or []):
        if not isinstance(o, dict):
            continue
        page = str(o.get("page") or "?")
        pidx = o.get("page_index")
        base = {"page": page, "page_index": pidx, "output_index": i}
        if o.get("ok") is False:
            items.append(
                {
                    **base,
                    "kind": "error",
                    "error": str(o.get("error") or "?"),
                    "quality_score": None,
                }
            )
            continue
        raw = o.get("quality_score")
        if raw is None:
            continue
        try:
            sc = float(raw)
        except (TypeError, ValueError):
            continue
        if sc < pass_score or o.get("quality_ok") is False:
            issues = o.get("quality_issues") if isinstance(o.get("quality_issues"), list) else []
            items.append(
                {
                    **base,
                    "kind": "low_quality",
                    "quality_score": sc,
                    "quality_issues": issues[:4],
                }
            )
    return items


def build_review_queue(
    job: dict[str, Any],
    *,
    pass_score: float = _DEFAULT_PASS,
) -> dict[str, Any]:
    outputs = list(job.get("outputs") or [])
    items = review_items_from_outputs(outputs, pass_score=pass_score)
    return {
        "ok": True,
        "version": REVIEW_QUEUE_VERSION,
        "job_id": job.get("job_id") or "",
        "rel": job.get("rel") or "",
        "status": job.get("status") or "",
        "items": items,
        "total": len(items),
        "pass_threshold": pass_score,
    }
