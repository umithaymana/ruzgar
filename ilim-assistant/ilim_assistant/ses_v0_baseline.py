"""
V0 — STT/TTS gecikme baseline ölçümü (ms).

Ağır model indirme yoksa STT `skip`; TTS Edge kısa cümle + stream ilk-byte.
"""
from __future__ import annotations

import asyncio
import json
import os
import struct
import tempfile
import time
import wave
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

V0_VERSION = "ses-v0-baseline-v1-2026-10-23"


def _write_silent_wav(path: Path, *, seconds: float = 0.6, rate: int = 16000) -> None:
    n = int(rate * seconds)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(struct.pack("<" + "h" * n, *([0] * n)))


def measure_stt_baseline(*, allow_model_load: bool = True) -> dict[str, Any]:
    out: dict[str, Any] = {
        "available": False,
        "model": None,
        "get_model_ms": None,
        "transcribe_silent_ms": None,
        "note": "",
    }
    try:
        from ilim_assistant.stt_whisper import (
            get_model,
            stt_runtime_available,
            whisper_model_name,
        )
    except Exception as exc:
        out["note"] = f"import:{exc}"
        return out
    if not stt_runtime_available():
        out["note"] = "RUZGAR_STT kapalı veya faster-whisper yok"
        return out
    out["available"] = True
    out["model"] = whisper_model_name()
    if not allow_model_load:
        out["note"] = "model yükleme atlandı (RUZGAR_V0_STT_LOAD=0)"
        return out
    if os.environ.get("RUZGAR_V0_STT_LOAD", "1").strip().lower() in (
        "0",
        "false",
        "no",
    ):
        out["note"] = "model yükleme atlandı (RUZGAR_V0_STT_LOAD=0)"
        return out
    t0 = time.perf_counter()
    try:
        get_model()
        out["get_model_ms"] = round((time.perf_counter() - t0) * 1000.0, 1)
    except Exception as exc:
        out["note"] = f"get_model:{exc}"
        return out
    fd, tmp = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    wav = Path(tmp)
    try:
        _write_silent_wav(wav)
        from ilim_assistant.stt_whisper import transcribe_file_detailed

        t1 = time.perf_counter()
        transcribe_file_detailed(wav, language="tr")
        out["transcribe_silent_ms"] = round((time.perf_counter() - t1) * 1000.0, 1)
    except Exception as exc:
        out["note"] = (out.get("note") or "") + f" transcribe:{exc}"
    finally:
        try:
            wav.unlink(missing_ok=True)
        except OSError:
            pass
    return out


async def _measure_tts_async() -> dict[str, Any]:
    out: dict[str, Any] = {
        "edge_available": False,
        "synth_full_ms": None,
        "stream_first_byte_ms": None,
        "bytes": 0,
        "voice": "tr-TR-AhmetNeural",
        "note": "",
    }
    try:
        from ilim_assistant.tts_service import edge_available, edge_tts_import
    except Exception as exc:
        out["note"] = f"import:{exc}"
        return out
    if not edge_available():
        out["note"] = "edge-tts yok"
        return out
    out["edge_available"] = True
    edge_tts = edge_tts_import()
    text = "Merhaba Ümit abi, Rüzgar ses baseline."
    voice = os.environ.get("RUZGAR_TTS_VOICE", "tr-TR-AhmetNeural").strip() or out["voice"]
    out["voice"] = voice

    # Tam save (kısa) — birincil ölçüm (stream bazen NoAudioReceived)
    t1 = time.perf_counter()
    fd, tmp = tempfile.mkstemp(suffix=".mp3")
    os.close(fd)
    path = Path(tmp)
    try:
        comm2 = edge_tts.Communicate(text, voice)
        await comm2.save(str(path))
        out["synth_full_ms"] = round((time.perf_counter() - t1) * 1000.0, 1)
        out["bytes"] = path.stat().st_size
    except Exception as exc:
        out["note"] = (out.get("note") or "") + f" save:{exc}"
    finally:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass

    # Stream ilk-byte (ikincil; başarısızsa not)
    t0 = time.perf_counter()
    first = None
    total = 0
    try:
        comm = edge_tts.Communicate(text, voice)
        async for chunk in comm.stream():
            if chunk.get("type") == "audio":
                data = chunk.get("data") or b""
                if data and first is None:
                    first = (time.perf_counter() - t0) * 1000.0
                total += len(data or b"")
        if first is not None:
            out["stream_first_byte_ms"] = round(first, 1)
            out["bytes"] = max(int(out.get("bytes") or 0), total)
        else:
            out["note"] = (out.get("note") or "") + " stream:no_audio_chunk"
    except Exception as exc:
        out["note"] = (out.get("note") or "") + f" stream:{type(exc).__name__}"
    return out


def measure_tts_baseline() -> dict[str, Any]:
    return asyncio.run(_measure_tts_async())


def run_v0_baseline() -> dict[str, Any]:
    payload = {
        "version": V0_VERSION,
        "ts": datetime.now(timezone.utc).isoformat(),
        "stt": measure_stt_baseline(),
        "tts": measure_tts_baseline(),
    }
    return payload


def write_v0_baseline_doc(payload: dict[str, Any], path: Path) -> None:
    stt = payload.get("stt") or {}
    tts = payload.get("tts") or {}
    lines = [
        "# V0 — STT/TTS gecikme baseline — 2026-10-23",
        "",
        f"`{payload.get('version')}` · `{payload.get('ts')}`",
        "",
        "## STT (Whisper)",
        "",
        f"| Alan | Değer |",
        f"|------|--------|",
        f"| available | {stt.get('available')} |",
        f"| model | {stt.get('model')} |",
        f"| get_model_ms | {stt.get('get_model_ms')} |",
        f"| transcribe_silent_ms | {stt.get('transcribe_silent_ms')} |",
        f"| note | {stt.get('note') or '—'} |",
        "",
        "## TTS (Edge)",
        "",
        f"| Alan | Değer |",
        f"|------|--------|",
        f"| edge_available | {tts.get('edge_available')} |",
        f"| voice | {tts.get('voice')} |",
        f"| stream_first_byte_ms | {tts.get('stream_first_byte_ms')} |",
        f"| synth_full_ms | {tts.get('synth_full_ms')} |",
        f"| bytes | {tts.get('bytes')} |",
        f"| note | {tts.get('note') or '—'} |",
        "",
        "## Sonraki",
        "",
        "**V1** — Whisper `get_model` + TTS pool prime (boot 1–3’ü geciktirmeden).",
        "",
        "```json",
        json.dumps(payload, ensure_ascii=False, indent=2),
        "```",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
