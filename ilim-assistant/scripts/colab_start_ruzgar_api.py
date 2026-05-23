#!/usr/bin/env python3
"""
Google Colab'da Rüzgar API (desktop_server) + ngrok tüneli.

Kullanım (Colab hücresinde):
  %cd /content/ruzgar/ilim-assistant
  !python scripts/colab_start_ruzgar_api.py --ngrok-token YOUR_NGROK_TOKEN
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

_IA = Path(__file__).resolve().parents[1]


def _apply_colab_env() -> None:
    os.environ.setdefault("RUZGAR_CORS_PERMISSIVE", "1")
    os.environ.setdefault("RUZGAR_OLLAMA_ONLY", "0")
    os.environ.setdefault("RUZGAR_DISABLE_LOCAL_OLLAMA", "1")
    os.environ.setdefault("RUZGAR_LIGHT_CHAT", "1")
    os.environ.setdefault("RUZGAR_SKIP_RAG_WARMUP", "1")
    os.environ.setdefault("RUZGAR_STREAM_PREFETCH_BUNDLE", "0")
    os.environ.setdefault("RUZGAR_GEMINI_ONLY", "0")
    os.environ.setdefault("RUZGAR_GEMINI_DAEMON", "0")
    os.environ.setdefault("RUZGAR_BRAIN_FALLBACK_CHAIN", "gemini,groq")
    os.environ.setdefault("RUZGAR_API_PORT", "8779")
    try:
        from ilim_assistant.env_bootstrap import ensure_ruzgar_env

        ensure_ruzgar_env()
    except Exception:
        pass


def _load_brain_env() -> None:
    p = _IA / "RUZGAR_BRAIN.env"
    if not p.is_file():
        print("UYARI: RUZGAR_BRAIN.env yok — Colab'da GLOBAL_API_KEY / GROQ_API_KEY ortamına yazın.")
        return
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and v:
            os.environ[k] = v


def _pip(*specs: str) -> None:
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-q", *specs],
        cwd=str(_IA),
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Rüzgar API + ngrok (Colab)")
    ap.add_argument("--port", type=int, default=8779)
    ap.add_argument("--ngrok-token", default=os.environ.get("NGROK_AUTHTOKEN", ""))
    ap.add_argument("--no-ngrok", action="store_true")
    args = ap.parse_args()

    os.chdir(_IA)
    _pip("uvicorn[standard]", "pyngrok", "httpx")
    _apply_colab_env()
    _load_brain_env()

    if not os.environ.get("GLOBAL_API_KEY", "").strip():
        print("HATA: GLOBAL_API_KEY yok. RUZGAR_BRAIN.env veya Colab gizli değişkeni doldurun.")
        return 1

    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "desktop_server:app",
            "--host",
            "0.0.0.0",
            "--port",
            str(args.port),
        ],
        cwd=str(_IA),
        env=os.environ.copy(),
    )
    time.sleep(8)
    if proc.poll() is not None:
        print("API süreci hemen kapandı — uvicorn loglarına bakın.")
        return 1

    if args.no_ngrok:
        print(f"Yerel (Colab içi): http://127.0.0.1:{args.port}/api/health")
        proc.wait()
        return 0

    if not args.ngrok_token.strip():
        print("ngrok token gerekli: https://dashboard.ngrok.com/get-started/your-authtoken")
        print("  python scripts/colab_start_ruzgar_api.py --ngrok-token TOKEN")
        proc.terminate()
        return 1

    from pyngrok import conf, ngrok

    conf.get_default().auth_token = args.ngrok_token.strip()
    tunnel = ngrok.connect(args.port, bind_tls=True)
    public = getattr(tunnel, "public_url", None) or str(tunnel)
    public = public.rstrip("/")

    print("\n" + "=" * 60)
    print("Rüzgar Colab motoru hazır")
    print("Bu adresi PC'de ruzgar-desktop/ruzgar_remote_api.txt dosyasına yazın:")
    print(public)
    print("=" * 60)
    print("\nPowerShell (PC):")
    print(f'  .\\scripts\\Set-RuzgarColabUrl.ps1 -Url "{public}"')
    print("\nSonra: .\\Ruzgar.ps1")
    print("=" * 60 + "\n")

    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
    ngrok.disconnect(public)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
