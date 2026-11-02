"""
V4 — Barge-in / mic↔TTS kilidi (sözleşme).

UI (`ruzgar-desktop/app.js`) uygular:
1. Mic basılınca aktif TTS kesilir (barge-in), sonra dinleme başlar.
2. Kayıt varken TTS pump/play başlamaz (mic kilidi).
3. Settle kısa (echo / yarış).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

V4_VERSION = "ses-v4-barge-in-v1-2026-11-03"

# UI sabitleriyle hizalı (smoke doğrular)
BARGE_IN_FLAG = "RUZGAR_BARGE_IN"
BARGE_SETTLE_MS = 80
REQUIRED_JS_MARKERS = (
    "RUZGAR_BARGE_IN",
    "bargeInStopTtsForMic",
    "ttsBlockedByMicLock",
    "isMicRecordingActive",
)


def desktop_app_js() -> Path:
    return Path(__file__).resolve().parents[2] / "ruzgar-desktop" / "app.js"


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
    # Eski davranış: micPointerDown içinde isTtsActive → return (barge yok)
    # Yeni: bargeInStopTtsForMic çağrısı mic akışında olmalı
    out["mic_has_barge_call"] = "await bargeInStopTtsForMic()" in text or "bargeInStopTtsForMic()" in text
    out["pump_respects_mic_lock"] = "ttsBlockedByMicLock()" in text and "runTtsPump" in text
    out["ok"] = not missing and bool(out["mic_has_barge_call"]) and bool(out["pump_respects_mic_lock"])
    return out


def v4_contract() -> dict[str, Any]:
    return {
        "version": V4_VERSION,
        "barge_in": True,
        "settle_ms": BARGE_SETTLE_MS,
        "rules": [
            "mic_down_while_tts → stop_tts_then_listen",
            "recording_active → tts_play_blocked",
            "tts_must_not_block_mic_without_barge",
        ],
        "flag": BARGE_IN_FLAG,
    }
