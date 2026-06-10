# Created by Ümit & Gökçenur
"""Ana Motor Faz W2 — video URL metadata (indirme yok, sohbet içi bilgi)."""

from __future__ import annotations

import os
import re
from typing import Any

_INFO_CUE_RE = re.compile(
    r"(?:bilgi|özet|ozet|metadata|meta\s*veri|başlık|baslik|süre|sure|kanal|"
    r"ne\s+kadar|kaç\s+dakika|kac\s+dakika|açıkla|acikla|tanıt|tanit|"
    r"bu\s+link|şu\s+link|su\s+link|videoda\s+ne)",
    re.I,
)
_ACTION_CUE_RE = re.compile(
    r"(?:indir|download|kes|kurgu|birleştir|birlestir|altyazı|altyazi|"
    r"göm|gom|mux|transcode|dönüştür|donustur|oynat|panelde\s+aç|panelde\s+ac)",
    re.I,
)


def video_url_info_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_VIDEO_URL_INFO", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _wants_url_info(message: str, urls: list[str]) -> bool:
    if not urls:
        return False
    raw = (message or "").strip()
    if _ACTION_CUE_RE.search(raw):
        return False
    if _INFO_CUE_RE.search(raw):
        return True
    # Yalnızca URL — bilgi isteği say (indirme komutu yok)
    stripped = re.sub(r"https?://\S+", "", raw).strip()
    return len(stripped) < 12


def _fetch_metadata(url: str) -> dict[str, Any]:
    try:
        import yt_dlp  # type: ignore[import-untyped]

        opts: dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "extract_flat": False,
        }
        try:
            from ilim_assistant.motorlar.video_motoru import _ytdlp_cookie_opts

            cookies = _ytdlp_cookie_opts()
            if cookies:
                opts.update(cookies)
        except Exception:
            pass
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url.strip(), download=False) or {}
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:300]}

    if not isinstance(info, dict):
        return {"ok": False, "error": "Metadata alınamadı."}

    duration = info.get("duration")
    dur_s = ""
    if isinstance(duration, (int, float)) and duration > 0:
        m, s = divmod(int(duration), 60)
        h, m = divmod(m, 60)
        dur_s = f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

    desc = str(info.get("description") or "").strip()
    if len(desc) > 400:
        desc = desc[:400] + "…"

    return {
        "ok": True,
        "title": str(info.get("title") or "?")[:200],
        "channel": str(info.get("uploader") or info.get("channel") or "")[:120],
        "duration": dur_s,
        "duration_sec": duration,
        "view_count": info.get("view_count"),
        "url": info.get("webpage_url") or url,
        "description": desc,
    }


def maybe_video_url_info(message: str) -> dict[str, Any]:
    if not video_url_info_enabled():
        return {"ok": True, "handled": False, "reason": "video_url_info_disabled"}

    raw = (message or "").strip()
    if not raw:
        return {"ok": True, "handled": False, "reason": "empty"}

    try:
        from ilim_assistant.motorlar.video_faz71 import extract_urls
    except Exception:
        return {"ok": True, "handled": False, "reason": "video_faz71_missing"}

    urls = extract_urls(raw)
    if not _wants_url_info(raw, urls):
        return {"ok": True, "handled": False, "reason": "not_info_request"}

    meta = _fetch_metadata(urls[0])
    if not meta.get("ok"):
        return {
            "ok": False,
            "handled": False,
            "error": str(meta.get("error") or "Video bilgisi alınamadı."),
        }

    views = meta.get("view_count")
    views_s = f" · {int(views):,} izlenme".replace(",", ".") if isinstance(views, int) else ""
    dur = meta.get("duration") or "?"
    ch = meta.get("channel") or "?"
    lines = [
        f"Ümit abi, **video bilgisi** (indirme yok):",
        "",
        f"**{meta.get('title')}**",
        f"Kanal: {ch} · Süre: {dur}{views_s}",
        f"URL: {meta.get('url')}",
    ]
    if meta.get("description"):
        lines.extend(["", str(meta.get("description"))])
    lines.append("")
    lines.append("_(Sohbet içi backend — yt-dlp metadata)_")

    return {
        "ok": True,
        "handled": True,
        "reply": "\n".join(lines),
        "channel": "video_url_info",
        "url": urls[0],
    }
