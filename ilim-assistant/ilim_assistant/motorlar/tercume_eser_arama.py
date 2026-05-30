# Created by Ümit & Gökçenur
"""Tercüme atölyesi — B planı: DuckDuckGo genel + güvenilir site: sorguları, birleşik liste."""

from __future__ import annotations

import re
import time
from typing import Any
from urllib.parse import urlparse

TERCUME_ESER_ARAMA_VERSION = "tercume-eser-arama-b-2026-05-31"

# (etiket, ek sorgu parçası — site: DDG’de bazen boş döner; alan adı eklenir)
_TRUSTED_SITE_QUERIES: list[tuple[str, str]] = [
    ("Google Scholar", "scholar.google.com"),
    ("Internet Archive", "archive.org"),
    ("Genel", ""),
    ("Yazma Eserler", "yazmalar.gov.tr"),
    ("Şamile", "shamela.ws"),
    ("Wikisource", "wikisource.org"),
    ("Gutenberg", "gutenberg.org"),
]

_NOISE_WORDS = re.compile(
    r"\b(imam-?ı?|imam|eser|eserleri|eserlerini|kitap|kitabı|pdf|ara|arat|bul)\b",
    re.IGNORECASE,
)


def _normalize_url(url: str) -> str:
    u = (url or "").strip()
    if not u:
        return ""
    try:
        p = urlparse(u)
        host = (p.hostname or "").lower()
        path = (p.path or "").rstrip("/")
        return f"{p.scheme}://{host}{path}"
    except Exception:
        return u


def _ddgs_rows(query: str, max_results: int) -> list[dict[str, Any]]:
    from duckduckgo_search import DDGS

    raw: list[dict[str, Any]] = []
    try:
        with DDGS() as ddgs:
            raw = list(
                ddgs.text(
                    query,
                    max_results=max_results,
                    region="tr-tr",
                    safesearch="moderate",
                    backend="auto",
                )
            )
        if not raw:
            with DDGS() as ddgs:
                raw = list(ddgs.text(query, max_results=max_results, region="tr-tr"))
    except Exception:
        return []
    out: list[dict[str, Any]] = []
    for r in raw or []:
        if not isinstance(r, dict):
            continue
        href = str(r.get("href") or "").strip()
        if not href.startswith("http"):
            continue
        out.append(
            {
                "title": str(r.get("title") or "").strip() or href,
                "snippet": str(r.get("body") or "").strip(),
                "url": href,
            }
        )
    return out


def _refine_user_query(raw: str) -> str:
    t = (raw or "").strip()
    t = re.sub(r"^(?:ara|arat|bul)\s*[:：]\s*", "", t, flags=re.IGNORECASE).strip()
    t = re.sub(
        r"\b(eserlerini|kitaplarını|eserini|eserlerini|kitabını)\s*(?:ara|arat|bul)?\s*$",
        "",
        t,
        flags=re.IGNORECASE,
    ).strip()
    t = re.sub(r"\b(ara|arat|bul)\b\s*$", "", t, flags=re.IGNORECASE).strip()
    t = re.sub(r"\s+", " ", t).strip()
    return t[:200]


def _core_terms(base: str) -> str:
    """«12 imam» gibi gürültüyü azalt: ayırt edici kelimeler öne çıkar."""
    t = _NOISE_WORDS.sub(" ", base)
    t = re.sub(r"\s+", " ", t).strip()
    return t or base


def scholar_search_url(query: str) -> str:
    from urllib.parse import quote_plus

    q = _refine_user_query(query)
    if not q:
        return "https://scholar.google.com/?hl=tr"
    return f"https://scholar.google.com/scholar?q={quote_plus(q)}&hl=tr"


def _build_query_for_source(base: str, site_hint: str) -> str:
    core = _core_terms(base)
    if site_hint == "scholar.google.com":
        return f"{core} site:scholar.google.com"
    if site_hint == "archive.org":
        return f"{core} archive.org pdf"
    if site_hint:
        return f"{core} {site_hint} pdf"
    return f"{core} pdf kitap türkçe"


def _archive_org_rows(query: str, max_results: int = 6) -> list[dict[str, Any]]:
    """Internet Archive advancedsearch — DDG gürültüsünden bağımsız PDF/eser adayları."""
    from urllib.parse import quote_plus
    import json
    from urllib.request import Request, urlopen

    core = _core_terms(_refine_user_query(query))
    if not core or len(core) < 3:
        return []
    q = f"({core}) AND mediatype:texts"
    url = (
        "https://archive.org/advancedsearch.php?"
        f"q={quote_plus(q)}&fl[]=identifier,title,description&"
        f"rows={max_results}&output=json"
    )
    try:
        req = Request(url, headers={"User-Agent": "RuzgarTercume/1.0"})
        with urlopen(req, timeout=18) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
    except Exception:
        return []
    docs = (data.get("response") or {}).get("docs") or []
    out: list[dict[str, Any]] = []
    for d in docs:
        if not isinstance(d, dict):
            continue
        ident = str(d.get("identifier") or "").strip()
        if not ident:
            continue
        title = d.get("title")
        if isinstance(title, list):
            title = title[0] if title else ident
        title_s = str(title or ident).strip()
        desc = d.get("description")
        if isinstance(desc, list):
            desc = desc[0] if desc else ""
        details_url = f"https://archive.org/details/{ident}"
        out.append(
            {
                "title": title_s[:200],
                "snippet": str(desc or "")[:320],
                "url": details_url,
                "source": "Internet Archive (API)",
            }
        )
    return out


def search_eser_merged(
    user_query: str,
    *,
    max_per_query: int = 7,
    max_total: int = 22,
    delay_sec: float = 0.35,
) -> dict[str, Any]:
    """
  B planı: genel + site:archive.org vb. sorgular; URL tekrarı atılır.
  Groq kullanılmaz.
  """
    base = _refine_user_query(user_query)
    if not base:
        return {"ok": False, "error": "Arama metni boş.", "items": []}

    seen: set[str] = set()
    items: list[dict[str, Any]] = []
    queries_run: list[dict[str, str]] = [{"label": "Archive API", "query": base}]

    for row in _archive_org_rows(base, max_results=min(8, max_per_query + 2)):
        key = _normalize_url(row["url"])
        if not key or key in seen:
            continue
        seen.add(key)
        items.append(row)
        if len(items) >= max_total:
            break

    for label, site_hint in _TRUSTED_SITE_QUERIES:
        if len(items) >= max_total:
            break
        q = _build_query_for_source(base, site_hint)
        queries_run.append({"label": label, "query": q})
        rows = _ddgs_rows(q, max_per_query)
        for row in rows:
            key = _normalize_url(row["url"])
            if not key or key in seen:
                continue
            seen.add(key)
            items.append(
                {
                    "title": row["title"],
                    "snippet": row["snippet"][:320],
                    "url": row["url"],
                    "source": label,
                }
            )
            if len(items) >= max_total:
                break
        if delay_sec > 0:
            time.sleep(delay_sec)

    def _sort_key(row: dict[str, Any]) -> tuple[int, str]:
        src = str(row.get("source") or "")
        scholar_first = 0 if src == "Google Scholar" else 1
        return (scholar_first, str(row.get("title") or ""))

    items.sort(key=_sort_key)

    return {
        "ok": True,
        "version": TERCUME_ESER_ARAMA_VERSION,
        "query": base,
        "items": items,
        "total": len(items),
        "queries_run": queries_run,
        "scholar_url": scholar_search_url(base),
    }
