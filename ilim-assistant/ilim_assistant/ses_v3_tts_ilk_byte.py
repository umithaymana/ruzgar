"""
V3 — TTS ilk-byte: kısa metinde in-process stream + NoAudio retry + workers/rate.

V0 baseline first-byte ~1686 ms (Edge). Kısa sohbet parçalarında ProcessPool IPC
gecikmeyi şişiriyordu; V3 kısa yolda doğrudan Edge stream toplar.
"""
from __future__ import annotations

import asyncio
import os
import tempfile
import time
from pathlib import Path
from typing import Any

V3_VERSION = "ses-v3-tts-ilk-byte-v1-2026-11-21"

# UI ilk cümle tamponu ~130; birleşik parçalar ~520 — üstü pool yoluna düşer.
# FB cila: sohbet ilk parçaları V3'te kalsın (prosody concat first-byte şişirmesin).
_DEFAULT_FAST_CHARS = 640

# Aşama C/D — son ölçüm (text_ready→first_byte sunucu tarafı)
_LAST_FIRST_BYTE: dict[str, Any] = {}
ASAMA_C_TTS_TARGET_MS = 1000.0
ASAMA_D_TTS_KEEP_MS = 886.0


def last_tts_first_byte() -> dict[str, Any]:
    return dict(_LAST_FIRST_BYTE)

def v3_enabled() -> bool:
    return os.environ.get("RUZGAR_TTS_V3", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def v3_fast_chars() -> int:
    try:
        return max(48, int(os.environ.get("RUZGAR_TTS_V3_FAST_CHARS", str(_DEFAULT_FAST_CHARS))))
    except ValueError:
        return _DEFAULT_FAST_CHARS


def v3_retries() -> int:
    try:
        return max(0, int(os.environ.get("RUZGAR_TTS_V3_RETRIES", "2")))
    except ValueError:
        return 2


def v3_skip_meta() -> bool:
    return os.environ.get("RUZGAR_TTS_V3_SKIP_META", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def v3_workers_default() -> int:
    """Uzun metin / paralel prefetch için havuz boyutu (env yoksa 2)."""
    raw = os.environ.get("RUZGAR_TTS_MP_WORKERS", "").strip()
    if raw:
        try:
            return max(1, int(raw))
        except ValueError:
            return 2
    return 2


def wants_v3_fast_path(text: str) -> bool:
    if not v3_enabled():
        return False
    t = (text or "").strip()
    return 2 <= len(t) <= v3_fast_chars()


def _is_no_audio(exc: BaseException) -> bool:
    name = type(exc).__name__
    msg = str(exc)
    return "NoAudioReceived" in name or "NoAudioReceived" in msg


async def edge_stream_collect_mp3(
    text: str,
    *,
    voice: str,
    rate: str,
    pitch: str,
    retries: int | None = None,
) -> dict[str, Any]:
    """
    Edge stream → ham mp3 bayt. İlk audio chunk ms + retry sayacı.
    NoAudioReceived / boş stream / ağ hatalarında yeniden dener (Aşama D).
    """
    from ilim_assistant.tts_service import edge_tts_import

    try:
        from ilim_assistant.ses_asama_d import classify_edge_error
    except Exception:
        classify_edge_error = None  # type: ignore

    attempts = v3_retries() if retries is None else max(0, retries)
    edge_tts = edge_tts_import()
    last_err = ""
    last_kind = ""
    for attempt in range(attempts + 1):
        t0 = time.perf_counter()
        first_ms: float | None = None
        buf = bytearray()
        try:
            comm = edge_tts.Communicate(text.strip(), voice, rate=rate, pitch=pitch)
            async for chunk in comm.stream():
                if chunk.get("type") != "audio":
                    continue
                data = chunk.get("data") or b""
                if not data:
                    continue
                if first_ms is None:
                    first_ms = (time.perf_counter() - t0) * 1000.0
                buf.extend(data)
            if buf:
                result = {
                    "ok": True,
                    "bytes": bytes(buf),
                    "first_byte_ms": round(first_ms, 1) if first_ms is not None else None,
                    "total_ms": round((time.perf_counter() - t0) * 1000.0, 1),
                    "attempts": attempt + 1,
                    "note": "",
                    "metric": "text_ready→first_audio_chunk",
                    "under_1s": (
                        first_ms is not None and float(first_ms) < ASAMA_C_TTS_TARGET_MS
                    ),
                    "under_d_keep": (
                        first_ms is not None and float(first_ms) <= ASAMA_D_TTS_KEEP_MS
                    ),
                    "under_900": (
                        first_ms is not None and float(first_ms) < 900.0
                    ),
                    "asama_d": True,
                }
                _LAST_FIRST_BYTE.clear()
                _LAST_FIRST_BYTE.update(
                    {
                        k: v
                        for k, v in result.items()
                        if k != "bytes"
                    }
                )
                _LAST_FIRST_BYTE["bytes_len"] = len(result["bytes"])
                # FB cila — başarılı stream ılık işaretle
                try:
                    import ilim_assistant.ses_fb_cila as _fb

                    _fb._LAST_WARM = time.time()
                except Exception:
                    pass
                return result
            last_err = "stream:no_audio_chunk"
            last_kind = "no_audio"
        except Exception as exc:
            last_err = f"{type(exc).__name__}:{exc}"[:180]
            if classify_edge_error is not None:
                info = classify_edge_error(exc)
                last_kind = str(info.get("kind") or "")
                if not info.get("retryable", True) or attempt >= attempts:
                    break
            elif not _is_no_audio(exc) and "no_audio" not in last_err.lower():
                if attempt >= attempts:
                    break
            # Aşama D: kısa üstel bekleme (0.08 / 0.16 / 0.24…)
            await asyncio.sleep(0.08 * (attempt + 1))
            continue
        await asyncio.sleep(0.08 * (attempt + 1))
    user_msg = last_err or "empty"
    if classify_edge_error is not None:
        info = classify_edge_error(last_err)
        user_msg = str(info.get("user_message") or user_msg)
        last_kind = str(info.get("kind") or last_kind)
    return {
        "ok": False,
        "bytes": b"",
        "first_byte_ms": None,
        "total_ms": None,
        "attempts": attempts + 1,
        "note": last_err or "empty",
        "error_kind": last_kind,
        "user_message": user_msg,
        "asama_d": True,
    }


async def synthesize_edge_mp3_v3_fast(
    text: str,
    *,
    voice: str,
    rate: str,
    pitch: str,
    meta: dict[str, Any],
) -> Path:
    """Kısa metin: in-process stream+retry; isteğe bağlı ID3 atla (sıcak yol)."""
    from ilim_assistant.tts_service import apply_mp3_metadata

    result = await edge_stream_collect_mp3(text, voice=voice, rate=rate, pitch=pitch)
    if not result.get("ok") or not result.get("bytes"):
        raise RuntimeError(result.get("note") or "V3 Edge TTS boş")
    fd, tmp = tempfile.mkstemp(suffix=".mp3")
    os.close(fd)
    out = Path(tmp)
    out.write_bytes(result["bytes"])
    if not v3_skip_meta():
        meta_full = {
            **meta,
            "engine": "edge-tts",
            "mimarlar": "Ümit & Gökçenur",
            "tts_v3": True,
            "first_byte_ms": result.get("first_byte_ms"),
            "attempts": result.get("attempts"),
        }
        apply_mp3_metadata(out, meta_full)
    return out


def measure_v3_compare(text: str | None = None) -> dict[str, Any]:
    """Smoke/ölçüm: V3 stream first-byte (senkron sarmalayıcı)."""
    sample = (text or "Merhaba Ümit abi, Rüzgar V3 ses testi.").strip()
    voice = os.environ.get("RUZGAR_TTS_VOICE", "tr-TR-AhmetNeural").strip() or "tr-TR-AhmetNeural"
    try:
        from ilim_assistant.ses_asama_d import default_rate

        rate = default_rate()
    except Exception:
        rate = os.environ.get("RUZGAR_TTS_V3_RATE", "+3%").strip() or "+3%"
    pitch = "+0Hz"

    async def _run() -> dict[str, Any]:
        from ilim_assistant.tts_service import edge_available

        if not edge_available():
            return {"version": V3_VERSION, "ok": False, "note": "edge-tts yok"}
        r = await edge_stream_collect_mp3(sample, voice=voice, rate=rate, pitch=pitch)
        return {
            "version": V3_VERSION,
            "ok": bool(r.get("ok")),
            "text_chars": len(sample),
            "voice": voice,
            "rate": rate,
            "first_byte_ms": r.get("first_byte_ms"),
            "total_ms": r.get("total_ms"),
            "attempts": r.get("attempts"),
            "bytes": len(r.get("bytes") or b""),
            "fast_chars": v3_fast_chars(),
            "workers_default": v3_workers_default(),
            "v0_baseline_first_byte_ms": 1686,
            "note": r.get("note") or "",
        }

    return asyncio.run(_run())
