# -*- coding: utf-8 -*-
"""V4 smoke — barge-in / mic↔TTS kilit sözleşmesi (UI işaretleri)."""
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
    from ilim_assistant.ses_v4_barge_in import (
        V4_VERSION,
        desktop_app_js,
        v4_contract,
        verify_ui_barge_in_markers,
    )

    failed = 0
    failed += _ok("v4-barge-in" in V4_VERSION, f"ver {V4_VERSION}")
    c = v4_contract()
    failed += _ok(c.get("barge_in") is True, "contract barge_in")
    # Aşama D — settle 80→40 (ses_v4_barge_in.BARGE_SETTLE_MS / app.js)
    failed += _ok(int(c.get("settle_ms") or 0) == 40, "settle_ms=40")

    app = desktop_app_js()
    failed += _ok(app.is_file(), f"app.js {app}")
    v = verify_ui_barge_in_markers(app)
    failed += _ok(not v.get("missing"), f"markers missing={v.get('missing')}")
    failed += _ok(bool(v.get("mic_has_barge_call")), "mic→bargeInStopTtsForMic")
    failed += _ok(bool(v.get("pump_respects_mic_lock")), "pump mic kilidi")
    failed += _ok(bool(v.get("ok")), "verify ok")

    text = app.read_text(encoding="utf-8") if app.is_file() else ""
    failed += _ok("const RUZGAR_BARGE_IN = true" in text, "RUZGAR_BARGE_IN=true")
    failed += _ok("ttsBlockedByMicLock()" in text, "play/pump kilit çağrıları")
    # Eski sert blok kalkmış olmalı (barge kapalı dal dışında)
    failed += _ok(
        "if (!RUZGAR_BARGE_IN && (perfBusy || isTtsActive()))" in text,
        "micPointerDown barge-aware",
    )
    failed += _ok("await bargeInStopTtsForMic()" in text, "await bargeIn")
    # Barge sohbeti abort etmesin (kopukluk önlemi)
    barge_fn = ""
    i0 = text.find("async function bargeInStopTtsForMic")
    if i0 >= 0:
        i1 = text.find("\nwindow.bargeInStopTtsForMic", i0)
        barge_fn = text[i0 : i1 if i1 > i0 else i0 + 2200]
    failed += _ok(
        "activeChatAbort?.abort()" not in barge_fn
        and "activeChatAbort.abort()" not in barge_fn,
        "barge TTS-only (no chat abort)",
    )

    doc = ROOT / "docs" / "V4_BARGE_IN_2026-11-03.md"
    failed += _ok(doc.is_file() and doc.stat().st_size > 60, f"doc {doc.name}")

    total = 13
    print(f"result: {total - failed}/{total} pass")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
