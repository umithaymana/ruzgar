# Created by Ümit & Gökçenur
"""Dilim 5 — Video bağ cilası: Faz E tek yüz + mutlu niyet + sohbet kaçmaz."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from ilim_assistant.ana_motor_faz_e_tek_yuz import (
        enrich_orchestra_faz_e,
        parse_video_gorev_intent,
    )
    from ilim_assistant.ruzgar_hub_sse_faz_e import detect_video_motor_action
    from ilim_assistant.ruzgar_orkestrasyon_faz_c import build_genel_orchestra_preview

    fails = 0
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    hit = parse_video_gorev_intent(f"şu videoyu indir {url}")
    ok = bool(hit) and hit.get("motor") == "video" and url in str(hit.get("url") or "")
    print(f"  {'OK' if ok else 'FAIL'} indir niyeti")
    if not ok:
        fails += 1

    hit2 = parse_video_gorev_intent(f"videoda: {url}")
    # videoda: öneki + URL — action gerekebilir
    ok2 = bool(hit2) and hit2.get("motor") == "video"
    print(f"  {'OK' if ok2 else 'FAIL'} videoda: öneki hit={bool(hit2)}")
    if not ok2:
        fails += 1

    orch, patch = build_genel_orchestra_preview(f"şu videoyu indir {url}")
    ua = orch.get("ui_action") or {}
    if ua.get("motor") != "video" or not patch.get("faz_e"):
        print("FAIL preview", ua, patch.get("faz_e"))
        fails += 1
    else:
        print("  OK preview faz_e video")

    # Sohbet video atölyesine kaçmasın
    for msg in ("nasılsın", "fotosentez nedir", "hava nasıl"):
        if parse_video_gorev_intent(msg) is not None:
            print("FAIL sohbet video hit", msg)
            fails += 1
        else:
            print(f"  OK negatif {msg!r}")

    if detect_video_motor_action("hava nasıl", {"mode": "video"}) is not None:
        print("FAIL video modunda sohbet atolye")
        fails += 1
    else:
        print("  OK video modunda sohbet→atolye yok")

    # Mevcut ui_action ezilmez
    skip = enrich_orchestra_faz_e(
        {"ui_action": {"type": "surface_handoff", "motor": "programlama"}},
        f"şu videoyu indir {url}",
    )
    if (skip.get("ui_action") or {}).get("motor") != "programlama":
        print("FAIL skip")
        fails += 1
    else:
        print("  OK 6c ui_action korunur")

    if fails:
        print(f"FAIL smoke_video_bag_cilasi_d5 fails={fails}")
        return 1
    print("PASS smoke_video_bag_cilasi_d5")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
