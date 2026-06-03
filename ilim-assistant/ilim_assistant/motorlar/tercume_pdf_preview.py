# Tercüme — PDF sayfa önizleme (PNG, isteğe bağlı PyMuPDF)
from __future__ import annotations

import base64
from pathlib import Path
from typing import Any


def pymupdf_available() -> bool:
    try:
        import fitz  # noqa: F401

        return True
    except ImportError:
        return False


def render_pdf_page_png_b64(
    target: Path,
    *,
    page: int = 1,
    dpi: int = 110,
    max_side_px: int = 1400,
) -> dict[str, Any]:
    """
    Tek PDF sayfasını PNG (base64) olarak döner.
    page: 1 tabanlı sayfa numarası.
    """
    if not pymupdf_available():
        return {
            "ok": False,
            "error": "PDF önizleme için: pip install pymupdf",
            "engine": None,
        }
    if target.suffix.lower() != ".pdf":
        return {"ok": False, "error": "Dosya PDF değil.", "engine": None}
    if not target.is_file():
        return {"ok": False, "error": "Dosya bulunamadı.", "engine": None}

    import fitz

    page_n = max(1, int(page))
    dpi_n = max(72, min(200, int(dpi)))
    try:
        doc = fitz.open(str(target))
    except Exception as exc:
        return {"ok": False, "error": f"PDF açılamadı: {exc}", "engine": "pymupdf"}

    try:
        n_pages = len(doc)
        if n_pages < 1:
            return {"ok": False, "error": "PDF boş.", "engine": "pymupdf", "pages_total": 0}
        idx = min(page_n, n_pages) - 1
        pg = doc[idx]
        zoom = dpi_n / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = pg.get_pixmap(matrix=mat, alpha=False)
        if max(pix.width, pix.height) > max_side_px:
            scale = max_side_px / float(max(pix.width, pix.height))
            mat2 = fitz.Matrix(zoom * scale, zoom * scale)
            pix = pg.get_pixmap(matrix=mat2, alpha=False)
        png = pix.tobytes("png")
        b64 = base64.b64encode(png).decode("ascii")
        return {
            "ok": True,
            "engine": "pymupdf",
            "page": idx + 1,
            "pages_total": n_pages,
            "width": pix.width,
            "height": pix.height,
            "image_base64": b64,
            "media_type": "image/png",
        }
    except Exception as exc:
        return {"ok": False, "error": f"Sayfa işlenemedi: {exc}", "engine": "pymupdf"}
    finally:
        doc.close()
