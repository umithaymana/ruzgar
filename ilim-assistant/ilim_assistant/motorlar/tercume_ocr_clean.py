# Created by Ümit & Gökçenur
"""OCR sonrası hafif temizleme — tercüme atölyesi."""

from __future__ import annotations

import re

OCR_CLEAN_VERSION = "tercume-ocr-clean-v1"


def clean_ocr_text(text: str) -> str:
    """Satır sonu tire, fazla boşluk, kontrol karakterleri."""
    t = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    if not t.strip():
        return t

    # kelime- \n devam → kelimedevam
    t = re.sub(r"(\w)-\n(\w)", r"\1\2", t)
    # yalnız harf kırılımları (Arap/Latin)
    t = re.sub(r"([\u0600-\u06FFa-zA-Z])-\n([\u0600-\u06FFa-zA-Z])", r"\1\2", t)

    t = re.sub(r"[ \t]+\n", "\n", t)
    t = re.sub(r"\n[ \t]+", "\n", t)
    t = re.sub(r"[ \t]{2,}", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)

    # OCR sık hata: l / I / | karışıklığı — dokunma (riskli); sadece boş satır trim
    lines = [ln.strip() for ln in t.split("\n")]
    t = "\n".join(lines)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()
