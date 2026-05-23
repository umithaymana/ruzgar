#!/usr/bin/env python3
"""Rüzgar API — önce .env/RUZGAR_BRAIN.env, sonra uvicorn (anahtar kaybı önlenir)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

_IA = Path(__file__).resolve().parent
if str(_IA) not in sys.path:
    sys.path.insert(0, str(_IA))
os.chdir(_IA)


def _bootstrap() -> None:
    from ilim_assistant.env_bootstrap import ensure_ruzgar_env, sync_global_api_key_aliases

    ensure_ruzgar_env()
    sync_global_api_key_aliases()
    from ilim_assistant.config import apply_global_api_key_to_runtime, gemini_ready

    apply_global_api_key_to_runtime()
    ok = gemini_ready()
    print(
        f"[Rüzgar] Gemini={'hazır' if ok else 'YOK'} "
        f"OllamaOnly={os.environ.get('RUZGAR_OLLAMA_ONLY', '?')}",
        file=sys.stderr,
        flush=True,
    )


def main() -> None:
    _bootstrap()
    import uvicorn

    port = int(os.environ.get("RUZGAR_API_PORT", "8779") or "8779")
    uvicorn.run(
        "desktop_server:app",
        host="127.0.0.1",
        port=port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
