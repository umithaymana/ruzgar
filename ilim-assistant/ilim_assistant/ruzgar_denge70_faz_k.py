# Created by Ümit & Gökçenur
"""Ana Motor — Faz K: denge70 çekim yardımcısı ve health."""

from __future__ import annotations

import os
import subprocess

DENGE70_FAZ_K_VERSION = "denge70-faz-k-v1-2026-06-11"


def denge70_model_name() -> str:
    return (
        os.environ.get("RUZGAR_BRAIN_DENGE70_MODEL", "").strip()
        or os.environ.get("OLLAMA_DENGE70_MODEL", "").strip()
        or "llama3.1:70b"
    )


def denge70_pull_hint() -> str:
    m = denge70_model_name()
    return f"ollama pull {m}"


def denge70_pull_command() -> list[str]:
    return ["ollama", "pull", denge70_model_name()]


def try_ollama_pull_denge70(*, timeout_sec: int = 30) -> dict[str, object]:
    """Yalnızca durum — gerçek pull kullanıcı/CI tetikler."""
    from ilim_assistant.llm_brain import denge70_readiness

    d = denge70_readiness()
    if d.get("ready"):
        return {
            "ok": True,
            "already_ready": True,
            "model": d.get("model"),
            "version": DENGE70_FAZ_K_VERSION,
        }
    cmd = denge70_pull_command()
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            check=False,
        )
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "cmd": " ".join(cmd),
            "stdout_tail": (proc.stdout or "")[-400:],
            "stderr_tail": (proc.stderr or "")[-400:],
            "version": DENGE70_FAZ_K_VERSION,
        }
    except FileNotFoundError:
        return {
            "ok": False,
            "error": "ollama bulunamadı",
            "hint": denge70_pull_hint(),
            "version": DENGE70_FAZ_K_VERSION,
        }
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "error": "pull zaman aşımı (kısa kontrol)",
            "hint": denge70_pull_hint(),
            "version": DENGE70_FAZ_K_VERSION,
        }


def denge70_faz_k_status() -> dict[str, object]:
    from ilim_assistant.llm_brain import denge70_readiness

    d = denge70_readiness()
    return {
        "version": DENGE70_FAZ_K_VERSION,
        "model": denge70_model_name(),
        "ready": bool(d.get("ready")),
        "hint": d.get("hint") or denge70_pull_hint(),
        "pull_cmd": denge70_pull_hint(),
    }
