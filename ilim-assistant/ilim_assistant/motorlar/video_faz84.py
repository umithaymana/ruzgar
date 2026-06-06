# Created by Ümit & Gökçenur
"""
Video motoru — Faz 84: YouTube isimle arama + sonuç listesi.

«şu filmi ara», «video ara: …» → yt-dlp ytsearch (indirme yok).
"""

from __future__ import annotations

import json
import os
import re
import time
import unicodedata
from pathlib import Path
from typing import Any

FAZ84_VERSION = "video-faz84-v2-2026-05-26"
_SEARCH_CACHE_FILE = "video_search_last.json"

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
_PICK_OPEN_RE = re.compile(
    r"(?:oynat|izle|aç|ac|panelde\s+aç|panelde\s+ac)\s*(?:#|no|numara)?\s*(\d{1,2})\b|"
    r"(\d{1,2})\s*(?:numarayı|numarayi|nolu)\s*(?:oynat|izle|aç|ac|panelde\s+aç|panelde\s+ac)|"
    r"(\d{1,2})\s*(?:numarayı|numarayi)\s*(?:panelde|sinemada)",
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


def parse_pick_open_index(message: str) -> int | None:
    m = _PICK_OPEN_RE.search(message or "")
    if not m:
        return None
    g = m.group(1) or m.group(2) or m.group(3)
    if not g:
        return None
    try:
        n = int(g)
        return n if 1 <= n <= 25 else None
    except ValueError:
        return None


def pick_from_last_search_by_index(
    idx: int,
    workspace_root: str | Path | None = None,
) -> dict[str, Any] | None:
    if idx < 1 or idx > 25:
        return None
    last = _load_last_search(workspace_root)
    rows = last.get("results") or []
    if not rows or idx > len(rows):
        return None
    row = rows[idx - 1]
    url = row.get("url") or ""
    if not url:
        return None
    return {"index": idx, "url": url, "title": row.get("title") or "", "row": row}


def pick_from_last_search(
    message: str,
    workspace_root: str | Path | None = None,
) -> dict[str, Any] | None:
    idx = parse_pick_index(message)
    if idx is None:
        idx = parse_pick_open_index(message)
    if idx is None:
        return None
    return pick_from_last_search_by_index(idx, workspace_root)


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
        "Sinema: «2 numarayı oynat» veya «2 numarayı panelde aç» · "
        "İndir: «2 numarayı indir» veya tam link."
    )
    lines.append(f"\n({FAZ84_VERSION})")
    return "\n".join(lines)


def maybe_search_and_pick(
    message: str,
    workspace_root: str | Path | None = None,
) -> str | None:
    """«3 numarayı indir» — son arama önbelleğinden."""
    if not _enabled():
        return None
    idx = parse_pick_index(message)
    if idx is None:
        return None
    picked = pick_from_last_search_by_index(idx, workspace_root)
    if not picked:
        return None
    from ilim_assistant.motorlar.video_faz71 import run_download_url

    return run_download_url(str(picked.get("url") or ""))


def maybe_search_and_open(
    message: str,
    workspace_root: str | Path | None = None,
) -> dict[str, Any] | None:
    """«3 numarayı oynat / panelde aç» — indirme yok."""
    if not _enabled():
        return None
    idx = parse_pick_open_index(message)
    if idx is None:
        return None
    picked = pick_from_last_search_by_index(idx, workspace_root)
    if not picked:
        return None
    return picked


_LAST_SEARCH: dict[str, Any] = {}


def _cache_path(workspace_root: str | Path | None = None) -> Path | None:
    try:
        from ilim_assistant.motorlar.programlama_motoru import repo_root

        root = repo_root(workspace_root)
        if root is None:
            return None
        d = root / ".ruzgar"
        d.mkdir(parents=True, exist_ok=True)
        return d / _SEARCH_CACHE_FILE
    except Exception:
        return None


def _save_last_search(data: dict[str, Any], workspace_root: str | Path | None = None) -> None:
    global _LAST_SEARCH
    _LAST_SEARCH = dict(data)
    path = _cache_path(workspace_root)
    if path is None:
        return
    try:
        payload = {**data, "saved_at": time.time()}
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass


def _load_last_search(workspace_root: str | Path | None = None) -> dict[str, Any]:
    if _LAST_SEARCH.get("results"):
        return dict(_LAST_SEARCH)
    path = _cache_path(workspace_root)
    if path is None or not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            _LAST_SEARCH.update(data)
            return dict(data)
    except (OSError, json.JSONDecodeError):
        pass
    return {}


def run_search(message: str, workspace_root: str | Path | None = None) -> str:
    q = extract_search_query(message)
    if len(q) < 2:
        return f"Ümit abi, ne arayayım? Örnek: «şu filmi ara: dune fragman»\n({FAZ84_VERSION})"
    data = search_youtube(q)
    if data.get("ok"):
        _save_last_search(data, workspace_root)
    return format_search_results(data)


def maybe_instant_faz84(
    message: str,
    workspace_root: str | Path | None = None,
) -> str | None:
    if not _enabled():
        return None
    raw = (message or "").strip()
    if not raw:
        return None
    pick = maybe_search_and_pick(raw, workspace_root)
    if pick:
        return pick
    if wants_video_search(raw):
        return run_search(raw, workspace_root)
    return None


def enrich_health_build(build: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(build or {})
    out["video_faz84"] = faz84_enabled()
    return out
