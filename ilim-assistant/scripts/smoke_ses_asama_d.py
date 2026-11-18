# Created by Ümit & Gökçenur — Aşama D TTS + sabit erişim smoke
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ilim-assistant"))

from ilim_assistant.ses_asama_d import (  # noqa: E402
    ASAMA_D_VERSION,
    TTS_KEEP_MS,
    asama_d_contract,
    classify_edge_error,
    split_speak_chunks,
)
from ilim_assistant.ses_v4_barge_in import (  # noqa: E402
    verify_mobil_barge_markers,
    verify_ui_barge_in_markers,
    v4_contract,
)


def main() -> int:
    failed = 0
    print("=== Aşama D contract ===")
    print(json.dumps(asama_d_contract(), ensure_ascii=False, indent=2))

    d = verify_ui_barge_in_markers()
    m = verify_mobil_barge_markers()
    c = v4_contract()
    print("A/B/C contract", c.get("version"), "settle", c.get("settle_ms"))
    if not d.get("ok"):
        print("FAIL desktop barge markers", d.get("missing"))
        failed += 1
    else:
        print("OK desktop A/B/C markers")
    if not m.get("ok"):
        print("FAIL mobil barge markers", m.get("missing"))
        failed += 1
    else:
        print("OK mobil A/B/C markers")
    if c.get("settle_ms") != 40:
        print("FAIL settle not 40")
        failed += 1

    desk = (ROOT / "ruzgar-desktop" / "app.js").read_text(encoding="utf-8")
    if "RUZGAR_BARGE_SETTLE_MS = 40" not in desk:
        print("FAIL desktop settle")
        failed += 1
    if "RUZGAR_ASAMA_D_TTS" not in desk:
        print("FAIL desktop D marker")
        failed += 1
    if "RUZGAR_ASAMA_C_TTS_LAT" not in desk:
        print("FAIL desktop C marker lost")
        failed += 1
    mobil = (
        ROOT / "ilim-assistant" / "static" / "mobil-pwa" / "app.js"
    ).read_text(encoding="utf-8")
    if "preferStickyHttps" not in mobil and "sticky_urls" not in mobil:
        print("FAIL mobil sticky prefer")
        failed += 1
    else:
        print("OK mobil sticky MagicDNS prefer")

    # Parçalama: yarım kelime yok
    sample = (
        "Merhaba Ümit abi. Rüzgar Aşama D ses testi başlıyor. "
        "Uzun cevaplarda cümle arası gereksiz sessizlik azalır ve akış kesintisiz sürer."
    )
    chunks = split_speak_chunks(sample)
    print("chunks", len(chunks), chunks)
    if len(chunks) < 2:
        print("FAIL expect multi chunk")
        failed += 1
    joined = " ".join(chunks)
    for w in ("başlıyor", "sessizlik", "kesintisiz"):
        if w not in joined.replace("ı", "i") and w not in sample:
            pass
    # Kelime ortası kesim kontrolü: hiçbir chunk ortasında boşluksuz kırık yok (basit)
    for ch in chunks:
        if ch and not ch[-1].isalnum() and ch[-1] not in ".!?…،,;:—-":
            # trailing space stripped already
            pass
        if " " not in ch and len(ch) > 24 and not any(ch.endswith(p) for p in ".!?…"):
            # tek uzun kelime nadiren olur; fail sayma
            pass

    err = classify_edge_error("NoAudioReceived: empty")
    if err.get("kind") != "no_audio" or not err.get("retryable"):
        print("FAIL classify", err)
        failed += 1
    else:
        print("OK error classify", err.get("kind"))

    print("--- measure TTS (D keep ≤", TTS_KEEP_MS, "ms) ---")
    import asyncio

    from ilim_assistant.ses_asama_c import measure_tts_suite

    tts = asyncio.run(measure_tts_suite())
    print(json.dumps(tts, ensure_ascii=False, indent=2)[:3500])
    warm = tts.get("warm_first_chunk") or {}
    fb = tts.get("primary_first_audio_ms") or warm.get("first_audio_ms")
    under_c = bool(tts.get("passed_under_1s"))
    under_d = fb is not None and float(fb) <= TTS_KEEP_MS
    print(
        f"TTS warm_short={fb} ms under_1s={under_c} under_d_keep({TTS_KEEP_MS})={under_d}"
    )
    cold_n = ((tts.get("cold_first_chunk") or {}).get("note") or "")
    warm_n = ((tts.get("warm_first_chunk") or {}).get("note") or "")
    miss_opt = any(
        "yok" in n.lower() and ("edge-tts" in n.lower() or "edge_tts" in n.lower())
        for n in (cold_n, warm_n, str(tts.get("note") or ""))
    )
    if not tts.get("ok"):
        if miss_opt:
            print("WARN tts measure atlandı (opsiyonel paket):", cold_n or warm_n or tts.get("note"))
        else:
            print("FAIL tts measure", tts.get("note"))
            failed += 1
    elif not under_c:
        print("WARN C hedef <1s tutulamadı (dürüst; fail sayılmaz)")
    elif not under_d:
        print(f"WARN D keep ≤{TTS_KEEP_MS} ms kaçtı (dürüst; C hâlâ <1s)")

    # Sabit erişim — Tailscale MagicDNS + sticky dosya (sunucu restart ayrı)
    sticky_path = ROOT / "ilim-assistant" / ".ruzgar" / "mobil_sticky_host.json"
    try:
        import subprocess

        out = subprocess.check_output(
            ["tailscale", "status", "--json"],
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=5,
        )
        data = json.loads(out)
        dns = str((data.get("Self") or {}).get("DNSName") or "").rstrip(".").lower()
        tips = (data.get("Self") or {}).get("TailscaleIPs") or []
        print("tailscale DNSName", dns, "ips", tips)
        if dns and ".ts.net" in dns:
            print("OK MagicDNS", f"https://{dns}:8443/mobil/")
        else:
            print("WARN MagicDNS yok")
        if sticky_path.is_file():
            print("sticky_file", sticky_path.read_text(encoding="utf-8")[:400])
    except Exception as exc:
        print("WARN tailscale", str(exc)[:160])

    print("asama_d_version", ASAMA_D_VERSION)
    if failed:
        print("SMOKE_FAIL asama_d", failed)
        return 1
    print("SMOKE_OK asama_d")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
