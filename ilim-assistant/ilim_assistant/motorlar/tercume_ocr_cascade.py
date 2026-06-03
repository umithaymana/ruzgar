# Created by Ümit & Gökçenur
"""Tercüme Faz 9 — çoklu OCR dili dene, en iyi kalite skorunu seç."""

from __future__ import annotations

import os
from typing import Any

OCR_CASCADE_VERSION = "tercume-ocr-cascade-v9-faz9-2026-05-31"

_DEFAULT_PRESETS = ("ara+osd", "tur+ara", "tur+eng", "eng", "tur")


def cascade_presets(*, src_lang: str = "auto") -> tuple[str, ...]:
    sl = (src_lang or "auto").strip().lower()[:2]
    if sl == "ar":
        return ("ara+osd", "ara", "tur+ara", "eng")
    if sl == "tr":
        return ("tur+ara", "tur+eng", "tur", "ara+osd", "eng")
    if sl == "fa":
        return ("fas+ara", "ara+osd", "tur+ara", "eng")
    raw = (os.environ.get("RUZGAR_TERCUME_OCR_CASCADE") or "").strip()
    if raw:
        return tuple(p.strip() for p in raw.split(",") if p.strip())
    return _DEFAULT_PRESETS


def ocr_pil_image_best(
    img: Any,
    *,
    src_lang: str = "auto",
    presets: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """PIL Image → en iyi OCR metni + kalite skoru."""
    from ilim_assistant.motorlar.tercume_ocr_clean import clean_ocr_text
    from ilim_assistant.motorlar.tercume_ocr_lang import resolve_ocr_lang
    from ilim_assistant.motorlar.tercume_read_pipeline import assess_page_quality

    try:
        import pytesseract
    except ImportError:
        return {"ok": False, "error": "pytesseract yok"}

    tried: list[dict[str, Any]] = []
    best: dict[str, Any] | None = None

    for preset in presets or cascade_presets(src_lang=src_lang):
        tess = resolve_ocr_lang(preset, src_lang=src_lang)
        try:
            raw = pytesseract.image_to_string(img, lang=tess) or ""
        except Exception as exc:
            tried.append({"preset": preset, "tesseract": tess, "error": str(exc)[:80]})
            continue
        text = clean_ocr_text(raw.strip())
        q = assess_page_quality(text, source_kind="ocr")
        row = {
            "preset": preset,
            "tesseract": tess,
            "quality": q.get("quality"),
            "quality_score": q.get("quality_score"),
            "chars": len(text),
        }
        tried.append(row)
        if best is None or float(q.get("score") or 0) > float(best.get("quality_score") or 0):
            best = {
                "ok": True,
                "text": text,
                "preset": preset,
                "tesseract": tess,
                "quality": q.get("quality"),
                "quality_score": q.get("quality_score"),
                "quality_hint": q.get("hint"),
                "tried": len(tried),
            }

    if not best or not str(best.get("text") or "").strip():
        return {
            "ok": False,
            "error": "OCR cascade boş — görsel kalitesi düşük olabilir",
            "attempts": tried,
            "version": OCR_CASCADE_VERSION,
        }
    best["attempts"] = tried
    best["version"] = OCR_CASCADE_VERSION
    return best


def ocr_pdf_page(
    pdf_path: str,
    page_index: int,
    *,
    src_lang: str = "auto",
) -> dict[str, Any]:
    """Tek PDF sayfası OCR (pdf2image gerekir)."""
    if os.environ.get("RUZGAR_TERCUME_PDF_OCR", "0").strip().lower() not in (
        "1",
        "true",
        "yes",
    ):
        return {"ok": False, "skipped": True, "reason": "RUZGAR_TERCUME_PDF_OCR kapalı"}
    try:
        from pdf2image import convert_from_path
    except ImportError:
        return {"ok": False, "error": "pip install pdf2image (+ poppler)"}

    page_no = max(1, int(page_index) + 1)
    try:
        images = convert_from_path(
            pdf_path,
            first_page=page_no,
            last_page=page_no,
            dpi=int(os.environ.get("RUZGAR_TERCUME_OCR_DPI", "200")),
        )
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:180]}
    if not images:
        return {"ok": False, "error": "Sayfa görseli üretilemedi"}
    hit = ocr_pil_image_best(images[0], src_lang=src_lang)
    hit["page_index"] = page_index
    return hit


def ocr_pdf_page_via_pymupdf(
    pdf_path: str,
    page_index: int,
    *,
    src_lang: str = "auto",
    dpi: int | None = None,
) -> dict[str, Any]:
    """PDF tek sayfa OCR — PyMuPDF ile rasterize (pdf2image gerekmez)."""
    try:
        import fitz
        from PIL import Image
    except ImportError:
        return {
            "ok": False,
            "error": "OCR için: pip install pymupdf pillow pytesseract (+ Tesseract kurulumu)",
        }

    page_no = max(1, int(page_index) + 1)
    dpi_n = dpi or int(os.environ.get("RUZGAR_TERCUME_OCR_DPI", "180"))
    try:
        doc = fitz.open(str(pdf_path))
    except Exception as exc:
        return {"ok": False, "error": f"PDF açılamadı: {str(exc)[:120]}"}

    try:
        if len(doc) < 1:
            return {"ok": False, "error": "PDF boş"}
        idx = min(page_no, len(doc)) - 1
        pg = doc[idx]
        zoom = max(72, dpi_n) / 72.0
        pix = pg.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    except Exception as exc:
        return {"ok": False, "error": f"Sayfa görüntüsü: {str(exc)[:120]}"}
    finally:
        doc.close()

    hit = ocr_pil_image_best(img, src_lang=src_lang)
    hit["page_index"] = idx
    hit["page"] = idx + 1
    hit["engine"] = "pymupdf+tesseract"
    return hit
