# Created by Ümit & Gökçenur
"""Tercüme analist — araştır, skorla, isteğe bağlı indir/oku/çevir (Faz 1 omurga)."""

from __future__ import annotations

import json
import os
import re
import unicodedata
from pathlib import Path
from typing import Any

TERCUME_ANALYST_VERSION = "tercume-analyst-v2-faz2-2026-05-31"

_ALIASES_PATH = Path(__file__).with_name("tercume_eser_aliases.json")

_HOST_BOOST: dict[str, int] = {
    "archive.org": 28,
    "archive.org/details": 30,
    "yazmalar.gov.tr": 20,
    "shamela.ws": 20,
    "wikisource.org": 16,
    "gutenberg.org": 14,
    "al-eman.com": 12,
    "scholar.google.com": 8,
}

_DOWNLOADABLE_EXT = (".pdf", ".epub", ".djvu", ".txt", ".zip")

_IRRELEVANT_HOST_FRAGMENTS = (
    "doctissimo",
    "ccm.net",
    "getmobil",
    "getir.com",
    "microsoft.com",
    "office",
    "vanodine",
    "evans",
    "3sat.de",
    "wikipedia.org/wiki/das_",
    "cambridge.org",
    "dictionary",
    "acne",
    "spielfilm",
)


def _norm(s: str) -> str:
    t = unicodedata.normalize("NFKD", (s or "").lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", t).strip()


def _load_aliases() -> dict[str, Any]:
    try:
        return json.loads(_ALIASES_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"authors": {}, "works": {}, "noise_phrases": []}


def _query_terms(query: str) -> list[str]:
    from ilim_assistant.motorlar.tercume_eser_arama import _core_terms, _refine_user_query

    base = _refine_user_query(query)
    core = _core_terms(base)
    parts = re.split(r"[^\w\u00c0-\u024f\u1e00-\u1eff]+", core, flags=re.UNICODE)
    return [p for p in parts if len(p) >= 3]


def _alias_hits(query: str, text: str, aliases: dict[str, Any]) -> list[str]:
    nq = _norm(query)
    nt = _norm(text)
    hits: list[str] = []
    for section in ("authors", "works"):
        block = aliases.get(section) or {}
        if not isinstance(block, dict):
            continue
        for label, syns in block.items():
            if not isinstance(syns, list):
                continue
            label_n = _norm(label)
            syns_n = [_norm(str(s)) for s in syns if _norm(str(s))]
            query_mentions = (label_n and label_n in nq) or any(s in nq for s in syns_n)
            if not query_mentions:
                continue
            if label_n and label_n in nt:
                hits.append(f"{section}:{label}")
                continue
            for sn in syns_n:
                if sn and sn in nt:
                    hits.append(f"{section}:{label}")
                    break
    return hits


def _likely_irrelevant(item: dict[str, Any], query: str, terms: list[str]) -> bool:
    blob = _norm(
        f"{item.get('title')} {item.get('snippet')} {item.get('url')}"
    )
    ul = str(item.get("url") or "").lower()
    for frag in _IRRELEVANT_HOST_FRAGMENTS:
        if frag in ul or frag in blob:
            return True
    if terms:
        matched = sum(1 for t in terms if _norm(t) in blob)
        if matched == 0:
            return True
    return False


def find_local_archive_matches(query: str, *, limit: int = 8) -> list[dict[str, Any]]:
    """Yerel ilim-assistant/arsiv içinde dosya adı eşleşmesi."""
    terms = _query_terms(query)
    if not terms:
        return []
    arsiv = _repo_root() / "ilim-assistant" / "arsiv"
    if not arsiv.is_dir():
        return []
    root = _repo_root()
    out: list[dict[str, Any]] = []
    allowed = {".pdf", ".txt", ".jsonl", ".epub", ".djvu", ".md"}
    for path in arsiv.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in allowed:
            continue
        name_n = _norm(path.name)
        if not any(_norm(t) in name_n for t in terms):
            continue
        try:
            rel = path.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            continue
        out.append(
            {
                "rel": rel,
                "name": path.name,
                "size_kb": max(1, path.stat().st_size // 1024),
            }
        )
        if len(out) >= limit:
            break
    return out


def score_search_item(item: dict[str, Any], query: str, aliases: dict[str, Any] | None = None) -> dict[str, Any]:
    """Arama satırına 0–100 skor ve gerekçe."""
    aliases = aliases or _load_aliases()
    url = str(item.get("url") or "")
    title = str(item.get("title") or "")
    snippet = str(item.get("snippet") or "")
    blob = f"{title} {snippet} {url}"
    nb = _norm(blob)
    nq = _norm(query)

    score = 10.0
    reasons: list[str] = ["temel"]

    ul = url.lower()
    for host, pts in _HOST_BOOST.items():
        if host in ul:
            score += pts
            reasons.append(f"host:{host.split('.')[0]}")
            break

    if any(ul.endswith(ext) or f"{ext}?" in ul or f"{ext}&" in ul for ext in _DOWNLOADABLE_EXT):
        score += 28
        reasons.append("dosya_uzantisi")

    terms = _query_terms(query)
    matched = 0
    for term in terms:
        tn = _norm(term)
        if tn and tn in nb:
            matched += 1
            score += 12
    if matched:
        reasons.append(f"terim:{matched}")

    for ah in _alias_hits(query, blob, aliases):
        score += 18
        reasons.append(f"alias:{ah}")

    for noise in aliases.get("noise_phrases") or []:
        nn = _norm(str(noise))
        if nn and nn in nb and not any(_norm(t) in nb for t in terms if len(t) > 5):
            score -= 35
            reasons.append(f"gurultu:{noise}")
            break

    if "rabbani" in nq or "rabban" in nq:
        if "12 imam" in nb or "on iki imam" in nb:
            score -= 40
            reasons.append("alakasiz:12_imam")

    if _likely_irrelevant(item, query, terms):
        score -= 48
        reasons.append("alakasiz:domain")

    if str(item.get("source") or "").endswith("(API)"):
        score += 12
        reasons.append("archive_api")

    dl = str(item.get("download_url") or "")
    if dl.lower().endswith(".pdf"):
        score += 22
        reasons.append("archive_pdf")

    if "(doğrudan)" in str(item.get("source") or ""):
        score += 8
        reasons.append("site_direct")

    score = max(0.0, min(100.0, score))
    if score >= 65:
        confidence = "high"
    elif score >= 35:
        confidence = "medium"
    else:
        confidence = "low"
    downloadable = bool(dl) or any(h in ul for h in _HOST_BOOST) or any(
        ext in ul for ext in _DOWNLOADABLE_EXT
    )
    return {
        **item,
        "score": round(score, 1),
        "confidence": confidence,
        "why_ranked": reasons[:6],
        "downloadable_hint": downloadable,
    }


def _local_search_items(matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for m in matches:
        rel = str(m.get("rel") or "")
        name = str(m.get("name") or rel)
        out.append(
            {
                "title": name,
                "snippet": f"Bu dosya zaten bilgisayarınızda: {rel}",
                "url": "",
                "source": "Yerel arşiv",
                "score": 100.0,
                "why_ranked": ["arsivde_var"],
                "downloadable_hint": False,
                "local_rel": rel,
                "open_hint": "Çalışma sekmesi → soldaki listeden dosyaya tıklayın",
            }
        )
    return out


def analyze_tercume_query(
    user_query: str,
    *,
    max_results: int = 22,
) -> dict[str, Any]:
    """Araştırma raporu: skorlu kaynaklar + önerilen indirme + Scholar."""
    from ilim_assistant.motorlar.tercume_atolye import local_first_search_enabled
    from ilim_assistant.motorlar.tercume_eser_arama import (
        search_eser_merged,
        scholar_search_url,
    )

    raw = (user_query or "").strip()
    if not raw:
        return {"ok": False, "error": "Sorgu boş.", "items": []}

    local_matches = find_local_archive_matches(raw)
    local_items = _local_search_items(local_matches)
    web_skipped = False

    if local_first_search_enabled() and local_items:
        search = {
            "ok": True,
            "query": raw,
            "items": [],
            "total": 0,
            "scholar_url": scholar_search_url(raw),
            "version": "local-first-skip-web",
        }
        web_skipped = True
    else:
        search = search_eser_merged(raw, max_total=max_results)
        if not search.get("ok"):
            return search

    aliases = _load_aliases()
    scored: list[dict[str, Any]] = list(local_items)

    for it in search.get("items") or []:
        if not isinstance(it, dict):
            continue
        row = score_search_item(it, raw, aliases)
        scored.append(row)

    scored.sort(key=lambda x: (-float(x.get("score") or 0), str(x.get("title") or "")))

    filtered = [x for x in scored if float(x.get("score") or 0) >= 22 or x.get("local_rel")]
    if not filtered and scored:
        filtered = scored[:3]
    scored = filtered

    top = scored[0] if scored else None
    top_score = float(top.get("score") or 0) if top else 0.0
    quality = "ok" if top_score >= 48 or (top and top.get("local_rel")) else "weak"
    suggested_url = ""
    suggested_reason = ""
    if top and top.get("local_rel"):
        suggested_reason = "arsivde_var"
    elif top and float(top.get("score") or 0) >= 35 and top.get("downloadable_hint"):
        suggested_url = str(top.get("download_url") or top.get("url") or "")
        suggested_reason = "; ".join(top.get("why_ranked") or [])

    summary_parts = []
    if web_skipped and local_items:
        summary_parts.append(
            "Arşivde bulundu — internet araması yapılmadı. "
            "Çalışma sekmesinden dosyayı açıp Çevir deyin."
        )
    elif quality == "weak":
        summary_parts.append(
            "İnternet sonuçları zayıf — soldaki yerel dosyalara veya Scholar'a bakın."
        )
    if local_matches and not web_skipped:
        names = ", ".join(m["name"][:40] for m in local_matches[:3])
        summary_parts.append(f"Yerel arşivde de var: {names}.")
    if top and top.get("local_rel"):
        summary_parts.append(
            f"Arşivde: «{str(top.get('title') or '')[:80]}» — listeden açıp çevirin."
        )
    elif top:
        summary_parts.append(
            f"En iyi aday: «{str(top.get('title') or '')[:80]}» "
            f"(skor {top.get('score')}, {top.get('source', '')})."
        )
    elif not summary_parts:
        summary_parts.append("Sonuç bulunamadı; sorguyu kısaltın veya yazar+eser adı yazın.")

    return {
        "ok": True,
        "version": TERCUME_ANALYST_VERSION,
        "query": search.get("query") or raw,
        "expanded_query": search.get("expanded_query") or "",
        "expand_notes": search.get("expand_notes") or [],
        "scholar_url": search.get("scholar_url") or scholar_search_url(raw),
        "items": scored,
        "total": len(scored),
        "suggested_download_url": suggested_url,
        "suggested_download_reason": suggested_reason,
        "summary": " ".join(summary_parts),
        "quality": quality,
        "local_archive_matches": local_matches,
        "local_first": web_skipped,
        "web_search_skipped": web_skipped,
        "search_version": search.get("version"),
    }


def _repo_root() -> Path:
    try:
        from ilim_assistant.motorlar.programlama_motoru import repo_root

        r = repo_root(None)
        if r:
            return Path(r)
    except Exception:
        pass
    return Path(__file__).resolve().parents[2]


def _resolve_rel(rel: str) -> Path:
    root = _repo_root()
    raw = (rel or "").strip().replace("\\", "/").lstrip("/")
    target = (root / raw.replace("/", os.sep)).resolve()
    target.relative_to(root.resolve())
    return target


def read_source_preview(rel: str, *, max_pages: int = 3) -> dict[str, Any]:
    """İndirilen/açık dosyadan kısa okuma önizlemesi."""
    from ilim_assistant.motorlar.tercume_atolye import split_text_into_pages

    raw = (rel or "").strip().replace("\\", "/").lstrip("/")
    if not raw:
        return {"ok": False, "error": "rel boş"}
    try:
        target = _resolve_rel(raw)
    except ValueError:
        return {"ok": False, "error": "Geçersiz yol"}
    if not target.is_file():
        return {"ok": False, "error": "Dosya yok"}

    ext = target.suffix.lower()
    pages: list[dict[str, Any]] = []
    meta: dict[str, Any] = {"ext": ext, "rel": raw}

    if ext == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError:
            return {"ok": False, "error": "pip install pypdf"}
        reader = PdfReader(str(target))
        n = len(reader.pages)
        take = min(max(1, max_pages), n)
        for i in range(take):
            try:
                t = (reader.pages[i].extract_text() or "").strip()
            except Exception:
                t = ""
            pages.append({"index": i, "text": t, "label": f"Sayfa {i + 1}"})
        meta["pages_total"] = n
        meta["pages_read"] = take
    elif ext in {".txt", ".md", ".html", ".htm"}:
        try:
            full = target.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            return {"ok": False, "error": str(exc)[:200]}
        chunks = split_text_into_pages(full, max_chars=2800)
        for p in chunks[: max(1, max_pages)]:
            pages.append(
                {
                    "index": p["index"],
                    "text": p["text"],
                    "label": f"Bölüm {int(p['index']) + 1}",
                }
            )
        meta["pages_total"] = len(chunks)
    else:
        return {
            "ok": False,
            "error": f"Önizleme henüz desteklenmiyor: {ext} (pdf/txt/md/html).",
        }

    preview_text = "\n\n".join(
        str(p.get("text") or "").strip() for p in pages if str(p.get("text") or "").strip()
    )[:12_000]

    return {
        "ok": True,
        "rel": raw,
        "pages": pages,
        "meta": meta,
        "preview_chars": len(preview_text),
        "preview_text": preview_text,
    }


def run_tercume_pipeline(
    user_query: str,
    *,
    download: bool = False,
    download_url: str = "",
    target_dir_rel: str = "ilim-assistant/arsiv/tercume-imports",
    read_preview_pages: int = 0,
    translate: bool = False,
    src_lang: str = "auto",
    tgt_lang: str = "tr",
    workspace_root: str | None = None,
) -> dict[str, Any]:
    """analyze → (isteğe indir) → (isteğe oku) → (isteğe ilk parça çevir)."""
    analysis = analyze_tercume_query(user_query)
    if not analysis.get("ok"):
        return analysis

    steps: list[dict[str, Any]] = [{"step": "analyze", "ok": True, "total": analysis.get("total")}]
    out: dict[str, Any] = {
        "ok": True,
        "version": TERCUME_ANALYST_VERSION,
        "query": analysis.get("query"),
        "analysis": analysis,
        "steps": steps,
    }

    url = (download_url or analysis.get("suggested_download_url") or "").strip()
    rel = ""

    if download:
        if not url:
            steps.append({"step": "download", "ok": False, "error": "İndirilecek URL yok (skor düşük veya sonuç boş)."})
            out["download"] = {"ok": False, "error": "URL yok"}
        else:
            from ilim_assistant.motorlar.arsiv_indirme import download_url_to_folder, resolve_arsiv_dir

            try:
                if target_dir_rel.startswith("ilim-assistant/arsiv/") or target_dir_rel == "ilim-assistant/arsiv":
                    folder = resolve_arsiv_dir(target_dir_rel)
                else:
                    folder = resolve_arsiv_dir(
                        f"ilim-assistant/arsiv/{target_dir_rel.lstrip('/')}"
                    )
            except ValueError as exc:
                steps.append({"step": "download", "ok": False, "error": str(exc)})
                out["download"] = {"ok": False, "error": str(exc)}
                folder = None

            if folder is not None:
                dl = download_url_to_folder(url, folder, timeout_sec=7200.0)
                steps.append({"step": "download", "ok": bool(dl.get("ok")), **{k: dl.get(k) for k in ("rel", "bytes", "error", "skipped")}})
                out["download"] = dl
                if dl.get("ok"):
                    rel = str(dl.get("rel") or "")

    if read_preview_pages > 0:
        read_rel = rel or ""
        if not read_rel:
            steps.append({"step": "read", "ok": False, "error": "Önce indirme gerekli veya rel verin."})
        else:
            preview = read_source_preview(read_rel, max_pages=read_preview_pages)
            steps.append({"step": "read", "ok": bool(preview.get("ok")), "preview_chars": preview.get("preview_chars")})
            out["read"] = preview

            if translate and preview.get("ok") and preview.get("preview_text"):
                from ilim_assistant.motorlar.tercume_atolye import append_apprentice_log, translate_chunk

                tr = translate_chunk(
                    str(preview.get("preview_text") or "")[:8000],
                    src_lang=src_lang,
                    tgt_lang=tgt_lang,
                    source_file=read_rel,
                    page_index=0,
                )
                steps.append({"step": "translate", "ok": bool(tr.get("ok"))})
                out["translate"] = tr
                if tr.get("ok") and workspace_root is not None:
                    append_apprentice_log(
                        workspace_root,
                        {
                            "lesson": "analyst_pipeline_translate",
                            "source_file": read_rel,
                            "query": user_query,
                            "tgt_lang": tgt_lang,
                        },
                    )

    return out
