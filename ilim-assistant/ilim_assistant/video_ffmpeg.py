# Created by Ümit & Gökçenur
"""FFmpeg / ffprobe yardımcıları — Video atölyesi (masaüstü API)."""

from __future__ import annotations

import json
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Any

# Kesme süresi üst sınırı (saniye) — aşırı uzun işleri kes
MAX_SEGMENT_SECONDS = 6 * 60 * 60
# FFmpeg işlem zaman aşımı (saniye)
DEFAULT_FFMPEG_TIMEOUT = 2 * 60 * 60


def ffmpeg_bin() -> str | None:
    return shutil.which("ffmpeg")


def ffprobe_bin() -> str | None:
    return shutil.which("ffprobe")


def ffmpeg_available() -> bool:
    return ffmpeg_bin() is not None


def ffprobe_available() -> bool:
    return ffprobe_bin() is not None


def ffprobe_json(path: str | Path) -> dict[str, Any]:
    exe = ffprobe_bin()
    if not exe:
        raise RuntimeError("ffprobe bulunamadı; FFmpeg kurun ve sistem PATH'ine ekleyin.")
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(str(p))
    cmd = [
        exe,
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(p.resolve()),
    ]
    r = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=120,
        encoding="utf-8",
        errors="replace",
    )
    if r.returncode != 0:
        err = (r.stderr or r.stdout or "").strip()[:1200]
        raise RuntimeError(err or f"ffprobe çıkış kodu {r.returncode}")
    return json.loads(r.stdout or "{}")


def summarize_probe(data: dict[str, Any]) -> dict[str, Any]:
    """İstemci için sade özet (tam ffprobe çıktısı gönderilmez)."""
    fmt = data.get("format") or {}
    streams = data.get("streams") or []
    try:
        duration = float(fmt.get("duration") or 0.0)
    except (TypeError, ValueError):
        duration = 0.0
    try:
        size = int(fmt.get("size") or 0)
    except (TypeError, ValueError):
        size = 0
    format_name = str(fmt.get("format_name") or "")
    v = next((s for s in streams if s.get("codec_type") == "video"), None)
    a = next((s for s in streams if s.get("codec_type") == "audio"), None)
    out: dict[str, Any] = {
        "duration_sec": duration,
        "size_bytes": size,
        "format_name": format_name,
        "has_video": v is not None,
        "has_audio": a is not None,
        "stream_count": len(streams),
    }
    if v:
        try:
            w = int(v.get("width") or 0)
            h = int(v.get("height") or 0)
        except (TypeError, ValueError):
            w, h = 0, 0
        out["video"] = {
            "codec": v.get("codec_name"),
            "width": w,
            "height": h,
            "pix_fmt": v.get("pix_fmt"),
            "avg_frame_rate": v.get("avg_frame_rate"),
        }
    if a:
        try:
            ch = int(a.get("channels") or 0)
        except (TypeError, ValueError):
            ch = 0
        out["audio"] = {
            "codec": a.get("codec_name"),
            "sample_rate": a.get("sample_rate"),
            "channels": ch,
        }
    return out


def export_directory(repo_root: Path) -> Path:
    """Çıktı dosyaları: `<repo>/.ruzgar-video-export/`"""
    d = Path(repo_root).resolve() / ".ruzgar-video-export"
    d.mkdir(parents=True, exist_ok=True)
    return d


def run_ffmpeg_args(
    argv_after_binary: list[str],
    *,
    timeout_sec: int = DEFAULT_FFMPEG_TIMEOUT,
) -> str:
    """
    ffmpeg'i güvenli liste argümanlarıyla çalıştırır.
    `argv_after_binary`: ffmpeg ikilisinden sonraki argümanlar (-y, -i, ...).
    Hata durumunda stderr döner.
    """
    exe = ffmpeg_bin()
    if not exe:
        raise RuntimeError("ffmpeg bulunamadı; PATH'e ekleyin.")
    cmd = [exe] + argv_after_binary
    r = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout_sec,
        encoding="utf-8",
        errors="replace",
    )
    if r.returncode != 0:
        err = (r.stderr or r.stdout or "").strip()[:4000]
        raise RuntimeError(err or f"ffmpeg çıkış kodu {r.returncode}")
    return (r.stderr or "").strip()


def _concat_escape_path(p: Path) -> str:
    """concat demuxer satırı için tek tırnak kaçışı."""
    s = p.resolve().as_posix()
    return s.replace("'", "'\\''")


def trim_media(
    input_path: Path,
    output_path: Path,
    *,
    start_sec: float,
    duration_sec: float,
    copy_streams: bool,
    timeout_sec: int = DEFAULT_FFMPEG_TIMEOUT,
) -> None:
    """Zaman aralığı kes — `-ss` girişten sonra (tahmini kare uyumu)."""
    sp = float(start_sec)
    dur = float(duration_sec)
    if sp < 0 or dur <= 0:
        raise ValueError("Geçersiz başlangıç veya süre.")
    if dur > MAX_SEGMENT_SECONDS:
        raise ValueError(f"Kesim süresi en fazla {MAX_SEGMENT_SECONDS // 3600} saat olabilir.")

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    argv = [
        "-y",
        "-i",
        str(Path(input_path).resolve()),
        "-ss",
        str(sp),
        "-t",
        str(dur),
    ]
    if copy_streams:
        argv.extend(["-c", "copy"])
    else:
        argv.extend(
            [
                "-c:v",
                "libx264",
                "-preset",
                "fast",
                "-crf",
                "23",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-movflags",
                "+faststart",
            ]
        )
    argv.append(str(out_path.resolve()))
    run_ffmpeg_args(argv, timeout_sec=timeout_sec)


def trim_remote_media(
    input_url: str,
    output_path: Path,
    *,
    start_sec: float,
    duration_sec: float,
    copy_streams: bool = False,
    http_headers: dict[str, str] | None = None,
    timeout_sec: int | None = None,
) -> None:
    """
    Uzak akıştan yalnızca istenen aralığı kes — tam dosya indirmez.
    `-ss` girişten önce: HTTP/HLS üzerinde hızlı atlama.
    """
    url = (input_url or "").strip()
    if not url:
        raise ValueError("Akış URL boş.")
    sp = float(start_sec)
    dur = float(duration_sec)
    if sp < 0 or dur <= 0:
        raise ValueError("Geçersiz başlangıç veya süre.")
    if dur > MAX_SEGMENT_SECONDS:
        raise ValueError(f"Kesim süresi en fazla {MAX_SEGMENT_SECONDS // 3600} saat olabilir.")

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if timeout_sec is None:
        timeout_sec = min(DEFAULT_FFMPEG_TIMEOUT, max(300, int(dur * 4 + 180)))

    argv: list[str] = ["-y"]
    if http_headers:
        header_lines = "".join(f"{k}: {v}\r\n" for k, v in http_headers.items() if k and v is not None)
        if header_lines:
            argv.extend(["-headers", header_lines])
    argv.extend(
        [
            "-ss",
            str(sp),
            "-i",
            url,
            "-t",
            str(dur),
        ]
    )
    if copy_streams:
        argv.extend(["-c", "copy", "-avoid_negative_ts", "make_zero"])
    else:
        argv.extend(
            [
                "-c:v",
                "libx264",
                "-preset",
                "fast",
                "-crf",
                "23",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-movflags",
                "+faststart",
            ]
        )
    argv.append(str(out_path.resolve()))
    run_ffmpeg_args(argv, timeout_sec=timeout_sec)


def ffprobe_remote_json(
    input_url: str,
    *,
    http_headers: dict[str, str] | None = None,
    timeout_sec: int = 120,
) -> dict[str, Any]:
    """Uzak akış/dosya URL üzerinde ffprobe."""
    exe = ffprobe_bin()
    if not exe:
        raise RuntimeError("ffprobe bulunamadı; PATH'e ekleyin.")
    url = (input_url or "").strip()
    if not url:
        raise ValueError("URL boş.")
    cmd = [
        exe,
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
    ]
    if http_headers:
        header_lines = "".join(f"{k}: {v}\r\n" for k, v in http_headers.items() if k and v is not None)
        if header_lines:
            cmd.extend(["-headers", header_lines])
    cmd.append(url)
    r = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout_sec,
        encoding="utf-8",
        errors="replace",
    )
    if r.returncode != 0:
        err = (r.stderr or r.stdout or "").strip()[:1200]
        raise RuntimeError(err or f"ffprobe çıkış kodu {r.returncode}")
    return json.loads(r.stdout or "{}")


def transcode_to_mp4(
    input_path: Path,
    output_path: Path,
    *,
    timeout_sec: int = DEFAULT_FFMPEG_TIMEOUT,
) -> None:
    """Tam dosyayı H.264 + AAC MP4'e çevirir."""
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    argv = [
        "-y",
        "-i",
        str(Path(input_path).resolve()),
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "23",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-movflags",
        "+faststart",
        str(out_path.resolve()),
    ]
    run_ffmpeg_args(argv, timeout_sec=timeout_sec)


def concat_two_files(
    path_a: Path,
    path_b: Path,
    output_path: Path,
    *,
    copy_streams: bool = True,
    timeout_sec: int = DEFAULT_FFMPEG_TIMEOUT,
) -> None:
    """İki medya dosyasını concat demuxer ile birleştirir (codec uyumu kullanıcıya bağlı)."""
    pa = Path(path_a).resolve()
    pb = Path(path_b).resolve()
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    list_body = (
        f"file '{_concat_escape_path(pa)}'\nfile '{_concat_escape_path(pb)}'\n"
    )
    tmp_list = out_path.parent / f"_concat_list_{uuid.uuid4().hex}.txt"
    try:
        tmp_list.write_text(list_body, encoding="utf-8")
        argv = ["-y", "-f", "concat", "-safe", "0", "-i", str(tmp_list.resolve())]
        if copy_streams:
            argv.extend(["-c", "copy"])
        else:
            argv.extend(
                [
                    "-c:v",
                    "libx264",
                    "-preset",
                    "fast",
                    "-crf",
                    "23",
                    "-c:a",
                    "aac",
                    "-b:a",
                    "192k",
                    "-movflags",
                    "+faststart",
                ]
            )
        argv.append(str(out_path.resolve()))
        run_ffmpeg_args(argv, timeout_sec=timeout_sec)
    finally:
        try:
            if tmp_list.is_file():
                tmp_list.unlink()
        except OSError:
            pass


def concat_many_files(
    paths: list[Path],
    output_path: Path,
    *,
    copy_streams: bool = True,
    timeout_sec: int = DEFAULT_FFMPEG_TIMEOUT,
) -> None:
    """Birden fazla medya dosyasını sırayla birleştirir (kurgu / timeline mix)."""
    resolved = [Path(p).resolve() for p in paths if str(p).strip()]
    if len(resolved) < 1:
        raise ValueError("En az bir dosya gerekli.")
    if len(resolved) == 1:
        import shutil

        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(resolved[0], out_path)
        return

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    list_body = "".join(
        f"file '{_concat_escape_path(p)}'\n" for p in resolved
    )
    tmp_list = out_path.parent / f"_concat_list_{uuid.uuid4().hex}.txt"
    try:
        tmp_list.write_text(list_body, encoding="utf-8")
        argv = ["-y", "-f", "concat", "-safe", "0", "-i", str(tmp_list.resolve())]
        if copy_streams:
            argv.extend(["-c", "copy"])
        else:
            argv.extend(
                [
                    "-c:v",
                    "libx264",
                    "-preset",
                    "fast",
                    "-crf",
                    "23",
                    "-c:a",
                    "aac",
                    "-b:a",
                    "192k",
                    "-movflags",
                    "+faststart",
                ]
            )
        argv.append(str(out_path.resolve()))
        run_ffmpeg_args(argv, timeout_sec=timeout_sec)
    finally:
        try:
            if tmp_list.is_file():
                tmp_list.unlink()
        except OSError:
            pass


def generate_silence_mp3(
    output_path: Path,
    duration_ms: int,
    *,
    sample_rate: int = 24000,
    timeout_sec: int = 120,
) -> None:
    """Belirtilen sürede sessiz MP3 üretir (TTS parça birleştirme — Faz S1)."""
    ms = max(40, int(duration_ms))
    sec = ms / 1000.0
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    argv = [
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"anullsrc=r={sample_rate}:cl=mono",
        "-t",
        f"{sec:.3f}",
        "-c:a",
        "libmp3lame",
        "-q:a",
        "4",
        str(out_path.resolve()),
    ]
    run_ffmpeg_args(argv, timeout_sec=timeout_sec)


def generate_silence_wav(
    output_path: Path,
    duration_ms: int,
    *,
    sample_rate: int = 22050,
    timeout_sec: int = 120,
) -> None:
    """Belirtilen sürede sessiz WAV üretir (dublaj zaman çizelgesi — Faz S6)."""
    ms = max(40, int(duration_ms))
    sec = ms / 1000.0
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    argv = [
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"anullsrc=r={sample_rate}:cl=mono",
        "-t",
        f"{sec:.3f}",
        "-c:a",
        "pcm_s16le",
        str(out_path.resolve()),
    ]
    run_ffmpeg_args(argv, timeout_sec=timeout_sec)


def audio_duration_sec(path: str | Path) -> float:
    """Ses/video dosyası süresi (saniye)."""
    data = ffprobe_json(path)
    try:
        return max(0.0, float(data.get("format", {}).get("duration") or 0.0))
    except (TypeError, ValueError):
        return 0.0


def extract_audio_for_stt(
    input_path: Path,
    output_wav: Path,
    *,
    sample_rate: int = 16000,
    max_duration_sec: float | None = None,
    timeout_sec: int = DEFAULT_FFMPEG_TIMEOUT,
) -> None:
    """Video veya ses dosyasından Whisper için 16 kHz mono WAV çıkarır (Faz S2)."""
    src = Path(input_path).resolve()
    if not src.is_file():
        raise FileNotFoundError(src)
    out_path = Path(output_wav)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    argv = ["-y", "-i", str(src), "-vn"]
    if max_duration_sec is not None and max_duration_sec > 0:
        argv.extend(["-t", f"{float(max_duration_sec):.3f}"])
    argv.extend(
        [
            "-acodec",
            "pcm_s16le",
            "-ar",
            str(int(sample_rate)),
            "-ac",
            "1",
            str(out_path.resolve()),
        ]
    )
    run_ffmpeg_args(argv, timeout_sec=timeout_sec)


def concat_audio_files(
    paths: list[Path],
    output_path: Path,
    *,
    copy_streams: bool = True,
    timeout_sec: int = DEFAULT_FFMPEG_TIMEOUT,
) -> None:
    """Ses dosyalarını sırayla birleştirir (MP3/WAV — prosody TTS hattı)."""
    resolved = [Path(p).resolve() for p in paths if str(p).strip()]
    if len(resolved) < 1:
        raise ValueError("En az bir ses dosyası gerekli.")
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if len(resolved) == 1:
        import shutil

        shutil.copy2(resolved[0], out_path)
        return

    list_body = "".join(
        f"file '{_concat_escape_path(p)}'\n" for p in resolved
    )
    tmp_list = out_path.parent / f"_concat_audio_{uuid.uuid4().hex}.txt"
    try:
        tmp_list.write_text(list_body, encoding="utf-8")
        argv = ["-y", "-f", "concat", "-safe", "0", "-i", str(tmp_list.resolve())]
        if copy_streams:
            argv.extend(["-c", "copy"])
        else:
            argv.extend(["-c:a", "libmp3lame", "-q:a", "2"])
        argv.append(str(out_path.resolve()))
        run_ffmpeg_args(argv, timeout_sec=timeout_sec)
    finally:
        try:
            if tmp_list.is_file():
                tmp_list.unlink()
        except OSError:
            pass


# Altyazı gömme (burn-in): .srt / .ass / .ssa / .vtt (ffmpeg + libass)
_ALLOWED_SUBTITLE_SUFFIXES = frozenset({".srt", ".ass", ".ssa", ".vtt"})


def _vf_subtitles_filter(sub_path: Path) -> str:
    """libavfilter subtitles= için tek -vf argümanı (Windows sürücü yolu dahil)."""
    p = Path(sub_path).resolve().as_posix().replace("\\", "/")
    p = p.replace("'", r"\'")
    if len(p) >= 2 and p[1] == ":":
        p = p[0] + "\\:" + p[2:]
    return f"subtitles='{p}'"


def burn_subtitles_into_mp4(
    input_video: Path,
    subtitle_path: Path,
    output_path: Path,
    *,
    timeout_sec: int = DEFAULT_FFMPEG_TIMEOUT,
) -> None:
    """Altyazıyı görüntüye gömer; video H.264 yeniden kodlanır, ses varsa kopyalanır."""
    suf = Path(subtitle_path).suffix.lower()
    if suf not in _ALLOWED_SUBTITLE_SUFFIXES:
        raise ValueError(
            "Desteklenen altyazı uzantıları: " + ", ".join(sorted(_ALLOWED_SUBTITLE_SUFFIXES))
        )
    iv = Path(input_video).resolve()
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    vf = _vf_subtitles_filter(Path(subtitle_path))

    probe_data = ffprobe_json(iv)
    has_audio = bool(summarize_probe(probe_data).get("has_audio"))

    argv: list[str] = [
        "-y",
        "-i",
        str(iv),
        "-vf",
        vf,
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "23",
    ]
    if has_audio:
        argv.extend(["-c:a", "copy"])
    argv.extend(["-movflags", "+faststart", str(out_path.resolve())])
    run_ffmpeg_args(argv, timeout_sec=timeout_sec)


def mux_replace_audio(
    video_path: Path,
    audio_path: Path,
    output_path: Path,
    *,
    copy_video: bool = True,
    shortest: bool = True,
    timeout_sec: int = DEFAULT_FFMPEG_TIMEOUT,
) -> None:
    """Videodaki sesi harici ses dosyasıyla değiştirir (çıktı MP4)."""
    vp = Path(video_path).resolve()
    ap = Path(audio_path).resolve()
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    argv = [
        "-y",
        "-i",
        str(vp),
        "-i",
        str(ap),
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
    ]
    if copy_video:
        argv.extend(["-c:v", "copy"])
    else:
        argv.extend(
            [
                "-c:v",
                "libx264",
                "-preset",
                "fast",
                "-crf",
                "23",
            ]
        )
    argv.extend(["-c:a", "aac", "-b:a", "192k"])
    if shortest:
        argv.append("-shortest")
    argv.extend(["-movflags", "+faststart", str(out_path.resolve())])
    run_ffmpeg_args(argv, timeout_sec=timeout_sec)
