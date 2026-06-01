#!/usr/bin/env python3
"""Faz 16B — inceleme kuyruğu smoke."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))


def main() -> int:
    from ilim_assistant.motorlar.tercume_review_queue import (
        REVIEW_QUEUE_VERSION,
        build_review_queue,
        review_items_from_outputs,
    )

    if "v16b" not in REVIEW_QUEUE_VERSION:
        print("FAIL version", REVIEW_QUEUE_VERSION)
        return 1

    outs = [
        {"page": "Sayfa 1", "page_index": 0, "ok": True, "quality_score": 90},
        {"page": "Sayfa 2", "page_index": 1, "ok": True, "quality_score": 40, "quality_ok": False},
        {"page": "Sayfa 3", "page_index": 2, "ok": False, "error": "timeout"},
    ]
    items = review_items_from_outputs(outs)
    if len(items) != 2:
        print("FAIL items", items)
        return 1
    if items[0].get("kind") != "low_quality" or items[0].get("output_index") != 1:
        print("FAIL low_quality item", items[0])
        return 1
    if items[1].get("kind") != "error" or items[1].get("output_index") != 2:
        print("FAIL error item", items[1])
        return 1

    q = build_review_queue({"job_id": "j1", "rel": "x.pdf", "status": "done", "outputs": outs})
    if not q.get("ok") or q.get("total") != 2:
        print("FAIL build", q)
        return 1

    from ilim_assistant.motorlar.tercume_atolye import workbench_config

    rv = workbench_config().get("review_faz16b") or {}
    if rv.get("route") != "/api/tercume/review-queue":
        print("FAIL review_faz16b", rv)
        return 1

    print("OK tercume faz16b — review queue items + build")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
