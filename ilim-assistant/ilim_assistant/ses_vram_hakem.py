# Created by Ümit & Gökçenur
"""8 GB VRAM hakemi — Ollama / XTTS / Whisper çalışma sırası.

İlke: aynı anda GPU'da ağır iki iş olmasın.
Whisper varsayılan CPU (zaten); XTTS öncesi Ollama unload + empty_cache;
XTTS sonrası isteğe bağlı Ollama kısa keep_alive.
"""
from __future__ import annotations

import os
import threading
import time
from contextlib import contextmanager
from typing import Any, Iterator, Literal

VRAM_VERSION = "ses-vram-hakem-v1-2026-11-21"

Owner = Literal["idle", "xtts", "whisper", "ollama", "other"]

_lock = threading.RLock()
_owner: Owner = "idle"
_owner_since: float = 0.0
_LAST: dict[str, Any] = {}


def vram_hakem_enabled() -> bool:
    return os.environ.get("RUZGAR_VRAM_HAKEM", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def vram_budget_mb() -> int:
    try:
        return max(2048, int(os.environ.get("RUZGAR_VRAM_BUDGET_MB", "8192")))
    except ValueError:
        return 8192


def snapshot() -> dict[str, Any]:
    with _lock:
        free = None
        total = None
        try:
            import torch

            if torch.cuda.is_available():
                free, total = torch.cuda.mem_get_info(0)
                free = int(free // (1024 * 1024))
                total = int(total // (1024 * 1024))
        except Exception:
            pass
        return {
            "version": VRAM_VERSION,
            "enabled": vram_hakem_enabled(),
            "budget_mb": vram_budget_mb(),
            "owner": _owner,
            "owner_age_s": round(time.time() - _owner_since, 1) if _owner_since else 0,
            "cuda_free_mb": free,
            "cuda_total_mb": total,
            "last": dict(_LAST),
        }


def _empty_cuda() -> None:
    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
    except Exception:
        pass


def unload_whisper_gpu() -> dict[str, Any]:
    """Whisper CUDA'daysa modeli bırak (CPU varsayılan — çoğu zaman no-op)."""
    out: dict[str, Any] = {"ok": True, "action": "none"}
    try:
        from ilim_assistant.stt_whisper import unload_model, whisper_runtime_meta

        meta = whisper_runtime_meta()
        if str(meta.get("device") or "").lower() == "cuda":
            info = unload_model()
            _empty_cuda()
            out["action"] = "whisper_unloaded"
            out["info"] = info
        else:
            out["action"] = "whisper_cpu_or_empty"
            out["device"] = meta.get("device")
    except Exception as exc:
        out = {"ok": False, "note": str(exc)[:160]}
    return out


def unload_ollama_vram() -> dict[str, Any]:
    """Ollama modeli VRAM'den düşür (keep_alive=0)."""
    out: dict[str, Any] = {"ok": False, "action": "skip"}
    if not vram_hakem_enabled():
        out["note"] = "hakem kapalı"
        return out
    if os.environ.get("RUZGAR_VRAM_UNLOAD_OLLAMA", "1").strip().lower() in (
        "0",
        "false",
        "no",
        "off",
    ):
        out["note"] = "RUZGAR_VRAM_UNLOAD_OLLAMA=0"
        return out
    try:
        from ilim_assistant.llm_ollama import (
            DEFAULT_OLLAMA_CHAT_MODEL,
            _http_session_singleton,
            _ollama_api_root,
            ollama_reachable,
        )

        if not ollama_reachable(timeout_sec=2.0):
            out["note"] = "ollama_unreachable"
            return out
        model = (
            os.environ.get("RUZGAR_BRAIN_DENGE_MODEL")
            or os.environ.get("OLLAMA_CHAT_MODEL")
            or DEFAULT_OLLAMA_CHAT_MODEL
        ).strip()
        root = _ollama_api_root()
        r = _http_session_singleton().post(
            f"{root}/api/generate",
            json={
                "model": model,
                "prompt": ".",
                "stream": False,
                "keep_alive": 0,
                "options": {"num_predict": 1},
            },
            timeout=20.0,
        )
        out["ok"] = r.status_code == 200
        out["action"] = "ollama_keep_alive_0"
        out["status"] = r.status_code
        out["model"] = model
    except Exception as exc:
        out = {"ok": False, "note": str(exc)[:160]}
    return out


def restore_ollama_warm() -> dict[str, Any]:
    """XTTS sonrası sohbet için kısa keep_alive (opsiyon)."""
    if os.environ.get("RUZGAR_VRAM_RESTORE_OLLAMA", "0").strip().lower() not in (
        "1",
        "true",
        "yes",
        "on",
    ):
        return {"ok": True, "action": "skip_restore"}
    try:
        from ilim_assistant.llm_ollama import preload_primary_chat_model

        return {"ok": True, "action": "preload", "result": preload_primary_chat_model(timeout_sec=45)}
    except Exception as exc:
        return {"ok": False, "note": str(exc)[:160]}


def acquire(owner: Owner, *, prepare: bool = True) -> dict[str, Any]:
    global _owner, _owner_since, _LAST
    with _lock:
        prev = _owner
        actions: list[dict[str, Any]] = []
        if prepare and vram_hakem_enabled() and owner == "xtts":
            actions.append(unload_whisper_gpu())
            actions.append(unload_ollama_vram())
            _empty_cuda()
        _owner = owner
        _owner_since = time.time()
        _LAST = {
            "acquire": owner,
            "prev": prev,
            "actions": actions,
            "ts": time.time(),
        }
        return {"ok": True, "owner": owner, "prev": prev, "actions": actions}


def release(owner: Owner | None = None, *, restore: bool = False) -> dict[str, Any]:
    global _owner, _owner_since, _LAST
    with _lock:
        if owner and _owner != owner and _owner != "idle":
            return {"ok": False, "note": f"owner_mismatch have={_owner} want={owner}"}
        prev = _owner
        _owner = "idle"
        _owner_since = time.time()
        _empty_cuda()
        rest = restore_ollama_warm() if restore else {"ok": True, "action": "no_restore"}
        _LAST = {"release": prev, "restore": rest, "ts": time.time()}
        return {"ok": True, "prev": prev, "restore": rest}


@contextmanager
def hold(owner: Owner, *, prepare: bool = True, restore: bool = False) -> Iterator[dict[str, Any]]:
    info = acquire(owner, prepare=prepare)
    try:
        yield info
    finally:
        release(owner, restore=restore)
