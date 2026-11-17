# Created by Ümit & Gökçenur
"""F7 — Ses kalitesi: TTS first-byte yeniden ölçüm + profil/STT yüzeyi özeti."""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from typing import Any

F7_VERSION = "ses-f7-kalite-v1-2026-11-17"

# V0 mühür notu (ses_v3 docstring): Edge first-byte ~1686 ms
V0_TTS_FIRST_BYTE_REF_MS = 1686.0
V3_TARGET_FIRST_BYTE_MS = 900.0  # V3 kısa yol hedef üstü (rehber)

_LAST: dict[str, Any] = {}


def f7_enabled() -> bool:
    return os.environ.get("RUZGAR_SES_F7", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def last_f7_report() -> dict[str, Any]:
    return dict(_LAST)


def profile_ton_snapshot() -> dict[str, Any]:
    """F7.3 — Alim/Edip/Asistan rate-pitch özeti."""
    from ilim_assistant.motorlar.ses_motoru import (
        EDGE_VOICES,
        IcerikYolu,
        SesKarakteri,
        edge_pitch_string,
        edge_rate_yuzdesi,
        profil_aciklamasi,
    )
    from ilim_assistant.tts_service import read_ses_ayarlari

    ayar = read_ses_ayarlari()
    aktif = str(ayar.get("karakter") or "asistan")
    out: dict[str, Any] = {"aktif": aktif, "profiller": {}}
    for kar in SesKarakteri:
        icerik = IcerikYolu.genel
        out["profiller"][kar.value] = {
            "voice": EDGE_VOICES.get(kar),
            "rate": edge_rate_yuzdesi(
                karakter=kar,
                icerik=icerik,
                hiz_carpani=float(ayar.get("hiz", 0.92)),
                huzur_carpani=float(ayar.get("huzur", 0.88)),
            ),
            "pitch": edge_pitch_string(kar, icerik),
            "aciklama": (profil_aciklamasi(kar) or "")[:160],
        }
    return out


def clone_policy_snapshot() -> dict[str, Any]:
    """F7.4 — klon yalnız onaylı/açık yolda."""
    try:
        from ilim_assistant.motorlar.ses_klon_motoru import (
            clone_enabled,
            clone_status_snapshot,
            xtts_runtime_available,
        )

        st = clone_status_snapshot()
        return {
            "enabled_env": clone_enabled(),
            "xtts_ready": xtts_runtime_available(),
            "policy": "auto_yalniz_ayar_veya_backend_clone",
            "hint": "RUZGAR_TTS_CLONE=0 ile kapat; backend=clone veya ayar tercih ile aç.",
            "status": st,
        }
    except Exception as exc:
        return {"enabled_env": False, "error": str(exc)[:160]}


async def measure_tts_first_byte_f7() -> dict[str, Any]:
    """F7.1 — V3 hızlı yol ile first-byte; V0 ref ile karşılaştır."""
    from ilim_assistant.ses_v3_tts_ilk_byte import (
        V3_VERSION,
        edge_stream_collect_mp3,
        v3_enabled,
    )
    from ilim_assistant.tts_service import edge_available

    out: dict[str, Any] = {
        "ok": False,
        "v3_enabled": v3_enabled(),
        "v3_version": V3_VERSION,
        "v0_ref_first_byte_ms": V0_TTS_FIRST_BYTE_REF_MS,
        "v3_target_ms": V3_TARGET_FIRST_BYTE_MS,
        "first_byte_ms": None,
        "total_ms": None,
        "vs_v0": None,
        "note": "",
    }
    if not edge_available():
        out["note"] = "edge-tts yok"
        return out
    voice = os.environ.get("RUZGAR_TTS_VOICE", "tr-TR-AhmetNeural").strip() or (
        "tr-TR-AhmetNeural"
    )
    text = "Merhaba Ümit abi, Rüzgar F7 first-byte."
    try:
        res = await edge_stream_collect_mp3(
            text, voice=voice, rate="-8%", pitch="+0Hz"
        )
        out["ok"] = bool(res.get("ok"))
        out["first_byte_ms"] = res.get("first_byte_ms")
        out["total_ms"] = res.get("total_ms")
        out["attempts"] = res.get("attempts")
        out["note"] = res.get("note") or ""
        fb = out["first_byte_ms"]
        if fb is not None:
            delta = float(V0_TTS_FIRST_BYTE_REF_MS) - float(fb)
            out["vs_v0"] = {
                "delta_ms": round(delta, 1),
                "faster_than_v0": delta > 0,
                "under_v3_target": float(fb) <= V3_TARGET_FIRST_BYTE_MS,
            }
    except Exception as exc:
        out["note"] = str(exc)[:200]
    return out


def measure_stt_warmup_f7() -> dict[str, Any]:
    """F7.5 — Whisper ısınma (mobil sürekli için soğuk ilk turu kes)."""
    from ilim_assistant.ses_v1_isinma import prime_stt_whisper

    t0 = time.perf_counter()
    stt = prime_stt_whisper()
    stt["wall_ms"] = round((time.perf_counter() - t0) * 1000.0, 1)
    return stt


def run_f7_report(*, measure_tts: bool = True, warm_stt: bool = True) -> dict[str, Any]:
    global _LAST
    report: dict[str, Any] = {
        "version": F7_VERSION,
        "ts": datetime.now(timezone.utc).isoformat(),
        "enabled": f7_enabled(),
        "profiles": profile_ton_snapshot(),
        "clone": clone_policy_snapshot(),
        "stt_warmup": {},
        "tts_first_byte": {},
    }
    if warm_stt:
        report["stt_warmup"] = measure_stt_warmup_f7()
    if measure_tts and f7_enabled():
        try:
            import asyncio

            report["tts_first_byte"] = asyncio.run(measure_tts_first_byte_f7())
        except Exception as exc:
            report["tts_first_byte"] = {"ok": False, "note": str(exc)[:200]}
    _LAST = report
    return report
