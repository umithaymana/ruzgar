"""Web araması (DuckDuckGo) ve isteğe bağlı sayfa metni çekme."""

from __future__ import annotations

import os
import re
from typing import List, Tuple

_URL_IN_TEXT = re.compile(r"https?://[^\s\]>\"\'\)]+", re.IGNORECASE)


_MAX_FETCH_CHARS = int(os.environ.get("WEB_FETCH_MAX_CHARS", "18000"))
_FETCH_TIMEOUT = float(os.environ.get("WEB_FETCH_TIMEOUT", "12"))
_USER_AGENT = os.environ.get(
    "WEB_USER_AGENT",
    "Mozilla/5.0 (compatible; IlimAssistant/0.1; +local-education)",
)


def _ddgs_search(query: str, max_results: int) -> List[dict]:
    from duckduckgo_search import DDGS

    rows = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            rows.append(r)
    return rows


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

    lines: List[str] = []
    try:
        results = _ddgs_search(q, max_results=max_results)
    except Exception as e:
        return f"[Web araması başarısız: {e}]"

    if not results:
        return "[Web: sonuç bulunamadı.]"

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

    for j, u in enumerate(urls_to_fetch, 1):
        txt, st = fetch_url_text(u)
        if txt:
            lines.append(f"\n--- Sayfa metni #{j} ({st}) ---\n{u}\n\n{txt}")
        else:
            lines.append(f"\n--- Sayfa alınamadı ---\n{u}\n{st}")

    return "\n".join(lines)
