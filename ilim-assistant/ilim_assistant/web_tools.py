"""Web araması (DuckDuckGo) ve isteğe bağlı sayfa metni çekme."""

from __future__ import annotations

import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple

_URL_IN_TEXT = re.compile(r"https?://[^\s\]>\"\'\)]+", re.IGNORECASE)

# Kısa süreli arama önbelleği — aynı oturumda tekrar sorguları hızlandırır
_SEARCH_CACHE: dict[str, tuple[float, list]] = {}
_CACHE_TTL_SEC = float(os.environ.get("WEB_SEARCH_CACHE_TTL", "300"))


def web_fast_mode_enabled() -> bool:
    return os.environ.get("RUZGAR_WEB_FAST", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


_MAX_FETCH_CHARS = int(os.environ.get("WEB_FETCH_MAX_CHARS", "12000"))
_FETCH_TIMEOUT = float(os.environ.get("WEB_FETCH_TIMEOUT", "6"))
_USER_AGENT = os.environ.get(
    "WEB_USER_AGENT",
    "Mozilla/5.0 (compatible; IlimAssistant/0.1; +local-education)",
)


def _ddgs_search(query: str, max_results: int) -> List[dict]:
    from duckduckgo_search import DDGS

    q = (query or "").strip()
    if not q:
        return []
    cache_key = f"{q}|{max_results}"
    now = time.time()
    cached = _SEARCH_CACHE.get(cache_key)
    if cached and (now - cached[0]) < _CACHE_TTL_SEC:
        return list(cached[1])

    rows: list[dict] = []
    with DDGS() as ddgs:
        for r in ddgs.text(q, max_results=max_results):
            rows.append(r)
    _SEARCH_CACHE[cache_key] = (now, rows)
    return rows


def _fetch_urls_parallel(urls: List[str], *, max_workers: int = 4) -> list[tuple[str, str, str]]:
    """Paralel sayfa çekimi — (url, metin, durum)."""
    if not urls:
        return []
    workers = max(1, min(max_workers, len(urls), 6))
    out: list[tuple[str, str, str]] = []

    def _one(u: str) -> tuple[str, str, str]:
        txt, st = fetch_url_text(u)
        return u, txt, st

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(_one, u): u for u in urls}
        for fut in as_completed(futs):
            try:
                out.append(fut.result())
            except Exception as e:
                out.append((futs[fut], "", str(e)))
    return out


def extract_http_urls(text: str, max_n: int = 12) -> List[str]:
    """Mesaj içindeki http(s) adresleri (yinelenmez sıra)."""
    seen: set[str] = set()
    out: List[str] = []
    for m in _URL_IN_TEXT.finditer(text or ""):
        u = m.group(0).rstrip(".,);:]\"'»")
        if u not in seen:
            seen.add(u)
            out.append(u)
            if len(out) >= max_n:
                break
    return out


def strip_urls_for_search(text: str) -> str:
    """Arama kutusu için metinden URL kırpılır (sorgu daha temiz olur)."""
    t = _URL_IN_TEXT.sub(" ", text or "")
    return re.sub(r"\s+", " ", t).strip()


_LEADING_WAKE = re.compile(r"^\s*(rüzgar|ruzgar)[\s,;:–\-]*", re.IGNORECASE)
_FILLER_PHRASES = re.compile(
    r"\b(lütfen|rica\s*ederim|rica\s*etsem|bana\s+söyle|bana\s+anlat|"
    r"söyler\s*misin|söyler\s*mısın|anlatır\s*mısın|yardım\s*et|"
    r"merhaba|selam|iyi\s*günler|iyi\s*akşamlar|saygılar)\b\.?",
    re.IGNORECASE,
)


def refined_search_query(message: str) -> str:
    """
    DuckDuckGo için daha kısa ve odaklı sorgu (hız + daha ilgili snippet).
    Boş kalırsa strip_urls_for_search çıktısına düşer.
    """
    raw = (message or "").strip()
    t = strip_urls_for_search(raw)
    t = _LEADING_WAKE.sub("", t).strip()
    t = _FILLER_PHRASES.sub(" ", t)
    t = re.sub(r"\s+", " ", t).strip()
    if not t:
        t = strip_urls_for_search(raw).strip()
    try:
        cap = max(80, int(os.environ.get("WEB_QUERY_MAX_CHARS", "240")))
    except ValueError:
        cap = 240
    if len(t) > cap:
        t = t[:cap].rsplit(" ", 1)[0].strip()
    return t


def build_message_link_context(message: str) -> str:
    """
    Kullanıcı mesajına yapıştırdığı doğrudan bağlantıları okur ve metin özetleri üretir.
    ENABLE_WEB_LINK_READ=0 ile kapatılır.
    """
    if os.environ.get("ENABLE_WEB_LINK_READ", "1").strip() in ("0", "false", "no"):
        return ""
    max_urls = max(1, int(os.environ.get("WEB_MESSAGE_URL_MAX", "5")))
    max_each = int(os.environ.get("WEB_LINK_MAX_CHARS_EACH", str(_MAX_FETCH_CHARS)))
    urls = extract_http_urls(message, max_n=max_urls)
    if not urls:
        return ""

    lines: List[str] = [
        "=== Mesajdaki bağlantılar (sayfa metni — doğrulanmamış) ===",
        "Bu blok, kullanıcının mesajına eklediği URL’lerden çekilmiştir; paywall veya bot engeli olabilir.",
    ]
    for u in urls:
        txt, st = fetch_url_text(u, max_chars=max_each)
        if txt:
            lines.append(f"\n--- Sayfa ({st}) ---\n{u}\n\n{txt}")
        else:
            lines.append(f"\n--- Sayfa alınamadı ---\n{u}\n{st}")
    return "\n".join(lines)


def fetch_url_text(url: str, max_chars: int = _MAX_FETCH_CHARS) -> Tuple[str, str]:
    """
    Basit HTML → düz metin. Bazı siteler bot trafiğini engelleyebilir.
    Dönüş: (metin veya hata özeti, kısa durum)
    """
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError as e:
        return "", f"eksik paket: {e}"

    try:
        r = requests.get(
            url,
            timeout=_FETCH_TIMEOUT,
            headers={"User-Agent": _USER_AGENT, "Accept-Language": "tr,en;q=0.9"},
        )
        r.raise_for_status()
        ct = (r.headers.get("Content-Type") or "").lower()
        # charset yoksa requests bazen ISO-8859-1 varsayar; modern siteler UTF-8’dir
        if "charset=" not in ct:
            r.encoding = "utf-8"
        if "text/html" not in ct and "application/xhtml" not in ct:
            return "", f"HTML değil: {ct[:80]}"

        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "noscript", "svg"]):
            tag.decompose()
        text = soup.get_text(separator="\n")
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        body = re.sub(r"\n{3,}", "\n\n", "\n".join(lines))
        if len(body) > max_chars:
            body = body[:max_chars] + "\n\n[… kesildi …]"
        return body, "ok"
    except Exception as e:
        return "", str(e)


def build_web_context(
    query: str,
    max_results: int = 10,
    fetch_first_n_urls: int = 0,
) -> str:
    """
    Arama sonuçları + ilk N benzersiz URL'den metin çekme.
    İçerik doğrulanmamıştır; kaynaklara şüphe ile yaklaş.
    """
    q = (query or "").strip()
    if not q:
        return ""

    try:
        results = _ddgs_search(q, max_results=max_results)
    except Exception as e:
        return f"[Web araması başarısız: {e}]"

    if not results:
        return "[Web: sonuç bulunamadı.]"

    lines: List[str] = []
    try:
        from ilim_assistant.ana_motor_guncellik import web_scan_stamp_line

        stamp = web_scan_stamp_line()
        if stamp:
            lines.append(stamp.rstrip())
    except Exception:
        pass

    lines.append(
        "=== Web araması (DuckDuckGo — doğrulanmamış; mümkünse resmi dokümantasyon / GitHub / açık kaynak URL’lerine öncelik ver) ==="
    )
    seen_urls: set[str] = set()
    urls_to_fetch: List[str] = []

    for i, r in enumerate(results, 1):
        title = (r.get("title") or "").strip()
        body = (r.get("body") or "").strip()
        href = (r.get("href") or "").strip()
        lines.append(f"{i}. {title}\n   {body}\n   URL: {href}")
        if (
            href.startswith("http")
            and fetch_first_n_urls > 0
            and len(urls_to_fetch) < fetch_first_n_urls
            and href not in seen_urls
        ):
            seen_urls.add(href)
            urls_to_fetch.append(href)

    for j, pack in enumerate(
        _fetch_urls_parallel(urls_to_fetch, max_workers=4) if web_fast_mode_enabled() else [],
        1,
    ):
        u, txt, st = pack
        if txt:
            lines.append(f"\n--- Sayfa metni #{j} ({st}) ---\n{u}\n\n{txt}")
        else:
            lines.append(f"\n--- Sayfa alınamadı ---\n{u}\n{st}")

    if not web_fast_mode_enabled():
        for j, u in enumerate(urls_to_fetch, 1):
            txt, st = fetch_url_text(u)
            if txt:
                lines.append(f"\n--- Sayfa metni #{j} ({st}) ---\n{u}\n\n{txt}")
            else:
                lines.append(f"\n--- Sayfa alınamadı ---\n{u}\n{st}")

    return "\n".join(lines)


def build_web_context_fast(
    query: str,
    max_results: int = 8,
    fetch_first_n_urls: int = 2,
) -> str:
    """Hızlı web — daha az sonuç, paralel fetch, önbellek."""
    if not web_fast_mode_enabled():
        return build_web_context(query, max_results=max_results, fetch_first_n_urls=fetch_first_n_urls)
    try:
        mr = int(os.environ.get("WEB_FAST_MAX_RESULTS", str(max_results)))
    except ValueError:
        mr = max_results
    try:
        nf = int(os.environ.get("WEB_FAST_FETCH_URLS", str(fetch_first_n_urls)))
    except ValueError:
        nf = fetch_first_n_urls
    return build_web_context(query, max_results=max(4, min(mr, 12)), fetch_first_n_urls=max(0, min(nf, 4)))


_TRUSTED_DOMAIN_HINTS: tuple[tuple[str, float], ...] = (
    (".gov.tr", 3.5),
    (".edu.tr", 3.0),
    (".edu/", 2.5),
    ("wikipedia.org", 2.8),
    ("britannica.com", 2.4),
    ("tedk.gov.tr", 3.5),
    ("tdk.gov.tr", 3.5),
    ("archive.org", 2.0),
    ("scholar.google", 2.5),
    ("reuters.com", 2.2),
    ("bbc.com", 2.0),
    ("aa.com.tr", 2.2),
    ("trtworld.com", 1.8),
)


def _url_trust_score(url: str) -> float:
    u = (url or "").lower()
    score = 1.0
    for hint, bonus in _TRUSTED_DOMAIN_HINTS:
        if hint in u:
            score += bonus
    if u.startswith("https://"):
        score += 0.15
    return score


def _merge_ddg_rows(rows: list[dict]) -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []
    for row in rows:
        href = (row.get("href") or "").strip()
        key = href.lower() or (row.get("title") or "")[:80].lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def expand_web_queries(query: str, *, primary: str = "bilgi") -> list[str]:
    """PRO — birincil + odaklı ikincil sorgular."""
    base = (query or "").strip()
    if not base:
        return []
    out = [base]
    if os.environ.get("RUZGAR_WEB_PRO_MULTI_QUERY", "1").strip().lower() in (
        "0",
        "false",
        "no",
    ):
        return out
    low = base.lower()
    if primary in ("bilgi", "bilim") and "wikipedia" not in low:
        out.append(f"{base} site:wikipedia.org")
    if primary == "bilim" and "tarih" not in low and any(
        x in low for x in ("osman", "fatih", "padişah", "padisah", "devri", "dönem")
    ):
        out.append(f"{base} tarih")
    if any(x in low for x in ("güncel", "guncel", "haber", "son dakika")):
        out.append(f"{base} haber")
    # Yinelenenleri koru sırayla
    seen: set[str] = set()
    uniq: list[str] = []
    for q in out:
        k = q.lower()
        if k not in seen:
            seen.add(k)
            uniq.append(q)
    return uniq[:3]


def _ddgs_news_search(query: str, max_results: int) -> list[dict]:
    q = (query or "").strip()
    if not q:
        return []
    try:
        from duckduckgo_search import DDGS

        rows: list[dict] = []
        with DDGS() as ddgs:
            for r in ddgs.news(q, max_results=max_results):
                rows.append(
                    {
                        "title": r.get("title") or "",
                        "body": r.get("body") or r.get("excerpt") or "",
                        "href": r.get("url") or r.get("link") or "",
                        "source": "news",
                    }
                )
        return rows
    except Exception:
        return []


def _wants_news_search(query: str) -> bool:
    low = (query or "").lower()
    return any(
        x in low
        for x in (
            "güncel",
            "guncel",
            "haber",
            "son dakika",
            "bugün",
            "bugun",
            "2024",
            "2025",
            "2026",
        )
    )


def build_web_context_pro(
    query: str,
    *,
    primary: str = "bilgi",
    max_results: int = 12,
    fetch_first_n_urls: int = 6,
) -> str:
    """
    Profesyonel web araştırması — çok sorgu, kaynak sıralama, derin sayfa okuma.
    """
    q = (query or "").strip()
    if not q:
        return ""

    try:
        per_q = max(4, min(int(os.environ.get("RUZGAR_WEB_PRO_PER_QUERY", "8")), 12))
    except ValueError:
        per_q = 8
    try:
        fetch_n = max(0, min(int(fetch_first_n_urls or 0), int(os.environ.get("RUZGAR_WEB_PRO_FETCH_URLS", "6"))))
    except ValueError:
        fetch_n = max(0, min(fetch_first_n_urls, 6))

    all_rows: list[dict] = []
    for sub_q in expand_web_queries(q, primary=primary):
        try:
            all_rows.extend(_ddgs_search(sub_q, max_results=per_q))
        except Exception:
            continue

    if _wants_news_search(q):
        all_rows.extend(_ddgs_news_search(q, max_results=min(6, per_q)))

    results = _merge_ddg_rows(all_rows)
    if not results:
        return "[Web PRO: sonuç bulunamadı.]"

    results.sort(
        key=lambda r: _url_trust_score(str(r.get("href") or "")),
        reverse=True,
    )
    results = results[: max(6, min(max_results, 16))]

    lines: list[str] = []
    try:
        from ilim_assistant.ana_motor_guncellik import web_scan_stamp_line

        stamp = web_scan_stamp_line()
        if stamp:
            lines.append(stamp.rstrip())
    except Exception:
        pass

    lines.append(
        "=== WEB ARAŞTIRMA PRO (DuckDuckGo + haber — çok kaynak; doğrulanmamış) ==="
    )
    lines.append(
        f"Sorgu: {q} · {len(results)} kaynak · sayfa derinliği: {fetch_n}"
    )

    seen_urls: set[str] = set()
    urls_to_fetch: list[str] = []

    for i, r in enumerate(results, 1):
        title = (r.get("title") or "").strip()
        body = (r.get("body") or "").strip()
        href = (r.get("href") or "").strip()
        src_tag = f" [{r.get('source')}]" if r.get("source") == "news" else ""
        trust = _url_trust_score(href)
        lines.append(
            f"{i}. [{trust:.1f}] {title}{src_tag}\n   {body}\n   URL: {href}"
        )
        if (
            href.startswith("http")
            and fetch_n > 0
            and len(urls_to_fetch) < fetch_n
            and href not in seen_urls
        ):
            seen_urls.add(href)
            urls_to_fetch.append(href)

    urls_to_fetch.sort(key=_url_trust_score, reverse=True)

    for j, pack in enumerate(_fetch_urls_parallel(urls_to_fetch, max_workers=5), 1):
        u, txt, st = pack
        if txt:
            lines.append(f"\n--- Sayfa metni PRO #{j} ({st}) ---\n{u}\n\n{txt}")
        else:
            lines.append(f"\n--- Sayfa alınamadı ---\n{u}\n{st}")

    lines.append(
        "\n[Talimat] Yanıtta mümkünse kaynak URL veya site adını kısaca belirt.\n"
    )
    return "\n".join(lines)
