"""
V1 — STT/TTS ısınma (port sonrası arka plan).

Boot 1–3 (ana motor → çekirdek → 5 ara) ve uvicorn portunu geciktirmez.
`desktop_server._sync_startup_warmups` içinden çağrılır.
"""
from __future__ import annotations

import os
import time
from typing import Any

V1_VERSION = "ses-v1-isinma-v1-2026-10-23"

_LAST: dict[str, Any] = {}


def ses_v1_warmup_enabled() -> bool:
    return os.environ.get("RUZGAR_SES_V1_WARMUP", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def last_warmup_status() -> dict[str, Any]:
    return dict(_LAST)


def prime_stt_whisper() -> dict[str, Any]:
    """Whisper get_model + Aşama C warm infer — soğuk ilk STT turunu keser."""
    out: dict[str, Any] = {
        "ok": False,
        "ms": None,
        "model": None,
        "note": "",
        "load_ms": None,
        "infer_ms": None,
    }
    if os.environ.get("RUZGAR_STT", "").strip().lower() in ("0", "false", "no"):
        out["note"] = "RUZGAR_STT=0"
        return out
    try:
        from ilim_assistant.stt_whisper import (
            stt_runtime_available,
            warm_stt_model,
            whisper_model_name,
        )

        if not stt_runtime_available():
            out["note"] = "faster-whisper yok"
            return out
        out["model"] = whisper_model_name()
        t0 = time.perf_counter()
        warm = warm_stt_model()
        out["ms"] = round((time.perf_counter() - t0) * 1000.0, 1)
        out["load_ms"] = warm.get("load_ms")
        out["infer_ms"] = warm.get("infer_ms")
        out["meta"] = warm.get("meta") or {}
        out["ok"] = bool(warm.get("ok"))
        out["note"] = warm.get("note") or ""
    except Exception as exc:
        out["note"] = str(exc)[:200]
    return out


def prime_tts_pool() -> dict[str, Any]:
    """Edge-TTS ProcessPool + Aşama C kısa stream ısınma (TLS/Edge yolu)."""
    out: dict[str, Any] = {
        "ok": False,
        "ms": None,
        "note": "",
        "pool_ms": None,
        "edge_first_byte_ms": None,
    }
    try:
        from ilim_assistant.tts_service import edge_available, prime_tts_process_pool

        if not edge_available():
            out["note"] = "edge-tts yok"
            return out
        t0 = time.perf_counter()
        prime_tts_process_pool()
        out["pool_ms"] = round((time.perf_counter() - t0) * 1000.0, 1)
        # Aşama C — idle Edge stream ısınma (barge flush bozulmaz; yalnız warm)
        try:
            from ilim_assistant.ses_v3_tts_ilk_byte import edge_stream_collect_mp3

            voice = (
                os.environ.get("RUZGAR_TTS_VOICE", "tr-TR-AhmetNeural").strip()
                or "tr-TR-AhmetNeural"
            )

            async def _warm() -> dict[str, Any]:
                return await edge_stream_collect_mp3(
                    "Merhaba.",
                    voice=voice,
                    rate="+0%",
                    pitch="+0Hz",
                    retries=1,
                )

            import asyncio

            warm_r = asyncio.run(_warm())
            out["edge_first_byte_ms"] = warm_r.get("first_byte_ms")
            out["edge_ok"] = bool(warm_r.get("ok"))
            if not warm_r.get("ok"):
                out["note"] = (warm_r.get("note") or "edge_warm_fail")[:160]
        except Exception as exc:
            out["note"] = f"edge_warm:{exc}"[:160]
        out["ms"] = round((time.perf_counter() - t0) * 1000.0, 1)
        out["ok"] = True
    except Exception as exc:
        out["note"] = str(exc)[:200]
    return out

def run_ses_v1_warmup(*, dry_run: bool = False) -> dict[str, Any]:
    """STT + TTS ısınma; dry_run=sadece kapı/versiyon (smoke)."""
    global _LAST
    report: dict[str, Any] = {
        "version": V1_VERSION,
        "enabled": ses_v1_warmup_enabled(),
        "dry_run": dry_run,
        "stt": {},
        "tts": {},
    }
    if dry_run or not ses_v1_warmup_enabled():
        report["stt"] = {"ok": False, "note": "dry_run_or_disabled"}
        report["tts"] = {"ok": False, "note": "dry_run_or_disabled"}
        _LAST = report
        return report
    report["stt"] = prime_stt_whisper()
    report["tts"] = prime_tts_pool()
    _LAST = report
    try:
        from ilim_assistant.ruzgar_tur_teshis_f0 import mark_warmup

        if report["stt"].get("ok") or report["tts"].get("ok"):
            mark_warmup("whisper_tts", True)
    except Exception:
        pass
    try:
        print(
            f"[Rüzgar V1] STT ısınma ok={report['stt'].get('ok')} "
            f"ms={report['stt'].get('ms')} · TTS ok={report['tts'].get('ok')} "
            f"ms={report['tts'].get('ms')}",
            flush=True,
        )
    except Exception:
        pass
    return report
