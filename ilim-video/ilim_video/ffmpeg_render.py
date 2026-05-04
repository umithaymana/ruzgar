"""
Sabit görsel + sahne başına ses dosyası → ardı ardına birleştirilmiş MP4.

Önkoşul: sistemde `ffmpeg` kurulu ve PATH'te olmalı (https://ffmpeg.org).
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List


def _which_ffmpeg() -> str:
    p = shutil.which("ffmpeg")
    if not p:
        raise FileNotFoundError("ffmpeg bulunamadı. Windows için ffmpeg indirip PATH'e ekleyin.")
    return p


def scene_clip(image_path: Path, wav_path: Path, out_mp4: Path, ffmpeg_exe: str) -> None:
    """Tek sahne: döngü görsel + wav → mp4."""
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ffmpeg_exe,
        "-y",
        "-loop",
        "1",
        "-i",
        str(image_path),
        "-i",
        str(wav_path),
        "-c:v",
        "libx264",
        "-tune",
        "stillimage",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-pix_fmt",
        "yuv420p",
        "-shortest",
        str(out_mp4),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        raise RuntimeError(r.stderr or "ffmpeg sahne hatası")


def concat_segments(segment_mp4s: List[Path], final_out: Path, ffmpeg_exe: str) -> None:
    """Concat demuxer ile birleştirme."""
    final_out.parent.mkdir(parents=True, exist_ok=True)
    lst = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8")
    try:
        for p in segment_mp4s:
            # ffmpeg concat için güvenli yol kaçışı
            safe = str(p.resolve()).replace("'", "'\\''")
            lst.write(f"file '{safe}'\n")
        lst.close()
        cmd = [
            ffmpeg_exe,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            lst.name,
            "-c",
            "copy",
            str(final_out),
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        if r.returncode != 0:
            raise RuntimeError(r.stderr or "ffmpeg birleştirme hatası")
    finally:
        Path(lst.name).unlink(missing_ok=True)


def render_from_assets(
    manifest_json: Path,
    image_per_scene: Path | None,
    default_image: Path,
    audio_dir: Path,
    final_mp4: Path,
) -> Path:
    """
    manifest_json: scene_planner çıktısı; sahne_id sırasına göre ses dosyası aranır:
    audio_dir içinde 001.wav veya scene_1.wav biçimi.
    """
    ffmpeg_exe = _which_ffmpeg()
    plan = json.loads(manifest_json.read_text(encoding="utf-8"))
    scenes = plan.get("scenes") or []
    if not scenes:
        raise ValueError("Plan içinde sahne yok.")
    tmp_parts: List[Path] = []
    td = Path(tempfile.mkdtemp(prefix="ilim_vid_"))

    try:
        for i, sc in enumerate(scenes):
            sid = int(sc.get("scene_id", i + 1))
            wav = audio_dir / f"{sid:03d}.wav"
            if not wav.is_file():
                wav = audio_dir / f"scene_{sid}.wav"
            if not wav.is_file():
                raise FileNotFoundError(f"Ses dosyası yok: {sid} için {audio_dir}")

            img = image_per_scene / f"{sid:03d}.jpg" if image_per_scene else None
            if img and not img.is_file():
                img = image_per_scene / f"{sid:03d}.png"
            use_img = img if img and img.is_file() else default_image
            if not use_img.is_file():
                raise FileNotFoundError(f"Görsel yok: {use_img}")

            part = td / f"part_{sid:03d}.mp4"
            scene_clip(use_img, wav, part, ffmpeg_exe)
            tmp_parts.append(part)

        concat_segments(tmp_parts, final_mp4, ffmpeg_exe)
        return final_mp4
    finally:
        for p in td.glob("*"):
            p.unlink(missing_ok=True)
        td.rmdir()
