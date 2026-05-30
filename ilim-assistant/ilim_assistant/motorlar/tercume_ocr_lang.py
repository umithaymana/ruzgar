# Created by Ümit & Gökçenur
"""Tercüme OCR — Tesseract dil kodları (Arapça / Osmanlıca dahil)."""

from __future__ import annotations

OCR_LANG_VERSION = "tercume-ocr-lang-v2"

# Resmi Tesseract paketinde "ota" yok; Osmanlıca Perso-Arap harfler Arapça (ara) OCR ile okunur.
PRESETS: dict[str, str] = {
    "auto": "tur+eng",
    "tur+eng": "tur+eng",
    "tur": "tur",
    "ara": "ara",
    "ota": "ara+osd",
    "ara+ota": "ara+osd",
    "tur+ara": "tur+ara",
    "tur+ota": "tur+ara",
    "eng": "eng",
}

PRESET_LABELS: dict[str, str] = {
    "auto": "Otomatik (kaynak dile göre)",
    "tur+eng": "Türkçe + İngilizce",
    "tur": "Türkçe",
    "ara": "Arapça",
    "ota": "Osmanlıca (Arapça OCR)",
    "ara+ota": "Arapça + Osmanlıca script",
    "tur+ara": "Türkçe + Arapça",
    "tur+ota": "Türkçe + Arapça (Osmanlıca)",
    "eng": "İngilizce",
}


def resolve_ocr_lang(raw: str, *, src_lang: str = "auto") -> str:
    key = (raw or "auto").strip().lower()
    if key in PRESETS and key != "auto":
        return PRESETS[key]
    sl = (src_lang or "auto").strip().lower()[:2]
    if sl == "ar":
        return "ara+osd"
    if sl == "fa":
        return "fas+ara"
    if sl == "tr":
        return "tur+ara"
    if sl == "en":
        return "eng"
    return PRESETS["auto"]


def ocr_config_for_api() -> dict:
    return {
        "version": OCR_LANG_VERSION,
        "presets": [{"id": k, "label": PRESET_LABELS.get(k, k), "tesseract": v} for k, v in PRESETS.items()],
        "hint": "Osmanlıca metinler Perso-Arap harfle yazılır; resmi Tesseract paketinde ota yok, ara+osd kullanılır.",
    }
