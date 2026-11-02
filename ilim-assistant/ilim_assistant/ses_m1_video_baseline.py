"""
M1 — Video motor baseline + uçtan uca FFmpeg borusu (yerel, indirme yok).

Ölçüm: ffmpeg/ffprobe/yt-dlp hazır · gen→probe→trim→concat · hub niyet.
"""
from __future__ import annotations

import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

M1_VERSION = "ses-m1-video-baseline-v1-2026-11-03"


def _ffmpeg() -> str:
    from ilim_assistant.video_ffmpeg import ffmpeg_bin

    exe = ffmpeg_bin()
    if not exe:
        raise RuntimeError("ffmpeg yok")
    return exe


def make_test_mp4(path: Path, *, seconds: float = 2.0) -> Path:
    ff = _ffmpeg()
    path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ff,
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"color=c=blue:s=320x240:d={seconds}",
        "-f",
        "lavfi",
        "-i",
        f"sine=f=440:d={seconds}",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-shortest",
        str(path),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0 or not path.is_file():
        raise RuntimeError((r.stderr or r.stdout or "ffmpeg gen fail")[-400:])
    return path


def stage_engines() -> dict[str, Any]:
    from ilim_assistant.motorlar.video_motoru import ytdlp_available
    from ilim_assistant.video_ffmpeg import ffmpeg_available, ffprobe_available

    return {
        "ok": ffmpeg_available() and ffprobe_available(),
        "ffmpeg": ffmpeg_available(),
        "ffprobe": ffprobe_available(),
        "ytdlp": ytdlp_available(),
    }


def stage_pipeline() -> dict[str, Any]:
    from ilim_assistant.video_ffmpeg import concat_two_files, ffprobe_json, trim_media

    out: dict[str, Any] = {"ok": False, "trim_ms": None, "concat_ms": None, "note": ""}
    td = Path(tempfile.mkdtemp(prefix="ruzgar_m1_"))
    try:
        src = make_test_mp4(td / "src.mp4", seconds=2.0)
        meta = ffprobe_json(src)
        dur = float((meta.get("format") or {}).get("duration") or 0)
        cut1 = td / "a.mp4"
        cut2 = td / "b.mp4"
        t0 = time.perf_counter()
        trim_media(src, cut1, start_sec=0.2, duration_sec=0.8, copy_streams=False)
        out["trim_ms"] = round((time.perf_counter() - t0) * 1000.0, 1)
        trim_media(src, cut2, start_sec=0.9, duration_sec=0.8, copy_streams=False)
        joined = td / "join.mp4"
        t1 = time.perf_counter()
        # trim re-encode sonrası copy kırılgan olabilir → güvenli birleştir
        concat_two_files(cut1, cut2, joined, copy_streams=False)
        out["concat_ms"] = round((time.perf_counter() - t1) * 1000.0, 1)
        jdur = float((ffprobe_json(joined).get("format") or {}).get("duration") or 0)
        out["ok"] = (
            dur >= 1.5
            and cut1.stat().st_size > 500
            and joined.stat().st_size > 500
            and jdur >= 1.0
        )
        out["src_dur"] = dur
        out["join_dur"] = jdur
        out["join_bytes"] = joined.stat().st_size
    except Exception as exc:
        out["note"] = str(exc)[:240]
    return out


def stage_hub_intent() -> dict[str, Any]:
    from ilim_assistant.motorlar.ana_motor_hub_faz76 import (
        is_video_download_request,
        is_video_workflow_request,
    )
    from ilim_assistant.ruzgar_hub_sse_faz_e import detect_video_motor_action

    cases = [
        ("bu videoyu indir https://youtu.be/dQw4w9WgXcQ", True, True),
        ("videoyu 10 saniyeden 30 a kes", True, False),
        ("hava nasıl", False, False),
        ("selam rüzgar", False, False),
    ]
    fail = 0
    details = []
    for msg, exp_wf, exp_dl in cases:
        wf = bool(is_video_workflow_request(msg))
        dl = bool(is_video_download_request(msg))
        # download ⇒ workflow True
        ok_wf = wf is True if (exp_wf or exp_dl) else wf is False
        # for download case workflow is True
        if exp_dl:
            ok_wf = wf is True
        elif not exp_wf:
            ok_wf = wf is False
        else:
            ok_wf = wf is True
        ok_dl = dl is exp_dl
        act = detect_video_motor_action(msg, {"mode": "video"})
        want_act = exp_wf or exp_dl
        ok_act = (act is not None) is want_act
        row_ok = ok_wf and ok_dl and ok_act
        if not row_ok:
            fail += 1
        details.append(
            {
                "msg": msg[:40],
                "ok": row_ok,
                "wf": wf,
                "dl": dl,
                "act": bool(act),
            }
        )
    return {"ok": fail == 0, "fail": fail, "cases": details}


def stage_api_routes() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[1]
    ds = (root / "desktop_server.py").read_text(encoding="utf-8")
    need = (
        "/api/video/probe",
        "/api/video/trim",
        "/api/video/concat",
        "/api/video/download",
        "/api/video/burn-subtitles",
        "/api/video/edit/mix",
    )
    missing = [r for r in need if r not in ds]
    return {"ok": not missing, "missing": missing}


def run_m1_baseline() -> dict[str, Any]:
    report: dict[str, Any] = {"version": M1_VERSION, "ok": False, "stages": {}}
    report["stages"]["engines"] = stage_engines()
    report["stages"]["pipeline"] = stage_pipeline()
    report["stages"]["hub_intent"] = stage_hub_intent()
    report["stages"]["api_routes"] = stage_api_routes()
    report["ok"] = all(bool((s or {}).get("ok")) for s in report["stages"].values())
    return report
