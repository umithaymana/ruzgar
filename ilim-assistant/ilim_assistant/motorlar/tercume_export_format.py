# Created by Ümit & Gökçenur
"""Tercüme Faz 14E — md/html çıktı biçimlendirme."""

from __future__ import annotations

import html
import re
from typing import Any

EXPORT_FORMAT_VERSION = "tercume-export-format-v14e-2026-05-29"


def _title_from_rel(source_rel: str) -> str:
    raw = (source_rel or "").strip().replace("\\", "/")
    leaf = raw.split("/")[-1] if raw else ""
    stem = re.sub(r"\.[^.]+$", "", leaf) or "Çeviri"
    return stem.replace("_", " ").strip() or "Çeviri"


def _looks_like_heading(para: str) -> bool:
    p = para.strip()
    if not p or len(p) > 96 or "\n" in p:
        return False
    if p.endswith((".", "?", "!", ":", "؛", "。")):
        return False
    if len(p.split()) > 14:
        return False
    return True


def format_export_body(
    text: str,
    fmt: str,
    *,
    title: str = "",
    source_rel: str = "",
    tgt_lang: str = "tr",
) -> str:
    """Ham çeviri metnini md veya html belgeye sar."""
    body = (text or "").strip()
    if not body:
        return ""
    code = (fmt or "txt").strip().lower()
    if code not in ("md", "html"):
        return body + ("\n" if not body.endswith("\n") else "")

    doc_title = (title or "").strip() or _title_from_rel(source_rel)
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]

    if code == "md":
        lines = [f"# {doc_title}", ""]
        if source_rel:
            lines.append(f"*Kaynak:* `{source_rel.replace('`', '')}`  ")
            lines.append(f"*Hedef dil:* {tgt_lang}")
            lines.append("")
        for para in paragraphs:
            if _looks_like_heading(para):
                lines.append(f"## {para}")
            else:
                lines.append(para)
            lines.append("")
        return "\n".join(lines).strip() + "\n"

    parts: list[str] = []
    for para in paragraphs:
        if _looks_like_heading(para):
            parts.append(f"<h2>{html.escape(para)}</h2>")
        else:
            inner = html.escape(para).replace("\n", "<br>\n")
            parts.append(f"<p>{inner}</p>")
    content = "\n".join(parts)
    src_bit = (
        f'<p class="source">Kaynak: <code>{html.escape(source_rel)}</code> · '
        f"Hedef: {html.escape(tgt_lang)}</p>"
        if source_rel
        else ""
    )
    title_esc = html.escape(doc_title)
    return (
        "<!DOCTYPE html>\n"
        '<html lang="tr">\n<head>\n'
        '<meta charset="utf-8">\n'
        f"<title>{title_esc}</title>\n"
        "<style>\n"
        "body{font-family:Georgia,'Times New Roman',serif;max-width:46rem;margin:2rem auto;"
        "line-height:1.65;padding:0 1.25rem;color:#1a1a1a;}\n"
        "h1{font-size:1.55rem;border-bottom:1px solid #ccc;padding-bottom:.35rem;}\n"
        "h2{font-size:1.12rem;margin-top:1.4rem;color:#333;}\n"
        "p{margin:.75rem 0;}\n"
        ".source{font-size:.88rem;color:#555;}\n"
        "code{font-size:.85rem;}\n"
        "</style>\n</head>\n<body>\n"
        f"<h1>{title_esc}</h1>\n{src_bit}\n{content}\n</body>\n</html>\n"
    )


def export_meta(fmt: str) -> dict[str, Any]:
    return {
        "version": EXPORT_FORMAT_VERSION,
        "format": fmt,
        "supports": ["txt", "md", "html", "docx"],
    }
