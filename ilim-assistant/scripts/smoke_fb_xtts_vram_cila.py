# -*- coding: utf-8 -*-
# Created by Ümit & Gökçenur
"""Smoke — first-byte cila + XTTS iptal + VRAM hakemi."""
from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _ok(cond: bool, label: str) -> int:
    print(("OK" if cond else "FAIL"), "-", label)
    return 0 if cond else 1


def main() -> int:
    failed = 0
    total = 0

    def check(cond: bool, label: str) -> None:
        nonlocal failed, total
        total += 1
        failed += _ok(cond, label)

    from ilim_assistant.ses_fb_cila import (
        FB_VERSION,
        TARGET_FIRST_BYTE_MS,
        measure_first_byte_suite_sync,
        prefer_v3_over_prosody,
        write_fb_docs,
    )
    from ilim_assistant.ses_xtts_iptal import (
        CloneCancelled,
        begin_job,
        cancel_all,
        check as xtts_check,
        current_gen,
        iptal_enabled,
    )
    from ilim_assistant.ses_vram_hakem import (
        VRAM_VERSION,
        acquire,
        release,
        snapshot,
        vram_hakem_enabled,
    )

    check("fb-cila" in FB_VERSION, f"fb ver {FB_VERSION}")
    check(TARGET_FIRST_BYTE_MS == 900.0, "hedef 900")
    check(
        prefer_v3_over_prosody("Merhaba Ümit abi.", karakter="muhabbet", icerik_genel=True),
        "muhabbet→V3 tercih",
    )
    check(
        not prefer_v3_over_prosody("x" * 900, karakter="tilavet", icerik_genel=False),
        "uzun tilavet V3 zorlamaz",
    )

    # First-byte ölçüm (ağ bağımlı — medyan rapor; soft hedef)
    report = measure_first_byte_suite_sync(rounds=3)
    check(bool(report.get("ok")), f"fb ölçüm ok note={report.get('note')}")
    med = report.get("median_ms")
    check(med is not None and float(med) > 0, f"median={med}")
    # Soft: regressiyon tavanı 2000; under_900 bilgi
    check(med is not None and float(med) < 2000, f"median <2000 got={med}")
    print(
        f"FB median={med} min={report.get('min_ms')} "
        f"under_900={report.get('under_900')} samples={report.get('samples_ms')}"
    )
    paths = write_fb_docs(report)
    check(Path(paths["md"]).is_file(), "fb doc")

    # XTTS iptal
    check(iptal_enabled(), "iptal açık")
    tok = begin_job()
    check(isinstance(tok, int), f"begin tok={tok}")
    cancel_all(reason="smoke")
    raised = False
    try:
        xtts_check(tok)
    except CloneCancelled:
        raised = True
    check(raised, "iptal→CloneCancelled")
    check(current_gen() > tok, "gen arttı")

    ds = (ROOT / "desktop_server.py").read_text(encoding="utf-8")
    check("/api/tts/cancel" in ds, "API cancel")
    check("prefer_v3_over_prosody" in ds, "API fb cila")
    check("warm_edge_stream" in ds, "API edge warm")

    app_js = ROOT.parent / "ruzgar-desktop" / "app.js"
    check(
        "/api/tts/cancel" in app_js.read_text(encoding="utf-8"),
        "desktop barge→cancel",
    )
    mob = ROOT / "static" / "mobil-pwa" / "app.js"
    check("/api/tts/cancel" in mob.read_text(encoding="utf-8"), "mobil stop→cancel")

    # VRAM hakemi
    check("vram-hakem" in VRAM_VERSION, f"vram {VRAM_VERSION}")
    check(vram_hakem_enabled(), "vram açık")
    snap0 = snapshot()
    check("budget_mb" in snap0, f"budget={snap0.get('budget_mb')}")
    acq = acquire("xtts", prepare=True)
    check(acq.get("ok") is True, "acquire xtts")
    check(snapshot().get("owner") == "xtts", "owner xtts")
    rel = release("xtts", restore=False)
    check(rel.get("ok") is True, "release")
    check(snapshot().get("owner") == "idle", "owner idle")

    # Cached XTTS + iptal entegrasyonu (runtime varsa kısa; yoksa yapı yeter)
    from ilim_assistant.motorlar.ses_klon_motoru import (
        coz_referans_yolu,
        xtts_runtime_available,
    )

    check(
        "unload_xtts_cached" in (ROOT / "ilim_assistant" / "motorlar" / "ses_klon_motoru.py").read_text(
            encoding="utf-8"
        ),
        "xtts cache unload",
    )
    if xtts_runtime_available():
        from ilim_assistant.motorlar.ses_klon_motoru import synthesize_clone_wav
        from ilim_assistant.tts_service import read_ses_ayarlari

        ay = read_ses_ayarlari()
        ref = coz_referans_yolu("muhabbet", ayar=ay)
        check(ref is not None and ref.is_file(), f"BUSENAZ ref={ref}")
        # İptal bayrağı açıkken synthesize → CloneCancelled (boşa GPU yok)
        tok2 = begin_job()
        cancel_all(reason="smoke_precancel")
        precancel_ok = False
        try:
            synthesize_clone_wav(
                "Kısa iptal testi.",
                ref,
                language="tr",
                cancel_token=tok2,
            )
        except CloneCancelled:
            precancel_ok = True
        except Exception as e:
            print("WARN precancel:", type(e).__name__, e)
        check(precancel_ok, "klon precancel→CloneCancelled")
    else:
        print("xtts runtime yok — iptal yapı testleri yeterli")
        check(True, "xtts skip")

    print(f"result: {total - failed}/{total} pass")
    print(f"FB under_900={report.get('under_900')} median={med}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
