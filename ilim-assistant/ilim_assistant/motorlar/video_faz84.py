# Created by Ümit & Gökçenur
"""
Video motoru — Faz 84: YouTube isimle arama + sonuç listesi.

«şu filmi ara», «video ara: …» → yt-dlp ytsearch (indirme yok).
"""

from __future__ import annotations

import os
import re
import unicodedata
from typing import Any

FAZ84_VERSION = "video-faz84-v1-2026-05-26"

_SEARCH_CUE_RE = re.compile(
    r"(?:şu\s+filmi\s+ara|filmi\s+ara|video\s+ara|youtube\s+ara|video\s+bul|"
    r"youtube\s+bul|klip\s+ara|(?:ara|bul)\s+.*\b(?:film|video|youtube|klip)\b)",
    re.I,
)
_PICK_RE = re.compile(
    r"(?:indir|download)\s*(?:#|no|numara)?\s*(\d{1,2})\b|"
    r"(\d{1,2})\s*(?:numarayı|numarayi|nolu)\s*indir",
    re.I,
)
_STRIP_PREFIX_RE = re.compile(
    r"^(?:şu\s+filmi\s+ara|filmi\s+ara|video\s+ara|youtube\s+ara|video\s+bul|"
    r"youtube\s+bul|klip\s+ara|ara|bul)\s*:?\s*",
    re.I,
)


def _enabled() -> bool:
    return os.environ.get("RUZGAR_VIDEO_FAZ84", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz84_enabled() -> bool:
    return _enabled()


def _ascii_fold(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def wants_video_search(message: str) -> bool:
    if not _enabled():
        return False
    raw = (message or "").strip()
    if not raw:
        return False
    from ilim_assistant.motorlar.video_faz71 import extract_urls

    if extract_urls(raw):
        return False
    return bool(_SEARCH_CUE_RE.search(_ascii_fold(raw)))


def extract_search_query(message: str) -> str:
    raw = (message or "").strip()
    q = _STRIP_PREFIX_RE.sub("", raw).strip()
    q = re.sub(r"^(?:youtube|video|film|klip)\s+", "", q, flags=re.I).strip()
    return q[:200]


def parse_pick_index(message: str) -> int | None:
    m = _PICK_RE.search(message or "")
    if not m:
        return None
    g = m.group(1) or m.group(2)
    if not g:
        return None
    try:
        n = int(g)
        return n if 1 <= n <= 25 else None
    except ValueError:
        return None


def search_youtube(query: str, *, max_results: int = 8) -> dict[str, Any]:
    """yt-dlp ytsearch — yalnızca metadata."""
    q = (query or "").strip()
    if len(q) < 2:
        return {"ok": False, "error": "Arama metni çok kısa.", "results": []}
    cap = max(3, min(int(os.environ.get("RUZGAR_VIDEO_SEARCH_MAX", "8")), 15))
    try:
        import yt_dlp  # type: ignore[import-untyped]

        opts: dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "skip_download": True,
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(f"ytsearch{cap}:{q}", download=False)
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:300], "results": []}

    entries: list[dict[str, Any]] = []
    raw_entries = []
    if isinstance(info, dict):
        raw_entries = info.get("entries") or []
    for ent in raw_entries:
        if not isinstance(ent, dict):
            continue
        vid = ent.get("id") or ""
        if not vid and ent.get("url"):
            m = re.search(r"v=([\w-]{6,})", str(ent.get("url")))
            vid = m.group(1) if m else ""
        url = ent.get("webpage_url") or ent.get("url") or ""
        if vid and "youtube" not in (url or ""):
            url = f"https://www.youtube.com/watch?v={vid}"
        entries.append(
            {
                "title": str(ent.get("title") or "?")[:120],
                "id": vid,
                "url": url,
                "duration_sec": ent.get("duration"),
                "channel": str(ent.get("uploader") or ent.get("channel") or "")[:80],
            }
        )
    if not entries:
        return {"ok": False, "error": "Sonuç bulunamadı.", "results": [], "query": q}
    return {"ok": True, "query": q, "results": entries, "version": FAZ84_VERSION}


def format_search_results(data: dict[str, Any]) -> str:
    if not data.get("ok"):
        return f"Ümit abi, arama başarısız: {data.get('error', '?')}\n({FAZ84_VERSION})"
    lines = [
        f"Ümit abi, **YouTube arama** — «{data.get('query', '')}»",
        "",
    ]
    for i, row in enumerate(data.get("results") or [], 1):
        dur = row.get("duration_sec")
        dur_s = f" · {int(dur)} sn" if isinstance(dur, (int, float)) and dur else ""
        ch = row.get("channel") or ""
        ch_s = f" · {ch}" if ch else ""
        lines.append(f"{i}. **{row.get('title', '?')}**{dur_s}{ch_s}")
        lines.append(f"   {row.get('url', '')}")
    lines.append("")
    lines.append(
        "İndirmek için: tam linki yapıştırın veya "
        "«2 numarayı indir» yazın."
    )
    lines.append(f"\n({FAZ84_VERSION})")
    return "\n".join(lines)


def maybe_search_and_pick(message: str) -> str | None:
    """«3 numarayı indir» — son arama önbelleğinden."""
    if not _enabled():
        return None
    idx = parse_pick_index(message)
    if idx is None:
        return None
    last = _load_last_search()
    rows = last.get("results") or []
    if not rows or idx > len(rows):
        return None
    url = rows[idx - 1].get("url") or ""
    if not url:
        return None
    from ilim_assistant.motorlar.video_faz71 import run_download_url

    return run_download_url(url)


_LAST_SEARCH: dict[str, Any] = {}


def _save_last_search(data: dict[str, Any]) -> None:
    global _LAST_SEARCH
    _LAST_SEARCH = dict(data)


def _load_last_search() -> dict[str, Any]:
    return dict(_LAST_SEARCH)


def run_search(message: str) -> str:
    q = extract_search_query(message)
    if len(q) < 2:
        return f"Ümit abi, ne arayayım? Örnek: «şu filmi ara: dune fragman»\n({FAZ84_VERSION})"
    data = search_youtube(q)
    if data.get("ok"):
        _save_last_search(data)
    return format_search_results(data)


def maybe_instant_faz84(message: str) -> str | None:
    if not _enabled():
        return None
    raw = (message or "").strip()
    if not raw:
        return None
    pick = maybe_search_and_pick(raw)
    if pick:
        return pick
    if wants_video_search(raw):
        return run_search(raw)
    return None


def enrich_health_build(build: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(build or {})
    out["video_faz84"] = faz84_enabled()
    return out
