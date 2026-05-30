# Created by Ümit & Gökçenur
"""Tercüme atölyesi — B planı: DuckDuckGo genel + güvenilir site: sorguları, birleşik liste."""

from __future__ import annotations

import re
import time
from typing import Any
from urllib.parse import urlparse

TERCUME_ESER_ARAMA_VERSION = "tercume-eser-arama-v2-2026-05-31"

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


def _load_eser_aliases() -> dict[str, Any]:
    import json
    from pathlib import Path

    path = Path(__file__).with_name("tercume_eser_aliases.json")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"authors": {}, "works": {}, "noise_phrases": []}


def _norm_token(s: str) -> str:
    t = (s or "").lower()
    t = re.sub(r"[^\w\u00c0-\u024f]+", " ", t, flags=re.UNICODE)
    return re.sub(r"\s+", " ", t).strip()


def expand_search_query(user_query: str) -> tuple[str, list[str]]:
    """Faz 2 — alias tablosu ile arama metnini zenginleştir."""
    base = _refine_user_query(user_query)
    if not base:
        return "", []
    aliases = _load_eser_aliases()
    nb = _norm_token(base)
    extras: list[str] = []
    notes: list[str] = []

    for section, label in (("authors", "yazar"), ("works", "eser")):
        block = aliases.get(section) or {}
        if not isinstance(block, dict):
            continue
        for canonical, syns in block.items():
            if not isinstance(syns, list):
                continue
            keys = [_norm_token(canonical), *[_norm_token(str(s)) for s in syns]]
            keys = [k for k in keys if k]
            if not any(k in nb for k in keys):
                continue
            for k in keys:
                if k and k not in nb and k not in extras:
                    extras.append(k)
            notes.append(f"{label}:{canonical}")

    if not extras:
        return base, notes
    expanded = re.sub(r"\s+", " ", f"{base} {' '.join(extras[:6])}").strip()[:220]
    return expanded, notes


def _trusted_site_entry_rows(base: str) -> list[dict[str, Any]]:
    """Doğrudan site arama linkleri (DDG gürültüsünden bağımsız giriş noktaları)."""
    from urllib.parse import quote_plus

    core = _core_terms(_refine_user_query(base))
    if not core:
        return []
    q = quote_plus(core)
    return [
        {
            "title": f"Google Scholar: {core[:80]}",
            "snippet": "Akademik makale ve kitap atıfları",
            "url": scholar_search_url(base),
            "source": "Google Scholar (doğrudan)",
        },
        {
            "title": f"Şamile arama: {core[:80]}",
            "snippet": "shamela.ws — Arapça/Osmanlıca eser arşivi",
            "url": f"https://shamela.ws/search?q={q}",
            "source": "Şamile (doğrudan)",
        },
        {
            "title": f"Yazma Eserler: {core[:80]}",
            "snippet": "yazmalar.gov.tr — dijital yazma eser kütüphanesi",
            "url": f"https://yazmalar.gov.tr/arama?Kelime={q}",
            "source": "Yazma Eserler (doğrudan)",
        },
    ]


def _archive_pdf_download_url(identifier: str) -> str:
    """Archive.org metadata → ilk uygun PDF indirme linki."""
    import json
    from urllib.request import Request, urlopen

    ident = (identifier or "").strip()
    if not ident:
        return ""
    url = f"https://archive.org/metadata/{ident}"
    try:
        req = Request(url, headers={"User-Agent": "RuzgarTercume/2.0"})
        with urlopen(req, timeout=14) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
    except Exception:
        return ""
    files = data.get("files") or []
    preferred: list[str] = []
    for f in files:
        if not isinstance(f, dict):
            continue
        name = str(f.get("name") or "")
        fmt = str(f.get("format") or "").lower()
        if not name.lower().endswith(".pdf"):
            continue
        if "abbyy" in name.lower() or "jp2" in name.lower():
            continue
        preferred.append(name)
    if not preferred:
        return ""
    pick = sorted(preferred, key=lambda n: (len(n), n))[0]
    from urllib.parse import quote

    return f"https://archive.org/download/{quote(ident, safe='')}/{quote(pick, safe='')}"


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
        pdf_url = _archive_pdf_download_url(ident)
        out.append(
            {
                "title": title_s[:200],
                "snippet": str(desc or "")[:320],
                "url": details_url,
                "download_url": pdf_url,
                "archive_identifier": ident,
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

    expanded, expand_notes = expand_search_query(base)
    search_q = expanded or base

    seen: set[str] = set()
    items: list[dict[str, Any]] = []
    queries_run: list[dict[str, str]] = [
        {"label": "Archive API", "query": search_q},
    ]

    for row in _trusted_site_entry_rows(base):
        key = _normalize_url(row["url"])
        if not key or key in seen:
            continue
        seen.add(key)
        items.append(row)

    for row in _archive_org_rows(search_q, max_results=min(8, max_per_query + 2)):
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

    if expanded and expanded != base:
        queries_run.insert(0, {"label": "Alias genişletme", "query": expanded})

    def _sort_key(row: dict[str, Any]) -> tuple[int, str]:
        src = str(row.get("source") or "")
        direct = 0 if "(doğrudan)" in src or "(API)" in src else 1
        scholar_first = 0 if "Scholar" in src else direct
        return (scholar_first, str(row.get("title") or ""))

    items.sort(key=_sort_key)

    return {
        "ok": True,
        "version": TERCUME_ESER_ARAMA_VERSION,
        "query": base,
        "expanded_query": expanded if expanded != base else "",
        "expand_notes": expand_notes,
        "items": items,
        "total": len(items),
        "queries_run": queries_run,
        "scholar_url": scholar_search_url(base),
    }
