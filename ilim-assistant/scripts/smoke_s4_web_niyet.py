# -*- coding: utf-8 -*-
"""S4 smoke — Ümit emri web sırası niyet-koşullu."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _ok(cond: bool, label: str) -> int:
    print(("OK" if cond else "FAIL"), "-", label)
    return 0 if cond else 1


def main() -> int:
    from ilim_assistant.ruzgar_umed_cevap_emri import (
        S4_WEB_NIYET_VERSION,
        public_meta,
        s4_web_niyet_enabled,
        should_defer_web_to_rest,
        wants_early_web,
    )

    failed = 0
    failed += _ok("s4-web-niyet" in S4_WEB_NIYET_VERSION, f"ver {S4_WEB_NIYET_VERSION}")
    failed += _ok(s4_web_niyet_enabled(), "s4 enabled default")

    # Erken web — güncel / canlı / açık istek
    early_cases = [
        "bugün dolar kuru ne",
        "son dakika haberleri",
        "Galatasaray maç skoru",
        "webden bak: Türkiye nüfusu",
        "internetten bak hava durumu Istanbul",
        "Turkiyede kac universite var",
    ]
    for msg in early_cases:
        ew = wants_early_web(msg)
        defer = should_defer_web_to_rest(msg)
        failed += _ok(ew and not defer, f"early {msg[:36]!r} early={ew} defer={defer}")

    # İkincil — ansiklopedik / sohbet (local-first)
    defer_cases = [
        "fotosentez nedir",
        "Lale Devri nedir",
        "nasilsin",
        "osmanli devletini kim kurdu",
    ]
    for msg in defer_cases:
        ew = wants_early_web(msg)
        defer = should_defer_web_to_rest(msg)
        failed += _ok(not ew and defer, f"defer {msg[:36]!r} early={ew} defer={defer}")

    meta = public_meta("bugun dolar")
    failed += _ok(bool(meta.get("s4_web_niyet")), f"meta s4 {meta.get('s4_version')}")
    failed += _ok(bool(meta.get("early_web")), "meta early_web for dolar")

    # Kapat bayrağı
    os.environ["RUZGAR_UMED_S4_WEB_NIYET"] = "0"
    try:
        failed += _ok(not wants_early_web("bugun dolar kuru"), "flag off → no early")
        failed += _ok(should_defer_web_to_rest("bugun dolar kuru"), "flag off → defer")
    finally:
        os.environ.pop("RUZGAR_UMED_S4_WEB_NIYET", None)

    doc = ROOT / "docs" / "S4_WEB_NIYET_2026-11-03.md"
    failed += _ok(doc.is_file() and doc.stat().st_size > 80, f"doc {doc.name}")

    total = 2 + len(early_cases) + len(defer_cases) + 4
    print(f"result: {total - failed}/{total} pass")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
