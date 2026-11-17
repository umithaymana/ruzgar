# Created by Ümit & Gökçenur
"""Niyet düzeltme + pretreat + bilgi guard smoke."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from ilim_assistant.idrak_on_islem import pretreat_user_turn
    from ilim_assistant.ruzgar_soru_yazim import apply_stt_niyet_fix, resolve_user_niyet
    from ilim_assistant.ruzgar_tek_beyin_bilgi_guard import assess_bilgi_topic_alignment

    cases = [
        ("foto senrez nedir", "fotosentez"),
        ("foto sentez nedir", "fotosentez"),
        ("osman li kimdir", "osmanlı"),
        ("pey gamber kimdir", "peygamber"),
        ("yapay zekâ nedir", "yapay"),
    ]
    for raw, needle in cases:
        fixed, meta = resolve_user_niyet(raw)
        assert needle in fixed.lower(), (raw, fixed, meta)
        assert meta.get("changed") or needle in raw.lower(), (raw, fixed)

    pre = pretreat_user_turn("foto senrez nedir")
    assert "fotosentez" in pre.text.lower()
    assert pre.changed

    stt = apply_stt_niyet_fix({"text": "foto senrez nedir", "ok": True})
    assert "fotosentez" in stt["text"].lower()
    assert stt.get("text_raw")

    reply = (
        "Fotosentez, bitkilerin ışık enerjisini kullanarak karbondioksit ve sudan "
        "organik madde üretmesidir."
    )
    ok, ov, reason = assess_bilgi_topic_alignment("foto senrez nedir", reply)
    assert ok, (ok, ov, reason)

    print("smoke_soru_yazim_guard OK v2")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
