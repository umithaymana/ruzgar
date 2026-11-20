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


def _api_host() -> str:
    """Bugün kapı 127.0.0.1. Halka açılışta RUZGAR_API_HOST veya --host, kimlik ve TLS ile."""
    if "--host" in sys.argv:
        i = sys.argv.index("--host")
        if i + 1 < len(sys.argv) and sys.argv[i + 1].strip():
            return sys.argv[i + 1].strip()
    return (os.environ.get("RUZGAR_API_HOST") or "127.0.0.1").strip() or "127.0.0.1"


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
    """.cursorrules — port açılmadan ana motor → çekirdek → 7 ara motor (sıra kilitli)."""
    from ilim_assistant.ruzgar_boot_kilit import boot_motorlar_anaonce

    boot_motorlar_anaonce(announce=True)


def main() -> None:
    forced = (os.environ.get("RUZGAR_CI_FORCED_PORT") or "").strip()
    _bootstrap()
    # Kilit: DEFER yalnız yardımcı ısınma (RAG vb.); motor 1–3 sırası her zaman port öncesi.
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
    host = _api_host()
    # Health / mobil erişim gerçek bind ile aynı kalsın (--host CLI env'yi ezmesin)
    os.environ["RUZGAR_API_HOST"] = host
    os.environ["RUZGAR_API_PORT"] = str(port)
    print(f"[Rüzgar] API bind {host}:{port}", file=sys.stderr, flush=True)
    uvicorn.run(
        "desktop_server:app",
        host=host,
        port=port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
