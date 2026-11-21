# -*- coding: utf-8 -*-
# Created by Ümit & Gökçenur
"""Smoke — duygu hattı (STT→TTS) + köşeli etiket prosodi."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    failed = 0
    total = 0

    def check(cond: bool, label: str) -> None:
        nonlocal failed, total
        total += 1
        print(("OK" if cond else "FAIL"), "-", label)
        if not cond:
            failed += 1

    from ilim_assistant.dinamit_gelisme import (
        emotion_ses_adjustments,
        fuse_emotion,
        infer_emotion_from_text,
        merge_pitch,
    )
    from ilim_assistant.ses_etiket_prosodi import (
        DURAK_CARPAN_MAX,
        ETIKET_VERSION,
        HIZ_MIN,
        RATE_EXTRA_MIN,
        apply_rate_pitch_extras,
        parse_ses_etiketleri,
        strip_etiket_smoke_cases,
    )
    from ilim_assistant.motorlar.ses_motoru import IcerikYolu
    from ilim_assistant.motorlar.ses_prosody import DurakTuru, durak_suresi_ms

    check("etiket-prosodi" in ETIKET_VERSION, f"ver {ETIKET_VERSION}")
    check("v2" in ETIKET_VERSION, "etiket v2 sınır")

    # Metin duygu
    check(infer_emotion_from_text("çok yoruldum bugün") == "yorgun", "infer yorgun")
    check(infer_emotion_from_text("harika süper") == "mutlu", "infer mutlu")
    check(infer_emotion_from_text("bu önemli ve ciddi") == "ciddi", "infer ciddi")
    check(fuse_emotion("merhaba", 0.15) == "yorgun", "fuse energy→yorgun")
    check(fuse_emotion("merhaba", 0.85) == "mutlu", "fuse energy→mutlu")
    check(fuse_emotion("yoruldum", 0.9) == "yorgun", "metin öncelikli")

    h, hz, p = emotion_ses_adjustments("ciddi")
    check(h < 1.0 and hz < 1.0 and "-3" in p, f"ciddi adj h={h} p={p}")
    check(merge_pitch("+1Hz", "-3Hz") == "-2Hz", "merge_pitch")

    # Etiket ayıklama
    for girdi, beklenen, tags in strip_etiket_smoke_cases():
        et = parse_ses_etiketleri(girdi)
        ok_txt = et.temiz_metin == beklenen
        ok_tags = et.etiketler == tags
        check(ok_txt and ok_tags, f"etiket {girdi!r} → {et.temiz_metin!r} {et.etiketler}")
        if tags:
            check("[" not in et.temiz_metin and "]" not in et.temiz_metin, f"ham etiket yok: {girdi!r}")

    et_k = parse_ses_etiketleri("[korku] Dikkat et.")
    check(et_k.rate_extra_pct < 0 and et_k.pitch_extra_hz < 0, "korku rate/pitch")
    check("korku" not in et_k.temiz_metin.lower() or "[" not in et_k.temiz_metin, "korku temiz")

    et_d = parse_ses_etiketleri("A [duraksama:0.8s] B")
    check(et_d.force_prosody and "\n\n" in et_d.temiz_metin, "duraksama→paragraf")
    check(et_d.durak_ek_ms == 800, f"durak_ms={et_d.durak_ek_ms}")
    check(et_d.koru_etiket_durak is True, "duraksama koru flag")
    check(
        1.0 <= et_d.durak_carpani <= DURAK_CARPAN_MAX + 1e-9,
        f"durak_carpani≤{DURAK_CARPAN_MAX} got={et_d.durak_carpani}",
    )

    # Yığın etiket — soft clamp (aşırı yavaş/alçak yok)
    et_y = parse_ses_etiketleri("[korku][vurgulu][fısıltı] ucu")
    check(et_y.hiz_carpani >= HIZ_MIN, f"yığın hiz≥{HIZ_MIN} got={et_y.hiz_carpani}")
    check(
        et_y.rate_extra_pct >= RATE_EXTRA_MIN,
        f"yığın rate≥{RATE_EXTRA_MIN} got={et_y.rate_extra_pct}",
    )
    check(
        et_y.pitch_extra_hz >= -8 and et_y.pitch_extra_hz <= 6,
        f"yığın pitch clamp got={et_y.pitch_extra_hz}",
    )
    check("[" not in et_y.temiz_metin, "yığın ham etiket yok")

    # Çift duraksama — tek hedef (max), çarpımsal şişme yok
    et_dd = parse_ses_etiketleri("A [duraksama:0.8s] B [duraksama:1.5s] C")
    check(et_dd.durak_ek_ms == 1200, f"durak max tavan got={et_dd.durak_ek_ms}")
    check(et_dd.durak_carpani <= DURAK_CARPAN_MAX + 1e-9, "çift durak carpani tavan")

    # Prosody: etiket koruması lean'i atlar; 0.8s dengeli aralıkta
    ms_koru = durak_suresi_ms(
        DurakTuru.paragraf,
        icerik=IcerikYolu.genel,
        durak_carpani=et_d.durak_carpani,
        huzur_carpani=0.88,
        koru_etiket_durak=True,
        etiket_hedef_ms=800,
    )
    check(500 <= ms_koru <= 1000, f"duraksama 0.8s kulak aralığı ms={ms_koru}")
    ms_lean = durak_suresi_ms(
        DurakTuru.paragraf,
        icerik=IcerikYolu.genel,
        durak_carpani=et_d.durak_carpani,
        huzur_carpani=0.88,
        koru_etiket_durak=False,
    )
    check(ms_koru >= ms_lean, f"koru≥lean ({ms_koru}>={ms_lean})")

    r, p2 = apply_rate_pitch_extras("-10%", "+0Hz", et_k)
    check(r.endswith("%") and "Hz" in p2, f"apply extras r={r} p={p2}")

    # API / istemci bağları (statik)
    ds = (ROOT / "desktop_server.py").read_text(encoding="utf-8")
    check("fuse_emotion" in ds and "mic_energy" in ds, "STT fuse+mic_energy")
    check("parse_ses_etiketleri" in ds, "TTS etiket")
    check("emotion_ses_adjustments" in ds, "TTS emotion_ses_adjustments")
    check("apply_rate_pitch_extras" in ds, "TTS rate/pitch extras")
    check('payload["emotion"]' in ds or "payload[\"emotion\"]" in ds, "STT emotion payload")
    check("koru_etiket_durak" in ds, "API koru_etiket_durak")

    desk = ROOT.parent / "ruzgar-desktop" / "app.js"
    desk_txt = desk.read_text(encoding="utf-8")
    check("mic_energy" in desk_txt and "lastVoiceEmotion" in desk_txt, "desktop STT emotion")
    check("payload.emotion" in desk_txt, "desktop TTS emotion")

    mob = ROOT / "static" / "mobil-pwa" / "app.js"
    mob_txt = mob.read_text(encoding="utf-8")
    check("lastVoiceEmotion" in mob_txt, "mobil lastVoiceEmotion")
    check("payload.emotion" in mob_txt, "mobil TTS emotion")
    check("j.emotion" in mob_txt, "mobil STT emotion oku")

    # AST — api_stt Form mic_energy
    try:
        tree = ast.parse(ds)
        stt_ok = False
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "api_stt":
                args = [a.arg for a in node.args.args]
                stt_ok = "mic_energy" in args
                break
        check(stt_ok, "api_stt(mic_energy=Form)")
    except SyntaxError as e:
        check(False, f"desktop_server AST: {e}")

    print(f"\n=== smoke_duygu_etiket_hat: {total - failed}/{total} OK ===")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
