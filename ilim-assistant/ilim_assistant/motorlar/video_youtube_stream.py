# Created by Ümit & Gökçenur
"""YouTube sinema akışı — geriye uyumluluk katmanı."""

from __future__ import annotations

from ilim_assistant.motorlar.video_stream import (
    StreamPrepareResult,
    get_stream_session,
    prepare_stream,
    prepare_youtube_stream,
    resolve_ytdlp_stream_url as resolve_youtube_stream_url,
)

__all__ = [
    "StreamPrepareResult",
    "get_stream_session",
    "prepare_stream",
    "prepare_youtube_stream",
    "resolve_youtube_stream_url",
]
