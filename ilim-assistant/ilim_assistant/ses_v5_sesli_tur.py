"""
V5 — Sesli tur uçtan uca (STT → voice_turn → TTS) + Faz V mühür malzemesi.

Canlı LLM / mikrofon zorunlu değil: decode + V3 TTS + sözleşme + UI zinciri.
"""
from __future__ import annotations

import asyncio
import os
import struct
import tempfile
import time
import wave
from pathlib import Path
from typing import Any

V5_VERSION = "ses-v5-sesli-tur-v1-2026-11-03"

# Offline e2e üst tavan (ağ + model ılık)
E2E_BUDGET_MS = 20_000

UI_CHAIN_MARKERS = (
    "voiceTurn",
    "maybeResumeVoiceListenAfterReply",
    "bargeInStopTtsForMic",
    "ttsBlockedByMicLock",
    "isSesliTurFazKEnabled",
    "waitTtsIdle",
)


def desktop_app_js() -> Path:
    return Path(__file__).resolve().parents[2] / "ruzgar-desktop" / "app.js"


def _silent_wav(path: Path, *, seconds: float = 0.5, rate: int = 16000) -> None:
    n = int(rate * seconds)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(struct.pack("<" + "h" * n, *([0] * n)))


def verify_ui_voice_chain(app_js: Path | None = None) -> dict[str, Any]:
    path = app_js or desktop_app_js()
    missing: list[str] = []
    if not path.is_file():
        return {"ok": False, "missing": ["app.js"], "path": str(path)}
    text = path.read_text(encoding="utf-8")
    for m in UI_CHAIN_MARKERS:
        if m not in text:
            missing.append(m)
    return {"ok": not missing, "missing": missing, "path": str(path)}


def verify_voice_turn_contract() -> dict[str, Any]:
    from ilim_assistant.ruzgar_sesli_tur_faz_k import sesli_tur_enabled, sesli_tur_status
    from ilim_assistant.ruzgar_tek_beyin_oturum import (
        build_voice_turn_addon,
        dost_max_tokens,
        dost_prior_depth,
    )

    addon = build_voice_turn_addon()
    st = sesli_tur_status()
    tok_v = dost_max_tokens(mood_active=False, voice_turn=True)
    tok_n = dost_max_tokens(mood_active=False, voice_turn=False)
    depth_v = dost_prior_depth(mood_active=False, voice_turn=True)
    depth_n = dost_prior_depth(mood_active=False, voice_turn=False)
    # voice_turn yanıtı token tavanı ile kısaltır (TTS için)
    return {
        "ok": bool(
            sesli_tur_enabled()
            and st.get("enabled")
            and isinstance(addon, str)
            and len(addon) > 20
            and tok_v <= tok_n
            and tok_v <= 700
            and "SESLİ TUR" in addon
        ),
        "sesli_tur": st,
        "addon_chars": len(addon or ""),
        "max_tokens_voice": tok_v,
        "max_tokens_normal": tok_n,
        "prior_depth_voice": depth_v,
        "prior_depth_normal": depth_n,
    }


def stage_stt() -> dict[str, Any]:
    out: dict[str, Any] = {"ok": False, "ms": None, "note": ""}
    try:
        from ilim_assistant.stt_whisper import (
            _decode_audio_f32,
            stt_runtime_available,
            transcribe_file_detailed,
        )
    except Exception as exc:
        out["note"] = f"import:{exc}"
        return out
    if not stt_runtime_available():
        out["note"] = "stt yok"
        return out
    fd, tmp = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    wav = Path(tmp)
    try:
        _silent_wav(wav)
        t0 = time.perf_counter()
        audio = _decode_audio_f32(wav)
        if audio is None or getattr(audio, "size", 0) < 100:
            out["note"] = "decode empty"
            return out
        # Model ılıksa kısa; soğuksa V1 zaten ısındırmış olmalı — yine de timeout yok
        if os.environ.get("RUZGAR_V5_STT_TRANSCRIBE", "1").strip().lower() not in (
            "0",
            "false",
            "no",
        ):
            transcribe_file_detailed(wav, language="tr")
        out["ms"] = round((time.perf_counter() - t0) * 1000.0, 1)
        out["ok"] = True
    except Exception as exc:
        out["note"] = str(exc)[:200]
    finally:
        try:
            wav.unlink(missing_ok=True)
        except OSError:
            pass
    return out


def stage_tts() -> dict[str, Any]:
    out: dict[str, Any] = {"ok": False, "first_byte_ms": None, "total_ms": None, "note": ""}
    try:
        from ilim_assistant.ses_v3_tts_ilk_byte import edge_stream_collect_mp3
        from ilim_assistant.tts_service import edge_available
    except Exception as exc:
        out["note"] = f"import:{exc}"
        return out
    if not edge_available():
        out["note"] = "edge yok"
        return out
    voice = os.environ.get("RUZGAR_TTS_VOICE", "tr-TR-AhmetNeural").strip() or "tr-TR-AhmetNeural"

    async def _run() -> dict[str, Any]:
        return await edge_stream_collect_mp3(
            "Merhaba Ümit abi, Rüzgar sesli tur V5.",
            voice=voice,
            rate="+0%",
            pitch="+0Hz",
        )

    try:
        r = asyncio.run(_run())
        out["ok"] = bool(r.get("ok"))
        out["first_byte_ms"] = r.get("first_byte_ms")
        out["total_ms"] = r.get("total_ms")
        out["note"] = r.get("note") or ""
        out["bytes"] = len(r.get("bytes") or b"")
    except Exception as exc:
        out["note"] = str(exc)[:200]
    return out


def run_v5_e2e(*, skip_live_audio: bool = False) -> dict[str, Any]:
    """STT+TTS canlı + sözleşme + UI zinciri."""
    t0 = time.perf_counter()
    report: dict[str, Any] = {
        "version": V5_VERSION,
        "ok": False,
        "budget_ms": E2E_BUDGET_MS,
        "stages": {},
    }
    report["stages"]["contract"] = verify_voice_turn_contract()
    report["stages"]["ui_chain"] = verify_ui_voice_chain()
    if skip_live_audio:
        report["stages"]["stt"] = {"ok": True, "note": "skipped"}
        report["stages"]["tts"] = {"ok": True, "note": "skipped"}
    else:
        report["stages"]["stt"] = stage_stt()
        report["stages"]["tts"] = stage_tts()
    report["elapsed_ms"] = round((time.perf_counter() - t0) * 1000.0, 1)
    stages_ok = all(bool((s or {}).get("ok")) for s in report["stages"].values())
    under_budget = report["elapsed_ms"] <= E2E_BUDGET_MS
    report["ok"] = stages_ok and under_budget
    report["under_budget"] = under_budget
    return report
