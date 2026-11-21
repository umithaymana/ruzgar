# -*- coding: utf-8 -*-
# Created by Ümit & Gökçenur
"""S0 smoke — Ses tavanı ölçüm kartı + rapor tabanı."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _ok(cond: bool, label: str) -> int:
    print(("OK" if cond else "FAIL"), "-", label)
    return 0 if cond else 1


def main() -> int:
    from ilim_assistant.ses_s0_olcum import (
        S0_VERSION,
        TAVAN_PROFILLER_HEDEF,
        run_s0_card,
        s0_enabled,
        sealed_refs,
        write_s0_docs,
    )

    failed = 0
    failed += _ok("s0-tavan-olcum" in S0_VERSION, f"ver {S0_VERSION}")
    failed += _ok(s0_enabled(), "S0 varsayılan açık")

    refs = sealed_refs()
    failed += _ok(
        float(refs["v0_tts_first_byte_ms"]) == 1686.0, "V0 first-byte ref 1686"
    )
    failed += _ok(
        float(refs["v3_target_first_byte_ms"]) < float(refs["v0_tts_first_byte_ms"]),
        "V3 hedef < V0",
    )
    failed += _ok(
        list(TAVAN_PROFILLER_HEDEF) == ["muhabbet", "alim", "tilavet"],
        f"tavan profiller {TAVAN_PROFILLER_HEDEF}",
    )

    # Smoke hızlı: canlı Edge yok (LIVE=0). Canlı: RUZGAR_S0_LIVE=1
    os.environ.setdefault("RUZGAR_S0_LIVE", "0")
    live_flag = os.environ.get("RUZGAR_S0_LIVE", "0").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
        "",
    )
    card = run_s0_card(live_tts=live_flag)
    failed += _ok(isinstance(card.get("ozet"), dict), "ozet block")
    failed += _ok(isinstance(card.get("robot"), dict), "robot block")
    failed += _ok(isinstance(card.get("profiller"), dict), "profiller block")
    failed += _ok(isinstance(card.get("mobil_esitlik"), dict), "mobil block")

    ozet = card["ozet"]
    failed += _ok(
        float(ozet.get("yapi_robot_0_5") or 0) >= 4.0,
        f"yapi_robot>={ozet.get('yapi_robot_0_5')}",
    )
    failed += _ok(bool(ozet.get("mobil_esitlik_ok")), "mobil eşitlik sözleşme")
    gap = ozet.get("profil_gap") or []
    failed += _ok(
        "muhabbet" in gap and "tilavet" in gap,
        f"S1 gap beklenen gap={gap}",
    )
    failed += _ok(bool(ozet.get("s0_yesil")), f"s0_yesil={ozet.get('s0_yesil')}")

    paths = write_s0_docs(card)
    md = Path(paths["md"])
    js = Path(paths["json"])
    failed += _ok(md.is_file() and md.stat().st_size > 200, f"doc {md.name}")
    failed += _ok(js.is_file() and js.stat().st_size > 100, f"json {js.name}")
    md_txt = md.read_text(encoding="utf-8")
    failed += _ok("1686" in md_txt and "S1" in md_txt, "doc refs+S1")

    if live_flag:
        live = card.get("tts_live") or {}
        fb = live.get("first_byte_ms")
        failed += _ok(bool(live.get("ran")), "live ran")
        failed += _ok(
            fb is not None and float(fb) > 0 and float(fb) < 4500,
            f"live first_byte_ms={fb}",
        )
        print(
            f"live first_byte_ms={fb} total_ms={live.get('total_ms')} "
            f"note={live.get('note')}"
        )
    else:
        print("live skip (RUZGAR_S0_LIVE=0) — yapı kartı yeterli")

    # Plan dosyası varlık
    plan = ROOT.parent / "RUZGAR_SES_VIDEO_TAVAN_PLAN_2026-11-21.md"
    failed += _ok(plan.is_file(), "plan kilit dosyası")

    total = 16 if live_flag else 14
    print(f"result: {total - failed}/{total} pass")
    print(f"wrote {md.name} · {js.name}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
