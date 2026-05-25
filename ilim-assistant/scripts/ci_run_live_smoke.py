#!/usr/bin/env python3
"""CI: API baslat, health bekle, programlama_smoke --live calistir."""
from __future__ import annotations

import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

_IA = Path(__file__).resolve().parents[1]
_PORT = int(os.environ.get("RUZGAR_API_PORT", "8779") or "8779")
_BASE = f"http://127.0.0.1:{_PORT}"
_WAIT_SEC = int(os.environ.get("RUZGAR_CI_HEALTH_WAIT", "120") or "120")


def _health_ok() -> bool:
    try:
        with urllib.request.urlopen(f"{_BASE}/api/health", timeout=5) as r:
            if r.status != 200:
                return False
            raw = r.read().decode("utf-8", errors="replace")
            return '"ok"' in raw or "true" in raw.lower()
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def main() -> int:
    env = os.environ.copy()
    env.setdefault("RUZGAR_SKIP_RAG_WARMUP", "1")
    env.setdefault("RUZGAR_DISABLE_GEMINI", "1")
    env.setdefault("RUZGAR_DISABLE_GROQ", "1")
    env.setdefault("RUZGAR_FAZ17_LLM_SUGGEST", "0")
    env["RUZGAR_API_PORT"] = str(_PORT)

    proc = subprocess.Popen(
        [sys.executable, "run_desktop_api.py"],
        cwd=str(_IA),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    print(f"[ci] API baslatildi PID={proc.pid} port={_PORT}", flush=True)

    deadline = time.monotonic() + _WAIT_SEC
    ready = False
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            out = (proc.stdout.read() if proc.stdout else "") or ""
            print(f"[ci] API erken kapandi:\n{out[-4000:]}", flush=True)
            return 1
        if _health_ok():
            ready = True
            break
        time.sleep(2)

    if not ready:
        proc.kill()
        print(f"[ci] health timeout ({_WAIT_SEC}s)", flush=True)
        return 1

    print("[ci] health OK", flush=True)
    smoke = subprocess.run(
        [sys.executable, "scripts/programlama_smoke.py", "--live", _BASE],
        cwd=str(_IA),
        env=env,
    )
    proc.terminate()
    try:
        proc.wait(timeout=15)
    except subprocess.TimeoutExpired:
        proc.kill()
    return int(smoke.returncode or 0)


if __name__ == "__main__":
    raise SystemExit(main())
