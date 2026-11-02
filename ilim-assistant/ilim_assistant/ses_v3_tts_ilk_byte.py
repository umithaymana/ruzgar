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

V3_VERSION = "ses-v3-tts-ilk-byte-v1-2026-11-03"

# UI ilk cümle tamponu ~130; birleşik parçalar ~520 — üstü pool yoluna düşer.
_DEFAULT_FAST_CHARS = 520


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
    NoAudioReceived / boş stream'te yeniden dener.
    """
    from ilim_assistant.tts_service import edge_tts_import

    attempts = v3_retries() if retries is None else max(0, retries)
    edge_tts = edge_tts_import()
    last_err = ""
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
                return {
                    "ok": True,
                    "bytes": bytes(buf),
                    "first_byte_ms": round(first_ms, 1) if first_ms is not None else None,
                    "total_ms": round((time.perf_counter() - t0) * 1000.0, 1),
                    "attempts": attempt + 1,
                    "note": "",
                }
            last_err = "stream:no_audio_chunk"
        except Exception as exc:
            last_err = f"{type(exc).__name__}:{exc}"[:180]
            if not _is_no_audio(exc) and "no_audio" not in last_err.lower():
                # Ağ dışı beklenmeyen hata — bir kez daha dene, sonra kır
                if attempt >= attempts:
                    break
            await asyncio.sleep(0.12 * (attempt + 1))
            continue
        await asyncio.sleep(0.12 * (attempt + 1))
    return {
        "ok": False,
        "bytes": b"",
        "first_byte_ms": None,
        "total_ms": None,
        "attempts": attempts + 1,
        "note": last_err or "empty",
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
    rate = os.environ.get("RUZGAR_TTS_V3_RATE", "+0%").strip() or "+0%"
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
