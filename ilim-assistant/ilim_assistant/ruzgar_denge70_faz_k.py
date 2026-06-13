# Created by Ümit & Gökçenur
"""Ana Motor — Faz K / AC: denge70 çekim, RAM kapısı, otomatik pull ve zincir."""

from __future__ import annotations

import os
import subprocess
import threading
import time
from typing import Any

DENGE70_FAZ_K_VERSION = "denge70-otomasyon-v1-2026-06-13-faz-ac"

_pull_lock = threading.Lock()
_pull_job: dict[str, Any] = {
    "running": False,
    "phase": "idle",
    "reason": "",
    "started_at": 0.0,
    "finished_at": 0.0,
    "error": "",
    "stdout_tail": "",
}


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


def denge70_pull_timeout_sec() -> int:
    try:
        return max(120, int(os.environ.get("RUZGAR_DENGE70_PULL_TIMEOUT_SEC", "7200")))
    except ValueError:
        return 7200


def denge70_min_ram_gb() -> float:
    try:
        return max(8.0, float(os.environ.get("RUZGAR_DENGE70_MIN_RAM_GB", "14")))
    except ValueError:
        return 14.0


def denge70_ram_stats() -> dict[str, float | bool]:
    min_gb = denge70_min_ram_gb()
    if os.environ.get("RUZGAR_DENGE70_SKIP_RAM_CHECK", "0").strip().lower() in (
        "1",
        "true",
        "yes",
    ):
        return {
            "available_gb": min_gb,
            "total_gb": min_gb,
            "min_gb": min_gb,
            "sufficient": True,
        }
    try:
        import psutil  # type: ignore[import-not-found]

        vm = psutil.virtual_memory()
        avail = float(vm.available) / (1024**3)
        total = float(vm.total) / (1024**3)
        return {
            "available_gb": round(avail, 2),
            "total_gb": round(total, 2),
            "min_gb": min_gb,
            "sufficient": avail >= min_gb,
        }
    except Exception:
        return {
            "available_gb": 0.0,
            "total_gb": 0.0,
            "min_gb": min_gb,
            "sufficient": False,
        }


def denge70_ram_sufficient() -> bool:
    return bool(denge70_ram_stats().get("sufficient"))


def denge70_auto_chain_enabled() -> bool:
    return os.environ.get("RUZGAR_DENGE70_AUTO_CHAIN", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def denge70_auto_pull_enabled() -> bool:
    return os.environ.get("RUZGAR_DENGE70_AUTO_PULL", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def get_denge70_pull_job_status() -> dict[str, Any]:
    with _pull_lock:
        return dict(_pull_job)


def _set_pull_job(**kwargs: Any) -> None:
    with _pull_lock:
        _pull_job.update(kwargs)


def _pull_worker(*, reason: str) -> None:
    cmd = denge70_pull_command()
    timeout = denge70_pull_timeout_sec()
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        ok = proc.returncode == 0
        from ilim_assistant.llm_brain import denge70_readiness

        ready_after = bool(denge70_readiness().get("ready"))
        _set_pull_job(
            running=False,
            phase="done" if ok and ready_after else "failed",
            finished_at=time.time(),
            error="" if ok and ready_after else f"returncode={proc.returncode}",
            stdout_tail=(proc.stdout or proc.stderr or "")[-600:],
        )
        if ok and ready_after:
            print(
                f"[Rüzgar] denge70 hazır — {denge70_model_name()} ({reason})",
                flush=True,
            )
        elif not ok:
            print(
                f"[Rüzgar] denge70 pull başarısız ({reason}): "
                f"{(proc.stderr or proc.stdout or '')[-200:]}",
                flush=True,
            )
    except FileNotFoundError:
        _set_pull_job(
            running=False,
            phase="failed",
            finished_at=time.time(),
            error="ollama bulunamadı",
        )
    except subprocess.TimeoutExpired:
        _set_pull_job(
            running=False,
            phase="failed",
            finished_at=time.time(),
            error=f"zaman aşımı ({timeout}s)",
        )
    except Exception as exc:
        _set_pull_job(
            running=False,
            phase="failed",
            finished_at=time.time(),
            error=str(exc)[:200],
        )


def start_denge70_pull_background(*, reason: str = "manual") -> dict[str, Any]:
    """Arka planda ollama pull — RAM yeterliyse."""
    from ilim_assistant.llm_brain import denge70_readiness

    d = denge70_readiness()
    if d.get("ready"):
        return {
            "ok": True,
            "already_ready": True,
            "model": d.get("model"),
            "version": DENGE70_FAZ_K_VERSION,
        }

    with _pull_lock:
        if _pull_job.get("running"):
            return {
                "ok": True,
                "already_running": True,
                "job": dict(_pull_job),
                "version": DENGE70_FAZ_K_VERSION,
            }

    if not denge70_ram_sufficient():
        ram = denge70_ram_stats()
        return {
            "ok": False,
            "error": "ram_yetersiz",
            "min_ram_gb": ram.get("min_gb"),
            "available_gb": ram.get("available_gb"),
            "hint": f"En az {ram.get('min_gb')} GB boş RAM gerekli",
            "version": DENGE70_FAZ_K_VERSION,
        }

    try:
        from ilim_assistant.llm_ollama import ollama_reachable

        if not ollama_reachable():
            return {
                "ok": False,
                "error": "ollama_kapali",
                "hint": "ollama serve çalıştırın",
                "version": DENGE70_FAZ_K_VERSION,
            }
    except Exception:
        pass

    _set_pull_job(
        running=True,
        phase="pulling",
        reason=reason,
        started_at=time.time(),
        finished_at=0.0,
        error="",
        stdout_tail="",
    )
    threading.Thread(
        target=_pull_worker,
        kwargs={"reason": reason},
        daemon=True,
        name="denge70-pull",
    ).start()
    return {
        "ok": True,
        "started": True,
        "model": denge70_model_name(),
        "cmd": denge70_pull_hint(),
        "version": DENGE70_FAZ_K_VERSION,
    }


def should_auto_pull_on_startup() -> bool:
    if not denge70_auto_pull_enabled():
        return False
    from ilim_assistant.llm_brain import denge70_readiness

    if denge70_readiness().get("ready"):
        return False
    if not denge70_ram_sufficient():
        return False
    job = get_denge70_pull_job_status()
    if job.get("running"):
        return False
    try:
        from ilim_assistant.llm_ollama import ollama_reachable

        return bool(ollama_reachable())
    except Exception:
        return False


def maybe_auto_pull_on_startup() -> dict[str, Any]:
    """API açılışında — RAM yeterliyse 70B modeli arka planda indir."""
    if not should_auto_pull_on_startup():
        return {
            "ok": True,
            "skipped": True,
            "auto_pull": denge70_auto_pull_enabled(),
            "version": DENGE70_FAZ_K_VERSION,
        }
    out = start_denge70_pull_background(reason="startup_auto")
    print(
        f"[Rüzgar] denge70 otomatik pull başlatıldı — {denge70_pull_hint()}",
        flush=True,
    )
    return out


def try_ollama_pull_denge70(*, timeout_sec: int | None = None) -> dict[str, object]:
    """Senkron kısa pull (CI/smoke); uzun indirme için background kullanın."""
    from ilim_assistant.llm_brain import denge70_readiness

    d = denge70_readiness()
    if d.get("ready"):
        return {
            "ok": True,
            "already_ready": True,
            "model": d.get("model"),
            "version": DENGE70_FAZ_K_VERSION,
        }
    if not denge70_ram_sufficient():
        return {
            "ok": False,
            "error": "ram_yetersiz",
            "version": DENGE70_FAZ_K_VERSION,
        }
    cmd = denge70_pull_command()
    tmo = timeout_sec if timeout_sec is not None else min(30, denge70_pull_timeout_sec())
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=tmo,
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
            "error": "pull zaman aşımı (kısa kontrol — arka plan pull deneyin)",
            "hint": denge70_pull_hint(),
            "version": DENGE70_FAZ_K_VERSION,
        }


def denge70_auto_chain_ready() -> bool:
    if not denge70_auto_chain_enabled():
        return False
    from ilim_assistant.llm_brain import denge70_ready_for_chain

    return bool(denge70_ready_for_chain()) and denge70_ram_sufficient()


def denge70_faz_k_status() -> dict[str, object]:
    from ilim_assistant.llm_brain import denge70_readiness

    d = denge70_readiness()
    ram = denge70_ram_stats()
    job = get_denge70_pull_job_status()
    return {
        "version": DENGE70_FAZ_K_VERSION,
        "model": denge70_model_name(),
        "ready": bool(d.get("ready")),
        "ram_sufficient": bool(ram.get("sufficient")),
        "ram_available_gb": ram.get("available_gb"),
        "ram_total_gb": ram.get("total_gb"),
        "min_ram_gb": ram.get("min_gb"),
        "auto_chain": denge70_auto_chain_enabled(),
        "auto_chain_ready": denge70_auto_chain_ready(),
        "auto_pull": denge70_auto_pull_enabled(),
        "pull_job": job,
        "hint": d.get("hint") or denge70_pull_hint(),
        "pull_cmd": denge70_pull_hint(),
    }
