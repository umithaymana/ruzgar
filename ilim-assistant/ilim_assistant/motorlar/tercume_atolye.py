# Created by Ümit & Gökçenur
"""Tercüme atölyesi — dosya açma, sayfalama, çeviri promptu, çırak günlüğü."""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any

ATOLYE_VERSION = "tercume-atolye-v2-2026-05-29"
_APPRENTICE_FILE = "tercume_apprentice.jsonl"
_MAX_APPRENTICE = 200

BOOK_EXTENSIONS = (
    ".pdf",
    ".docx",
    ".epub",
    ".fb2",
    ".mobi",
    ".azw",
    ".azw3",
    ".kfx",
    ".djvu",
    ".djv",
    ".rtf",
    ".txt",
    ".md",
    ".markdown",
    ".html",
    ".htm",
    ".srt",
    ".vtt",
)
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff")

_LANG_LABEL = {
    "auto": "Otomatik",
    "tr": "Türkçe",
    "en": "İngilizce",
    "ar": "Arapça",
    "de": "Almanca",
    "fr": "Fransızca",
    "fa": "Farsça",
    "ru": "Rusça",
}

_GRAMMAR_HINTS: dict[str, str] = {
    "tr": "Türkçe imla ve noktalama (TDK çizgisine yakın), özel adları koru.",
    "en": "Standard English spelling and punctuation (US/UK tutarlı tek seçenek).",
    "ar": "Modern Standard Arabic; hareke ekleme unless source has them.",
    "de": "Neue deutsche Rechtschreibung; Substantive groß.",
    "fr": "Orthographe française; espaces avant : ; ? !",
    "fa": "Persian script; ی عربی kullanma.",
    "ru": "Russian orthography; ё where standard.",
}


def grammar_directive(tgt_lang: str) -> str:
    code = (tgt_lang or "en").strip().lower()[:2]
    return _GRAMMAR_HINTS.get(code, "Hedef dilin imla ve dil bilgisi kurallarına tam uy.")


def is_book_extension(path: str) -> bool:
    low = (path or "").lower()
    return low.endswith(BOOK_EXTENSIONS) or low.endswith(IMAGE_EXTENSIONS)


def split_text_into_pages(text: str, *, max_chars: int = 3200) -> list[dict[str, Any]]:
    raw = (text or "").replace("\r\n", "\n")
    if not raw.strip():
        return []
    if "\f" in raw:
        parts = [p.strip() for p in raw.split("\f") if p.strip()]
        return [{"index": i, "text": p} for i, p in enumerate(parts)]
    marker_re = re.compile(
        r"(?:^|\n)(?:---+\s*sayfa\s*(\d+)\s*---+|(?:\f|Page\s+(\d+)))",
        re.I | re.M,
    )
    if marker_re.search(raw):
        chunks = marker_re.split(raw)
        pages: list[dict[str, Any]] = []
        buf: list[str] = []
        idx = 0
        for part in chunks:
            if part is None:
                continue
            if isinstance(part, str) and part.strip().isdigit():
                if buf:
                    pages.append({"index": idx, "text": "".join(buf).strip()})
                    idx += 1
                    buf = []
                continue
            if part:
                buf.append(str(part))
        if buf:
            pages.append({"index": idx, "text": "".join(buf).strip()})
        if pages:
            return pages
    pages = []
    start = 0
    idx = 0
    while start < len(raw):
        end = min(len(raw), start + max_chars)
        if end < len(raw):
            cut = raw.rfind("\n\n", start, end)
            if cut > start + max_chars // 2:
                end = cut
        chunk = raw[start:end].strip()
        if chunk:
            pages.append({"index": idx, "text": chunk})
            idx += 1
        start = end if end > start else start + max_chars
    return pages or [{"index": 0, "text": raw.strip()}]


def build_translation_system_prompt(tgt_lang: str) -> str:
    label = _LANG_LABEL.get(tgt_lang, tgt_lang)
    gram = grammar_directive(tgt_lang)
    return (
        "Sen profesyonel bir çevirmensin. Yalnızca hedef dilde çeviri metnini ver.\n"
        f"Hedef dil: {label}.\n"
        f"Kural: {gram}\n"
        "Kaynak anlamı bire bir aktar; özetleme veya yorum ekleme.\n"
        "Başlık ve paragraf yapısını koru.\n"
        f"{ATOLYE_VERSION}\n"
    )


def build_translation_user_prompt(
    chunk: str,
    *,
    src_lang: str,
    tgt_lang: str,
    source_file: str = "",
    page_index: int | None = None,
) -> str:
    src_l = _LANG_LABEL.get(src_lang, src_lang or "Otomatik")
    extra = ""
    if source_file:
        extra += f"\nKaynak dosya: {source_file}"
    if page_index is not None:
        extra += f"\nBölüm/sayfa: {page_index + 1}"
    return (
        f"Kaynak dil: {src_l}\n"
        f"Çevir (yalnızca hedef dilde çıktı):{extra}\n\n---\n\n{chunk}"
    )


def translate_chunk(
    text: str,
    *,
    src_lang: str = "auto",
    tgt_lang: str = "en",
    source_file: str = "",
    page_index: int | None = None,
) -> dict[str, Any]:
    chunk = (text or "").strip()
    if not chunk:
        return {"ok": False, "error": "Metin boş"}
    if len(chunk) > 24_000:
        chunk = chunk[:24_000] + "\n\n… [parça kısaltıldı]"
    system = build_translation_system_prompt(tgt_lang)
    user = build_translation_user_prompt(
        chunk,
        src_lang=src_lang,
        tgt_lang=tgt_lang,
        source_file=source_file,
        page_index=page_index,
    )
    try:
        from ilim_assistant.ruzgar_egitim_anlama import _llm_complete

        out = (_llm_complete(system, user, max_tokens=4000) or "").strip()
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:200]}
    if not out:
        return {"ok": False, "error": "LLM yanıt vermedi (Ollama/bulut kontrol edin)."}
    return {"ok": True, "text": out, "tgt_lang": tgt_lang}


def _apprentice_path(workspace_root: str | Path | None) -> Path | None:
    try:
        from ilim_assistant.motorlar.programlama_motoru import repo_root

        root = repo_root(workspace_root)
        if root is None:
            return None
        d = root / ".ruzgar"
        d.mkdir(parents=True, exist_ok=True)
        return d / _APPRENTICE_FILE
    except Exception:
        return None


def append_apprentice_log(
    workspace_root: str | Path | None,
    entry: dict[str, Any],
) -> None:
    """Programlama motorunun ileride okuyabileceği kısa ders satırı."""
    path = _apprentice_path(workspace_root)
    if path is None:
        return
    row = {
        "ts": time.time(),
        "version": ATOLYE_VERSION,
        **entry,
    }
    try:
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        lines = path.read_text(encoding="utf-8").splitlines()
        if len(lines) > _MAX_APPRENTICE:
            path.write_text("\n".join(lines[-_MAX_APPRENTICE:]) + "\n", encoding="utf-8")
    except Exception:
        pass


def read_apprentice_log(workspace_root: str | Path | None, *, limit: int = 12) -> list[dict[str, Any]]:
    path = _apprentice_path(workspace_root)
    if path is None or not path.is_file():
        return []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
        out: list[dict[str, Any]] = []
        for line in lines[-limit:]:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return out
    except Exception:
        return []


def workbench_config() -> dict[str, Any]:
    return {
        "version": ATOLYE_VERSION,
        "book_extensions": list(BOOK_EXTENSIONS),
        "image_extensions": list(IMAGE_EXTENSIONS),
        "output_formats": ["txt", "md", "html"],
        "default_work_root": os.environ.get(
            "RUZGAR_TERCUME_WORK_ROOT",
            "ilim-assistant/arsiv",
        ),
        "langs": _LANG_LABEL,
    }
