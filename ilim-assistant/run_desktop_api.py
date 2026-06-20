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


def _boot_motorlar_locked() -> None:
    """.cursorrules — port açılmadan ana motor → çekirdek → 5 ara motor (sıra kilitli)."""
    import importlib

    importlib.import_module("ilim_assistant.main_engine")
    importlib.import_module("ilim_assistant.motorlar.ruzgar_cekirdegi")
    for name in (
        "ilim_assistant.ses_motoru",
        "ilim_assistant.video_motoru",
        "ilim_assistant.okuma_motoru",
        "ilim_assistant.mimar_motoru",
        "ilim_assistant.tercume_motoru",
        "ilim_assistant.motorlar.hafiza_motoru",
        "ilim_assistant.programlama_motoru",
    ):
        importlib.import_module(name)
    print("[Rüzgar] Motor boot tamam (port öncesi).", file=sys.stderr, flush=True)


def main() -> None:
    forced = (os.environ.get("RUZGAR_CI_FORCED_PORT") or "").strip()
    _bootstrap()
    from ilim_assistant.config import defer_motor_boot

    if not defer_motor_boot():
        _boot_motorlar_locked()
    import asyncio
    import sys
    import uvicorn

    if sys.platform == "win32":
        def _win_proactor_noise_handler(loop, context):
            exc = context.get("exception")
            if isinstance(exc, OSError) and getattr(exc, "winerror", None) == 64:
                return
            loop.default_exception_handler(context)

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.set_exception_handler(_win_proactor_noise_handler)
        except Exception:
            pass

    if forced:
        port = int(forced)
    else:
        port = int(os.environ.get("RUZGAR_API_PORT", "8779") or "8779")
    uvicorn.run(
        "desktop_server:app",
        host="127.0.0.1",
        port=port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
