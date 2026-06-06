# Created by Ümit & Gökçenur
"""
V8 — AI sahne klibi (Runway image-to-video).

Ortam:
  RUNWAY_API_KEY veya RUNWAYML_API_SECRET
  RUZGAR_RUNWAY_MODEL=gen4_turbo  (varsayılan; görsel zorunlu, ucuz)
  RUZGAR_RUNWAY_API_BASE=https://api.dev.runwayml.com
"""

from __future__ import annotations

import base64
import mimetypes
import os
import time
import urllib.request
from pathlib import Path
from typing import Any

import requests

from ilim_assistant.video_ffmpeg import DEFAULT_FFMPEG_TIMEOUT, run_ffmpeg_args

_RUNWAY_VERSION = "2024-11-06"
_DEFAULT_BASE = "https://api.dev.runwayml.com"


def _runway_api_key() -> str:
    return (
        os.environ.get("RUNWAY_API_KEY", "").strip()
        or os.environ.get("RUNWAYML_API_SECRET", "").strip()
        or os.environ.get("RUNWAYML_API_KEY", "").strip()
    )


def generative_available() -> bool:
    return bool(_runway_api_key())


def generative_status() -> dict[str, str | bool]:
    return {
        "available": generative_available(),
        "provider": "runway",
        "model": os.environ.get("RUZGAR_RUNWAY_MODEL", "gen4_turbo").strip() or "gen4_turbo",
        "hint": "Runway: RUNWAY_API_KEY veya RUNWAYML_API_SECRET (.env).",
    }


def _runway_headers() -> dict[str, str]:
    key = _runway_api_key()
    if not key:
        raise RuntimeError("Runway API anahtarı yok (RUNWAY_API_KEY).")
    return {
        "Authorization": f"Bearer {key}",
        "X-Runway-Version": _RUNWAY_VERSION,
        "Content-Type": "application/json",
    }


def _api_base() -> str:
    return (os.environ.get("RUZGAR_RUNWAY_API_BASE", _DEFAULT_BASE) or _DEFAULT_BASE).rstrip("/")


def _image_data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{data}"


def _ratio_for_size(width: int, height: int) -> str:
    if width >= height * 1.2:
        return "1280:720"
    if height >= width * 1.2:
        return "720:1280"
    return "960:960"


def _runway_duration(audio_wav: Path) -> int:
    from ilim_assistant.video_ffmpeg import ffprobe_json

    try:
        meta = ffprobe_json(audio_wav)
        dur = float(meta.get("format", {}).get("duration") or 5.0)
    except Exception:
        dur = 5.0
    dur_i = int(round(dur))
    dur_i = max(2, min(dur_i, 10))
    model = os.environ.get("RUZGAR_RUNWAY_MODEL", "gen4_turbo").strip() or "gen4_turbo"
    if model.startswith("veo3") and dur_i not in (8,):
        dur_i = 8
    return dur_i


def _poll_runway_task(task_id: str, *, timeout_sec: float = 600.0) -> str:
    url = f"{_api_base()}/v1/tasks/{task_id}"
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        resp = requests.get(url, headers=_runway_headers(), timeout=60)
        resp.raise_for_status()
        data = resp.json()
        status = str(data.get("status") or "").upper()
        if status in ("SUCCEEDED", "COMPLETED"):
            out = data.get("output") or data.get("artifacts") or []
            if isinstance(out, list) and out:
                first = out[0]
                if isinstance(first, str):
                    return first
                if isinstance(first, dict):
                    return str(first.get("url") or first.get("uri") or "")
            raise RuntimeError("Runway görevi tamamlandı ama çıktı URL yok.")
        if status in ("FAILED", "CANCELLED", "CANCELED"):
            detail = data.get("failure") or data.get("failureReason") or data
            raise RuntimeError(f"Runway görevi başarısız: {detail}")
        time.sleep(float(os.environ.get("RUZGAR_RUNWAY_POLL_SEC", "4")))
    raise RuntimeError("Runway görevi zaman aşımı.")


def _download_file(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "Ruzgar/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        dest.write_bytes(resp.read())


def _create_runway_task(
    *,
    prompt_text: str,
    image: Path | None,
    width: int,
    height: int,
    audio_wav: Path,
) -> str:
    model = os.environ.get("RUZGAR_RUNWAY_MODEL", "gen4_turbo").strip() or "gen4_turbo"
    payload: dict[str, Any] = {
        "model": model,
        "promptText": (prompt_text or "Cinematic scene, gentle natural motion").strip()[:900],
        "ratio": _ratio_for_size(width, height),
        "duration": _runway_duration(audio_wav),
    }
    if image and image.is_file():
        payload["promptImage"] = _image_data_uri(image)
    elif model in ("gen4_turbo",):
        raise RuntimeError(f"{model} için sahne görseli gerekli.")

    resp = requests.post(
        f"{_api_base()}/v1/image_to_video",
        headers=_runway_headers(),
        json=payload,
        timeout=90,
    )
    if resp.status_code >= 400:
        raise RuntimeError(f"Runway API {resp.status_code}: {resp.text[:400]}")
    task_id = str(resp.json().get("id") or resp.json().get("taskId") or "").strip()
    if not task_id:
        raise RuntimeError(f"Runway görev kimliği alınamadı: {resp.text[:200]}")
    return task_id


def render_generative_scene(
    image: Path | None,
    prompt_text: str,
    audio_wav: Path,
    out_mp4: Path,
    *,
    width: int,
    height: int,
    crf: int = 20,
    preset: str = "medium",
) -> None:
    """Runway klip + TTS ses → sahne MP4."""
    if not generative_available():
        raise RuntimeError("Runway API anahtarı yok.")
    work = out_mp4.parent
    work.mkdir(parents=True, exist_ok=True)
    raw = work / f"_gen_{out_mp4.stem}.mp4"
    try:
        task_id = _create_runway_task(
            prompt_text=prompt_text,
            image=image,
            width=width,
            height=height,
            audio_wav=audio_wav,
        )
        video_url = _poll_runway_task(task_id)
        _download_file(video_url, raw)
        _mux_generative_clip(raw, audio_wav, out_mp4, width=width, height=height, crf=crf, preset=preset)
    finally:
        raw.unlink(missing_ok=True)


def _mux_generative_clip(
    video: Path,
    audio_wav: Path,
    out_mp4: Path,
    *,
    width: int,
    height: int,
    crf: int,
    preset: str,
) -> None:
    run_ffmpeg_args(
        [
            "-y",
            "-i",
            str(video.resolve()),
            "-i",
            str(audio_wav.resolve()),
            "-vf",
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1",
            "-c:v",
            "libx264",
            "-preset",
            str(preset),
            "-crf",
            str(crf),
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-shortest",
            "-movflags",
            "+faststart",
            str(out_mp4.resolve()),
        ],
        timeout_sec=max(DEFAULT_FFMPEG_TIMEOUT, 900),
    )


def scene_generative_prompt(scene: dict) -> str:
    parts = [
        str(scene.get("visual_prompt") or "").strip(),
        str(scene.get("motion_prompt") or "").strip(),
        str(scene.get("action") or "").strip(),
    ]
    text = ". ".join(p for p in parts if p)
    return text or str(scene.get("narration") or "")[:400]
