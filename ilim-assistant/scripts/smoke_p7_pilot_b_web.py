# -*- coding: utf-8 -*-
"""P7 smoke — Pilot B statik vitrin."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
WS = ROOT.parent
PILOT = WS / "projects" / "pilot-b-vitrin"


def _ok(cond: bool, label: str) -> int:
    print(("OK" if cond else "FAIL"), "-", label)
    return 0 if cond else 1


def main() -> int:
    failed = 0
    failed += _ok(PILOT.is_dir(), "pilot dir")
    html = PILOT / "index.html"
    css = PILOT / "css" / "styles.css"
    js = PILOT / "js" / "app.js"
    failed += _ok(html.is_file(), "index.html")
    failed += _ok(css.is_file(), "styles.css")
    failed += _ok(js.is_file(), "app.js")

    text = html.read_text(encoding="utf-8")
    failed += _ok("Pilot B Vitrin" in text, "title/h1")
    failed += _ok("Rüzgar" in text or "Ruzgar" in text, "brand")
    failed += _ok('id="btn-hello"' in text, "hello button")
    failed += _ok('id="ozellikler"' in text, "features section")

    js_t = js.read_text(encoding="utf-8")
    failed += _ok("Pilot B" in js_t, "js message")

    css_t = css.read_text(encoding="utf-8")
    failed += _ok(".brand" in css_t, "css brand")

    # P5 verify helper
    from ilim_assistant.motorlar.programlama_p5_scaffold_boru import (
        verify_product_scaffold,
    )

    v = verify_product_scaffold(
        WS, template_id="static_site", scope_rel="projects/pilot-b-vitrin"
    )
    failed += _ok(bool(v.get("ok")), f"p5 verify {v.get('detail')!r}")

    total = 11
    print(f"result: {total - failed}/{total} pass")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
