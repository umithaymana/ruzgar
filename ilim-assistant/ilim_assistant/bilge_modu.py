"""Bilge Modu: genel kultur hub (Wikipedia + ansiklopedi + akademik arama).

Umit & Gokcenur - Ruzgar'in ortak entelektuel sinir sistemi.
"""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

_PKG_ROOT = Path(__file__).resolve().parent.parent
_CACHE_FILE = _PKG_ROOT / "hafiza" / "bilge_gunluk.json"
_UA = "Ruzgar-BilgeModu/1.0 (+local assistant)"


def bilge_enabled() -> bool:
    return os.environ.get("RUZGAR_BILGE_MODE", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def bilge_heartbeat() -> str:
    if not bilge_enabled():
        return ""
    return (
        "[BILGE MODU - Umit & Gokcenur] Genel kultur sorularinda yerel hafiza yetmezse "
        "Wikipedia/ansiklopedik/akademik kaynaklara baglan, sonra hikmetli ve akici bir sentez ver.\n"
    )


def _http_json(url: str, timeout_sec: float) -> dict | list | None:
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            raw = resp.read().decode("utf-8", errors="ignore")
        return json.loads(raw)
    except Exception:
        return None


def _wiki_summary(query: str, timeout_sec: float) -> str:
    q = urllib.parse.quote(query.strip().replace(" ", "_"))
    url = f"https://tr.wikipedia.org/api/rest_v1/page/summary/{q}"
    data = _http_json(url, timeout_sec)
    if isinstance(data, dict):
        ex = str(data.get("extract") or "").strip()
        title = str(data.get("title") or query).strip()
        if ex:
            return f"Wikipedia ({title}): {ex}"
    return ""


def _wiki_search_fallback(query: str, timeout_sec: float) -> str:
    params = urllib.parse.urlencode(
        {
            "action": "opensearch",
            "search": query,
            "limit": "3",
            "namespace": "0",
            "format": "json",
        }
    )
    url = f"https://tr.wikipedia.org/w/api.php?{params}"
    data = _http_json(url, timeout_sec)
    if isinstance(data, list) and len(data) >= 3 and isinstance(data[2], list):
        descs = [str(x).strip() for x in data[2] if str(x).strip()]
        if descs:
            return "Wikipedia arama ozeti: " + " | ".join(descs[:3])
    return ""


def _wikidata_context(query: str, timeout_sec: float) -> str:
    params = urllib.parse.urlencode(
        {
            "action": "wbsearchentities",
            "search": query,
            "language": "tr",
            "format": "json",
            "limit": "3",
        }
    )
    url = f"https://www.wikidata.org/w/api.php?{params}"
    data = _http_json(url, timeout_sec)
    if not isinstance(data, dict):
        return ""
    out: list[str] = []
    for row in (data.get("search") or [])[:3]:
        if not isinstance(row, dict):
            continue
        label = str(row.get("label") or "").strip()
        desc = str(row.get("description") or "").strip()
        if label and desc:
            out.append(f"{label}: {desc}")
    if out:
        return "Wikidata: " + " | ".join(out)
    return ""


def _openalex_context(query: str, timeout_sec: float) -> str:
    q = urllib.parse.quote(query.strip())
    url = f"https://api.openalex.org/works?search={q}&per-page=3"
    data = _http_json(url, timeout_sec)
    if not isinstance(data, dict):
        return ""
    rows = data.get("results") or []
    out: list[str] = []
    for r in rows[:3]:
        if not isinstance(r, dict):
            continue
        title = str(r.get("display_name") or "").strip()
        year = r.get("publication_year")
        if title:
            out.append(f"{title} ({year})" if year else title)
    if out:
        return "Akademik arsiv (OpenAlex): " + " | ".join(out)
    return ""


def _britannica_context(query: str, timeout_sec: float) -> str:
    """Opsiyonel: BRITANNICA_API_URL + BRITANNICA_API_KEY varsa kullan."""
    base = (os.environ.get("BRITANNICA_API_URL") or "").strip()
    key = (os.environ.get("BRITANNICA_API_KEY") or "").strip()
    if not base or not key:
        return ""
    qs = urllib.parse.urlencode({"q": query, "key": key, "limit": "3"})
    url = f"{base}?{qs}"
    data = _http_json(url, timeout_sec)
    if isinstance(data, dict):
        rows = data.get("results") or data.get("items") or []
        out: list[str] = []
        for r in rows[:3]:
            if not isinstance(r, dict):
                continue
            title = str(r.get("title") or "").strip()
            snippet = str(r.get("snippet") or r.get("description") or "").strip()
            if title and snippet:
                out.append(f"{title}: {snippet}")
        if out:
            return "Britannica API: " + " | ".join(out)
    return ""


def is_general_culture_query(message: str) -> bool:
    low = (message or "").lower()
    if not low.strip():
        return False
    if any(k in low for k in ("hava", "kod", "python", "stacktrace", "hata", "debug")):
        return False
    keys = (
        "tarih",
        "sanat",
        "bilim",
        "felsefe",
        "coğraf",
        "cograf",
        "kültür",
        "kultur",
        "kimdir",
        "nedir",
        "neden",
        "nasıl",
        "nasil",
        "hangi",
    )
    return any(k in low for k in keys) or len(low.split()) >= 6


def should_trigger_bilge(
    message: str,
    *,
    mode_norm: str,
    local_hits: list[tuple[str, str, float]],
) -> bool:
    if not bilge_enabled():
        return False
    if mode_norm in {"ses", "hizli"}:
        return False
    if not is_general_culture_query(message):
        return False
    if not local_hits:
        return True
    best = float(local_hits[0][2])
    try:
        thresh = float(os.environ.get("BILGE_LOCAL_HIT_MIN", "0.40"))
    except ValueError:
        thresh = 0.40
    return best < thresh


def run_knowledge_hub_connector(query: str) -> str:
    """Paralel kaynak tarama; toplam sure hedefi <10 sn."""
    if not bilge_enabled():
        return ""
    q = (query or "").strip()
    if not q:
        return ""

    try:
        src_timeout = float(os.environ.get("BILGE_SOURCE_TIMEOUT_SEC", "2.8"))
    except ValueError:
        src_timeout = 2.8

    jobs = {
        "wiki_summary": lambda: _wiki_summary(q, src_timeout),
        "wiki_fallback": lambda: _wiki_search_fallback(q, src_timeout),
        "wikidata": lambda: _wikidata_context(q, src_timeout),
        "openalex": lambda: _openalex_context(q, src_timeout),
        "britannica": lambda: _britannica_context(q, src_timeout),
    }
    out: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=5) as ex:
        futs = {ex.submit(fn): name for name, fn in jobs.items()}
        for fut in as_completed(futs):
            name = futs[fut]
            try:
                out[name] = str(fut.result() or "").strip()
            except Exception:
                out[name] = ""

    lines: list[str] = []
    for k in ("wiki_summary", "wiki_fallback", "wikidata", "openalex", "britannica"):
        v = (out.get(k) or "").strip()
        if v:
            lines.append(v)
    if not lines:
        return ""
    return (
        "[KNOWLEDGE HUB CONNECTOR - BILGE MODU]\n"
        + "\n".join(f"- {ln}" for ln in lines)
        + "\n[/KNOWLEDGE HUB CONNECTOR]"
    )


def bilge_synthesis_directive() -> str:
    return (
        "\n\n[SYNTHESIS ENGINE - Umit & Gokcenur]\n"
        "Ham bilgiyi oldugu gibi dokme. Tarih, sanat ve bilim bilgisini birlestirip "
        "akici, hikmetli ve okunur bir anlatimla sun. Gerekirse 1-2 cumlelik baglamsal "
        "yorum ekle, fakat uydurma yapma.\n"
    )


def _today_in_history(timeout_sec: float = 3.0) -> list[str]:
    now = datetime.now()
    url = f"https://api.wikimedia.org/feed/v1/wikipedia/tr/onthisday/events/{now.month}/{now.day}"
    data = _http_json(url, timeout_sec)
    if not isinstance(data, dict):
        return []
    events = data.get("events") or []
    out: list[str] = []
    for ev in events[:5]:
        if not isinstance(ev, dict):
            continue
        year = ev.get("year")
        text = str(ev.get("text") or "").strip()
        if text:
            out.append(f"{year}: {text}" if year else text)
    return out


def warmup_daily_culture_sync() -> None:
    if not bilge_enabled():
        return
    _CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    if _CACHE_FILE.is_file():
        try:
            old = json.loads(_CACHE_FILE.read_text(encoding="utf-8"))
            if str(old.get("date")) == today and old.get("items"):
                return
        except Exception:
            pass
    items = _today_in_history()
    payload = {"date": today, "items": items}
    _CACHE_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def get_daily_culture_brief() -> str:
    if not bilge_enabled() or not _CACHE_FILE.is_file():
        return ""
    try:
        payload = json.loads(_CACHE_FILE.read_text(encoding="utf-8"))
        items = payload.get("items") or []
        if not items:
            return ""
        sample = items[:3]
        return "Tarihte bugun notlari: " + " | ".join(sample)
    except Exception:
        return ""
