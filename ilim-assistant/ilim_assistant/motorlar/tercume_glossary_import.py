# Created by Ümit & Gökçenur
"""Tercüme Faz 14F — kullanıcı sözlüğü CSV/JSON içe aktarma."""

from __future__ import annotations

import csv
import io
import json
import re
from typing import Any

GLOSSARY_IMPORT_VERSION = "tercume-glossary-import-v17f-2026-05-29"
_MAX_IMPORT_ROWS = 250


def _norm_row(raw: dict[str, Any]) -> dict[str, str] | None:
    if not isinstance(raw, dict):
        return None
    src = str(
        raw.get("src")
        or raw.get("source")
        or raw.get("term")
        or raw.get("kaynak")
        or ""
    ).strip()
    if len(src) < 2:
        return None
    tr = str(raw.get("tr") or raw.get("target_tr") or raw.get("hedef") or "").strip()
    en = str(raw.get("en") or raw.get("target_en") or "").strip()
    ar = str(raw.get("ar") or raw.get("target_ar") or "").strip()
    tgt = str(raw.get("tgt") or raw.get("target") or raw.get("translation") or "").strip()
    if tgt and not tr and not en and not ar:
        tr = tgt
    if not tr and not en and not ar:
        return None
    return {
        "src": src,
        "tr": tr,
        "en": en,
        "ar": ar,
        "scope": str(raw.get("scope") or raw.get("file") or "").strip().replace("\\", "/"),
        "note": str(raw.get("note") or raw.get("not") or "")[:200],
    }


def parse_glossary_json(text: str) -> list[dict[str, str]]:
    data = json.loads(text)
    rows: list[Any] = []
    if isinstance(data, dict):
        inner = data.get("entries") or data.get("terms") or data.get("rows")
        if isinstance(inner, list):
            rows = inner
    elif isinstance(data, list):
        rows = data
    out: list[dict[str, str]] = []
    for item in rows:
        row = _norm_row(item if isinstance(item, dict) else {})
        if row:
            out.append(row)
        if len(out) >= _MAX_IMPORT_ROWS:
            break
    return out


def parse_glossary_csv(text: str) -> list[dict[str, str]]:
    sample = (text or "")[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    if not reader.fieldnames:
        return []
    fields = {f.lower().strip(): f for f in reader.fieldnames if f}
    out: list[dict[str, str]] = []
    for line in reader:
        if len(out) >= _MAX_IMPORT_ROWS:
            break
        raw: dict[str, Any] = {}
        for key, col in fields.items():
            raw[key] = line.get(col, "")
        row = _norm_row(raw)
        if row:
            out.append(row)
    return out


def detect_glossary_format(text: str, hint: str = "") -> str:
    h = (hint or "").strip().lower()
    if h in ("json", "csv"):
        return h
    t = (text or "").strip()
    if t.startswith("{") or t.startswith("["):
        return "json"
    if ";" in t[:500] and "," not in t[:80]:
        return "csv"
    return "csv"


def parse_glossary_import(text: str, fmt: str = "") -> dict[str, Any]:
    blob = (text or "").strip()
    if not blob:
        return {"ok": False, "error": "İçerik boş."}
    if len(blob) > 1_500_000:
        return {"ok": False, "error": "Dosya çok büyük (1.5 MB)."}
    code = detect_glossary_format(blob, fmt)
    try:
        if code == "json":
            rows = parse_glossary_json(blob)
        else:
            rows = parse_glossary_csv(blob)
    except json.JSONDecodeError as exc:
        return {"ok": False, "error": f"JSON okunamadı: {exc}"}
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:200]}
    if not rows:
        return {
            "ok": False,
            "error": "Geçerli terim satırı bulunamadı (src + tr/en/ar gerekli).",
        }
    return {
        "ok": True,
        "format": code,
        "rows": rows,
        "count": len(rows),
        "version": GLOSSARY_IMPORT_VERSION,
    }
