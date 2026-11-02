# -*- coding: utf-8 -*-
"""M1 smoke — Video motor baseline (ffmpeg boru + hub niyet + API)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _ok(cond: bool, label: str) -> int:
    print(("OK" if cond else "FAIL"), "-", label)
    return 0 if cond else 1


def main() -> int:
    from ilim_assistant.ses_m1_video_baseline import M1_VERSION, run_m1_baseline

    failed = 0
    failed += _ok("m1-video" in M1_VERSION, f"ver {M1_VERSION}")
    r = run_m1_baseline()
    st = r.get("stages") or {}
    eng = st.get("engines") or {}
    pipe = st.get("pipeline") or {}
    hub = st.get("hub_intent") or {}
    api = st.get("api_routes") or {}

    failed += _ok(bool(eng.get("ffmpeg")), "ffmpeg")
    failed += _ok(bool(eng.get("ffprobe")), "ffprobe")
    failed += _ok(bool(eng.get("ytdlp")), "ytdlp")
    failed += _ok(bool(pipe.get("ok")), f"pipeline note={pipe.get('note')}")
    failed += _ok(
        pipe.get("trim_ms") is not None and float(pipe["trim_ms"]) < 30_000,
        f"trim_ms={pipe.get('trim_ms')}",
    )
    failed += _ok(
        pipe.get("concat_ms") is not None and float(pipe["concat_ms"]) < 30_000,
        f"concat_ms={pipe.get('concat_ms')}",
    )
    failed += _ok(bool(hub.get("ok")), f"hub_intent fail={hub.get('fail')} cases={hub.get('cases')}")
    failed += _ok(bool(api.get("ok")), f"api missing={api.get('missing')}")
    failed += _ok(bool(r.get("ok")), "baseline ok")

    # M1 yama: sohbet niyeti video dock'u spamlemesin
    from ilim_assistant.ruzgar_hub_sse_faz_e import detect_video_motor_action

    failed += _ok(
        detect_video_motor_action("hava nasıl", {"mode": "video"}) is None,
        "video modunda sohbet → atolye yok",
    )
    failed += _ok(
        detect_video_motor_action("videoyu kes 0-10", {"mode": "genel"}) is not None,
        "kes niyeti → atolye",
    )

    doc = ROOT / "docs" / "M1_VIDEO_BASELINE_2026-11-03.md"
    failed += _ok(doc.is_file() and doc.stat().st_size > 80, f"doc {doc.name}")

    print(
        f"trim_ms={pipe.get('trim_ms')} concat_ms={pipe.get('concat_ms')} "
        f"join_dur={pipe.get('join_dur')}"
    )
    total = 13
    print(f"result: {total - failed}/{total} pass")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
