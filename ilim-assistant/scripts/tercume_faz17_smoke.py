#!/usr/bin/env python3
"""Faz 17 — 14F import, 14G DOCX, TMX, hizalı diff smoke."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))


def main() -> int:
    from ilim_assistant.motorlar.tercume_aligned_diff import (
        ALIGNED_DIFF_VERSION,
        build_aligned_diff,
    )
    from ilim_assistant.motorlar.tercume_export_docx import DOCX_EXPORT_VERSION, docx_available
    from ilim_assistant.motorlar.tercume_glossary_import import (
        GLOSSARY_IMPORT_VERSION,
        parse_glossary_import,
    )
    from ilim_assistant.motorlar.tercume_tmx import TMX_VERSION, build_tmx, parse_tmx

    if "v17f" not in GLOSSARY_IMPORT_VERSION:
        print("FAIL glossary import version")
        return 1

    csv_hit = parse_glossary_import("kaynak,tr\nMerhaba,Hello\n", "csv")
    if not csv_hit.get("ok") or csv_hit.get("count") != 1:
        print("FAIL csv", csv_hit)
        return 1

    json_hit = parse_glossary_import(
        '{"entries":[{"src":"kitap","tr":"book"}]}',
        "json",
    )
    if not json_hit.get("ok"):
        print("FAIL json", json_hit)
        return 1

    tmx = build_tmx([("a", "b"), ("c", "d")], src_lang="tr", tgt_lang="en")
    back = parse_tmx(tmx)
    if len(back) < 2:
        print("FAIL tmx roundtrip", back)
        return 1

    diff = build_aligned_diff("Bir\n\nİki", "One\n\nTwo")
    if not diff.get("ok") or diff.get("total", 0) < 2:
        print("FAIL aligned diff", diff)
        return 1
    if "v17" not in ALIGNED_DIFF_VERSION:
        print("FAIL diff version", ALIGNED_DIFF_VERSION)
        return 1

    with tempfile.TemporaryDirectory() as td:
        from ilim_assistant.motorlar.tercume_user_glossary import import_from_text, list_entries

        imp = import_from_text("term,en\nsmoke_word,smoke_tr\n", "csv", merge=True)
        if not imp.get("ok"):
            print("FAIL import_from_text", imp)
            return 1
        lst = list_entries(limit=200)
        ids = [e.get("src") for e in lst.get("entries") or [] if isinstance(e, dict)]
        if "smoke_word" not in ids:
            print("FAIL glossary persist", ids[-5:])
            return 1

    if docx_available():
        from ilim_assistant.motorlar.tercume_export_docx import build_docx_bytes

        raw = build_docx_bytes("Test paragraf.\n\nİkinci.", title="Smoke")
        if len(raw) < 2000:
            print("FAIL docx bytes too small", len(raw))
            return 1
    else:
        print("SKIP docx — python-docx yok")

    if "v17g" not in DOCX_EXPORT_VERSION or "v17" not in TMX_VERSION:
        print("FAIL export/tmx versions")
        return 1

    from ilim_assistant.motorlar.tercume_atolye import workbench_config

    wb = workbench_config()
    for key in ("glossary_import_faz14f", "export_docx_faz14g", "tmx_faz17", "aligned_diff_faz17"):
        if key not in wb:
            print("FAIL workbench", key)
            return 1

    from desktop_server import app

    paths = {getattr(r, "path", "") for r in app.routes}
    for route in (
        "/api/tercume/user-glossary/import",
        "/api/tercume/tmx/export",
        "/api/tercume/tmx/import",
        "/api/tercume/aligned-diff",
    ):
        if route not in paths:
            print("FAIL route", route)
            return 1

    print("OK tercume faz17 — import + tmx + aligned diff + routes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
