# Created by Ümit & Gökçenur
"""Tercüme OCR — Tesseract dil kodları (Arapça / Osmanlıca dahil)."""

from __future__ import annotations

OCR_LANG_VERSION = "tercume-ocr-lang-v1"

# Tesseract lang kodları (kurulumda paket gerekir: ara, ota, tur, …)
PRESETS: dict[str, str] = {
    "auto": "tur+eng",
    "tur+eng": "tur+eng",
    "tur": "tur",
    "ara": "ara",
    "ota": "ota",
    "ara+ota": "ara+ota",
    "tur+ara": "tur+ara",
    "tur+ota": "tur+ota",
    "eng": "eng",
}

PRESET_LABELS: dict[str, str] = {
    "auto": "Otomatik (kaynak dile göre)",
    "tur+eng": "Türkçe + İngilizce",
    "tur": "Türkçe",
    "ara": "Arapça",
    "ota": "Osmanlıca (ota)",
    "ara+ota": "Arapça + Osmanlıca",
    "tur+ara": "Türkçe + Arapça",
    "tur+ota": "Türkçe + Osmanlıca",
    "eng": "İngilizce",
}


def resolve_ocr_lang(raw: str, *, src_lang: str = "auto") -> str:
    key = (raw or "auto").strip().lower()
    if key in PRESETS and key != "auto":
        return PRESETS[key]
    sl = (src_lang or "auto").strip().lower()[:2]
    if sl == "ar":
        return "ara+ota"
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
        "hint": "Osmanlıca için Tesseract ota dil paketi kurulu olmalı.",
    }
