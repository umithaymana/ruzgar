# Created by Ümit & Gökçenur
"""
Videodan klon referans sesi — ffmpeg ile temiz konuşma/tilavet segmenti.

Profiller: kuran · gazel · ilahi (+ alim/edip/asistan)
"""

from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path
from typing import Any

from ilim_assistant.motorlar.ses_klon_motoru import (
    normalize_reference_to_wav,
    referans_klasoru,
)
from ilim_assistant.motorlar.ses_motoru import normalize_ses_karakteri

MIMAR = "Ümit & Gökçenur"
VID_REF_VERSION = "ses-videodan-referans-v1-2026-06-06"

_REPO_ROOT = Path(__file__).resolve().parents[3]
_ILIM_ROOT = Path(__file__).resolve().parents[2]

TILAVET_PROFILLER = frozenset({"kuran", "gazel", "ilahi"})
KABUL_PROFILLER = TILAVET_PROFILLER | {"alim", "edip", "asistan"}


def _repo_rel(abs_path: Path) -> str:
    try:
        return abs_path.resolve().relative_to(_REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return abs_path.resolve().as_posix()


def normalize_profil(raw: str) -> str:
    s = (raw or "").strip().lower()
    if s in TILAVET_PROFILLER:
        return s
    kar = normalize_ses_karakteri(s)
    return kar.value


def referans_dosyasi(profil: str) -> Path:
    p = normalize_profil(profil)
    return referans_klasoru() / f"{p}.wav"


def _resolve_video_path(video_rel: str) -> Path:
    rel = (video_rel or "").strip().replace("\\", "/").lstrip("/")
    if not rel:
        raise ValueError("video_rel gerekli.")
    target = (_REPO_ROOT / rel).resolve()
    if not target.is_file():
        raise FileNotFoundError(f"Video dosyası yok: {rel}")
    ext = target.suffix.lower()
    if ext not in {".mp4", ".mkv", ".webm", ".mov", ".avi", ".m4v", ".mp3", ".wav", ".m4a"}:
        raise ValueError(f"Desteklenmeyen medya: {ext or '?'}")
    return target


def _clamp_duration(duration_sec: float | None) -> float:
    try:
        d = float(duration_sec if duration_sec is not None else 90.0)
    except (TypeError, ValueError):
        d = 90.0
    return max(15.0, min(120.0, d))


def extract_reference_from_video_file(
    video_rel: str,
    profil: str = "kuran",
    *,
    start_sec: float = 0.0,
    duration_sec: float | None = None,
) -> dict[str, Any]:
    """Yerel videodan referans WAV çıkarır ve arsiv/ses-referans/{profil}.wav kaydeder."""
    from ilim_assistant.video_ffmpeg import ffmpeg_available, run_ffmpeg_args

    if not ffmpeg_available():
        raise RuntimeError("ffmpeg gerekli — PATH'e ekleyin.")

    src = _resolve_video_path(video_rel)
    prof = normalize_profil(profil)
    start = max(0.0, float(start_sec or 0))
    dur = _clamp_duration(duration_sec)
    out = referans_dosyasi(prof)

    fd, tmp = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    tmp_path = Path(tmp)
    try:
        run_ffmpeg_args(
            [
                "-y",
                "-ss",
                f"{start:.3f}",
                "-t",
                f"{dur:.3f}",
                "-i",
                str(src.resolve()),
                "-vn",
                "-ar",
                "22050",
                "-ac",
                "1",
                "-c:a",
                "pcm_s16le",
                str(tmp_path.resolve()),
            ],
            timeout_sec=600,
        )
        normalize_reference_to_wav(tmp_path, out)
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass

    rel_out = _repo_rel(out)
    return {
        "ok": True,
        "profil": prof,
        "referans_rel": rel_out,
        "bytes": out.stat().st_size,
        "start_sec": start,
        "duration_sec": dur,
        "source_video": video_rel,
        "version": VID_REF_VERSION,
        "mimarlar": MIMAR,
    }


def extract_reference_from_url(
    url: str,
    profil: str = "kuran",
    *,
    duration_sec: float | None = None,
) -> dict[str, Any]:
    """URL → yt-dlp ses indir → referans WAV (video indirmeden)."""
    from ilim_assistant.motorlar.video_motoru import download_audio_with_yt_dlp

    watch = (url or "").strip()
    if not watch:
        raise ValueError("URL gerekli.")
    prof = normalize_profil(profil)
    dur = _clamp_duration(duration_sec)

    audio = download_audio_with_yt_dlp(watch, max_duration_sec=int(dur))
    if not audio.ok or not audio.file_path:
        raise RuntimeError(audio.error or "URL'den ses alınamadı.")

    src = (_REPO_ROOT / audio.file_path).resolve()
    if not src.is_file():
        raise FileNotFoundError(f"Ses dosyası oluşmadı: {audio.file_path}")

    out = referans_dosyasi(prof)
    normalize_reference_to_wav(src, out)
    rel_out = _repo_rel(out)

    return {
        "ok": True,
        "profil": prof,
        "referans_rel": rel_out,
        "bytes": out.stat().st_size,
        "duration_sec": dur,
        "source_url": watch,
        "audio_source_rel": audio.file_path,
        "title": audio.title,
        "version": VID_REF_VERSION,
        "mimarlar": MIMAR,
    }


def profil_from_chat(metin: str) -> str:
    low = (metin or "").lower()
    if re.search(r"\bilahi\b|naat|ilahi", low):
        return "ilahi"
    if re.search(r"\bgazel\b|kaside|beyit|divan", low):
        return "gazel"
    if re.search(r"\bkuran\b|tilavet|ayet|sure|mevlid", low):
        return "kuran"
    if re.search(r"\bedip\b|sair", low):
        return "edip"
    if re.search(r"\balim\b|bilge", low):
        return "alim"
    return "kuran"


def referans_durum_snapshot() -> dict[str, Any]:
    refs: dict[str, bool] = {}
    for p in sorted(KABUL_PROFILLER):
        refs[p] = referans_dosyasi(p).is_file()
    return {
        "profiller": refs,
        "referans_dir": referans_klasoru().relative_to(_REPO_ROOT.resolve()).as_posix()
        if str(referans_klasoru()).startswith(str(_REPO_ROOT.resolve()))
        else str(referans_klasoru()),
        "version": VID_REF_VERSION,
    }
