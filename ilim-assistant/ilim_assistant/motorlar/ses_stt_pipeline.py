# Created by Ümit & Gökçenur
"""
Faz S2 — video/ses → Whisper transkript boru hattı.

FFmpeg ile videodan ses çıkarır; faster-whisper ile metin + segment + SRT üretir.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from ilim_assistant.stt_whisper import (
    TranscribeResult,
    segments_to_srt,
    transcribe_file_detailed,
)
from ilim_assistant.video_ffmpeg import extract_audio_for_stt, ffmpeg_available

VIDEO_SUFFIXES = frozenset(
    {
        ".mp4",
        ".mkv",
        ".webm",
        ".avi",
        ".mov",
        ".m4v",
        ".ts",
        ".flv",
        ".wmv",
        ".mpg",
        ".mpeg",
    }
)
AUDIO_SUFFIXES = frozenset(
    {
        ".wav",
        ".mp3",
        ".ogg",
        ".m4a",
        ".aac",
        ".flac",
        ".wma",
        ".opus",
        ".webm",
    }
)


def stt_max_duration_sec() -> float | None:
    raw = os.environ.get("RUZGAR_STT_MAX_SEC", "7200").strip().lower()
    if raw in ("0", "none", "unlimited", "all"):
        return None
    try:
        sec = float(raw)
        return max(30.0, sec) if sec > 0 else None
    except ValueError:
        return 7200.0


def normalize_stt_language(lang: str | None) -> str | None:
    if not lang:
        return None
    s = lang.strip().lower()
    if s in ("auto", "detect", "none", ""):
        return None
    return lang.strip()[:16]


def is_video_file(path: Path) -> bool:
    return path.suffix.lower() in VIDEO_SUFFIXES


def is_audio_file(path: Path) -> bool:
    return path.suffix.lower() in AUDIO_SUFFIXES


def guess_stt_upload_suffix(filename: str) -> str:
    """Yüklenen dosya adından geçici dosya uzantısı (ffmpeg/Whisper için doğru konteyner)."""
    fn = (filename or "").lower().replace("\\", "/")
    base = fn.rsplit("/", 1)[-1]
    for ext in (
        *sorted(VIDEO_SUFFIXES, key=len, reverse=True),
        *sorted(AUDIO_SUFFIXES, key=len, reverse=True),
    ):
        if base.endswith(ext):
            return ext
    return ".webm"


def stt_max_upload_bytes() -> int:
    raw = os.environ.get("RUZGAR_STT_MAX_UPLOAD_MB", "800").strip()
    try:
        mb = float(raw)
        return max(16, int(mb * 1024 * 1024))
    except ValueError:
        return 800 * 1024 * 1024


def prepare_audio_for_stt(src: Path) -> tuple[Path, bool]:
    """
    STT için 16 kHz mono WAV hazırlar.
    Dönüş: (yol, geçici_mi) — geçici dosyalar çağıran tarafından silinmeli.
    """
    src = Path(src)
    if not src.is_file():
        raise FileNotFoundError(src)

    if src.suffix.lower() == ".wav":
        return src, False

    if is_video_file(src) or (src.suffix.lower() not in {".wav"}):
        if not ffmpeg_available():
            raise RuntimeError(
                "Video/ses dönüşümü için ffmpeg gerekli. "
                "https://ffmpeg.org/download.html — kurun ve PATH'e ekleyin."
            )
        fd, tmp = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        out = Path(tmp)
        extract_audio_for_stt(
            src,
            out,
            max_duration_sec=stt_max_duration_sec(),
        )
        return out, True

    raise ValueError(f"Desteklenmeyen medya uzantısı: {src.suffix}")


def transcribe_media_path(
    src: str | Path,
    *,
    language: str | None = None,
) -> TranscribeResult:
    """Video veya ses dosyasını transkribe eder (dil otomatik veya ipucu)."""
    src_path = Path(src)
    wl = normalize_stt_language(language)
    wav_path, temp = prepare_audio_for_stt(src_path)
    try:
        return transcribe_file_detailed(wav_path, wl)
    finally:
        if temp:
            try:
                wav_path.unlink(missing_ok=True)
            except OSError:
                pass


def write_srt_for_result(
    result: TranscribeResult,
    output_path: str | Path,
) -> Path:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(segments_to_srt(result.segments), encoding="utf-8")
    return out
