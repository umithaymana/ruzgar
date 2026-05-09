# Created by Ümit & Gökçenur
"""Osmanlıca OCR — arşiv sayfa görselleri ve matbu metinler için temel modül (ileride Tesseract / özel model)."""

from __future__ import annotations

import os
from pathlib import Path


def osmanlica_ocr_enabled() -> bool:
    return os.environ.get("RUZGAR_OSMANLICA_OCR", "0").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def transcribe_legacy_page(
    image_path: str | Path | None,
    *,
    fallback_text: str | None = None,
) -> str:
    """
    Yer tutucu: görüntüden metin çıkarma henüz bağlanmadı.
    `fallback_text` OCR kapalıyken veya hata halinde kullanılacak düz metin.
    """
    if not osmanlica_ocr_enabled():
        return (fallback_text or "").strip()
    # İleride: örn. paddleocr / tesseract + eski yazı eğitimi
    _ = image_path
    return (fallback_text or "").strip()
