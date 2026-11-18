# Created by Ümit & Gökçenur — Aşama C STT/TTS latency smoke
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ilim-assistant"))

from ilim_assistant.ses_asama_c import (  # noqa: E402
    ASAMA_C_VERSION,
    TTS_TARGET_MS,
    run_asama_c_report,
)
from ilim_assistant.ses_v4_barge_in import (  # noqa: E402
    verify_mobil_barge_markers,
    verify_ui_barge_in_markers,
    v4_contract,
)


def main() -> int:
    failed = 0
    d = verify_ui_barge_in_markers()
    m = verify_mobil_barge_markers()
    c = v4_contract()
    print("contract", c.get("version"), "a_kept", c.get("asama_a_kept"), "b_kept", c.get("asama_b_kept"))
    if not d.get("ok"):
        print("FAIL desktop markers", d.get("missing"))
        failed += 1
    else:
        print("OK desktop markers (+Aşama C lat)")
    if not m.get("ok"):
        print("FAIL mobil markers", m.get("missing"))
        failed += 1
    else:
        print("OK mobil markers (+Aşama C lat)")
    if c.get("settle_ms") != 40:
        print("FAIL settle not 40")
        failed += 1
    # Aşama A settle literal korunmalı
    desk = (ROOT / "ruzgar-desktop" / "app.js").read_text(encoding="utf-8")
    if "RUZGAR_BARGE_SETTLE_MS = 40" not in desk:
        print("FAIL desktop settle")
        failed += 1
    if "RUZGAR_ASAMA_C_TTS_LAT" not in desk:
        print("FAIL desktop C marker")
        failed += 1

    print("--- measure STT/TTS ---")
    report = run_asama_c_report(stt=True, tts=True)
    print(json.dumps(report, ensure_ascii=False, indent=2)[:4000])
    stt = report.get("stt") or {}
    tts = report.get("tts") or {}
    real = report.get("stt_real_tr") or {}

    def _missing_opt(note: str) -> bool:
        n = (note or "").lower()
        return "yok" in n and ("faster-whisper" in n or "edge-tts" in n or "edge_tts" in n)

    if not stt.get("ok") and not real.get("ok"):
        note = stt.get("note") or real.get("note") or ""
        if _missing_opt(note):
            print("WARN stt measure atlandı (opsiyonel paket):", note)
        else:
            print("FAIL stt measure", note)
            failed += 1
    else:
        src = real if real.get("ok") else stt
        print(
            "OK stt avg_ms=",
            src.get("latency_ms_avg"),
            "min=",
            src.get("latency_ms_min"),
            "max=",
            src.get("latency_ms_max"),
            "src=",
            "real_tr" if real.get("ok") else "synthetic",
        )
    if not tts.get("ok"):
        # cold/warm notelarından paket yokluğunu yakala
        cold_n = ((tts.get("cold_first_chunk") or {}).get("note") or "")
        warm_n = ((tts.get("warm_first_chunk") or {}).get("note") or "")
        note = tts.get("note") or cold_n or warm_n or ""
        if _missing_opt(cold_n) or _missing_opt(warm_n) or _missing_opt(note):
            print("WARN tts measure atlandı (opsiyonel paket):", cold_n or warm_n or note)
        else:
            print("FAIL tts measure", note)
            failed += 1
    else:
        warm = tts.get("warm_first_chunk") or {}
        fb = tts.get("primary_first_audio_ms") or warm.get("first_audio_ms")
        under = tts.get("passed_under_1s")
        cold = (tts.get("cold_first_chunk") or {}).get("first_audio_ms")
        mid = (tts.get("warm_mid_sentence") or {}).get("first_audio_ms")
        print(
            f"TTS text_ready→first_audio warm_short={fb} ms "
            f"cold={cold} mid={mid} target<{TTS_TARGET_MS} under_1s={under}"
        )
        if not under:
            print("WARN TTS hedef <1s tutulamadı (dürüst rapor; fail sayılmaz)")
    print("asama_c_version", ASAMA_C_VERSION)
    if failed:
        print("SMOKE_FAIL asama_c", failed)
        return 1
    print("SMOKE_OK asama_c")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
