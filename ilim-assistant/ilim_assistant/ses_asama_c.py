# Created by Ümit & Gökçenur
"""
Aşama C — Türkçe Whisper STT hız/kalite + TTS text_ready→first_audio ölçümü.

Hedef TTS: < 1000 ms (metin hazır → ilk ses chunk / play start).
A/B barge contract bozulmaz; yalnız ölçüm + STT/TTS latency iyileştirme.
"""

from __future__ import annotations

import os
import tempfile
import time
import wave
from pathlib import Path
from typing import Any

ASAMA_C_VERSION = "ses-asama-c-v1-2026-11-18"
TTS_TARGET_MS = 1000.0

# Kısa TR cümle seti (WER proxy / latency bench)
TR_BENCH_PHRASES = (
    "Merhaba Rüzgar",
    "Bugün hava nasıl",
    "Lütfen tekrar eder misin",
)


def asama_c_contract() -> dict[str, Any]:
    return {
        "version": ASAMA_C_VERSION,
        "tts_target_ms": TTS_TARGET_MS,
        "metric_tts": "text_ready→first_audio",
        "stt_defaults": {
            "model": "small",
            "device": "cpu",
            "compute": "int8",
            "language": "tr",
            "beam": 1,
        },
        "ios_notes": [
            "Safari Audio.play NotAllowedError — user gesture unlock şart",
            "playsInline + unlockMobileAudio; A2HS mic Settings",
            "text_ready→play ölçümü gesture sonrası güvenilir",
        ],
        "asama_a_b_kept": True,
    }


def _write_tone_wav(path: Path, *, seconds: float = 1.2, freq: float = 440.0) -> Path:
    """Mic yokken sentetik 16 kHz mono WAV (Whisper bench)."""
    import math
    import struct

    rate = 16000
    n = max(1, int(rate * seconds))
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        frames = bytearray()
        for i in range(n):
            # yumuşak sinus + düşük genlik — sessizlikten biraz daha «konuşma benzeri»
            t = i / rate
            amp = 0.22 * math.sin(2 * math.pi * freq * t)
            # zarf (baş/son fade)
            env = 1.0
            fade = int(rate * 0.05)
            if i < fade:
                env = i / fade
            elif i > n - fade:
                env = (n - i) / fade
            sample = int(max(-1.0, min(1.0, amp * env)) * 32767)
            frames.extend(struct.pack("<h", sample))
        w.writeframes(bytes(frames))
    return path


def measure_stt_tr_latency(
    *,
    phrases: tuple[str, ...] | None = None,
    seconds: float = 1.0,
) -> dict[str, Any]:
    """
    Server-side timed transcribe (gerçek mic yok).
    Sentetik WAV → Whisper; latency = decode+transcribe duvar saati.
    Not: ton ≠ gerçek TR konuşma; WER bu bench'te iddia edilmez.
    """
    from ilim_assistant.stt_whisper import (
        build_transcribe_kwargs,
        stt_runtime_available,
        transcribe_file_detailed,
        warm_stt_model,
        whisper_model_name,
        whisper_runtime_meta,
    )

    out: dict[str, Any] = {
        "ok": False,
        "version": ASAMA_C_VERSION,
        "model": whisper_model_name(),
        "samples": [],
        "warm": {},
        "note": "",
    }
    if not stt_runtime_available():
        out["note"] = "faster-whisper yok"
        return out
    out["warm"] = warm_stt_model()
    samples: list[dict[str, Any]] = []
    phrases = phrases or TR_BENCH_PHRASES
    with tempfile.TemporaryDirectory(prefix="ruzgar_asama_c_stt_") as td:
        td_path = Path(td)
        for i, phrase in enumerate(phrases):
            wav = td_path / f"tr_{i}.wav"
            _write_tone_wav(wav, seconds=seconds, freq=420.0 + i * 40.0)
            t0 = time.perf_counter()
            try:
                result = transcribe_file_detailed(wav, language="tr")
                ms = round((time.perf_counter() - t0) * 1000.0, 1)
                samples.append(
                    {
                        "label": phrase,
                        "ok": True,
                        "latency_ms": ms,
                        "text": (result.text or "")[:120],
                        "duration_sec": result.duration_sec,
                        "kwargs": build_transcribe_kwargs("tr", duration_sec=seconds),
                    }
                )
            except Exception as exc:
                samples.append(
                    {
                        "label": phrase,
                        "ok": False,
                        "latency_ms": round((time.perf_counter() - t0) * 1000.0, 1),
                        "error": str(exc)[:160],
                    }
                )
    out["samples"] = samples
    ok_ms = [s["latency_ms"] for s in samples if s.get("ok")]
    out["ok"] = bool(ok_ms)
    out["latency_ms_avg"] = round(sum(ok_ms) / len(ok_ms), 1) if ok_ms else None
    out["latency_ms_min"] = min(ok_ms) if ok_ms else None
    out["latency_ms_max"] = max(ok_ms) if ok_ms else None
    out["meta"] = whisper_runtime_meta()
    return out


async def measure_tts_text_ready_to_first_audio(
    text: str | None = None,
    *,
    warm_first: bool = False,
) -> dict[str, Any]:
    """
    Ölçüm noktası: text_ready (Communicate başı) → first_audio_chunk.
    Hedef: < 1000 ms.
    """
    from ilim_assistant.ses_v3_tts_ilk_byte import edge_stream_collect_mp3
    from ilim_assistant.tts_service import edge_available

    sample = (text or "Merhaba Ümit abi.").strip()
    voice = (
        os.environ.get("RUZGAR_TTS_VOICE", "tr-TR-AhmetNeural").strip()
        or "tr-TR-AhmetNeural"
    )
    out: dict[str, Any] = {
        "ok": False,
        "version": ASAMA_C_VERSION,
        "metric": "text_ready→first_audio",
        "target_ms": TTS_TARGET_MS,
        "text_chars": len(sample),
        "voice": voice,
        "first_audio_ms": None,
        "total_ms": None,
        "passed_under_1s": False,
        "warmed": False,
        "note": "",
    }
    if not edge_available():
        out["note"] = "edge-tts yok"
        return out
    if warm_first:
        await edge_stream_collect_mp3(
            "Merhaba.", voice=voice, rate="+0%", pitch="+0Hz", retries=1
        )
        out["warmed"] = True
    # text_ready anı = stream çağrısı başı (edge_stream_collect_mp3 içinde t0)
    t_ready = time.perf_counter()
    r = await edge_stream_collect_mp3(
        sample, voice=voice, rate="+0%", pitch="+0Hz", retries=1
    )
    wall = round((time.perf_counter() - t_ready) * 1000.0, 1)
    fb = r.get("first_byte_ms")
    out["ok"] = bool(r.get("ok"))
    out["first_audio_ms"] = fb
    out["total_ms"] = r.get("total_ms") or wall
    out["attempts"] = r.get("attempts")
    out["bytes"] = len(r.get("bytes") or b"")
    if fb is not None:
        out["passed_under_1s"] = float(fb) < TTS_TARGET_MS
        out["delta_to_target_ms"] = round(float(fb) - TTS_TARGET_MS, 1)
    else:
        out["note"] = r.get("note") or "no_first_byte"
    return out


async def measure_tts_suite() -> dict[str, Any]:
    """Soğuk + ılık; kısa ilk-chunk (UI) ve orta cümle."""
    cold = await measure_tts_text_ready_to_first_audio(
        "Merhaba Ümit abi.", warm_first=False
    )
    warm_short = await measure_tts_text_ready_to_first_audio(
        "Merhaba Ümit abi.", warm_first=True
    )
    warm_mid = await measure_tts_text_ready_to_first_audio(
        "Merhaba Ümit abi, Rüzgar Aşama C ses testi.", warm_first=False
    )
    under = bool(warm_short.get("passed_under_1s"))
    return {
        "ok": bool(cold.get("ok") or warm_short.get("ok")),
        "metric": "text_ready→first_audio",
        "target_ms": TTS_TARGET_MS,
        "cold_first_chunk": cold,
        "warm_first_chunk": warm_short,
        "warm_mid_sentence": warm_mid,
        "passed_under_1s": under,
        "primary_first_audio_ms": warm_short.get("first_audio_ms"),
        "note": (
            "UI ilk chunk ~kısa cümle; warm_first_chunk hedef <1s "
            "(Edge ısınma sonrası). Soğuk ilk tur ekstra TLS cezası alabilir."
        ),
    }


def measure_tts_sync(text: str | None = None) -> dict[str, Any]:
    import asyncio

    if text:
        return asyncio.run(measure_tts_text_ready_to_first_audio(text, warm_first=True))
    return asyncio.run(measure_tts_suite())


async def measure_stt_tr_real_audio() -> dict[str, Any]:
    """Edge ile gerçek TR MP3 üret → Whisper latency (WER proxy değil, timed)."""
    from ilim_assistant.ses_v3_tts_ilk_byte import edge_stream_collect_mp3
    from ilim_assistant.stt_whisper import (
        stt_runtime_available,
        transcribe_file_detailed,
        warm_stt_model,
        whisper_model_name,
        whisper_runtime_meta,
    )
    from ilim_assistant.tts_service import edge_available

    out: dict[str, Any] = {
        "ok": False,
        "version": ASAMA_C_VERSION,
        "model": whisper_model_name(),
        "samples": [],
        "note": "edge_mp3→whisper",
    }
    if not stt_runtime_available():
        out["note"] = "faster-whisper yok"
        return out
    if not edge_available():
        out["note"] = "edge-tts yok — gerçek TR ses üretilemedi"
        return out
    warm_stt_model()
    voice = (
        os.environ.get("RUZGAR_TTS_VOICE", "tr-TR-AhmetNeural").strip()
        or "tr-TR-AhmetNeural"
    )
    samples: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="ruzgar_asama_c_stt_real_") as td:
        td_path = Path(td)
        for i, phrase in enumerate(TR_BENCH_PHRASES):
            audio = await edge_stream_collect_mp3(
                phrase, voice=voice, rate="+0%", pitch="+0Hz", retries=1
            )
            if not audio.get("ok") or not audio.get("bytes"):
                samples.append(
                    {
                        "label": phrase,
                        "ok": False,
                        "error": audio.get("note") or "no_audio",
                    }
                )
                continue
            mp3 = td_path / f"tr_{i}.mp3"
            mp3.write_bytes(audio["bytes"])
            t0 = time.perf_counter()
            try:
                result = transcribe_file_detailed(mp3, language="tr")
                ms = round((time.perf_counter() - t0) * 1000.0, 1)
                samples.append(
                    {
                        "label": phrase,
                        "ok": True,
                        "latency_ms": ms,
                        "text": (result.text or "")[:120],
                        "duration_sec": result.duration_sec,
                    }
                )
            except Exception as exc:
                samples.append(
                    {
                        "label": phrase,
                        "ok": False,
                        "latency_ms": round((time.perf_counter() - t0) * 1000.0, 1),
                        "error": str(exc)[:160],
                    }
                )
    out["samples"] = samples
    ok_ms = [s["latency_ms"] for s in samples if s.get("ok") and "latency_ms" in s]
    out["ok"] = bool(ok_ms)
    out["latency_ms_avg"] = round(sum(ok_ms) / len(ok_ms), 1) if ok_ms else None
    out["latency_ms_min"] = min(ok_ms) if ok_ms else None
    out["latency_ms_max"] = max(ok_ms) if ok_ms else None
    out["meta"] = whisper_runtime_meta()
    return out


def run_asama_c_report(*, stt: bool = True, tts: bool = True) -> dict[str, Any]:
    import asyncio

    report: dict[str, Any] = {
        "version": ASAMA_C_VERSION,
        "contract": asama_c_contract(),
        "stt_synthetic_tone": {},
        "stt_real_tr": {},
        "tts": {},
    }
    if stt:
        report["stt_synthetic_tone"] = measure_stt_tr_latency()
        try:
            report["stt_real_tr"] = asyncio.run(measure_stt_tr_real_audio())
        except Exception as exc:
            report["stt_real_tr"] = {"ok": False, "note": str(exc)[:200]}
    if tts:
        report["tts"] = measure_tts_sync()
    tts_r = report.get("tts") or {}
    report["tts_under_1s"] = bool(tts_r.get("passed_under_1s"))
    # Geriye uyum: stt = gerçek TR varsa o, yoksa sentetik
    real = report.get("stt_real_tr") or {}
    report["stt"] = real if real.get("ok") else report.get("stt_synthetic_tone") or {}
    return report
