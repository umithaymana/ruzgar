# -*- coding: utf-8 -*-
"""V0 smoke — STT/TTS gecikme baseline ölçümü + doküman."""
from __future__ import annotations

import json
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
    # Smoke hızlı kalsın; tam STT load için: RUZGAR_V0_STT_LOAD=1
    os.environ.setdefault("RUZGAR_V0_STT_LOAD", "0")

    from ilim_assistant.ses_v0_baseline import (
        V0_VERSION,
        run_v0_baseline,
        write_v0_baseline_doc,
    )

    failed = 0
    failed += _ok("v0-baseline" in V0_VERSION, f"ver {V0_VERSION}")

    payload = run_v0_baseline()
    failed += _ok(isinstance(payload.get("stt"), dict), "stt block")
    failed += _ok(isinstance(payload.get("tts"), dict), "tts block")

    tts = payload["tts"]
    stt = payload["stt"]
    # En az TTS yolu ölçülebilir veya dürüst skip
    failed += _ok(
        bool(tts.get("edge_available"))
        or bool(tts.get("note"))
        or tts.get("stream_first_byte_ms") is not None,
        f"tts ölçüm edge={tts.get('edge_available')} first={tts.get('stream_first_byte_ms')}",
    )
    failed += _ok(
        stt.get("available") is False or stt.get("model") or stt.get("note"),
        f"stt durum avail={stt.get('available')}",
    )

    doc = ROOT / "docs" / "V0_STT_TTS_BASELINE_2026-10-23.md"
    write_v0_baseline_doc(payload, doc)
    failed += _ok(doc.is_file() and doc.stat().st_size > 80, f"doc {doc.name}")

    js = ROOT / "docs" / "V0_STT_TTS_BASELINE_2026-10-23.json"
    js.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    failed += _ok(js.is_file(), "json snapshot")

    print(
        f"tts_first_byte_ms={tts.get('stream_first_byte_ms')} "
        f"synth_full_ms={tts.get('synth_full_ms')} "
        f"stt_get_model_ms={stt.get('get_model_ms')}"
    )
    total = 7
    print(f"result: {total - failed}/{total} pass")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
