#!/usr/bin/env python3
"""Smoke — Faz E tek yüz: sohbet → Tercüme / Video quiet handoff (3 cümle + negatifler)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from ilim_assistant.ana_motor_faz_e_tek_yuz import (
        enrich_orchestra_faz_e,
        parse_faz_e_intent,
        parse_tercume_gorev_intent,
        parse_video_gorev_intent,
    )
    from ilim_assistant.ruzgar_orkestrasyon_faz_c import build_genel_orchestra_preview

    fails = 0

    # 1) SRT çeviri niyeti
    srt_msg = "altyazilar/ornek.srt dosyasını İngilizceye çevir"
    hit = parse_tercume_gorev_intent(srt_msg)
    ok = bool(hit) and hit.get("motor") == "tercume" and hit.get("kind") == "tercume_gorev"
    ok = ok and "ornek.srt" in str(hit.get("path") or "")
    print(f"  {'OK' if ok else 'FAIL'} SRT çeviri hit={bool(hit)} path={(hit or {}).get('path')!r}")
    if not ok:
        fails += 1

    # 2) Metin → tercüme atölye öneki
    txt_msg = "tercümede: Bu uzun bir örnek cümle, paneli doldurmak için yazıldı."
    hit2 = parse_tercume_gorev_intent(txt_msg)
    ok2 = bool(hit2) and hit2.get("kind") == "tercume_gorev" and bool(hit2.get("text"))
    print(f"  {'OK' if ok2 else 'FAIL'} tercüme atölye hit={bool(hit2)}")
    if not ok2:
        fails += 1

    # 3) Video URL + indir
    vid_msg = "şu videoyu indir https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    hit3 = parse_video_gorev_intent(vid_msg)
    ok3 = (
        bool(hit3)
        and hit3.get("motor") == "video"
        and hit3.get("kind") == "video_gorev"
        and "youtube.com" in str(hit3.get("url") or "")
    )
    print(f"  {'OK' if ok3 else 'FAIL'} video URL hit={bool(hit3)} url={(hit3 or {}).get('url')!r}")
    if not ok3:
        fails += 1

    # Negatif: bilgi sorusu / yüzey gönder / kısa anlık
    for msg in (
        "nasılsın bugün",
        "belgeyi tercümeye gönder",
        "merhaba'yı İngilizceye çevir",
    ):
        neg = parse_faz_e_intent(msg)
        okn = neg is None
        print(f"  {'OK' if okn else 'FAIL'} negatif {msg[:40]!r} hit={bool(neg)}")
        if not okn:
            fails += 1

    orch = enrich_orchestra_faz_e({}, srt_msg)
    ua = orch.get("ui_action") or {}
    if not orch.get("quiet") or ua.get("motor") != "tercume" or ua.get("kind") != "tercume_gorev":
        print("FAIL enrich tercume", ua)
        fails += 1
    else:
        print("  OK enrich_orchestra_faz_e tercume")

    orch_v = enrich_orchestra_faz_e({}, vid_msg)
    uav = orch_v.get("ui_action") or {}
    if uav.get("motor") != "video" or not uav.get("url"):
        print("FAIL enrich video", uav)
        fails += 1
    else:
        print("  OK enrich_orchestra_faz_e video")

    # 6c önce gelirse E ezmez
    orch_skip = enrich_orchestra_faz_e(
        {"ui_action": {"type": "surface_handoff", "motor": "programlama"}},
        srt_msg,
    )
    if orch_skip.get("ui_action", {}).get("motor") != "programlama":
        print("FAIL skip when ui_action set", orch_skip.get("ui_action"))
        fails += 1
    else:
        print("  OK mevcut ui_action korunur")

    orch2, patch = build_genel_orchestra_preview(vid_msg)
    ua2 = orch2.get("ui_action") or {}
    if ua2.get("motor") != "video" or not patch.get("faz_e"):
        print("FAIL preview", ua2, patch.get("faz_e"))
        fails += 1
    else:
        print("  OK build_genel_orchestra_preview faz_e")

    if fails:
        print(f"FAIL {fails}")
        return 1
    print("PASS ana_motor_faz_e_smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
