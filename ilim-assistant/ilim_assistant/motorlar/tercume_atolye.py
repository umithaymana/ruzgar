# Created by Ümit & Gökçenur
"""Tercüme atölyesi — dosya açma, sayfalama, çeviri promptu, çırak günlüğü."""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any

ATOLYE_VERSION = "tercume-atolye-v2-2026-05-31"
_MAX_TRANSLATE_UNIT_CHARS = 500
_MULTILINE_MAX_LINES = 32
_MULTILINE_MAX_TOTAL = 8000

_EN_LEAK_WORDS = frozenset(
    {
        "something",
        "went",
        "wrong",
        "the",
        "when",
        "that",
        "this",
        "with",
        "from",
        "have",
        "been",
        "even",
        "broke",
        "car",
        "london",
    }
)
_EN_TOKEN_RE = re.compile(r"\b[a-z]{3,}\b", re.IGNORECASE)
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


def tercume_pdf_max_pages() -> int:
    """0 / all = tüm sayfalar (çok ciltli kitap)."""
    raw = os.environ.get("RUZGAR_TERCUME_PDF_MAX_PAGES", "5000").strip().lower()
    if raw in ("0", "all", "none", "unlimited"):
        return 999_999
    try:
        return max(1, int(raw))
    except ValueError:
        return 5000


def tercume_chunk_max_chars() -> int:
    try:
        return max(2000, int(os.environ.get("RUZGAR_TERCUME_CHUNK_CHARS", "24000")))
    except ValueError:
        return 24000


def local_first_search_enabled() -> bool:
    return os.environ.get("RUZGAR_TERCUME_LOCAL_FIRST", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def grammar_directive(tgt_lang: str) -> str:
    code = (tgt_lang or "en").strip().lower()[:2]
    return _GRAMMAR_HINTS.get(code, "Hedef dilin imla ve dil bilgisi kurallarına tam uy.")


def _tercume_repo_root() -> Path:
    try:
        from ilim_assistant.motorlar.programlama_motoru import repo_root

        r = repo_root(None)
        if r:
            return Path(r)
    except Exception:
        pass
    return Path(__file__).resolve().parents[2]


def extract_book_full_text(rel: str) -> dict[str, Any]:
    """Tam kitap metni (PDF sayfa sınırı tercume_pdf_max_pages ile)."""
    raw = (rel or "").strip().replace("\\", "/").lstrip("/")
    if not raw:
        return {"ok": False, "error": "rel boş"}
    root = _tercume_repo_root()
    target = (root / raw.replace("/", os.sep)).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError:
        return {"ok": False, "error": "Geçersiz yol"}
    if not target.is_file():
        return {"ok": False, "error": "Dosya yok"}

    ext = target.suffix.lower()
    parts: list[str] = []

    if ext == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError:
            return {"ok": False, "error": "pip install pypdf"}
        reader = PdfReader(str(target))
        cap = min(len(reader.pages), tercume_pdf_max_pages())
        for i in range(cap):
            try:
                t = (reader.pages[i].extract_text() or "").strip()
            except Exception:
                t = ""
            if t:
                parts.append(t)
    elif ext in {".txt", ".md", ".markdown", ".html", ".htm"}:
        try:
            full = target.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            return {"ok": False, "error": str(exc)[:200]}
        parts = [p["text"] for p in split_text_into_pages(full) if str(p.get("text") or "").strip()]
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
        parts = [full] if full.strip() else []
    else:
        return {"ok": False, "error": f"Toplu çeviri: {ext} henüz desteklenmiyor (pdf/txt/docx)."}

    text = "\n\n".join(parts).strip()
    if not text:
        return {"ok": False, "error": "Metin çıkarılamadı (boş PDF veya taranmış sayfa — OCR gerekebilir)."}
    return {"ok": True, "rel": raw, "text": text, "chars": len(text)}


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


def build_translation_system_prompt(
    tgt_lang: str,
    *,
    strict: bool = False,
    glossary_block: str = "",
) -> str:
    label = _LANG_LABEL.get(tgt_lang, tgt_lang)
    gram = grammar_directive(tgt_lang)
    strict_block = ""
    if strict:
        strict_block = (
            "ZORUNLU: Kaynaktaki her cümle ve satırın TAMAMINI hedef dilde yaz.\n"
            "Kaynak dilde kelime bırakma (özel ad / evrensel kısaltma hariç).\n"
            "Eksik çeviri, özet veya karışık dil yasak.\n"
        )
    body = (
        "Sen profesyonel bir çevirmensin. Yalnızca hedef dilde çeviri metnini ver.\n"
        f"Hedef dil: {label}.\n"
        f"Kural: {gram}\n"
        f"{strict_block}"
        "Kaynak anlamı bire bir aktar; özetleme veya yorum ekleme.\n"
        "Satır sonlarını koru; her satır ayrı cümle ise ayrı çevir.\n"
        "Başlık ve paragraf yapısını koru.\n"
    )
    if glossary_block:
        body += f"\n{glossary_block.strip()}\n"
    body += f"{ATOLYE_VERSION}\n"
    return body


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


def split_translation_units(text: str) -> list[str]:
    """Kısa çok satırlı metinleri satır satır çevir (eksik satır riskini azaltır)."""
    raw = (text or "").replace("\r\n", "\n").strip()
    if not raw:
        return []
    lines = [ln.strip() for ln in raw.split("\n") if ln.strip()]
    if (
        len(lines) >= 2
        and len(lines) <= _MULTILINE_MAX_LINES
        and len(raw) <= _MULTILINE_MAX_TOTAL
        and all(len(ln) <= _MAX_TRANSLATE_UNIT_CHARS for ln in lines)
    ):
        return lines
    return [raw]


def _target_lang_code(tgt_lang: str) -> str:
    return (tgt_lang or "en").strip().lower()[:2] or "en"


def translation_leaked_source_language(output: str, tgt_lang: str) -> bool:
    """Hedef Türkçe/Arapça vb. iken çıktıda belirgin İngilizce sızıntı."""
    code = _target_lang_code(tgt_lang)
    if code in ("en",):
        return False
    out = (output or "").strip()
    if not out:
        return False
    tokens = [t.lower() for t in _EN_TOKEN_RE.findall(out)]
    if not tokens:
        return False
    leak = [t for t in tokens if t in _EN_LEAK_WORDS]
    if leak:
        return True
    if len(tokens) >= 4 and code == "tr":
        return True
    return False


def _llm_translate(system: str, user: str, *, max_tokens: int = 4000) -> str:
    from ilim_assistant.motorlar.tercume_llm import translate_completion

    res = translate_completion(system, user, max_tokens=max_tokens)
    if res.get("ok"):
        return str(res.get("text") or "").strip()
    code = str(res.get("error_code") or "translate_failed")
    hint = str(res.get("hint_tr") or res.get("error") or "Çeviri başarısız.")
    raise RuntimeError(f"{code}: {hint}")


def _build_faz4_context(
    unit: str,
    *,
    source_file: str,
    tgt_lang: str,
) -> tuple[str, dict[str, Any]]:
    from ilim_assistant.motorlar.tercume_context_rag import archive_context_snippets
    from ilim_assistant.motorlar.tercume_glossary import active_glossary_sets, glossary_directive
    from ilim_assistant.motorlar.tercume_translate_memory import (
        consistency_block,
        seed_pairs_from_glossary,
    )

    seed_pairs_from_glossary(source_file, unit, tgt_lang=tgt_lang)
    gloss = glossary_directive(unit, source_file=source_file, tgt_lang=tgt_lang, max_terms=16)
    mem = consistency_block(source_file, tgt_lang=tgt_lang)
    rag, rag_hits = archive_context_snippets(unit, source_file=source_file)
    blocks = [b for b in (gloss, mem, rag) if b]
    meta = {
        "glossary_sets": active_glossary_sets(unit, source_file),
        "rag_snippets": len(rag_hits),
        "memory_active": bool(mem),
    }
    return "\n\n".join(blocks), meta


def _translate_unit(
    unit: str,
    *,
    src_lang: str,
    tgt_lang: str,
    source_file: str,
    page_index: int | None,
    line_note: str = "",
) -> str:
    context_block, _ctx = _build_faz4_context(
        unit,
        source_file=source_file,
        tgt_lang=tgt_lang,
    )
    system = build_translation_system_prompt(tgt_lang, strict=True, glossary_block=context_block)
    user = build_translation_user_prompt(
        unit,
        src_lang=src_lang,
        tgt_lang=tgt_lang,
        source_file=source_file,
        page_index=page_index,
    )
    if line_note:
        user = f"{line_note}\n\n{user}"
    out = _llm_translate(system, user)
    if translation_leaked_source_language(out, tgt_lang):
        retry_sys = (
            build_translation_system_prompt(tgt_lang, strict=True, glossary_block=context_block)
            + "\nÖnceki yanıt yetersizdi — kalan yabancı kelimeleri de çevir.\n"
        )
        retry_user = (
            f"Hedef dil: {_LANG_LABEL.get(tgt_lang, tgt_lang)}\n"
            f"Yalnızca hedef dilde, eksiksiz çevir:\n\n{unit}"
        )
        out2 = _llm_translate(retry_sys, retry_user)
        if out2:
            out = out2
    return out


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
        return {"ok": False, "error": "Metin boş", "error_code": "empty_text"}
    if len(chunk) > tercume_chunk_max_chars():
        chunk = chunk[: tercume_chunk_max_chars()] + "\n\n… [parça kısaltıldı]"
    units = split_translation_units(chunk)
    if not units:
        return {"ok": False, "error": "Metin boş", "error_code": "empty_text"}
    _ctx_meta: dict[str, Any] = {}
    try:
        if len(units) == 1:
            _pre_ctx, _ctx_meta = _build_faz4_context(
                units[0],
                source_file=source_file,
                tgt_lang=tgt_lang,
            )
            out = _translate_unit(
                units[0],
                src_lang=src_lang,
                tgt_lang=tgt_lang,
                source_file=source_file,
                page_index=page_index,
            )
            mode = "block"
        else:
            parts: list[str] = []
            for i, unit in enumerate(units):
                if i == 0:
                    _, _ctx_meta = _build_faz4_context(
                        unit,
                        source_file=source_file,
                        tgt_lang=tgt_lang,
                    )
                parts.append(
                    _translate_unit(
                        unit,
                        src_lang=src_lang,
                        tgt_lang=tgt_lang,
                        source_file=source_file,
                        page_index=page_index,
                        line_note=f"Satır {i + 1}/{len(units)} — yalnızca bu satırı çevir.",
                    )
                )
            out = "\n".join(parts)
            mode = "multiline"
    except RuntimeError as exc:
        msg = str(exc)
        if ":" in msg:
            code, _, hint = msg.partition(":")
            return {
                "ok": False,
                "error": hint.strip() or msg,
                "error_code": code.strip(),
                "hint_tr": hint.strip(),
            }
        return {"ok": False, "error": msg[:200], "error_code": "translate_failed"}
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:200], "error_code": "translate_error"}
    if not out:
        return {
            "ok": False,
            "error": "LLM yanıt vermedi.",
            "error_code": "empty_response",
            "hint_tr": "Ollama serve ve model pull kontrol edin (llama3.1:8b).",
        }
    from ilim_assistant.motorlar.tercume_translate_memory import record_translation

    record_translation(
        source_file,
        source_text=chunk,
        translated=out,
        tgt_lang=tgt_lang,
    )
    from ilim_assistant.motorlar.tercume_translate_quality import score_translation

    quality = score_translation(chunk, out, tgt_lang=tgt_lang)
    return {
        "ok": True,
        "text": out,
        "tgt_lang": tgt_lang,
        "mode": mode,
        "units": len(units),
        "glossary_sets": _ctx_meta.get("glossary_sets") or [],
        "rag_snippets": _ctx_meta.get("rag_snippets") or 0,
        "memory_active": _ctx_meta.get("memory_active", False),
        "translate_faz4": True,
        "quality": quality,
    }


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
    from ilim_assistant.motorlar.tercume_ocr_lang import ocr_config_for_api

    pdf_cap = tercume_pdf_max_pages()
    return {
        "version": ATOLYE_VERSION,
        "analyst_version": "tercume-analyst-v5-faz5-2026-05-31",
        "analyst_routes": [
            "/api/tercume/analyze",
            "/api/tercume/pipeline",
            "/api/tercume/import-from-search",
            "/api/tercume/pipeline-start",
            "/api/tercume/jobs/{job_id}",
            "/api/tercume/pipeline-cancel",
        ],
        "batch_routes": [
            "/api/tercume/batch-start",
            "/api/tercume/batch-status",
            "/api/tercume/batch-cancel",
        ],
        "read_routes": [
            "/api/tercume/read-start",
            "/api/tercume/read-status",
            "/api/tercume/read-cancel",
        ],
        "read_pipeline_version": "tercume-read-pipeline-v3-faz3-2026-05-31",
        "translate_faz4": {
            "version": "tercume-translate-faz4-2026-05-31",
            "glossary": True,
            "archive_rag": True,
            "chunk_memory": True,
            "env": {
                "RUZGAR_TERCUME_RAG": "1",
                "RUZGAR_TERCUME_MEMORY": "1",
            },
        },
        "analyst_faz5": {
            "version": "tercume-analyst-job-v5-faz5-2026-05-31",
            "import_from_search": True,
            "background_pipeline": True,
            "job_resolver": "/api/tercume/jobs/{job_id}",
        },
        "bridge_faz6": {
            "version": "tercume-hafiza-bridge-v6-faz6-2026-05-31",
            "genel_hafiza": True,
            "knowledge_rag": True,
            "routes": [
                "/api/tercume/bridge-preview",
                "/api/tercume/bridge-save",
                "/api/tercume/bridge-log",
            ],
            "env": {
                "RUZGAR_TERCUME_BRIDGE": "1",
                "RUZGAR_TERCUME_BRIDGE_KNOWLEDGE": "1",
            },
        },
        "report_faz7": {
            "version": "tercume-analyst-report-v7-faz7-2026-05-31",
            "markdown_report": True,
            "auto_import": True,
            "routes": [
                "/api/tercume/report",
                "/api/tercume/report-start",
            ],
            "output_dir": "ilim-assistant/arsiv/tercume-output/reports",
            "env": {"RUZGAR_TERCUME_REPORT": "1"},
        },
        "super_faz8": {
            "version": "tercume-super-analyst-v8-faz8-2026-05-31",
            "chain": ["analyze", "import", "read", "translate", "report"],
            "routes": ["/api/tercume/super-start"],
            "env": {"RUZGAR_TERCUME_SUPER": "1"},
        },
        "preflight_faz9": {
            "version": "tercume-preflight-v9-faz9-2026-05-31",
            "routes": ["/api/tercume/preflight"],
            "ocr_cascade": True,
            "translate_quality_score": True,
            "env": {
                "RUZGAR_TERCUME_PDF_OCR": "0",
                "RUZGAR_TERCUME_OCR_FIX_PAGES": "5",
            },
        },
        "ocr_lang": ocr_config_for_api(),
        "translation_policy": {
            "local_first_search": local_first_search_enabled(),
            "pdf_max_pages": pdf_cap if pdf_cap < 999_999 else "all",
            "chunk_max_chars": tercume_chunk_max_chars(),
            "glossary": True,
            "modes": {
                "single": "Kutudaki metin — kısa parça, birkaç satır",
                "page": "Dosyayı aç — sayfa sayfa (PDF gerçek sayfa)",
                "full": "Dosyayı aç — tamamı (uzun sürer, Durdur ile kesilir)",
            },
            "multi_volume": "Her cilt ayrı dosya — sırayla aç, Tamamı modu ile çevir",
            "langs": "Kaynak otomatik veya seçili; hedef dili siz seçersiniz",
        },
        "book_extensions": list(BOOK_EXTENSIONS),
        "image_extensions": list(IMAGE_EXTENSIONS),
        "output_formats": ["txt", "md", "html"],
        "default_work_root": os.environ.get(
            "RUZGAR_TERCUME_WORK_ROOT",
            "ilim-assistant/arsiv",
        ),
        "langs": _LANG_LABEL,
        "readiness_faz13": {
            "version": "tercume-readiness-v13-2026-06-01",
            "route": "/api/tercume/readiness",
        },
    }
