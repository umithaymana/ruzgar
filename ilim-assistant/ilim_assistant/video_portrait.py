# Created by Ümit & Gökçenur
"""
V7.2 — Portre canlandırma (SadTalker / özel komut).

Gerçek dudak senkronu için harici model gerekir. Kurulum:
  RUZGAR_SADTALKER_ROOT=C:/AI/SadTalker
  RUZGAR_SADTALKER_PYTHON=python  (isteğe bağlı)

Alternatif: RUZGAR_PORTRAIT_CMD şablonu
  {python} {image} {audio} {output_dir}
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from ilim_assistant.video_ffmpeg import DEFAULT_FFMPEG_TIMEOUT, run_ffmpeg_args

_PORTRAIT_FACE_HINTS = (
    "face",
    "portrait",
    "portre",
    "yüz",
    "yuz",
    "smile",
    "gülümse",
    "gulumse",
    "konuş",
    "konus",
    "talk",
    "lip",
    "dudak",
    "selfie",
    "portre",
)


def portrait_available() -> bool:
    if os.environ.get("RUZGAR_PORTRAIT_CMD", "").strip():
        return True
    root = _sadtalker_root()
    if not root:
        return False
    inference = root / "inference.py"
    return inference.is_file()


def portrait_status() -> dict[str, str | bool]:
    root = _sadtalker_root()
    cmd = os.environ.get("RUZGAR_PORTRAIT_CMD", "").strip()
    return {
        "available": portrait_available(),
        "sadtalker_root": str(root) if root else "",
        "custom_cmd": bool(cmd),
        "hint": (
            "SadTalker: RUZGAR_SADTALKER_ROOT ve inference.py — "
            "veya RUZGAR_PORTRAIT_CMD şablonu."
        ),
    }


def _sadtalker_root() -> Path | None:
    raw = os.environ.get("RUZGAR_SADTALKER_ROOT", "").strip()
    if not raw:
        return None
    p = Path(raw).expanduser().resolve()
    return p if p.is_dir() else None


def _portrait_python() -> str:
    return (
        os.environ.get("RUZGAR_SADTALKER_PYTHON", "").strip()
        or os.environ.get("RUZGAR_PORTRAIT_PYTHON", "").strip()
        or sys.executable
    )


def scene_wants_portrait(scene: dict) -> bool:
    if scene.get("character_ids"):
        return True
    blob = " ".join(
        [
            str(scene.get("motion_prompt") or ""),
            str(scene.get("action") or ""),
            str(scene.get("visual_prompt") or ""),
            str(scene.get("narration") or ""),
        ]
    ).lower()
    return any(h in blob for h in _PORTRAIT_FACE_HINTS)


def render_portrait_scene(
    image: Path,
    audio_wav: Path,
    out_mp4: Path,
    *,
    width: int,
    height: int,
    crf: int = 20,
    preset: str = "medium",
) -> None:
    """Fotoğraf + TTS ses → konuşan portre klip."""
    if not portrait_available():
        raise RuntimeError("Portre modu yapılandırılmamış (SadTalker yok).")
    if not image.is_file():
        raise RuntimeError(f"Görsel bulunamadı: {image}")
    if not audio_wav.is_file():
        raise RuntimeError(f"Ses bulunamadı: {audio_wav}")

    work = out_mp4.parent / f"_portrait_{out_mp4.stem}"
    work.mkdir(parents=True, exist_ok=True)
    raw_mp4 = work / "raw.mp4"
    try:
        _run_portrait_engine(image, audio_wav, work, raw_mp4)
        if not raw_mp4.is_file():
            found = sorted(work.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
            if not found:
                raise RuntimeError("SadTalker çıktı MP4 üretmedi.")
            raw_mp4 = found[0]
        _fit_portrait_clip(raw_mp4, audio_wav, out_mp4, width=width, height=height, crf=crf, preset=preset)
    finally:
        shutil.rmtree(work, ignore_errors=True)


def _run_portrait_engine(image: Path, audio_wav: Path, work_dir: Path, expected_out: Path) -> None:
    custom = os.environ.get("RUZGAR_PORTRAIT_CMD", "").strip()
    timeout = float(os.environ.get("RUZGAR_PORTRAIT_TIMEOUT", "900"))
    py = _portrait_python()

    if custom:
        cmd = custom.format(
            python=py,
            image=str(image.resolve()),
            audio=str(audio_wav.resolve()),
            output=str(expected_out.resolve()),
            output_dir=str(work_dir.resolve()),
            sadtalker_root=str(_sadtalker_root() or ""),
        )
        subprocess.run(cmd, shell=True, check=True, timeout=timeout, cwd=str(work_dir))
        return

    root = _sadtalker_root()
    if not root:
        raise RuntimeError("RUZGAR_SADTALKER_ROOT ayarlı değil.")
    inference = root / "inference.py"
    args = [
        py,
        str(inference),
        "--driven_audio",
        str(audio_wav.resolve()),
        "--source_image",
        str(image.resolve()),
        "--result_dir",
        str(work_dir.resolve()),
        "--checkpoint_dir",
        str((root / "checkpoints").resolve()),
        "--size",
        "256",
        "--still",
        "--preprocess",
        "crop",
        "--cpu",
    ]
    enhancer = os.environ.get("RUZGAR_SADTALKER_ENHANCER", "").strip()
    if enhancer:
        args.extend(["--enhancer", enhancer])

    subprocess.run(
        args,
        check=True,
        timeout=timeout,
        cwd=str(root),
    )
    if not expected_out.is_file():
        candidates = list(work_dir.rglob("*.mp4"))
        if len(candidates) == 1:
            shutil.copy2(candidates[0], expected_out)


def _fit_portrait_clip(
    video: Path,
    audio_wav: Path,
    out_mp4: Path,
    *,
    width: int,
    height: int,
    crf: int,
    preset: str,
) -> None:
    """SadTalker çıktısını hedef çözünürlüğe getir; TTS sesini kullan."""
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
        timeout_sec=max(DEFAULT_FFMPEG_TIMEOUT, 600),
    )
