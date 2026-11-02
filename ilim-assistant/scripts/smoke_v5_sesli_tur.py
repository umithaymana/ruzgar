# -*- coding: utf-8 -*-
"""V5 smoke — sesli tur uçtan uca (STT→voice_turn→TTS) + UI zinciri."""
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
    from ilim_assistant.ses_v5_sesli_tur import (
        V5_VERSION,
        run_v5_e2e,
        verify_ui_voice_chain,
        verify_voice_turn_contract,
    )

    failed = 0
    failed += _ok("v5-sesli-tur" in V5_VERSION, f"ver {V5_VERSION}")

    c = verify_voice_turn_contract()
    failed += _ok(bool(c.get("ok")), f"voice_turn contract tok_v={c.get('max_tokens_voice')}")
    failed += _ok(int(c.get("addon_chars") or 0) > 20, "addon")

    ui = verify_ui_voice_chain()
    failed += _ok(bool(ui.get("ok")), f"ui_chain missing={ui.get('missing')}")

    skip = os.environ.get("RUZGAR_V5_SKIP_LIVE", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )
    e2e = run_v5_e2e(skip_live_audio=skip)
    stt = (e2e.get("stages") or {}).get("stt") or {}
    tts = (e2e.get("stages") or {}).get("tts") or {}
    failed += _ok(bool(stt.get("ok")), f"stt ok note={stt.get('note')} ms={stt.get('ms')}")
    failed += _ok(bool(tts.get("ok")), f"tts ok first={tts.get('first_byte_ms')} note={tts.get('note')}")
    failed += _ok(bool(e2e.get("under_budget")), f"budget elapsed={e2e.get('elapsed_ms')}")
    failed += _ok(bool(e2e.get("ok")), "e2e ok")

    # API kancaları
    ds = (ROOT / "desktop_server.py").read_text(encoding="utf-8")
    failed += _ok('voice_turn: bool' in ds or "voice_turn: bool =" in ds, "ChatBody voice_turn")
    failed += _ok("/api/stt" in ds and "@app.post" in ds, "stt route")
    failed += _ok('synthesize_edge_mp3_v3_fast' in ds, "tts V3 kanca")

    doc = ROOT / "docs" / "V5_FAZ_V_MUHUR_2026-11-03.md"
    failed += _ok(doc.is_file() and doc.stat().st_size > 80, f"doc {doc.name}")

    print(
        f"e2e elapsed_ms={e2e.get('elapsed_ms')} "
        f"stt_ms={stt.get('ms')} tts_first={tts.get('first_byte_ms')}"
    )
    total = 12
    print(f"result: {total - failed}/{total} pass")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
