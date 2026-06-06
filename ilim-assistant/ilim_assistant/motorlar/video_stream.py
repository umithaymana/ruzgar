# Created by Ümit & Gökçenur
"""Evrensel sinema akışı: yt-dlp · doğrudan video URL · HLS proxy oturumu."""

from __future__ import annotations

import os
import re
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlparse

from ilim_assistant.motorlar.video_motoru import (
    _format_ytdlp_error,
    _validate_url,
    _ytdlp_cookie_opts,
)

_STREAM_TTL_SEC = int(os.environ.get("RUZGAR_STREAM_TTL_SEC", "7200") or "7200")
_lock = threading.Lock()
_sessions: dict[str, dict[str, Any]] = {}

_DIRECT_EXT = (".mp4", ".webm", ".mkv", ".mov", ".m4v", ".ogv", ".avi")
_HLS_HINT = (".m3u8", ".m3u")


def _stream_format() -> str:
    return (
        os.environ.get(
            "RUZGAR_YTDLP_STREAM_FORMAT",
            "best[ext=mp4][height<=1080]/best[ext=mp4]/best[height<=1080]/best",
        ).strip()
        or "best[ext=mp4]/best"
    )


def _purge_expired() -> None:
    now = time.time()
    dead = [k for k, v in _sessions.items() if float(v.get("expires_at") or 0) < now]
    for k in dead:
        _sessions.pop(k, None)


def classify_stream_url(url: str) -> str:
    """direct | hls | ytdlp"""
    u = (url or "").strip()
    err = _validate_url(u)
    if err:
        raise ValueError(err)
    parsed = urlparse(u)
    path = (parsed.path or "").lower()
    query = (parsed.query or "").lower()
    if path.endswith(_HLS_HINT) or ".m3u8" in query:
        return "hls"
    if any(path.endswith(ext) for ext in _DIRECT_EXT):
        return "direct"
    return "ytdlp"


def _site_label(info: dict[str, Any], watch_url: str) -> str:
    extractor = str(info.get("extractor_key") or info.get("extractor") or "").strip()
    if extractor:
        return extractor.replace(":", "").strip() or "web"
    try:
        host = urlparse(watch_url).hostname or ""
        return host.replace("www.", "") or "web"
    except Exception:
        return "web"


def _pick_stream_url(info: dict[str, Any]) -> str:
    direct = str(info.get("url") or "").strip()
    if direct:
        return direct
    for fmt in reversed(info.get("formats") or []):
        if not isinstance(fmt, dict):
            continue
        if fmt.get("vcodec") in (None, "none"):
            continue
        u = str(fmt.get("url") or "").strip()
        if u:
            return u
    return ""


def resolve_ytdlp_stream_url(watch_url: str) -> tuple[str, dict[str, Any]]:
    err = _validate_url(watch_url)
    if err:
        raise ValueError(err)
    try:
        import yt_dlp  # type: ignore[import-untyped]
    except ImportError as e:
        raise ValueError("yt-dlp kurulu değil. pip install yt-dlp") from e

    cookie_attempts: list[dict[str, Any]] = [{}, _ytdlp_cookie_opts()]
    if _ytdlp_cookie_opts():
        cookie_attempts.append({"cookiesfrombrowser": ("chrome",)})

    last_exc: Exception | None = None
    for cookie_opts in cookie_attempts:
        ydl_opts: dict[str, Any] = {
            "format": _stream_format(),
            "quiet": True,
            "no_warnings": True,
            "noplaylist": os.environ.get("RUZGAR_YTDLP_PLAYLIST", "0").strip().lower()
            not in ("1", "true", "yes"),
            "skip_download": True,
            **cookie_opts,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(watch_url.strip(), download=False) or {}
            stream_url = _pick_stream_url(info)
            if stream_url:
                return stream_url, info
            last_exc = ValueError("Akış URL bulunamadı.")
        except Exception as exc:
            last_exc = exc
            msg = str(exc).lower()
            if "cookie" in msg or "could not copy" in msg:
                continue
            if "sign in" in msg or "bot" in msg:
                continue
            break

    if last_exc:
        raise last_exc
    raise ValueError("Video akış URL bulunamadı.")


@dataclass
class StreamPrepareResult:
    ok: bool
    token: str = ""
    title: str = ""
    video_id: str = ""
    duration_sec: float | None = None
    ext: str = "mp4"
    error: str | None = None
    stream_path: str = ""
    stream_type: str = "video"
    site: str = ""
    watch_url: str = ""


def _store_session(
    *,
    direct_url: str,
    watch_url: str,
    title: str,
    stream_type: str,
    site: str,
    video_id: str = "",
    duration: float | None = None,
    ext: str = "mp4",
    http_headers: dict[str, Any] | None = None,
) -> StreamPrepareResult:
    token = uuid.uuid4().hex[:16]
    with _lock:
        _purge_expired()
        _sessions[token] = {
            "direct_url": direct_url,
            "watch_url": watch_url,
            "title": title,
            "video_id": video_id,
            "stream_type": stream_type,
            "site": site,
            "ext": ext,
            "expires_at": time.time() + _STREAM_TTL_SEC,
            "http_headers": http_headers if isinstance(http_headers, dict) else {},
        }

    path = f"/api/video/stream/{token}"
    if stream_type == "hls":
        path = f"/api/video/stream/{token}/playlist.m3u8"

    return StreamPrepareResult(
        ok=True,
        token=token,
        title=title,
        video_id=video_id,
        duration_sec=duration,
        ext=ext,
        stream_path=path,
        stream_type=stream_type,
        site=site,
        watch_url=watch_url,
    )


def prepare_stream(watch_url: str) -> StreamPrepareResult:
    u = (watch_url or "").strip()
    try:
        kind = classify_stream_url(u)
    except ValueError as exc:
        return StreamPrepareResult(ok=False, error=str(exc))

    if kind == "direct":
        title = os.path.basename(urlparse(u).path) or "video"
        return _store_session(
            direct_url=u,
            watch_url=u,
            title=title,
            stream_type="video",
            site=_site_label({}, u),
            ext=os.path.splitext(title)[1].lstrip(".") or "mp4",
        )

    if kind == "hls":
        title = os.path.basename(urlparse(u).path) or "canlı akış"
        return _store_session(
            direct_url=u,
            watch_url=u,
            title=title,
            stream_type="hls",
            site=_site_label({}, u),
            ext="m3u8",
        )

    try:
        stream_url, info = resolve_ytdlp_stream_url(u)
    except Exception as exc:
        return StreamPrepareResult(ok=False, error=_format_ytdlp_error(exc))

    title = str(info.get("title") or info.get("id") or "video")
    vid = str(info.get("id") or "")
    dur_raw = info.get("duration")
    duration: float | None = None
    if dur_raw is not None:
        try:
            duration = float(dur_raw)
        except (TypeError, ValueError):
            duration = None

    return _store_session(
        direct_url=stream_url,
        watch_url=u,
        title=title,
        stream_type="video",
        site=_site_label(info, u),
        video_id=vid,
        duration=duration,
        ext=str(info.get("ext") or "mp4"),
        http_headers=info.get("http_headers") if isinstance(info.get("http_headers"), dict) else {},
    )


def prepare_youtube_stream(watch_url: str) -> StreamPrepareResult:
    """Geriye uyumluluk."""
    return prepare_stream(watch_url)


def get_stream_session(token: str) -> dict[str, Any] | None:
    safe = (token or "").strip()
    if not safe or len(safe) > 32:
        return None
    with _lock:
        _purge_expired()
        data = _sessions.get(safe)
        if not data:
            return None
        if float(data.get("expires_at") or 0) < time.time():
            _sessions.pop(safe, None)
            return None
        return dict(data)


def rewrite_hls_playlist(content: str, token: str, base_upstream: str) -> str:
    """Segment URI'lerini proxy üzerinden geçir."""
    lines_out: list[str] = []
    base_dir = base_upstream.rsplit("/", 1)[0] + "/"
    for line in content.splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#"):
            if raw.startswith("#") and "URI=" in raw:
                def _repl(m: re.Match[str]) -> str:
                    uri = m.group(1).strip('"')
                    abs_u = uri if uri.startswith("http") else base_dir + uri.lstrip("/")
                    enc = quote(abs_u, safe="")
                    return f'URI="/api/video/stream/{token}/seg?u={enc}"'

                lines_out.append(re.sub(r'URI="([^"]+)"', _repl, raw))
            else:
                lines_out.append(line)
            continue
        abs_u = raw if raw.startswith("http") else base_dir + raw.lstrip("/")
        if abs_u.lower().endswith(".m3u8") or ".m3u8?" in abs_u.lower():
            enc = quote(abs_u, safe="")
            lines_out.append(f"/api/video/stream/{token}/playlist.m3u8?u={enc}")
        else:
            enc = quote(abs_u, safe="")
            lines_out.append(f"/api/video/stream/{token}/seg?u={enc}")
    return "\n".join(lines_out) + "\n"


def resolve_stream_session(
    *,
    token: str = "",
    watch_url: str = "",
) -> dict[str, Any]:
    """Aktif oturum veya watch URL ile akış metadata döner."""
    tok = (token or "").strip()
    if tok:
        sess = get_stream_session(tok)
        if sess:
            return sess

    watch = (watch_url or "").strip()
    if not watch:
        raise ValueError("Akış oturumu yok — sinemada videoyu açın veya token/URL verin.")

    with _lock:
        _purge_expired()
        for data in _sessions.values():
            if str(data.get("watch_url") or "").strip() == watch:
                return dict(data)

    prep = prepare_stream(watch)
    if not prep.ok or not prep.token:
        raise ValueError(prep.error or "Akış hazırlanamadı.")
    sess = get_stream_session(prep.token)
    if not sess:
        raise ValueError("Akış oturumu açılamadı.")
    return sess


def probe_stream_session(
    *,
    token: str = "",
    watch_url: str = "",
) -> dict[str, Any]:
    from ilim_assistant.video_ffmpeg import ffprobe_remote_json, summarize_probe

    sess = resolve_stream_session(token=token, watch_url=watch_url)
    direct = str(sess.get("direct_url") or "").strip()
    if not direct:
        raise ValueError("Akış URL yok.")
    headers = sess.get("http_headers") if isinstance(sess.get("http_headers"), dict) else {}
    data = ffprobe_remote_json(direct, http_headers=headers)
    summary = summarize_probe(data)
    summary["stream_mode"] = True
    summary["title"] = sess.get("title") or ""
    summary["watch_url"] = sess.get("watch_url") or ""
    return summary


def trim_stream_segment(
    *,
    repo_root: Path,
    token: str = "",
    watch_url: str = "",
    start_sec: float,
    duration_sec: float,
    copy_streams: bool = False,
) -> str:
    """Akıştan kesim — çıktı `.ruzgar-video-export/` altına; göreli yol döner."""
    from ilim_assistant.video_ffmpeg import export_directory, trim_remote_media

    sess = resolve_stream_session(token=token, watch_url=watch_url)
    direct = str(sess.get("direct_url") or "").strip()
    if not direct:
        raise ValueError("Akış URL yok.")
    headers = sess.get("http_headers") if isinstance(sess.get("http_headers"), dict) else {}

    out_dir = export_directory(repo_root)
    title = str(sess.get("title") or "stream")[:40]
    safe_stem = re.sub(r"[^\w\-]+", "_", title).strip("_") or "stream"
    out_name = f"ruzgar_stream_trim_{uuid.uuid4().hex[:10]}_{safe_stem}.mp4"
    out_path = out_dir / out_name

    trim_remote_media(
        direct,
        out_path,
        start_sec=start_sec,
        duration_sec=duration_sec,
        copy_streams=copy_streams,
        http_headers=headers,
    )
    return out_path.relative_to(Path(repo_root).resolve()).as_posix()
