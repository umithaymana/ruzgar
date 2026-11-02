# -*- coding: utf-8 -*-
"""V3 smoke — TTS ilk-byte (kısa yol, retry, workers, API kanca)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _ok(cond: bool, label: str) -> int:
    print(("OK" if cond else "FAIL"), "-", label)
    return 0 if cond else 1


def main() -> int:
    from ilim_assistant.ses_v3_tts_ilk_byte import (
        V3_VERSION,
        measure_v3_compare,
        v3_enabled,
        v3_fast_chars,
        v3_workers_default,
        wants_v3_fast_path,
    )
    from ilim_assistant.tts_service import edge_available

    failed = 0
    failed += _ok("v3-tts-ilk-byte" in V3_VERSION, f"ver {V3_VERSION}")
    failed += _ok(v3_enabled(), "V3 varsayılan açık")
    failed += _ok(v3_fast_chars() >= 48, f"fast_chars={v3_fast_chars()}")
    failed += _ok(v3_workers_default() >= 2, f"workers_default={v3_workers_default()}")
    failed += _ok(wants_v3_fast_path("Merhaba Ümit abi."), "kısa metin fast path")
    failed += _ok(
        not wants_v3_fast_path("x" * (v3_fast_chars() + 20)),
        "uzun metin pool yolu",
    )

    ds = (ROOT / "desktop_server.py").read_text(encoding="utf-8")
    failed += _ok("synthesize_edge_mp3_v3_fast" in ds, "api_tts V3 kanca")
    failed += _ok("wants_v3_fast_path" in ds, "api_tts wants_v3")

    ts = (ROOT / "ilim_assistant" / "tts_service.py").read_text(encoding="utf-8")
    failed += _ok("RUZGAR_TTS_V3_RETRIES" in ts, "pool retry")
    failed += _ok("n = 2" in ts or 'n = 2' in ts, "workers varsayılan 2")

    if edge_available():
        m = measure_v3_compare()
        fb = m.get("first_byte_ms")
        failed += _ok(bool(m.get("ok")), f"ölçüm ok note={m.get('note')}")
        failed += _ok(
            fb is not None and float(fb) > 0,
            f"first_byte_ms={fb}",
        )
        # V0 mühür 1686 — ağ dalgalanır; üst tavan gevşek, regresyon yakala
        failed += _ok(
            fb is not None and float(fb) < 4500,
            f"first_byte <4500 (v0=1686) got={fb}",
        )
        print(
            f"measure first_byte_ms={fb} total_ms={m.get('total_ms')} "
            f"attempts={m.get('attempts')} bytes={m.get('bytes')}"
        )
    else:
        failed += _ok(False, "edge-tts yok")
        failed += 2  # ölçüm slotları

    doc = ROOT / "docs" / "V3_TTS_ILK_BYTE_2026-11-03.md"
    failed += _ok(doc.is_file() and doc.stat().st_size > 80, f"doc {doc.name}")

    total = 14
    print(f"result: {total - failed}/{total} pass")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
