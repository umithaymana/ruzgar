#!/usr/bin/env python3
"""Faz 15A — EPUB/FB2 okuma smoke."""
from __future__ import annotations

import sys
import tempfile
import zipfile
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))


def _mini_epub(path: Path) -> None:
    opf = """<?xml version="1.0"?>
<package xmlns="http://www.idpf.org/2007/opf" version="2.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Deneme Kitap</dc:title>
    <dc:creator>Test Yazar</dc:creator>
  </metadata>
  <manifest>
    <item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="ch1"/>
  </spine>
</package>"""
    xhtml = """<?xml version="1.0"?><html><head><title>Giris</title></head>
<body><p>Merhaba dunya.</p></body></html>"""
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr(
            "META-INF/container.xml",
            '<?xml version="1.0"?><container><rootfiles>'
            '<rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>'
            "</rootfiles></container>",
        )
        zf.writestr("content.opf", opf)
        zf.writestr("ch1.xhtml", xhtml)


def main() -> int:
    from ilim_assistant.motorlar.tercume_ebook_read import EBOOK_READ_VERSION, read_epub

    if "v16a" not in EBOOK_READ_VERSION and "v15a" not in EBOOK_READ_VERSION:
        print("FAIL version", EBOOK_READ_VERSION)
        return 1

    with tempfile.TemporaryDirectory() as td:
        epub = Path(td) / "t.epub"
        _mini_epub(epub)
        hit = read_epub(epub)
        if not hit.get("ok") or hit.get("title") != "Deneme Kitap":
            print("FAIL epub", hit)
            return 1
        if not hit.get("chapters") or "Merhaba" not in hit.get("text", ""):
            print("FAIL text", hit.get("text", "")[:100])
            return 1

    print("OK tercume faz15a — epub metadata + chapters")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
