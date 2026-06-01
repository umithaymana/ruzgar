# Created by Ümit & Gökçenur
"""Tercüme Faz 3 — okuma kalitesi, sayfa skoru, OCR temizliği."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

READ_PIPELINE_VERSION = "tercume-read-pipeline-v3-faz3-2026-05-31"

_WORD_RE = re.compile(r"[\w\u0600-\u06FF]+", re.UNICODE)
_ARABIC_RE = re.compile(r"[\u0600-\u06FF]")
_LATIN_RE = re.compile(r"[A-Za-z]")


def assess_page_quality(text: str, *, source_kind: str = "text") -> dict[str, Any]:
    """Sayfa metni: empty | low | ok + 0–100 skor."""
    t = (text or "").strip()
    if len(t) < 12:
        return {
            "quality": "empty",
            "score": 0,
            "hint": "Sayfa boş veya metin yok — taranmış PDF/görsel için OCR deneyin.",
        }

    words = _WORD_RE.findall(t)
    n_words = len(words)
    chars = len(t)
    arabic = len(_ARABIC_RE.findall(t))
    latin = len(_LATIN_RE.findall(t))

    if n_words < 18 and chars < 120:
        return {
            "quality": "low",
            "score": 28,
            "hint": "Çok az kelime — taranmış sayfa veya bozuk metin çıkarımı olabilir.",
        }

    if source_kind == "ocr" and n_words < 40:
        return {
            "quality": "low",
            "score": 40,
            "hint": "OCR metni kısa — görsel kalitesi düşük olabilir.",
        }

    # Anlamsız karakter yoğunluğu
    alnum = sum(1 for c in t if c.isalnum() or c in " \n\t")
    if chars > 80 and alnum / max(chars, 1) < 0.55:
        return {
            "quality": "low",
            "score": 32,
            "hint": "Metin okunaksız — OCR veya farklı kaynak PDF deneyin.",
        }

    score = 72.0
    if n_words >= 80:
        score += 12
    elif n_words >= 40:
        score += 6
    if arabic > 20 and latin < arabic // 3:
        score += 5
    if source_kind == "pdf" and n_words < 35:
        score -= 15

    score = max(0.0, min(100.0, score))
    q = "ok" if score >= 55 else "low"
    hint = ""
    if q == "low":
        hint = "Metin zayıf — sayfa taranmış olabilir; OCR düşünün."
    return {"quality": q, "score": round(score, 1), "hint": hint}


def enrich_pages(pages: list[dict[str, Any]], *, source_kind: str = "text") -> list[dict[str, Any]]:
    from ilim_assistant.motorlar.tercume_ocr_clean import clean_ocr_text

    out: list[dict[str, Any]] = []
    for p in pages:
        row = dict(p)
        text = str(row.get("text") or "")
        if source_kind == "ocr":
            text = clean_ocr_text(text)
        hit = assess_page_quality(text, source_kind=source_kind)
        row["text"] = text
        row["quality"] = hit["quality"]
        row["quality_score"] = hit["score"]
        row["quality_hint"] = hit["hint"]
        out.append(row)
    return out


def summarize_page_quality_meta(pages: list[dict[str, Any]]) -> dict[str, Any]:
    empty = sum(1 for p in pages if p.get("quality") == "empty")
    low = sum(1 for p in pages if p.get("quality") == "low")
    ok = sum(1 for p in pages if p.get("quality") == "ok")
    total = len(pages)
    ocr_recommended = total > 0 and (empty + low) >= max(1, total // 3)
    avg = 0.0
    if pages:
        avg = sum(float(p.get("quality_score") or 0) for p in pages) / len(pages)
    hint = ""
    if ocr_recommended:
        hint = (
            f"{empty + low}/{total} sayfa zayıf/boş — taranmış kitap olabilir; "
            "OCR dili seçip görsel/PDF tarayın veya metinli PDF kullanın."
        )
    elif empty:
        hint = f"{empty} boş sayfa atlandı."
    return {
        "quality_summary": {
            "total": total,
            "empty": empty,
            "low": low,
            "ok": ok,
            "avg_score": round(avg, 1),
            "ocr_recommended": ocr_recommended,
        },
        "read_hint": hint,
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


def resolve_book_path(rel: str) -> tuple[Path, str]:
    root = _repo_root()
    raw = (rel or "").strip().replace("\\", "/").lstrip("/")
    target = (root / raw.replace("/", os.sep)).resolve()
    target.relative_to(root.resolve())
    return target, raw


def extract_pdf_pages(
    target: Path,
    *,
    max_pages: int | None = None,
    page_from: int | None = None,
    page_to: int | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    from ilim_assistant.motorlar.tercume_atolye import tercume_pdf_max_pages

    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("pip install pypdf") from exc

    reader = PdfReader(str(target))
    n = len(reader.pages)
    start = max(0, int(page_from)) if page_from is not None else 0
    end = min(n, int(page_to) + 1) if page_to is not None else n
    if page_from is not None or page_to is not None:
        cap = max(0, end - start)
    else:
        cap = min(n, max_pages if max_pages is not None else tercume_pdf_max_pages())
        start = 0
        end = cap
    pages: list[dict[str, Any]] = []
    for i in range(start, end):
        try:
            t = (reader.pages[i].extract_text() or "").strip()
        except Exception:
            t = ""
        pages.append({"index": i, "text": t, "label": f"Sayfa {i + 1}"})
    meta: dict[str, Any] = {
        "ext": ".pdf",
        "pages_total": n,
        "pages_read": len(pages),
        "page_from": start,
        "page_to": end - 1 if pages else start,
    }
    if page_from is None and page_to is None and end < n:
        meta["pages_capped"] = True
        meta["pages_cap"] = end
    return pages, meta


def _maybe_ocr_weak_pdf_pages(
    pages: list[dict[str, Any]],
    target: Path,
    *,
    src_lang: str = "auto",
) -> list[dict[str, Any]]:
    import os

    if os.environ.get("RUZGAR_TERCUME_PDF_OCR", "0").strip().lower() not in (
        "1",
        "true",
        "yes",
    ):
        return pages
    try:
        max_fix = max(1, int(os.environ.get("RUZGAR_TERCUME_OCR_FIX_PAGES", "5")))
    except ValueError:
        max_fix = 5
    from ilim_assistant.motorlar.tercume_ocr_cascade import ocr_pdf_page

    fixed = 0
    out: list[dict[str, Any]] = []
    for p in pages:
        row = dict(p)
        if fixed < max_fix and row.get("quality") in ("empty", "low"):
            hit = ocr_pdf_page(str(target), int(row.get("index") or 0), src_lang=src_lang)
            if hit.get("ok") and str(hit.get("text") or "").strip():
                row["text"] = str(hit.get("text") or "")
                row["ocr_cascade"] = hit.get("preset")
                row["quality"] = hit.get("quality")
                row["quality_score"] = hit.get("quality_score")
                row["quality_hint"] = hit.get("quality_hint") or "OCR cascade ile okundu"
                fixed += 1
        out.append(row)
    return out


def extract_source_pages(
    rel: str,
    *,
    page_from: int | None = None,
    page_to: int | None = None,
) -> dict[str, Any]:
    """PDF/txt/docx/görsel — sayfa listesi + kalite (Faz 3)."""
    from ilim_assistant.motorlar.tercume_atolye import split_text_into_pages

    try:
        target, raw = resolve_book_path(rel)
    except ValueError:
        return {"ok": False, "error": "Geçersiz yol"}
    if not target.is_file():
        return {"ok": False, "error": "Dosya yok"}

    ext = target.suffix.lower()
    source_kind = "text"
    pages: list[dict[str, Any]] = []
    meta: dict[str, Any] = {"ext": ext, "read_pipeline": READ_PIPELINE_VERSION}

    if ext == ".pdf":
        try:
            pages, meta = extract_pdf_pages(target, page_from=page_from, page_to=page_to)
        except RuntimeError as exc:
            return {"ok": False, "error": str(exc)}
        source_kind = "pdf"
    elif ext in {".txt", ".md", ".markdown", ".html", ".htm"}:
        try:
            full = target.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            return {"ok": False, "error": str(exc)[:200]}
        for p in split_text_into_pages(full):
            pages.append(
                {
                    "index": p["index"],
                    "text": p["text"],
                    "label": f"Bölüm {int(p['index']) + 1}",
                }
            )
        meta["pages_total"] = len(pages)
    elif ext == ".docx":
        try:
            import docx  # type: ignore
        except ImportError:
            return {"ok": False, "error": "pip install python-docx"}
        try:
            doc = docx.Document(str(target))
            full = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except Exception as exc:
            return {"ok": False, "error": str(exc)[:200]}
        for p in split_text_into_pages(full):
            pages.append(
                {
                    "index": p["index"],
                    "text": p["text"],
                    "label": f"Bölüm {int(p['index']) + 1}",
                }
            )
        meta["pages_total"] = len(pages)
    elif ext in {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}:
        source_kind = "ocr"
        try:
            from PIL import Image
            import pytesseract
        except ImportError:
            return {"ok": False, "error": "OCR için pillow + pytesseract + Tesseract gerekli."}
        try:
            img = Image.open(target)
            from ilim_assistant.motorlar.tercume_ocr_cascade import ocr_pil_image_best

            hit = ocr_pil_image_best(
                img,
                src_lang=os.environ.get("RUZGAR_TERCUME_SRC_LANG", "auto"),
            )
            if not hit.get("ok"):
                return {"ok": False, "error": str(hit.get("error") or "OCR başarısız")}
            raw_text = str(hit.get("text") or "")
            meta["ocr_cascade"] = hit.get("preset")
            meta["ocr_quality_score"] = hit.get("quality_score")
        except Exception as exc:
            return {"ok": False, "error": f"OCR başarısız: {str(exc)[:180]}"}
        for p in split_text_into_pages(raw_text):
            pages.append(
                {
                    "index": p["index"],
                    "text": p["text"],
                    "label": f"OCR bölüm {int(p['index']) + 1}",
                }
            )
        meta["pages_total"] = len(pages)
    elif ext == ".epub":
        from ilim_assistant.motorlar.tercume_ebook_read import chapters_to_pages, read_epub

        hit = read_epub(target)
        if not hit.get("ok"):
            return {"ok": False, "error": str(hit.get("error") or "EPUB okunamadı")}
        pages = chapters_to_pages(list(hit.get("chapters") or []))
        meta.update(
            {
                "ebook_title": hit.get("title") or "",
                "ebook_author": hit.get("author") or "",
                "chapters_read": hit.get("chapters_read"),
                "source_kind": "epub",
            }
        )
        source_kind = "epub"
    elif ext == ".fb2":
        from ilim_assistant.motorlar.tercume_ebook_read import chapters_to_pages, read_fb2

        hit = read_fb2(target)
        if not hit.get("ok"):
            return {"ok": False, "error": str(hit.get("error") or "FB2 okunamadı")}
        pages = chapters_to_pages(list(hit.get("chapters") or []))
        meta.update(
            {
                "ebook_title": hit.get("title") or "",
                "ebook_author": hit.get("author") or "",
                "chapters_read": hit.get("chapters_read"),
                "source_kind": "fb2",
            }
        )
        source_kind = "fb2"
    else:
        return {
            "ok": False,
            "error": f"Okuma pipeline: {ext} henüz desteklenmiyor (pdf/txt/docx/epub/fb2/görsel).",
        }

    if page_from is not None or page_to is not None:
        start = max(0, int(page_from)) if page_from is not None else 0
        end = (
            min(len(pages), int(page_to) + 1)
            if page_to is not None
            else len(pages)
        )
        if start > 0 or end < len(pages):
            pages = pages[start:end]
            meta["page_from"] = start
            meta["page_to"] = start + len(pages) - 1 if pages else start

    pages = enrich_pages(pages, source_kind=source_kind)
    if ext == ".pdf" and source_kind == "pdf":
        pages = _maybe_ocr_weak_pdf_pages(
            pages,
            target,
            src_lang=os.environ.get("RUZGAR_TERCUME_SRC_LANG", "auto"),
        )
    meta.update(summarize_page_quality_meta(pages))
    return {"ok": True, "rel": raw, "pages": pages, "meta": meta}
