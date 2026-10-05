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


def _ddg_client():
    import warnings

    try:
        from ddgs import DDGS

        return DDGS
    except ImportError:
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message=r".*duckduckgo_search.*renamed to.*ddgs.*",
                category=RuntimeWarning,
            )
            from duckduckgo_search import DDGS  # type: ignore[no-redef]

            return DDGS


def _ddgs_search(query: str, max_results: int) -> List[dict]:
    q = (query or "").strip()
    if not q:
        return []
    cache_key = f"{q}|{max_results}"
    now = time.time()
    cached = _SEARCH_CACHE.get(cache_key)
    if cached and (now - cached[0]) < _CACHE_TTL_SEC:
        return list(cached[1])

    rows: list[dict] = []
    try:
        DDGS = _ddg_client()
        with DDGS() as ddgs:
            try:
                raw = list(
                    ddgs.text(
                        q,
                        max_results=max_results,
                        region="tr-tr",
                        safesearch="moderate",
                        backend="auto",
                    )
                )
            except TypeError:
                raw = list(ddgs.text(q, max_results=max_results))
            except Exception:
                raw = []
            if not raw:
                try:
                    raw = list(ddgs.text(q, max_results=max_results, region="wt-wt"))
                except Exception:
                    raw = []
            for r in raw or []:
                if isinstance(r, dict):
                    rows.append(r)
    except Exception:
        rows = []

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


def _query_focus_terms(query: str) -> set[str]:
    stop = {
        "nedir",
        "hangi",
        "kac",
        "kaç",
        "ne",
        "nasil",
        "nasıl",
        "icin",
        "için",
        "bir",
        "ile",
        "ve",
        "the",
        "what",
        "which",
        "where",
        "wikipedia",
        "mesala",
        "mesela",
    }
    out: set[str] = set()
    for w in re.findall(r"[a-zA-ZçğıöşüÇĞİÖŞÜ0-9]{3,}", (query or "").lower()):
        if w not in stop:
            out.add(w)
    return out


def _web_result_relevance(query: str, title: str, body: str, href: str = "") -> float:
    terms = _query_focus_terms(query)
    if not terms:
        return 1.0
    blob = f"{title} {body} {href}".lower()
    hits = sum(1 for t in terms if t in blob)
    score = hits / max(1, len(terms))
    host = ""
    try:
        from urllib.parse import urlparse

        host = (urlparse(href).netloc or "").lower()
    except Exception:
        host = ""
    if any(x in host for x in ("wikipedia.org", "britannica.com", "nasa.gov", "esa.int", "tubitak")):
        score += 0.45
    if any(
        x in host
        for x in (
            "aa.com.tr",
            "trthaber.com",
            "bbc.com",
            "reuters.com",
            "ntv.com.tr",
            "cnnturk.com",
            "haberturk.com",
            "sozcu.com.tr",
            "hurriyet.com.tr",
            "milliyet.com.tr",
            "fotomac.com.tr",
            "mackolik.com",
            "tff.org",
        )
    ):
        score += 0.35
    if any(x in host for x in ("eksisozluk", "instagram", "pinterest", "astrolog", "horoscope")):
        score -= 0.55
    if any(x in blob for x in ("burç", "burc", "astrology", "laptop", "ekran parlak")):
        score -= 0.4
    return score


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

    # Alakasız satırları ele: soru terimleriyle örtüşmeyen snippet/URL'yi modele verme.
    ranked: List[tuple[float, dict]] = []
    for r in results:
        title = (r.get("title") or "").strip()
        body = (r.get("body") or "").strip()
        href = (r.get("href") or "").strip()
        score = _web_result_relevance(q, title, body, href)
        if score < 0.18 and "wikipedia.org" not in href.lower():
            continue
        ranked.append((score, r))
    ranked.sort(key=lambda x: x[0], reverse=True)
    if not ranked:
        # Hepsi elendiyse en azından en yüksek skorlu 2 satırı bırak (tamamen boş bağlam olmasın)
        soft: List[tuple[float, dict]] = []
        for r in results:
            title = (r.get("title") or "").strip()
            body = (r.get("body") or "").strip()
            href = (r.get("href") or "").strip()
            soft.append((_web_result_relevance(q, title, body, href), r))
        soft.sort(key=lambda x: x[0], reverse=True)
        ranked = soft[:2]

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

    # Önce Wikipedia / güvenilir domain
    for _score, r in ranked:
        href = (r.get("href") or "").strip()
        if "wikipedia.org" in href.lower() and href.startswith("http") and href not in seen_urls:
            seen_urls.add(href)
            urls_to_fetch.append(href)

    for i, (_score, r) in enumerate(ranked, 1):
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

    urls_to_fetch = urls_to_fetch[: max(0, fetch_first_n_urls)]

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
    ("aa.com.tr", 2.4),
    ("trthaber.com", 2.3),
    ("trtworld.com", 1.8),
    ("ntv.com.tr", 2.0),
    ("cnnturk.com", 2.0),
    ("haberturk.com", 1.9),
    ("hurriyet.com.tr", 1.8),
    ("milliyet.com.tr", 1.8),
    ("sozcu.com.tr", 1.8),
    ("fotomac.com.tr", 2.0),
    ("mackolik.com", 2.0),
    ("tff.org", 2.2),
)


def _url_trust_score(url: str, *, query: str = "") -> float:
    u = (url or "").lower()
    score = 1.0
    for hint, bonus in _TRUSTED_DOMAIN_HINTS:
        if hint in u:
            score += bonus
    if u.startswith("https://"):
        score += 0.15
    qlow = (query or "").lower()
    sports_q = any(
        x in qlow
        for x in (
            "maç",
            "mac",
            "skor",
            "lig",
            "fikstür",
            "fikstur",
            "kupa",
            "erzurumspor",
            "fifa",
            "spor",
            "şampiyon",
            "sampiyon",
        )
    )
    if sports_q:
        # Yıl/takvim Vikipedi sayfaları spor sonucunu ezer — cezalandır
        if re.search(r"wikipedia\.org/wiki/20\d{2}$", u) or "/wiki/2026" in u or "/wiki/2025" in u:
            if "world_cup" not in u and "dünya" not in u and "kupa" not in u and "cup" not in u:
                score -= 4.0
        if any(x in u for x in ("takvim", "calendar", "haftanumarasi")):
            score -= 3.0
        if any(x in u for x in ("mackolik", "tff.org", "fotomac", "skorx", "erzurumspor.com", "fifa.com")):
            score += 2.5
        # Şehir/il sayfası (Erzurum) maç sorusunda yanıltıcı
        if re.search(r"wikipedia\.org/wiki/erzurum", u) and "spor" not in u:
            score -= 3.5
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
    if any(
        x in low
        for x in (
            "güncel",
            "guncel",
            "haber",
            "son dakika",
            "bugün",
            "bugun",
            "olay",
            "spor",
            "maç",
            "mac",
            "skor",
            "kupa",
            "fikstür",
            "fikstur",
            "erzurumspor",
            "fifa",
        )
    ):
        out.append(f"{base} haber")
        if any(
            x in low
            for x in (
                "spor",
                "maç",
                "mac",
                "skor",
                "lig",
                "transfer",
                "fikstür",
                "fikstur",
                "erzurumspor",
                "kupa",
            )
        ):
            out.append(f"{base} maç sonucu fikstür")
            if "mackolik" not in low:
                out.append(f"{base} site:mackolik.com")
            if "tff" not in low and "lig" in low:
                out.append(f"{base} site:tff.org")
    # Yinelenenleri koru sırayla
    seen: set[str] = set()
    uniq: list[str] = []
    for q in out:
        k = q.lower()
        if k not in seen:
            seen.add(k)
            uniq.append(q)
    return uniq[:4]


def _ddgs_news_search(query: str, max_results: int) -> list[dict]:
    q = (query or "").strip()
    if not q:
        return []
    try:
        DDGS = _ddg_client()
        rows: list[dict] = []
        with DDGS() as ddgs:
            try:
                raw = list(
                    ddgs.news(
                        q,
                        max_results=max_results,
                        region="tr-tr",
                        safesearch="moderate",
                    )
                )
            except TypeError:
                raw = list(ddgs.news(q, max_results=max_results))
            except Exception:
                raw = []
            for r in raw or []:
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
    try:
        from ilim_assistant.ruzgar_web_arastirma_pro import looks_like_live_web_needed

        if looks_like_live_web_needed(query):
            return True
    except Exception:
        pass
    return any(
        x in low
        for x in (
            "güncel",
            "guncel",
            "haber",
            "son dakika",
            "bugün",
            "bugun",
            "spor",
            "maç",
            "mac",
            "skor",
            "lig",
            "transfer",
            "2024",
            "2025",
            "2026",
        )
    )


def _sports_seed_rows(query: str) -> list[dict]:
    """DDG çökerse / saçmalarsa güvenilir spor sayfalarını tohumla."""
    low = (query or "").lower()
    rows: list[dict] = []
    try:
        from ilim_assistant.ana_motor_web_first import _fetch_wikipedia_rows

        wiki_q = query
        if any(x in low for x in ("dünya kupa", "dunya kupa", "world cup", "fifa")):
            wiki_q = "2026 FIFA Dünya Kupası"
            rows.append(
                {
                    "title": "2026 FIFA World Cup — Wikipedia",
                    "body": "2026 FIFA World Cup tournament page",
                    "href": "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup",
                    "source": "seed",
                }
            )
            rows.append(
                {
                    "title": "2026 FIFA Dünya Kupası — Vikipedi",
                    "body": "2026 FIFA Dünya Kupası turnuva sayfası",
                    "href": "https://tr.wikipedia.org/wiki/2026_FIFA_D%C3%BCnya_Kupas%C4%B1",
                    "source": "seed",
                }
            )
        elif "erzurum" in low:
            wiki_q = "Erzurumspor FK"
            rows.append(
                {
                    "title": "Erzurumspor FK Fikstür — Mackolik",
                    "body": "Erzurumspor FK güncel fikstür ve maçlar",
                    "href": "https://www.mackolik.com/takim/erzurumspor-fk/maçlar/ea2gyhkv6vwmxbxevdb4u3796",
                    "source": "seed",
                }
            )
            rows.append(
                {
                    "title": "Erzurumspor fikstür",
                    "body": "Erzurumspor resmi fikstür",
                    "href": "https://erzurumspor.com/fikstur",
                    "source": "seed",
                }
            )
        rows.extend(_fetch_wikipedia_rows(wiki_q, max_results=3) or [])
        # EN wiki for world cup
        if any(x in low for x in ("dünya kupa", "dunya kupa", "world cup", "fifa")):
            try:
                import json
                import urllib.parse
                import urllib.request

                api = (
                    "https://en.wikipedia.org/w/api.php?"
                    + urllib.parse.urlencode(
                        {
                            "action": "query",
                            "list": "search",
                            "srsearch": "2026 FIFA World Cup",
                            "format": "json",
                            "srlimit": 3,
                            "utf8": 1,
                        }
                    )
                )
                req = urllib.request.Request(
                    api, headers={"User-Agent": "RuzgarAssistant/1.0 (local)"}
                )
                with urllib.request.urlopen(req, timeout=8) as resp:
                    data = json.loads(resp.read().decode("utf-8", errors="replace"))
                for hit in list((data.get("query") or {}).get("search") or [])[:3]:
                    title = str(hit.get("title") or "").strip()
                    if not title:
                        continue
                    slug = urllib.parse.quote(title.replace(" ", "_"))
                    rows.append(
                        {
                            "title": title,
                            "body": re.sub(r"<[^>]+>", " ", str(hit.get("snippet") or "")),
                            "href": f"https://en.wikipedia.org/wiki/{slug}",
                            "source": "wikipedia_en",
                        }
                    )
            except Exception:
                pass
    except Exception:
        pass
    return rows


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
    sports_like = any(
        x in q.lower()
        for x in (
            "maç",
            "mac",
            "skor",
            "lig",
            "fikstür",
            "fikstur",
            "kupa",
            "erzurumspor",
            "fifa",
            "spor",
            "galatasaray",
            "fenerbahçe",
        )
    )
    if sports_like:
        all_rows.extend(_sports_seed_rows(q))

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

    def _rank(r: dict) -> float:
        href = str(r.get("href") or "")
        title = str(r.get("title") or "")
        body = str(r.get("body") or "")
        trust = _url_trust_score(href, query=q)
        rel = _web_result_relevance(q, title, body, href)
        src = str(r.get("source") or "")
        bonus = 2.0 if src in ("seed", "wikipedia_tr", "wikipedia_en") else 0.0
        return trust + (rel * 2.0) + bonus

    results.sort(key=_rank, reverse=True)
    # Alakasız (yıl takvimi / şehir) düşük skorları at
    filtered = [r for r in results if _rank(r) >= 0.8]
    results = (filtered or results)[: max(6, min(max_results, 16))]

    lines: list[str] = []
    try:
        from ilim_assistant.ana_motor_guncellik import web_scan_stamp_line

        stamp = web_scan_stamp_line()
        if stamp:
            lines.append(stamp.rstrip())
    except Exception:
        pass
    try:
        from ilim_assistant.fx_live import fx_live_context_line

        fx_line = fx_live_context_line(q)
        if fx_line:
            lines.append(fx_line.rstrip())
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
        src_tag = f" [{r.get('source')}]" if r.get("source") else ""
        trust = _url_trust_score(href, query=q)
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

    # Spor: seed URL'leri fetch listesinin başına al
    if sports_like:
        seed_urls = [
            str(r.get("href") or "")
            for r in results
            if r.get("source") in ("seed", "wikipedia_tr", "wikipedia_en")
            and str(r.get("href") or "").startswith("http")
        ]
        for su in reversed(seed_urls):
            if su in urls_to_fetch:
                urls_to_fetch.remove(su)
            urls_to_fetch.insert(0, su)
        urls_to_fetch = urls_to_fetch[: max(fetch_n, min(6, fetch_n + 2))]

    urls_to_fetch.sort(key=lambda u: _url_trust_score(u, query=q), reverse=True)

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
