# Created by Ümit & Gökçenur
"""
Ana Motor Faz AP — Web öncelikli hızlı yanıt (+ AP2 snippet/doğrulama ince ayarı).

Hedef: Bilgi/güncel sorularda Groq/Gemini/Ollama kotasına girmeden
DuckDuckGo snippet'lerinden doğrudan Türkçe cevap (LLM yok).
"""

from __future__ import annotations

import os
import re
from typing import Any, Iterator
from urllib.parse import urlparse

WEB_FIRST_VERSION = "web-first-faz-ap2b-v1-2026-06-14"

_STOP = frozenset(
    {
        "için",
        "icin",
        "olan",
        "olarak",
        "gibi",
        "daha",
        "çok",
        "cok",
        "kadar",
        "mi",
        "mı",
        "mu",
        "mü",
        "bir",
        "bu",
        "şu",
        "su",
        "o",
        "ve",
        "ile",
        "de",
        "da",
        "ki",
        "ne",
        "nasıl",
        "nasil",
        "neden",
        "hangi",
        "kim",
        "the",
        "and",
        "for",
        "ruzgar",
        "rüzgar",
        "suan",
        "şuan",
        "simdi",
        "şimdi",
        "guncel",
        "güncel",
        "hakkinda",
        "hakkında",
        "bana",
        "anlat",
        "soyle",
        "söyle",
    }
)

_TR_MAP = str.maketrans("çğıöşü", "cgiosu")

_LIST_Q_RE = re.compile(
    r"\b(kimler|kimlerle|neler|hangi|liste|taraf|ülkeler|ulkeler|aktör|aktor|muhalif|ittifak)\b",
    re.I,
)
# Türkçe soru terimi → snippet'te aranacak eşanlamlılar (İngilizce kaynaklar için)
_TERM_ALIASES: dict[str, tuple[str, ...]] = {
    "iran": ("iran", "tehran", "persian"),
    "israil": ("israel", "israeli", "gaza", "idf"),
    "israel": ("israel", "israeli"),
    "savas": ("war", "conflict", "fighting", "military", "attack", "strikes"),
    "savasiyor": ("war", "conflict", "fighting", "at war"),
    "catisma": ("conflict", "clash", "fighting"),
    "guncel": ("2026", "2025", "latest", "current", "today"),
    "ukrayna": ("ukraine", "ukrainian"),
    "rusya": ("russia", "russian"),
    "filistin": ("palestine", "palestinian", "gaza"),
    "gazze": ("gaza",),
    "abd": ("united states", "u.s.", "usa", "american"),
    "amerika": ("united states", "usa", "american"),
}
_KIMDIR_Q_RE = re.compile(
    r"\b(kimdir|kim\s*dir|nedir|ne\s*dir|kimi|kim\s*idi)\b",
    re.I,
)
_ZAMAN_Q_RE = re.compile(
    r"\b(ne\s*zaman|hangi\s*yıl|hangi\s*yil|kaç\s*yıl|kac\s*yil|tarih|yılında|yilinda)\b",
    re.I,
)
_GUVEN_RE = re.compile(r"\*\*Güven:\s*(yüksek|orta|düşük|dusuk)\*\*", re.I)
_BOILERPLATE_RE = re.compile(
    r"\b(read\s+more|learn\s+more|click\s+here|subscribe|cookie|sign\s+up|"
    r"jump\s+to\s+navigation|table\s+of\s+contents|see\s+also)\b",
    re.I,
)
_YEAR_RE = re.compile(r"\b(1[0-9]{3}|20[0-9]{2})\b")


def web_first_enabled() -> bool:
    return os.environ.get("RUZGAR_WEB_FIRST", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _min_term_coverage() -> float:
    try:
        return max(0.08, min(float(os.environ.get("RUZGAR_WEB_FIRST_MIN_COVERAGE", "0.22")), 0.6))
    except ValueError:
        return 0.22


def _min_relevance_score() -> float:
    try:
        return max(0.5, min(float(os.environ.get("RUZGAR_WEB_FIRST_MIN_RELEVANCE", "1.4")), 5.0))
    except ValueError:
        return 1.4


def _plan_primary(question_plan: Any | None) -> str:
    if question_plan is None:
        return ""
    if hasattr(question_plan, "primary"):
        return str(getattr(question_plan, "primary", "") or "").strip().lower()
    if isinstance(question_plan, dict):
        return str(question_plan.get("primary") or "").strip().lower()
    return ""


def _plan_web_query(question_plan: Any | None) -> str:
    if question_plan is None:
        return ""
    if hasattr(question_plan, "web_query"):
        return str(getattr(question_plan, "web_query", "") or "").strip()
    if isinstance(question_plan, dict):
        return str(question_plan.get("web_query") or "").strip()
    return ""


def _max_results() -> int:
    try:
        return max(4, min(int(os.environ.get("RUZGAR_WEB_FIRST_MAX_RESULTS", "8")), 12))
    except ValueError:
        return 8


def _fetch_urls_cap() -> int:
    try:
        return max(0, min(int(os.environ.get("RUZGAR_WEB_FIRST_FETCH_URLS", "0")), 2))
    except ValueError:
        return 0


def _news_enabled() -> bool:
    return os.environ.get("RUZGAR_WEB_FIRST_NEWS", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _norm(text: str) -> str:
    return (text or "").lower().translate(_TR_MAP)


def _extract_focus_terms(message: str) -> set[str]:
    raw = re.sub(r"[^\w\sçğıöşüÇĞİÖŞÜ]", " ", (message or ""))
    raw = _KIMDIR_Q_RE.sub(" ", raw)
    raw = _ZAMAN_Q_RE.sub(" ", raw)
    raw = re.sub(r"\b(rüzgar|ruzgar)\b", " ", raw, flags=re.I)
    out: set[str] = set()
    for w in raw.split():
        wl = w.lower().translate(_TR_MAP)
        if len(wl) >= 3 and wl not in _STOP:
            out.add(wl)
    return out


def _expand_terms_for_match(terms: set[str]) -> set[str]:
    expanded = set(terms)
    for t in terms:
        for alias in _TERM_ALIASES.get(t, ()):
            expanded.add(alias.lower())
    return expanded


def _geopolitics_english_query(message: str) -> str:
    try:
        from ilim_assistant.ana_motor_plan import looks_like_current_geopolitics_question

        if not looks_like_current_geopolitics_question(message):
            return ""
    except Exception:
        pass
    low = _norm(message)
    tokens: list[str] = []
    for key, en in (
        ("iran", "Iran"),
        ("israil", "Israel"),
        ("israel", "Israel"),
        ("ukrayna", "Ukraine"),
        ("rusya", "Russia"),
        ("filistin", "Palestine"),
        ("gazze", "Gaza"),
        ("abd", "United States"),
        ("amerika", "United States"),
        ("cin", "China"),
        ("taiwan", "Taiwan"),
        ("kore", "Korea"),
    ):
        if key in low and en not in tokens:
            tokens.append(en)
    if any(x in low for x in ("savas", "catisma", "kimlerle", "muhalif")):
        tokens.append("conflict")
    if any(x in low for x in ("suan", "simdi", "guncel", "haber", "bugun")):
        tokens.append("2026")
    return " ".join(tokens)


def _search_query_variants(
    message: str,
    question_plan: Any | None,
    *,
    idrak_pre: Any | None = None,
) -> list[str]:
    primary = _resolve_search_query(message, question_plan)
    variants: list[str] = []
    seen: set[str] = set()

    def _add(q: str) -> None:
        k = (q or "").strip().lower()
        if k and k not in seen:
            seen.add(k)
            variants.append(q.strip())

    _add(primary)
    from ilim_assistant.web_tools import refined_search_query

    _add(refined_search_query(message))
    eng = _geopolitics_english_query(message)
    if eng:
        _add(eng)
        _add(f"{eng} news")
    if idrak_pre is not None and getattr(idrak_pre, "intent", "") == "current_events":
        eq = str(getattr(idrak_pre, "effective_query", "") or message).strip()
        if eq:
            _add(eq)
            _add(_geopolitics_english_query(eq) or eq)
    try:
        from ilim_assistant.web_tools import expand_web_queries

        for q in expand_web_queries(primary or message, primary=_plan_primary(question_plan) or "bilgi"):
            _add(q)
    except Exception:
        pass
    return variants[:5]


def _fetch_wikipedia_rows(query: str, *, max_results: int = 3) -> list[dict]:
    q = (query or "").strip()
    if not q or len(q) < 3:
        return []
    try:
        import json
        import urllib.parse
        import urllib.request

        api = (
            "https://tr.wikipedia.org/w/api.php?"
            + urllib.parse.urlencode(
                {
                    "action": "query",
                    "list": "search",
                    "srsearch": q,
                    "format": "json",
                    "srlimit": max(1, min(max_results, 5)),
                    "utf8": 1,
                }
            )
        )
        req = urllib.request.Request(api, headers={"User-Agent": "RuzgarWebFirst/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
        hits = list((data.get("query") or {}).get("search") or [])
        rows: list[dict] = []
        for hit in hits[:max_results]:
            title = str(hit.get("title") or "").strip()
            snippet = re.sub(r"<[^>]+>", " ", str(hit.get("snippet") or ""))
            snippet = re.sub(r"\s+", " ", snippet).strip()
            if not title:
                continue
            slug = urllib.parse.quote(title.replace(" ", "_"))
            rows.append(
                {
                    "title": title,
                    "body": snippet,
                    "href": f"https://tr.wikipedia.org/wiki/{slug}",
                    "source": "wikipedia_tr",
                }
            )
        return rows
    except Exception:
        return []


def _question_kind(message: str) -> str:
    msg = message or ""
    if _LIST_Q_RE.search(msg):
        return "liste"
    if _KIMDIR_Q_RE.search(msg):
        return "kimdir"
    if _ZAMAN_Q_RE.search(msg):
        return "zaman"
    if any(x in _norm(msg) for x in ("guncel", "haber", "son dakika", "bugun")):
        return "guncel"
    return "genel"


def should_web_first_fast(
    message: str,
    mode_norm: str,
    question_plan: Any | None = None,
    *,
    history: list | None = None,
    idrak_pre: Any | None = None,
) -> bool:
    """Web snippet yolu — bulut/yerel LLM erken çıkışından önce."""
    if not web_first_enabled():
        return False
    if os.environ.get("ENABLE_WEB_SEARCH", "1").strip() in ("0", "false", "no"):
        return False
    if mode_norm not in ("genel", "uretim", "gelisim"):
        return False
    msg = (message or "").strip()
    if len(msg) < 4:
        return False

    try:
        from ilim_assistant.ana_motor_plan import (
            is_casual_conversation_turn,
            looks_like_clarification_short_query,
        )

        if is_casual_conversation_turn(msg, mode_norm, question_plan):
            return False
        if looks_like_clarification_short_query(msg) and not _plan_web_query(question_plan):
            return False
        from ilim_assistant.ana_motor_tercume_yurut import is_instant_translate_message

        if is_instant_translate_message(msg):
            return False
        from ilim_assistant.ruzgar_tek_beyin import personal_hafiza_blocks_bilgi_path

        if personal_hafiza_blocks_bilgi_path(msg):
            return False
    except Exception:
        pass

    primary = _plan_primary(question_plan)
    if primary in ("hafiza", "islem", "sohbet", "tercume", "programlama"):
        return False

    if idrak_pre is None:
        try:
            from ilim_assistant.ana_motor_idrak_zihin import analyze_turn, idrak_zihin_enabled

            if idrak_zihin_enabled():
                idrak_pre = analyze_turn(msg, history)
        except Exception:
            idrak_pre = None

    if idrak_pre is not None:
        if getattr(idrak_pre, "force_web", False):
            return True
        if getattr(idrak_pre, "intent", "") == "current_events":
            return True

    if question_plan is not None and getattr(question_plan, "prefer_web", False):
        if primary in ("", "bilgi", "bilim", "dilbilgisi", "hava"):
            return True

    try:
        from ilim_assistant.ruzgar_web_arastirma_pro import should_prioritize_web_research

        return should_prioritize_web_research(msg, question_plan, mode_norm)
    except Exception:
        return primary in ("bilgi", "bilim", "dilbilgisi", "hava")


def _resolve_search_query(message: str, question_plan: Any | None) -> str:
    wq = _plan_web_query(question_plan)
    if wq:
        return wq
    try:
        from ilim_assistant.ana_motor_plan import rewrite_web_search_query

        primary = _plan_primary(question_plan) or "bilgi"
        rq = rewrite_web_search_query(message, primary, "genel")
        if rq:
            return rq
    except Exception:
        pass
    from ilim_assistant.web_tools import refined_search_query

    return refined_search_query(message)


def _wants_news(message: str, idrak_pre: Any | None) -> bool:
    if not _news_enabled():
        return False
    if idrak_pre is not None and getattr(idrak_pre, "intent", "") == "current_events":
        return True
    from ilim_assistant.web_tools import _wants_news_search

    return _wants_news_search(message)


def fetch_web_rows_fast(
    message: str,
    question_plan: Any | None = None,
    *,
    idrak_pre: Any | None = None,
) -> tuple[list[dict], str]:
    """Hızlı DDG + çoklu sorgu + Wikipedia yedek."""
    if idrak_pre is None:
        try:
            from ilim_assistant.ana_motor_idrak_zihin import analyze_turn, idrak_zihin_enabled

            if idrak_zihin_enabled():
                idrak_pre = analyze_turn(message)
        except Exception:
            idrak_pre = None

    queries = _search_query_variants(message, question_plan, idrak_pre=idrak_pre)
    primary_query = queries[0] if queries else _resolve_search_query(message, question_plan)
    if not primary_query and not queries:
        return [], ""

    from ilim_assistant.web_tools import (
        _ddgs_news_search,
        _ddgs_search,
        _merge_ddg_rows,
        fetch_url_text,
    )

    rows: list[dict] = []
    for q in queries:
        try:
            rows.extend(_ddgs_search(q, max_results=_max_results()))
        except Exception:
            continue
        if len(rows) >= _max_results():
            break

    if _wants_news(message, idrak_pre):
        for q in queries[:2]:
            try:
                rows.extend(_ddgs_news_search(q, max_results=min(6, _max_results())))
            except Exception:
                continue

    merged = _merge_ddg_rows(rows)
    if len(merged) < 2:
        for q in queries[:3]:
            merged.extend(_fetch_wikipedia_rows(q, max_results=2))
        merged = _merge_ddg_rows(merged)

    if not merged:
        return [], primary_query

    terms = _extract_focus_terms(message)
    filtered = _filter_usable_rows(merged, terms, message)
    if filtered:
        merged = filtered
    else:
        merged = merged[: _max_results()]

    merged.sort(
        key=lambda r: _row_relevance(r, terms, message),
        reverse=True,
    )
    merged = merged[: _max_results()]

    fetch_n = _fetch_urls_cap()
    if fetch_n > 0:
        total_body = sum(len(str(r.get("body") or "")) for r in merged[:3])
        if total_body < 120:
            for row in merged[:fetch_n]:
                href = str(row.get("href") or "").strip()
                if not href.startswith("http"):
                    continue
                try:
                    txt, _st = fetch_url_text(href)
                    if txt:
                        cleaned = _clean_snippet_text(txt[:900])
                        row["body"] = _clean_snippet_text(
                            (str(row.get("body") or "") + " " + cleaned).strip()
                        )
                except Exception:
                    continue

    return merged, primary_query


def _domain(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower()
        return host[4:] if host.startswith("www.") else host
    except Exception:
        return ""


def _trust_score(href: str) -> float:
    from ilim_assistant.web_tools import _url_trust_score

    return _url_trust_score(href or "")


def _is_trusted(href: str) -> bool:
    return _trust_score(href) >= 2.4


def _clean_snippet_text(text: str) -> str:
    t = re.sub(r"\s+", " ", (text or "").strip())
    t = _BOILERPLATE_RE.sub(" ", t)
    t = re.sub(r"\[\d+\]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _word_set(text: str) -> set[str]:
    return {w for w in _norm(text).split() if len(w) >= 4}


def _overlap_ratio(a: str, b: str) -> float:
    wa, wb = _word_set(a), _word_set(b)
    if not wa or not wb:
        return 0.0
    inter = len(wa & wb)
    return inter / max(1, min(len(wa), len(wb)))


def _row_relevance(row: dict, terms: set[str], message: str) -> float:
    href = str(row.get("href") or "")
    title = _clean_snippet_text(str(row.get("title") or ""))
    body = _clean_snippet_text(str(row.get("body") or ""))
    blob = _norm(f"{title} {body}")
    expanded = _expand_terms_for_match(terms)
    term_hits = sum(1 for term in expanded if term in blob)
    trust = _trust_score(href)
    if str(row.get("source") or "") == "wikipedia_tr":
        trust = max(trust, 2.6)
    kind = _question_kind(message)
    bonus = 0.0
    if kind == "kimdir" and any(
        x in blob for x in ("dogdu", "dogum", "born", "padisah", "sultan", "was a", "biography")
    ):
        bonus += 0.8
    if kind == "zaman" and _YEAR_RE.search(body):
        bonus += 0.6
    if str(row.get("source") or "") == "news":
        bonus += 0.5
    length_bonus = min(len(body), 360) / 450.0
    return trust + term_hits * 1.35 + bonus + length_bonus


def _filter_usable_rows(rows: list[dict], terms: set[str], message: str) -> list[dict]:
    min_score = _min_relevance_score()
    out: list[dict] = []
    for row in rows:
        body = _clean_snippet_text(str(row.get("body") or ""))
        title = _clean_snippet_text(str(row.get("title") or ""))
        if len(body) < 24 and len(title) < 12:
            continue
        if _BOILERPLATE_RE.search(body) and len(body) < 80:
            continue
        score = _row_relevance({**row, "body": body, "title": title}, terms, message)
        if score < min_score and not _is_trusted(str(row.get("href") or "")):
            continue
        if any(
            _overlap_ratio(body, str(prev.get("body") or "")) > 0.72 for prev in out
        ):
            continue
        out.append({**row, "body": body, "title": title, "_rel": score})
    return out


def _best_excerpt(text: str, terms: set[str], *, max_len: int = 300, kind: str = "genel") -> str:
    t = _clean_snippet_text(text)
    if not t:
        return ""
    if len(t) <= max_len:
        return t
    sentences = re.split(r"(?<=[.!?])\s+", t)
    scored: list[tuple[float, str]] = []
    for s in sentences:
        if len(s) < 18:
            continue
        low = _norm(s)
        hit = sum(1.2 for term in terms if term in low)
        if kind == "kimdir" and any(x in low for x in ("was", "is a", "dogdu", "padisah", "sultan")):
            hit += 1.0
        if kind == "zaman" and _YEAR_RE.search(s):
            hit += 1.5
        scored.append((hit + len(s) / 500.0, s.strip()))
    if scored:
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[0][1][:max_len].strip()
    return t[:max_len].strip()


def _rank_rows(rows: list[dict], terms: set[str], message: str) -> list[dict]:
    return sorted(
        rows,
        key=lambda r: float(r.get("_rel") or _row_relevance(r, terms, message)),
        reverse=True,
    )


def _term_coverage(message: str, answer: str, terms: set[str] | None = None) -> float:
    focus = terms or _extract_focus_terms(message)
    if not focus:
        return 1.0
    blob = _norm(answer)
    expanded = _expand_terms_for_match(focus)
    hits = sum(1 for t in expanded if t in blob)
    # Normalize by focus size, cap bonus for alias hits
    base_hits = sum(1 for t in focus if t in blob or any(a in blob for a in _TERM_ALIASES.get(t, ())))
    return max(base_hits / len(focus), min(1.0, hits / max(len(expanded), 1)))


def _assess_consensus(rows: list[dict], terms: set[str], message: str = "") -> tuple[bool, str]:
    """Üst snippet'ler ortak anahtar kelime paylaşıyor mu."""
    if len(rows) < 2:
        return True, ""
    tops = rows[:3]
    blobs = [_norm(f"{r.get('title')} {r.get('body')}") for r in tops]
    shared = set(terms)
    for b in blobs:
        shared = {t for t in shared if t in b}
    if len(shared) >= max(1, len(terms) // 3):
        return True, ""
    year_sets = [_YEAR_RE.findall(_norm(f"{r.get('title')} {r.get('body')}")) for r in tops]
    flat_years = {y for ys in year_sets for y in ys}
    if _question_kind(message) == "zaman" and len(flat_years) >= 2:
        return False, (
            "Kaynak snippet'lerinde farklı yıllar görünüyor; "
            "en sık geçen tarihi öne aldım — emin değilsen «daha detaylı anlat» de."
        )
    if len(flat_years) >= 4:
        return False, (
            "Kaynak snippet'leri farklı dönemlere işaret ediyor; "
            "özet en güncel parçalara dayanıyor."
        )
    return len(shared) >= 1, ""


def _pick_guven_level(
    *,
    trusted_count: int,
    coverage: float,
    consensus_ok: bool,
    row_count: int,
) -> str:
    if trusted_count >= 2 and coverage >= 0.35 and consensus_ok:
        return "yüksek"
    if trusted_count >= 1 and coverage >= 0.28 and consensus_ok:
        return "yüksek"
    if coverage >= 0.22 and row_count >= 2 and consensus_ok:
        return "orta"
    if trusted_count >= 1 or coverage >= 0.18:
        return "orta"
    return "düşük"


def _format_body(parts: list[str], message: str, kind: str) -> str:
    if not parts:
        return ""
    if kind == "liste" or (len(parts) >= 2 and _LIST_Q_RE.search(message or "")):
        return "\n".join(f"- {p.rstrip('.')}" for p in parts[:4])
    if kind == "kimdir" and len(parts) == 1:
        return parts[0].rstrip(".") + "."
    if kind == "zaman" and len(parts) >= 1:
        lead = parts[0].rstrip(".")
        if _YEAR_RE.search(lead):
            return lead + "."
        years = _YEAR_RE.findall(" ".join(parts))
        if years:
            return f"{lead}. ({years[0]})"
        return lead + "."
    if len(parts) == 1:
        return parts[0].rstrip(".") + "."
    return " ".join(p.rstrip(".") + "." for p in parts[:3])


def _strip_guven_kaynak(text: str) -> str:
    t = re.sub(r"\n\n\*\*Kaynak:\*\*[^\n]*", "", text or "", flags=re.I)
    t = re.sub(r"\n\*\*Güven:\*\*[^\n]*", "", t, flags=re.I)
    t = re.sub(r"\n\n\*\*Güncellik:\*\*[^\n]*", "", t, flags=re.I)
    return t.strip()


def compose_web_first_reply(
    message: str,
    rows: list[dict],
    *,
    web_query: str = "",
) -> tuple[str, dict[str, Any]]:
    meta: dict[str, Any] = {
        "row_count": len(rows),
        "web_query": web_query,
        "sources": [],
        "used_rows": 0,
        "trusted_sources": 0,
    }
    if not rows:
        return "", meta

    terms = _extract_focus_terms(message)
    kind = _question_kind(message)
    ranked = _rank_rows(rows, terms, message)
    top = ranked[:4]

    parts: list[str] = []
    used_excerpts: set[str] = set()
    trusted = 0
    for row in top:
        title = str(row.get("title") or "").strip()
        body = str(row.get("body") or "").strip()
        href = str(row.get("href") or "").strip()
        excerpt = _best_excerpt(body or title, terms, max_len=340, kind=kind)
        if not excerpt or len(excerpt) < 22:
            continue
        sig = _norm(excerpt)[:90]
        if sig in used_excerpts:
            continue
        if any(_overlap_ratio(excerpt, prev) > 0.68 for prev in parts):
            continue
        used_excerpts.add(sig)
        parts.append(excerpt)
        dom = _domain(href)
        if dom:
            meta["sources"].append(dom)
        if _is_trusted(href):
            trusted += 1

    if not parts:
        for row in top[:2]:
            t = str(row.get("title") or "").strip()
            b = str(row.get("body") or "").strip()[:200]
            chunk = _clean_snippet_text(f"{t}. {b}" if t and b else (t or b))
            if len(chunk) >= 30:
                parts.append(chunk)
                dom = _domain(str(row.get("href") or ""))
                if dom:
                    meta["sources"].append(dom)

    if not parts:
        return "", meta

    body_out = _format_body(parts, message, kind)
    body_out = re.sub(r"\s+", " ", body_out).strip() if kind != "liste" else body_out.strip()
    if len(body_out) > 1300:
        body_out = body_out[:1297] + "…"

    meta["used_rows"] = len(parts)
    meta["trusted_sources"] = trusted
    srcs = list(dict.fromkeys(meta["sources"]))[:4]
    meta["sources"] = srcs
    return body_out, meta


def apply_web_first_quality_pass(
    message: str,
    reply: str,
    rows: list[dict],
    meta: dict[str, Any],
    *,
    idrak_pre: Any | None = None,
) -> tuple[str, dict[str, Any]]:
    """
    Kural tabanlı doğrulama — LLM yok; düşük kaliteyi reddet veya güveni ayarla.
    """
    verify: dict[str, Any] = {
        "applied": True,
        "reject": False,
        "coverage": 0.0,
        "consensus_ok": True,
        "guven": "orta",
    }
    body = _strip_guven_kaynak(reply)
    if not body:
        verify["reject"] = True
        verify["reason"] = "bos_cevap"
        return "", verify

    terms = _extract_focus_terms(message)
    coverage = _term_coverage(message, body, terms)
    verify["coverage"] = round(coverage, 3)

    ranked = _rank_rows(rows, terms, message) if rows else []
    consensus_ok, consensus_note = _assess_consensus(ranked[:3], terms, message)
    verify["consensus_ok"] = consensus_ok
    if consensus_note:
        verify["consensus_note"] = consensus_note

    trusted = int(meta.get("trusted_sources") or 0)
    guven = _pick_guven_level(
        trusted_count=trusted,
        coverage=coverage,
        consensus_ok=consensus_ok,
        row_count=int(meta.get("used_rows") or 0),
    )
    verify["guven"] = guven

    min_cov = _min_term_coverage()
    if coverage < min_cov * 0.55 and trusted == 0 and int(meta.get("used_rows") or 0) < 2:
        verify["reject"] = True
        verify["reason"] = "dusuk_ilgi"
        return "", verify

    if coverage < min_cov and guven == "düşük" and trusted == 0:
        verify["reject"] = True
        verify["reason"] = "dusuk_kapsam"
        return "", verify

    srcs = list(meta.get("sources") or [])
    out = body
    if srcs:
        out += f"\n\n**Kaynak:** {', '.join(srcs[:4])}"

    guven_line = f"**Güven:** {guven} — canlı web snippet birleşimi"
    if guven == "düşük":
        guven_line += "; konuyla tam örtüşme zayıf — «daha detaylı anlat» ile genişletebilirim"
    elif not consensus_ok:
        guven_line += "; kaynak parçaları kısmen farklı"
    out += f"\n{guven_line}"

    if consensus_note and guven != "yüksek":
        out += f"\n*{consensus_note}*"

    try:
        from ilim_assistant.ana_motor_guncellik import append_reply_freshness_stamp

        guncel = (
            getattr(idrak_pre, "intent", "") == "current_events"
            if idrak_pre is not None
            else False
        ) or _question_kind(message) in ("guncel", "liste")
        if guncel or any(x in _norm(message) for x in ("guncel", "haber", "bugun", "suan")):
            out = append_reply_freshness_stamp(out, web_was_used=True, user_message=message)
    except Exception:
        pass

    verify["accepted"] = True
    return out, verify


def build_web_first_reply(
    message: str,
    question_plan: Any | None = None,
    *,
    history: list | None = None,
    idrak_pre: Any | None = None,
) -> tuple[str, dict[str, Any]]:
    if idrak_pre is None:
        try:
            from ilim_assistant.ana_motor_idrak_zihin import analyze_turn, idrak_zihin_enabled

            if idrak_zihin_enabled():
                idrak_pre = analyze_turn(message, history)
        except Exception:
            idrak_pre = None

    rows, query = fetch_web_rows_fast(message, question_plan, idrak_pre=idrak_pre)
    draft, meta = compose_web_first_reply(message, rows, web_query=query)
    if not draft:
        meta["verify"] = {"reject": True, "reason": "compose_bos"}
        return "", meta
    final, verify = apply_web_first_quality_pass(
        message, draft, rows, meta, idrak_pre=idrak_pre
    )
    meta["verify"] = verify
    return final, meta


def iter_web_first_fast_reply(
    message: str,
    history: list,
    *,
    mode_norm: str = "genel",
    question_plan: Any | None = None,
    idrak_pre: Any | None = None,
) -> Iterator[str]:
    reply, _meta = build_web_first_reply(
        message,
        question_plan,
        history=history,
        idrak_pre=idrak_pre,
    )
    if not (reply or "").strip():
        return
    step = max(8, int(os.environ.get("RUZGAR_WEB_FIRST_STREAM_CHARS", "14")))
    for i in range(0, len(reply), step):
        yield reply[i : i + step]


def web_first_status() -> dict[str, Any]:
    return {
        "ok": True,
        "enabled": web_first_enabled(),
        "version": WEB_FIRST_VERSION,
        "max_results": _max_results(),
        "fetch_urls": _fetch_urls_cap(),
        "news": _news_enabled(),
        "min_coverage": _min_term_coverage(),
        "min_relevance": _min_relevance_score(),
        "summary_tr": "Web snippet öncelik + AP2 birleştirme/doğrulama ince ayarı",
    }
