# Created by Ümit & Gökçenur
"""Tercüme OCR — Tesseract kurulum durumu (bulut + yerel)."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

OCR_RUNTIME_VERSION = "tercume-ocr-runtime-v2"
_REQUIRED_LANGS = ("ara", "tur", "eng")


def _repo_tessdata() -> Path | None:
    try:
        from ilim_assistant.motorlar.programlama_motoru import repo_root

        r = repo_root(None)
        if r:
            hit = Path(r) / ".ruzgar" / "tessdata"
            if hit.is_dir():
                return hit
    except Exception:
        pass
    return None


def _tessdata_dirs() -> list[Path]:
    out: list[Path] = []
    repo_td = _repo_tessdata()
    if repo_td:
        out.append(repo_td)
    env = (os.environ.get("TESSDATA_PREFIX") or "").strip()
    if env:
        p = Path(env)
        out.append(p if p.name == "tessdata" else p / "tessdata")
    exe = shutil.which("tesseract")
    if exe:
        base = Path(exe).resolve().parent
        out.append(base / "tessdata")
    for guess in (
        Path("/usr/share/tesseract-ocr/5/tessdata"),
        Path("/usr/share/tesseract-ocr/4.00/tessdata"),
        Path(r"C:\Program Files\Tesseract-OCR\tessdata"),
        Path(r"C:\Program Files (x86)\Tesseract-OCR\tessdata"),
    ):
        if guess.is_dir():
            out.append(guess)
    seen: set[str] = set()
    uniq: list[Path] = []
    for p in out:
        key = str(p.resolve()) if p.exists() else str(p)
        if key not in seen:
            seen.add(key)
            uniq.append(p)
    return uniq


def _lang_files() -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    for td in _tessdata_dirs():
        if not td.is_dir():
            continue
        for code in _REQUIRED_LANGS:
            hit = td / f"{code}.traineddata"
            if hit.is_file():
                found.setdefault(code, []).append(str(hit))
    return found


def ocr_runtime_available() -> bool:
    try:
        import pytesseract  # type: ignore

        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def ocr_installed_langs() -> list[str]:
    if not ocr_runtime_available():
        return []
    try:
        import pytesseract  # type: ignore

        return sorted(pytesseract.get_languages(config="") or [])
    except Exception:
        return []


def ocr_runtime_status() -> dict[str, Any]:
    langs = ocr_installed_langs()
    files = _lang_files()
    has = {code: code in langs or code in files for code in _REQUIRED_LANGS}
    ready = ocr_runtime_available() and has.get("ara", False)
    missing = [c for c in _REQUIRED_LANGS if not has.get(c)]
    hint = "Bulutta OCR sunucuda calisir; kullanici kurmaz."
    if not ocr_runtime_available():
        hint = "Tesseract veya pytesseract eksik — Ruzgar_OCR_Kur.bat veya bulut Docker imaji."
    elif missing:
        hint = f"Eksik OCR dil paketi: {', '.join(missing)}. Ruzgar_OCR_Kur.bat ile tamamlayin."
    elif ready:
        hint = "Arapca OCR hazir (Osmanlica script icin ara kullanilir)."
    return {
        "version": OCR_RUNTIME_VERSION,
        "available": ocr_runtime_available(),
        "cloud_ready": ready,
        "arabic_ottoman_ready": ready,
        "langs_detected": langs,
        "lang_files": {k: v[0] for k, v in files.items()},
        "missing_langs": missing,
        "tessdata_dirs": [str(p) for p in _tessdata_dirs() if p.is_dir()],
        "hint": hint,
    }
