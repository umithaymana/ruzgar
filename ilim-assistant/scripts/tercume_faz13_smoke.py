#!/usr/bin/env python3
"""Faz 13 — tercüme LLM zinciri, readiness API, arama backend şeffaflığı."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))


def main() -> int:
    from ilim_assistant.motorlar.tercume_llm import (
        TERCUME_LLM_VERSION,
        translation_brain_status,
        translate_completion,
    )

    if "v13" not in TERCUME_LLM_VERSION:
        print("FAIL llm version", TERCUME_LLM_VERSION)
        return 1

    st = translation_brain_status()
    if "ready" not in st or "ollama_only" not in st:
        print("FAIL brain status keys", st)
        return 1

    from ilim_assistant.motorlar.tercume_readiness import (
        READINESS_VERSION,
        collect_tercume_readiness,
    )

    if "v13" not in READINESS_VERSION:
        print("FAIL readiness version", READINESS_VERSION)
        return 1
    rd = collect_tercume_readiness(need_internet=False)
    if not rd.get("ok") or "brain" not in rd:
        print("FAIL collect_tercume_readiness", rd)
        return 1

    from ilim_assistant.motorlar.tercume_eser_arama import duckduckgo_search_available

    sb_ok, sb_detail = duckduckgo_search_available()
    if not isinstance(sb_ok, bool) or not sb_detail:
        print("FAIL duckduckgo_search_available", sb_ok, sb_detail)
        return 1

    from ilim_assistant.motorlar.tercume_atolye import translate_chunk

    empty = translate_chunk("", tgt_lang="tr")
    if empty.get("ok"):
        print("FAIL empty translate should fail", empty)
        return 1
    if not empty.get("error_code"):
        print("FAIL empty translate needs error_code", empty)
        return 1

    from desktop_server import app

    paths = {getattr(r, "path", "") for r in app.routes}
    for need in ("/api/tercume/readiness", "/api/tercume/translate-chunk", "/api/tercume/config"):
        if need not in paths:
            print("FAIL route missing", need)
            return 1

    # Beyin yoksa yapılandırılmış hata dönmeli (boş çağrı değil)
    if not st.get("ready"):
        res = translate_completion("sys", "user", max_tokens=32)
        if res.get("ok") or not res.get("error_code") or not res.get("hint_tr"):
            print("FAIL translate_completion when not ready", res)
            return 1

    print(
        "OK tercume faz13 — llm",
        TERCUME_LLM_VERSION,
        "brain_ready=",
        st.get("ready"),
        "ddgs=",
        sb_ok,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
