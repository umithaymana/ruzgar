"""
V4.3 — Barge-in / mic↔TTS kilidi (Aşama A+B korumalı + Aşama C latency markers).

UI (`ruzgar-desktop/app.js` + mobil PWA) uygular:
1. Mic basılınca / kullanıcı konuşunca aktif TTS kesilir (barge-in).
2. Kayıt varken TTS pump/play başlamaz (mic kilidi) — yankı azaltma.
3. Settle kısa (echo / yarış).
4. «Sus / Dur / Kes» metin komutu TTS+kuyruk temizler.
5. Mobil: TTS sırasında mic VAD açık kalır (kayıt tutulur); barge duyulur.
6. Aşama B: ortak sabitler (settle/RMS/tick); mobil secureContext + mic fallback;
   Android/iOS autoplay gesture unlock (minimal).
7. Aşama C: text_ready→first_audio telemetri (A/B kuralları silinmez).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

V4_VERSION = "ses-v4-barge-in-v1.3-asama-c-2026-11-18"
ASAMA_A_KEPT = True
ASAMA_B_KEPT = True
ASAMA_C_MARKERS = True

BARGE_IN_FLAG = "RUZGAR_BARGE_IN"
BARGE_SETTLE_MS = 40
# Mobil barge: rms eşiği + ardışık tick (tick_ms * ticks ≈ kesilme gecikmesi)
MOBIL_BARGE_RMS = 0.03
MOBIL_BARGE_TICK_MS = 50
MOBIL_BARGE_TICKS = 2

STOP_WORDS_TR = ("sus", "dur", "kes", "sessiz", "sus ol", "kes sesi")

REQUIRED_JS_MARKERS = (
    "RUZGAR_BARGE_IN",
    "bargeInStopTtsForMic",
    "ttsBlockedByMicLock",
    "isMicRecordingActive",
    "looksLikeVoiceStopCommand",
    "silenceVoiceOutputNow",
    # Aşama C — text_ready→first_audio telemetri
    "RUZGAR_ASAMA_C_TTS_LAT",
    "markTtsTextReady",
    "markTtsFirstAudio",
)

REQUIRED_MOBIL_MARKERS = (
    "stopAllSpeech",
    "looksLikeVoiceStopCommand",
    "liveHoldRecord",
    "barge-in",
    # Aşama B — PC↔mobil ortak sabitler (ses_v4 contract)
    "RUZGAR_BARGE_SETTLE_MS = 40",
    "MOBIL_BARGE_RMS = 0.03",
    "MOBIL_BARGE_TICK_MS = 50",
    "MOBIL_BARGE_TICKS = 2",
    "getMicStream",
    "unlockMobileAudio",
    # Aşama C
    "RUZGAR_ASAMA_C_TTS_LAT",
    "markTtsTextReady",
    "markTtsFirstAudio",
)


def desktop_app_js() -> Path:
    return Path(__file__).resolve().parents[2] / "ruzgar-desktop" / "app.js"


def mobil_app_js() -> Path:
    return (
        Path(__file__).resolve().parents[1]
        / "static"
        / "mobil-pwa"
        / "app.js"
    )


def verify_ui_barge_in_markers(app_js: Path | None = None) -> dict[str, Any]:
    path = app_js or desktop_app_js()
    out: dict[str, Any] = {
        "version": V4_VERSION,
        "path": str(path),
        "ok": False,
        "missing": [],
        "mic_blocks_tts_without_barge": None,
        "pump_respects_mic_lock": None,
    }
    if not path.is_file():
        out["missing"] = ["app.js"]
        return out
    text = path.read_text(encoding="utf-8")
    missing = [m for m in REQUIRED_JS_MARKERS if m not in text]
    out["missing"] = missing
    out["mic_has_barge_call"] = (
        "await bargeInStopTtsForMic()" in text or "bargeInStopTtsForMic()" in text
    )
    out["pump_respects_mic_lock"] = (
        "ttsBlockedByMicLock()" in text and "runTtsPump" in text
    )
    out["settle_ms_ok"] = (
        "RUZGAR_BARGE_SETTLE_MS = 40" in text or "RUZGAR_BARGE_SETTLE_MS=40" in text
    )
    out["ok"] = (
        not missing
        and bool(out["mic_has_barge_call"])
        and bool(out["pump_respects_mic_lock"])
        and bool(out["settle_ms_ok"])
    )
    return out


def verify_mobil_barge_markers(app_js: Path | None = None) -> dict[str, Any]:
    path = app_js or mobil_app_js()
    out: dict[str, Any] = {
        "version": V4_VERSION,
        "path": str(path),
        "ok": False,
        "missing": [],
    }
    if not path.is_file():
        out["missing"] = ["mobil app.js"]
        return out
    text = path.read_text(encoding="utf-8")
    missing = [m for m in REQUIRED_MOBIL_MARKERS if m not in text]
    out["missing"] = missing
    out["ok"] = not missing
    return out


def v4_contract() -> dict[str, Any]:
    return {
        "version": V4_VERSION,
        "asama_a_kept": ASAMA_A_KEPT,
        "asama_b_kept": ASAMA_B_KEPT,
        "asama_c_markers": ASAMA_C_MARKERS,
        "barge_in": True,
        "settle_ms": BARGE_SETTLE_MS,
        "mobil_barge_rms": MOBIL_BARGE_RMS,
        "mobil_barge_ticks": MOBIL_BARGE_TICKS,
        "mobil_barge_tick_ms": MOBIL_BARGE_TICK_MS,
        "stop_words": list(STOP_WORDS_TR),
        "rules": [
            "mic_down_while_tts → stop_tts_then_listen",
            "recording_active → tts_play_blocked",
            "tts_must_not_block_mic_without_barge",
            "tts_playing → mic_vad_open_record_hold (mobil)",
            "stop_words → flush_queue_and_listen",
            "mobil_requires_secure_context_https",
            "mobil_getUserMedia_fallback_audio_true",
            "ios_autoplay_needs_user_gesture_unlock",
            "asama_c_text_ready_to_first_audio_telemetry",
        ],
        "platforms": {
            "desktop": "Electron/Chromium — settle + bargeInStopTtsForMic",
            "android": "Chrome/PWA HTTPS:8443 — getMicStream + barge VAD",
            "ios": "Safari gesture unlock + playsInline; mic A2HS/Settings kalır",
        },
        "flag": BARGE_IN_FLAG,
        "tts_latency_metric": "text_ready→first_audio",
        "tts_latency_target_ms": 1000,
    }
