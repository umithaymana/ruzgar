# Created by Ümit & Gökçenur — Aşama A barge-in smoke (bağımlılık yok)
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ilim-assistant"))

from ilim_assistant.ses_v4_barge_in import (  # noqa: E402
    verify_mobil_barge_markers,
    verify_ui_barge_in_markers,
    v4_contract,
)


def _stop_re_ok(text: str) -> bool:
    # JS ile aynı mantık (yaklaşık)
    t = text.strip().lower()
    t = re.sub(r"[!?.…,]+$", "", t).strip()
    return bool(
        re.match(
            r"^(sus|dur|kes|sessiz|sus\s*ol|kes\s*sesi|sus\s*lütfen|sus\s*lutfen)$",
            t,
            re.I,
        )
    )


def main() -> int:
    d = verify_ui_barge_in_markers()
    m = verify_mobil_barge_markers()
    c = v4_contract()
    failed = 0
    if not d.get("ok"):
        print("FAIL desktop markers", d)
        failed += 1
    else:
        print("OK desktop markers settle_ms=", c.get("settle_ms"))
    if not m.get("ok"):
        print("FAIL mobil markers", m)
        failed += 1
    else:
        print("OK mobil markers")
    for w in ("sus", "Dur", "KES", "sessiz"):
        if not _stop_re_ok(w):
            print("FAIL stop word", w)
            failed += 1
    for w in ("duraklat video", "kesinti nedir", ""):
        if _stop_re_ok(w):
            print("FAIL false positive", w)
            failed += 1
    # desktop settle literal
    desk = (ROOT / "ruzgar-desktop" / "app.js").read_text(encoding="utf-8")
    if "RUZGAR_BARGE_SETTLE_MS = 40" not in desk:
        print("FAIL settle not 40")
        failed += 1
    if "looksLikeVoiceStopCommand" not in desk:
        print("FAIL desktop stop helper")
        failed += 1
    print("contract_version", c.get("version"))
    if failed:
        print("SMOKE_FAIL", failed)
        return 1
    print("SMOKE_OK asama_a")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
