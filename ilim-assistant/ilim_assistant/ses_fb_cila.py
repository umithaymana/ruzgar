# Created by Ümit & Gökçenur
"""TTS first-byte cila — sıcak yol + Edge ısınma + <900 ms hedef ölçümü.

S0 canlı ~1311 ms (soğuk/ağ). V3 mühür ~820 ms (ılık). Bu dilim:
- Edge TLS/stream ısınmasını tutar
- Kısa muhabbet metninde prosody atlayıp V3 zorunlu
- Medyan ölçüm raporu
"""
from __future__ import annotations

import asyncio
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

FB_VERSION = "ses-fb-cila-v1-2026-11-21"
TARGET_FIRST_BYTE_MS = 900.0

_LAST_WARM: float = 0.0
_LAST_REPORT: dict[str, Any] = {}


def fb_cila_enabled() -> bool:
    return os.environ.get("RUZGAR_TTS_FB_CILA", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def warm_ttl_sec() -> float:
    try:
        return max(15.0, float(os.environ.get("RUZGAR_TTS_EDGE_WARM_TTL", "90")))
    except ValueError:
        return 90.0


def needs_edge_warm() -> bool:
    if not fb_cila_enabled():
        return False
    return (time.time() - _LAST_WARM) > warm_ttl_sec()


async def warm_edge_stream(*, force: bool = False) -> dict[str, Any]:
    """Kısa Edge stream — TLS/oturum ılık tut."""
    global _LAST_WARM
    from ilim_assistant.ses_v3_tts_ilk_byte import edge_stream_collect_mp3
    from ilim_assistant.tts_service import edge_available

    out: dict[str, Any] = {"ok": False, "skipped": False, "first_byte_ms": None}
    if not force and not needs_edge_warm():
        out["skipped"] = True
        out["ok"] = True
        out["note"] = "warm_fresh"
        return out
    if not edge_available():
        out["note"] = "edge yok"
        return out
    voice = os.environ.get("RUZGAR_TTS_VOICE", "tr-TR-EmelNeural").strip() or (
        "tr-TR-EmelNeural"
    )
    try:
        from ilim_assistant.ses_asama_d import default_rate

        rate = default_rate()
    except Exception:
        rate = "+3%"
    r = await edge_stream_collect_mp3(
        "Merhaba.", voice=voice, rate=rate, pitch="+0Hz", retries=1
    )
    out["ok"] = bool(r.get("ok"))
    out["first_byte_ms"] = r.get("first_byte_ms")
    out["note"] = r.get("note") or ""
    if out["ok"]:
        _LAST_WARM = time.time()
    return out


def prefer_v3_over_prosody(text: str, *, karakter: str, icerik_genel: bool) -> bool:
    """Kısa muhabbet/sohbet: prosody ffmpeg concat first-byte'ı şişirmesin."""
    if not fb_cila_enabled():
        return False
    t = (text or "").strip()
    if len(t) < 2:
        return False
    # İlk sohbet parçaları — V3 tavanı
    try:
        from ilim_assistant.ses_v3_tts_ilk_byte import v3_fast_chars, wants_v3_fast_path

        if not wants_v3_fast_path(t):
            return False
        # Çok kısa veya genel muhabbet
        kar = (karakter or "").strip().lower()
        if kar in ("muhabbet", "asistan", "edip", ""):
            return True
        if icerik_genel and len(t) <= min(280, v3_fast_chars()):
            return True
    except Exception:
        return len(t) <= 280 and (karakter or "").lower() in (
            "muhabbet",
            "asistan",
            "",
        )
    return False


async def measure_first_byte_suite(*, rounds: int = 3) -> dict[str, Any]:
    """Isın + N tur medyan first-byte."""
    global _LAST_REPORT
    from ilim_assistant.ses_v3_tts_ilk_byte import edge_stream_collect_mp3
    from ilim_assistant.tts_service import edge_available

    rounds = max(1, min(8, int(rounds)))
    report: dict[str, Any] = {
        "version": FB_VERSION,
        "ts": datetime.now(timezone.utc).isoformat(),
        "target_ms": TARGET_FIRST_BYTE_MS,
        "s0_ref_ms": 1311.0,
        "v3_seal_ms": 820.0,
        "ok": False,
        "samples_ms": [],
        "median_ms": None,
        "min_ms": None,
        "under_900": False,
        "warm": {},
    }
    if not edge_available():
        report["note"] = "edge-tts yok"
        _LAST_REPORT = report
        return report

    report["warm"] = await warm_edge_stream(force=True)
    voice = os.environ.get("RUZGAR_TTS_VOICE", "tr-TR-EmelNeural").strip() or (
        "tr-TR-EmelNeural"
    )
    try:
        from ilim_assistant.ses_asama_d import default_rate

        rate = default_rate()
    except Exception:
        rate = "+3%"
    text = "Merhaba Ümit abi, Rüzgar first-byte cila."
    samples: list[float] = []
    for _ in range(rounds):
        r = await edge_stream_collect_mp3(
            text, voice=voice, rate=rate, pitch="+0Hz", retries=1
        )
        fb = r.get("first_byte_ms")
        if r.get("ok") and fb is not None:
            samples.append(float(fb))
        await asyncio.sleep(0.15)
    report["samples_ms"] = [round(x, 1) for x in samples]
    if samples:
        ordered = sorted(samples)
        mid = ordered[len(ordered) // 2]
        report["median_ms"] = round(mid, 1)
        report["min_ms"] = round(ordered[0], 1)
        report["under_900"] = mid < TARGET_FIRST_BYTE_MS
        report["ok"] = True
        report["delta_vs_s0"] = round(1311.0 - mid, 1)
    _LAST_REPORT = report
    return report


def measure_first_byte_suite_sync(*, rounds: int = 3) -> dict[str, Any]:
    return asyncio.run(measure_first_byte_suite(rounds=rounds))


def last_fb_report() -> dict[str, Any]:
    return dict(_LAST_REPORT)


def write_fb_docs(report: dict[str, Any] | None = None) -> dict[str, str]:
    payload = report or last_fb_report() or measure_first_byte_suite_sync()
    docs = Path(__file__).resolve().parents[1] / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    js = docs / "FB_CILA_FIRST_BYTE_2026-11-21.json"
    md = docs / "FB_CILA_FIRST_BYTE_2026-11-21.md"
    js.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# TTS First-Byte Cila — 2026-11-21",
        "",
        f"`{payload.get('version')}`",
        "",
        f"- Hedef: **<{payload.get('target_ms')} ms**",
        f"- S0 canlı ref: {payload.get('s0_ref_ms')} ms",
        f"- Medyan: **{payload.get('median_ms')} ms** · min: {payload.get('min_ms')}",
        f"- Örnekler: `{payload.get('samples_ms')}`",
        f"- under_900: **{payload.get('under_900')}**",
        f"- Δ vs S0: {payload.get('delta_vs_s0')} ms",
        "",
        "*Ümit & Gökçenur Haymana'nın ortak projesi.*",
        "",
    ]
    md.write_text("\n".join(lines), encoding="utf-8")
    return {"json": str(js), "md": str(md)}
