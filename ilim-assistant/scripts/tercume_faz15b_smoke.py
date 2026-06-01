#!/usr/bin/env python3
"""Faz 15B — kullanıcı terim tablosu smoke."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))


def main() -> int:
    from ilim_assistant.motorlar import tercume_user_glossary as mod
    from ilim_assistant.motorlar.tercume_user_glossary import (
        USER_GLOSSARY_VERSION,
        add_entry,
        delete_entry,
        matching_user_terms,
        user_glossary_directive,
    )

    if "v15b" not in USER_GLOSSARY_VERSION:
        print("FAIL version", USER_GLOSSARY_VERSION)
        return 1

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / ".ruzgar").mkdir()
        orig = mod._glossary_path
        mod._glossary_path = lambda: root / ".ruzgar" / "tercume_user_glossary.json"  # type: ignore[method-assign]
        mod._repo_root = lambda: root  # type: ignore[method-assign]

        hit = add_entry(src="Makam", tr="Mertebe", en="Station")
        if not hit.get("ok"):
            print("FAIL add", hit)
            return 1
        pairs = matching_user_terms("bu Makam metni", source_file="x.pdf", tgt_lang="tr")
        if not pairs or pairs[0][0] != "Makam":
            print("FAIL match", pairs)
            return 1
        block = user_glossary_directive("Makam", source_file="x.pdf", tgt_lang="tr")
        if "Makam" not in block:
            print("FAIL directive", block)
            return 1
        eid = hit["entry"]["id"]
        delete_entry(eid)
        mod._glossary_path = orig  # type: ignore[method-assign]

    from desktop_server import app

    paths = {getattr(r, "path", "") for r in app.routes}
    for p in ("/api/tercume/user-glossary", "/api/tercume/user-glossary/add"):
        if p not in paths:
            print("FAIL route", p)
            return 1

    print("OK tercume faz15b — user glossary")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
