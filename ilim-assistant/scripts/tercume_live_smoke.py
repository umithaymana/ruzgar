#!/usr/bin/env python3
"""Faz 15C — canlı Ollama ile tek parça çeviri (isteğe bağlı)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))


def main() -> int:
    if os.environ.get("RUZGAR_TERCUME_LIVE_SMOKE", "1").strip().lower() in (
        "0",
        "false",
        "no",
    ):
        print("SKIP live smoke (RUZGAR_TERCUME_LIVE_SMOKE=0)")
        return 0

    from ilim_assistant.motorlar.tercume_llm import translation_brain_status

    st = translation_brain_status()
    if not st.get("ready"):
        print("SKIP Ollama hazır değil:", st.get("hint_tr") or st)
        return 0

    from ilim_assistant.motorlar.tercume_atolye import translate_chunk

    sample = "Bismillahirrahmanirrahim. Bu bir deneme cümlesidir."
    hit = translate_chunk(sample, src_lang="ar", tgt_lang="tr", source_file="live_smoke.txt")
    if not hit.get("ok"):
        print("FAIL translate", hit.get("error"), hit.get("hint_tr"))
        return 1
    out = str(hit.get("text") or "").strip()
    if len(out) < 8:
        print("FAIL short output", out)
        return 1
    q = hit.get("quality") or {}
    print("OK tercume live smoke —", out[:80].replace("\n", " "), f"score={q.get('score')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
