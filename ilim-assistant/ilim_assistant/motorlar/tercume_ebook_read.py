# Created by Ümit & Gökçenur
"""Tercüme Faz 15A — EPUB/FB2 bölüm + metadata okuma."""

from __future__ import annotations

import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

EBOOK_READ_VERSION = "tercume-ebook-read-v15a-2026-05-29"

_DC_NS = {
    "dc": "http://purl.org/dc/elements/1.1/",
    "opf": "http://www.idpf.org/2007/opf",
}


def _simple_html_to_text(html: str) -> str:
    s = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", html or "")
    s = re.sub(r"(?is)<br\s*/?>", "\n", s)
    s = re.sub(r"(?is)</p\s*>", "\n\n", s)
    s = re.sub(r"(?is)<h[1-6][^>]*>", "\n\n", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    s = re.sub(r"[ \t]{2,}", " ", s)
    return s.strip()


def _chapter_title_from_html(html: str, fallback: str) -> str:
    m = re.search(r"(?is)<title[^>]*>([^<]+)</title>", html or "")
    if m:
        t = re.sub(r"\s+", " ", m.group(1)).strip()
        if t and len(t) < 120:
            return t
    m = re.search(r"(?is)<h1[^>]*>([^<]+)</h1>", html or "")
    if m:
        t = re.sub(r"\s+", " ", m.group(1)).strip()
        if t and len(t) < 120:
            return t
    leaf = fallback.split("/")[-1]
    stem = re.sub(r"\.[^.]+$", "", leaf) or fallback
    return stem[:80]


def _epub_opf_path(zf: zipfile.ZipFile) -> str | None:
    try:
        raw = zf.read("META-INF/container.xml")
    except KeyError:
        return None
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return None
    for el in root.iter():
        if el.tag.endswith("rootfile") and el.get("full-path"):
            return str(el.get("full-path"))
    return None


def _parse_opf_metadata(opf_bytes: bytes) -> dict[str, str]:
    meta: dict[str, str] = {}
    try:
        root = ET.fromstring(opf_bytes)
    except ET.ParseError:
        return meta
    for el in root.iter():
        tag = el.tag.split("}")[-1] if "}" in el.tag else el.tag
        if tag == "title" and not meta.get("title"):
            meta["title"] = (el.text or "").strip()
        elif tag == "creator" and not meta.get("author"):
            meta["author"] = (el.text or "").strip()
    return meta


def _epub_spine_hrefs(zf: zipfile.ZipFile, opf_path: str) -> list[str]:
    try:
        opf_raw = zf.read(opf_path)
    except KeyError:
        return []
    try:
        root = ET.fromstring(opf_raw)
    except ET.ParseError:
        return []
    opf_dir = str(Path(opf_path).parent).replace("\\", "/")
    if opf_dir == ".":
        opf_dir = ""

    manifest: dict[str, str] = {}
    spine_ids: list[str] = []
    for el in root.iter():
        tag = el.tag.split("}")[-1] if "}" in el.tag else el.tag
        if tag == "item" and el.get("id") and el.get("href"):
            href = str(el.get("href")).replace("\\", "/")
            if opf_dir:
                href = f"{opf_dir}/{href}".lstrip("/")
            manifest[str(el.get("id"))] = href
        elif tag == "itemref" and el.get("idref"):
            spine_ids.append(str(el.get("idref")))

    out: list[str] = []
    for sid in spine_ids:
        href = manifest.get(sid)
        if not href:
            continue
        low = href.lower()
        if low.endswith((".xhtml", ".html", ".htm")):
            out.append(href)
    if out:
        return out
    names = sorted(
        n
        for n in zf.namelist()
        if n.lower().endswith((".xhtml", ".html", ".htm")) and not n.startswith("__")
    )
    return names


def read_epub(target: Path) -> dict[str, Any]:
    chapters: list[dict[str, Any]] = []
    meta: dict[str, Any] = {"format": "epub", "version": EBOOK_READ_VERSION}
    with zipfile.ZipFile(target, "r") as zf:
        opf = _epub_opf_path(zf)
        if opf:
            try:
                meta.update(_parse_opf_metadata(zf.read(opf)))
            except KeyError:
                pass
        hrefs = _epub_spine_hrefs(zf, opf) if opf else []
        if not hrefs:
            hrefs = [
                n
                for n in zf.namelist()
                if n.lower().endswith((".xhtml", ".html", ".htm"))
            ]
        for i, name in enumerate(hrefs):
            try:
                body = zf.read(name).decode("utf-8", errors="replace")
            except Exception:
                continue
            txt = _simple_html_to_text(body)
            if not txt:
                continue
            title = _chapter_title_from_html(body, name)
            chapters.append(
                {
                    "index": len(chapters),
                    "title": title,
                    "text": txt,
                    "href": name,
                }
            )
    parts = []
    for ch in chapters:
        parts.append(f"\n\n=== {ch['title']} ===\n\n{ch['text']}")
    return {
        "ok": True,
        "text": "\n".join(parts).strip(),
        "chapters": chapters,
        "chapters_read": len(chapters),
        "title": meta.get("title") or "",
        "author": meta.get("author") or "",
        "meta": meta,
    }


def read_fb2(target: Path) -> dict[str, Any]:
    chapters: list[dict[str, Any]] = []
    meta: dict[str, Any] = {"format": "fb2", "version": EBOOK_READ_VERSION}
    try:
        root = ET.fromstring(target.read_text(encoding="utf-8", errors="replace"))
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:200]}
    ns = {"fb": "http://www.gribuser.ru/xml/fictionbook/2.0"}
    title_el = root.find(".//fb:description/fb:title-info/fb:book-title", ns)
    author_el = root.find(".//fb:description/fb:title-info/fb:author/fb:first-name", ns)
    if title_el is not None and (title_el.text or "").strip():
        meta["title"] = (title_el.text or "").strip()
    if author_el is not None and (author_el.text or "").strip():
        meta["author"] = (author_el.text or "").strip()
    for sec in root.findall(".//fb:body/fb:section", ns):
        txt = " ".join((t or "").strip() for t in sec.itertext() if (t or "").strip())
        if not txt:
            continue
        idx = len(chapters)
        title_el2 = sec.find("fb:title", ns)
        title = (title_el2.text or "").strip() if title_el2 is not None else f"Bölüm {idx + 1}"
        chapters.append({"index": idx, "title": title or f"Bölüm {idx + 1}", "text": txt})
    parts = [f"\n\n=== {ch['title']} ===\n\n{ch['text']}" for ch in chapters]
    return {
        "ok": True,
        "text": "\n".join(parts).strip(),
        "chapters": chapters,
        "chapters_read": len(chapters),
        "title": meta.get("title") or "",
        "author": meta.get("author") or "",
        "meta": meta,
    }


def chapters_to_pages(chapters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pages: list[dict[str, Any]] = []
    for ch in chapters:
        if not isinstance(ch, dict):
            continue
        text = str(ch.get("text") or "").strip()
        if not text:
            continue
        idx = int(ch.get("index") if ch.get("index") is not None else len(pages))
        title = str(ch.get("title") or f"Bölüm {idx + 1}")
        pages.append({"index": idx, "text": text, "label": title})
    return pages
