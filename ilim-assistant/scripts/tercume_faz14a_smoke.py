#!/usr/bin/env python3
"""Faz 14A — arka plan sayfa çevirisi job API (list, partial_text, cancel)."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))


def main() -> int:
    from ilim_assistant.motorlar.tercume_batch_jobs import (
        BATCH_VERSION,
        cancel_batch_job,
        get_batch_job,
        list_batch_jobs,
    )

    if "faz14a" not in BATCH_VERSION:
        print("FAIL version", BATCH_VERSION)
        return 1

    lst = list_batch_jobs(limit=5)
    if not lst.get("ok") or "items" not in lst:
        print("FAIL list_batch_jobs", lst)
        return 1

    miss = get_batch_job("nonexistent_job_id_xyz")
    if miss.get("ok"):
        print("FAIL should miss job")
        return 1

    with tempfile.TemporaryDirectory() as td:
        from ilim_assistant.motorlar import tercume_batch_jobs as mod

        jobs_dir = Path(td) / "tercume_jobs"
        jobs_dir.mkdir(parents=True)
        jid = "smoke14a01"
        state = {
            "ok": True,
            "job_id": jid,
            "job_type": "page_range",
            "status": "running",
            "rel": "ilim-assistant/arsiv/test.pdf",
            "done": 2,
            "total": 10,
            "partial_text": "Merhaba dünya",
            "outputs": [{"page": "Sayfa 1", "ok": True, "quality_score": 88}],
            "ok_count": 2,
            "error_count": 0,
            "created_at": 1.0,
            "updated_at": 2.0,
        }
        (jobs_dir / f"{jid}.json").write_text(
            json.dumps(state, ensure_ascii=False),
            encoding="utf-8",
        )
        orig = mod._jobs_dir
        mod._jobs_dir = lambda: jobs_dir  # type: ignore[method-assign]

        hit = get_batch_job(jid)
        if not hit.get("ok") or hit.get("partial_text") != "Merhaba dünya":
            print("FAIL get_batch_job disk", hit)
            return 1

        listed = list_batch_jobs(limit=3)
        if not any(x.get("job_id") == jid for x in listed.get("items") or []):
            print("FAIL list contains job", listed)
            return 1

        c = cancel_batch_job(jid)
        if not c.get("ok"):
            print("FAIL cancel", c)
            return 1

        hit2 = get_batch_job(jid)
        if hit2.get("status") not in ("cancelling", "cancelled"):
            print("FAIL status after cancel", hit2.get("status"))
            return 1

        mod._jobs_dir = orig  # type: ignore[method-assign]

    from desktop_server import app

    paths = {getattr(r, "path", "") for r in app.routes}
    if "/api/tercume/batch-jobs" not in paths:
        print("FAIL route batch-jobs missing")
        return 1

    from ilim_assistant.motorlar.tercume_atolye import workbench_config

    cfg = workbench_config()
    faz14 = cfg.get("batch_faz14a") or {}
    if not faz14.get("page_range_background"):
        print("FAIL workbench batch_faz14a", faz14)
        return 1

    print("OK tercume faz14a — batch jobs + partial_text + routes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
