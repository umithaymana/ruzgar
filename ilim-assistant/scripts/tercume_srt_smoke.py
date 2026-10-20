# Created by Ümit & Gökçenur
"""Smoke — SRT parse / roundtrip / classify (LLM mock)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SAMPLE = """1
00:00:01,000 --> 00:00:03,000
Hello world

2
00:00:04,000 --> 00:00:06,500
How are you?
"""


def main() -> int:
    from ilim_assistant.motorlar import altyazi_fabrika as fab
    from ilim_assistant.motorlar.tercume_faz74 import classify_tercume_intent
    from ilim_assistant.motorlar.tercume_srt import (
        extract_srt_body_from_message,
        extract_srt_path_hint,
        looks_like_srt_body,
        maybe_run_srt_translate,
        translate_srt_text,
    )
    from ilim_assistant.ruzgar_motor_kernel import INTENT_DO

    assert looks_like_srt_body(SAMPLE)
    assert extract_srt_body_from_message("turkceye cevir:\n" + SAMPLE)
    assert extract_srt_path_hint("srt cevir: clips/demo.srt") == "clips/demo.srt"
    assert extract_srt_path_hint("nasilsin") is None

    intent = classify_tercume_intent(
        "turkceye cevir:\n" + SAMPLE, mode_norm="tercume"
    )
    assert intent.get("intent") == INTENT_DO
    assert intent.get("reason") == "translate_srt"
    print("OK classify translate_srt")

    # LLM yok — batch mock
    def _fake_batch(texts, *, src_lang, tgt_lang):
        return [f"TR:{t}" for t in texts]

    fab._subtitle_translate_batch = _fake_batch  # type: ignore[attr-defined]
    out = translate_srt_text(SAMPLE, src_lang="en", tgt_lang="tr")
    assert out["ok"] is True
    assert out["cue_count"] == 2
    assert "TR:Hello world" in out["srt"]
    assert "00:00:01,000 --> 00:00:03,000" in out["srt"]
    print("OK translate_srt_text mock")

    hit = maybe_run_srt_translate("ingilizceden turkceye cevir:\n" + SAMPLE)
    assert hit.get("handled") is True
    assert "```srt" in str(hit.get("reply") or "")
    print("OK maybe_run_srt_translate")

    print("PASS tercume_srt_smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
