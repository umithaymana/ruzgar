# Created by Ümit & Gökçenur
"""Tercüme Faz 17 — TMX terim dışa / içe aktarma."""

from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from typing import Any

TMX_VERSION = "tercume-tmx-v17-2026-05-29"
_MAX_TU = 500


def _esc(s: str) -> str:
    return html.escape((s or "").strip(), quote=False)


def build_tmx(
    units: list[tuple[str, str]],
    *,
    src_lang: str = "tr",
    tgt_lang: str = "en",
    creation_tool: str = "ruzgar-tercume",
) -> str:
    sl = (src_lang or "tr").strip().lower()[:8] or "tr"
    tl = (tgt_lang or "en").strip().lower()[:8] or "en"
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<tmx version="1.4">',
        "<header",
        f' creationtool="{_esc(creation_tool)}"',
        ' segtype="sentence"',
        ' adminlang="tr"',
        f' srclang="{_esc(sl)}"',
        ' datatype="PlainText"',
        "/>",
        "<body>",
    ]
    for src, tgt in units[:_MAX_TU]:
        if not src.strip() or not tgt.strip():
            continue
        lines.append("<tu>")
        lines.append(f'<tuv xml:lang="{_esc(sl)}"><seg>{_esc(src)}</seg></tuv>')
        lines.append(f'<tuv xml:lang="{_esc(tl)}"><seg>{_esc(tgt)}</seg></tuv>')
        lines.append("</tu>")
    lines.append("</body></tmx>")
    return "\n".join(lines) + "\n"


def parse_tmx(text: str) -> list[tuple[str, str]]:
    blob = (text or "").strip()
    if not blob:
        return []
    if "<tu" not in blob.lower():
        return []
    try:
        root = ET.fromstring(blob)
    except ET.ParseError:
        return _parse_tmx_regex(blob)
    out: list[tuple[str, str]] = []
    for tu in root.iter("tu"):
        segs: list[str] = []
        for tuv in tu.findall(".//tuv"):
            seg_el = tuv.find("seg")
            if seg_el is not None and (seg_el.text or "").strip():
                segs.append((seg_el.text or "").strip())
        if len(segs) >= 2:
            out.append((segs[0], segs[1]))
        elif len(segs) == 1:
            out.append((segs[0], segs[0]))
        if len(out) >= _MAX_TU:
            break
    return out


def _parse_tmx_regex(blob: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for block in re.findall(r"(?is)<tu\b[^>]*>.*?</tu>", blob):
        segs = re.findall(r"(?is)<seg[^>]*>(.*?)</seg>", block)
        clean = [re.sub(r"<[^>]+>", "", s).strip() for s in segs]
        clean = [html.unescape(c) for c in clean if c]
        if len(clean) >= 2:
            out.append((clean[0], clean[1]))
        if len(out) >= _MAX_TU:
            break
    return out


def collect_tmx_units(
    *,
    source_file: str = "",
    tgt_lang: str = "tr",
    include_glossary: bool = True,
    include_tm: bool = True,
) -> list[tuple[str, str]]:
    units: list[tuple[str, str]] = []
    seen: set[str] = set()

    def add(src: str, tgt: str) -> None:
        key = src.strip().lower()
        if len(key) < 2 or not tgt.strip() or key in seen:
            return
        seen.add(key)
        units.append((src.strip(), tgt.strip()))

    if include_glossary:
        from ilim_assistant.motorlar.tercume_user_glossary import list_entries

        hit = list_entries(limit=200)
        code = (tgt_lang or "tr").strip().lower()[:2] or "tr"
        col = {"tr": "tr", "en": "en", "ar": "ar"}.get(code, "tr")
        for e in hit.get("entries") or []:
            if not isinstance(e, dict):
                continue
            src = str(e.get("src") or "").strip()
            tgt = str(e.get(col) or e.get("tr") or e.get("en") or "").strip()
            if src and tgt:
                add(src, tgt)

    if include_tm and source_file:
        from ilim_assistant.motorlar.tercume_translate_memory import session_pair_list

        for p in session_pair_list(source_file, tgt_lang=tgt_lang):
            add(str(p.get("src") or ""), str(p.get("tgt") or ""))

    return units[:_MAX_TU]


def export_tmx_bundle(
    *,
    source_file: str = "",
    src_lang: str = "auto",
    tgt_lang: str = "tr",
) -> dict[str, Any]:
    sl = (src_lang or "auto").strip().lower()
    if sl in ("", "auto"):
        sl = "tr"
    tl = (tgt_lang or "tr").strip().lower()[:8] or "tr"
    units = collect_tmx_units(source_file=source_file, tgt_lang=tl)
    if not units:
        return {"ok": False, "error": "Dışa aktarılacak terim çifti yok."}
    body = build_tmx(units, src_lang=sl, tgt_lang=tl)
    return {
        "ok": True,
        "tmx": body,
        "units": len(units),
        "src_lang": sl,
        "tgt_lang": tl,
        "version": TMX_VERSION,
    }
