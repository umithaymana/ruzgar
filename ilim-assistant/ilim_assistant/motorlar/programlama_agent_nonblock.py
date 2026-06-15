# Created by Ümit & Gökçenur
"""
Programlama motoru — P8 / S10: agent sırasında API kilidi yok.

P7 threadpool doğrulaması:
  - Uzun senkron iş threadpool'da çalışırken lite health yanıt vermeli.
"""

from __future__ import annotations

import os
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

AGENT_NONBLOCK_VERSION = "programlama-agent-nonblock-v1-2026-06-15"
_DEFAULT_PORT = 8779
_HEALTH_TIMEOUT_SEC = 2.5
_BUSY_WORK_SEC = 3.0


def agent_nonblock_enabled() -> bool:
    return os.environ.get("RUZGAR_PROG_AGENT_NONBLOCK", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _api_port() -> int:
    try:
        from ilim_assistant.ruzgar_api_port import resolve_api_port

        return int(resolve_api_port())
    except Exception:
        raw = os.environ.get("RUZGAR_API_PORT", "").strip()
        if raw.isdigit():
            return int(raw)
        return _DEFAULT_PORT


def _lite_health_ms(port: int | None = None) -> tuple[bool, int, str]:
    p = port if port is not None else _api_port()
    url = f"http://127.0.0.1:{p}/api/health?lite=1"
    t0 = time.perf_counter()
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=_HEALTH_TIMEOUT_SEC) as resp:
            body = (resp.read() or b"")[:400].decode("utf-8", errors="replace")
        ms = int((time.perf_counter() - t0) * 1000)
        ok = '"ok":true' in body.replace(" ", "") or '"ok": true' in body
        return ok, ms, body[:120]
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        ms = int((time.perf_counter() - t0) * 1000)
        return False, ms, str(exc)[:120]


def _simulate_blocking_work(seconds: float) -> None:
  deadline = time.perf_counter() + max(0.5, seconds)
  n = 0
  while time.perf_counter() < deadline:
      n += 1
  _ = n


def run_agent_nonblock_gate(
    workspace_root: str | Path | None = None,
    *,
    port: int | None = None,
) -> dict[str, Any]:
    del workspace_root  # API port üzerinden ölçülür
    checks: dict[str, bool] = {}
    detail_parts: list[str] = []
    if not agent_nonblock_enabled():
        return {
            "ok": False,
            "detail": "RUZGAR_PROG_AGENT_NONBLOCK=0",
            "checks": checks,
            "version": AGENT_NONBLOCK_VERSION,
        }

    p = port if port is not None else _api_port()
    idle_ok, idle_ms, idle_snip = _lite_health_ms(p)
    checks["health_idle"] = idle_ok and idle_ms < int(_HEALTH_TIMEOUT_SEC * 1000)
    if not checks["health_idle"]:
        detail_parts.append(f"idle:{idle_ms}ms {idle_snip}")

    busy_result: dict[str, Any] = {"ok": False, "ms": 9999, "snip": "not_run"}
    worker_done = threading.Event()

    def _worker() -> None:
        nonlocal busy_result
        try:
            from starlette.concurrency import run_in_threadpool
            import anyio

            async def _run() -> None:
                await run_in_threadpool(_simulate_blocking_work, _BUSY_WORK_SEC)

            anyio.run(_run)
        except Exception:
            _simulate_blocking_work(_BUSY_WORK_SEC)
        worker_done.set()

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    time.sleep(0.35)
    busy_ok, busy_ms, busy_snip = _lite_health_ms(p)
    busy_result = {"ok": busy_ok, "ms": busy_ms, "snip": busy_snip}
    worker_done.wait(timeout=_BUSY_WORK_SEC + 5.0)

    checks["health_during_busy"] = busy_ok and busy_ms < int(_HEALTH_TIMEOUT_SEC * 1000)
    if not checks["health_during_busy"]:
        detail_parts.append(f"busy:{busy_ms}ms {busy_snip}")

    try:
        from starlette.concurrency import iterate_in_threadpool
        import anyio

        async def _probe_iterate() -> bool:
            def _gen():
                for i in range(4):
                    _simulate_blocking_work(0.4)
                    yield {"i": i}

            n = 0
            async for _ in iterate_in_threadpool(_gen()):
                n += 1
                ok_mid, ms_mid, _ = _lite_health_ms(p)
                if not ok_mid or ms_mid >= int(_HEALTH_TIMEOUT_SEC * 1000):
                    return False
            return n == 4

        checks["iterate_threadpool_health"] = bool(anyio.run(_probe_iterate))
    except Exception as exc:
        checks["iterate_threadpool_health"] = False
        detail_parts.append(f"iterate:{exc}")

    ok = all(checks.values()) if checks else False
    return {
        "ok": ok,
        "detail": "; ".join(detail_parts) if detail_parts else "agent nonblock gate",
        "checks": checks,
        "port": p,
        "idle_ms": idle_ms,
        "busy_ms": busy_ms,
        "version": AGENT_NONBLOCK_VERSION,
    }


def format_agent_nonblock_instant_report(rep: dict[str, Any]) -> str:
    checks = rep.get("checks") or {}
    lines = [
        "Ümit abi, **P8 agent non-block gate** (S10):",
        "",
        f"Sonuç: **{'OK' if rep.get('ok') else 'KIRIK'}**",
        f"Port: `{rep.get('port', 8779)}` · idle: {rep.get('idle_ms', '?')} ms · busy: {rep.get('busy_ms', '?')} ms",
    ]
    for key, val in checks.items():
        lines.append(f"- {'✓' if val else '✗'} {key}")
    if not rep.get("ok"):
        lines.append(
            "\n_Not: API kapalıysa veya eski sürüm (threadpool yok) çalışıyorsa KIRIK görünür — `Ruzgar.ps1 -ForceRestart`._"
        )
    lines.append(f"({AGENT_NONBLOCK_VERSION})")
    return "\n".join(lines)


def wants_agent_nonblock_gate(message: str) -> bool:
    low = (message or "").lower()
    return any(
        k in low
        for k in (
            "p8 gate",
            "p8 nonblock",
            "agent nonblock gate",
            "s10 gate",
            "api kilidi test",
        )
    )


def maybe_instant_agent_nonblock(
    message: str,
    workspace_root: str | Path | None,
) -> str | None:
    if not wants_agent_nonblock_gate(message):
        return None
    rep = run_agent_nonblock_gate(workspace_root)
    return format_agent_nonblock_instant_report(rep)
