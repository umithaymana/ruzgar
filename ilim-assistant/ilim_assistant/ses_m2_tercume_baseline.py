"""
M2 — Tercüme motor baseline (SRT mock + dil çifti + hub + API).

Canlı LLM zorunlu değil; SRT çevirisi mock batch ile ölçülür.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

M2_VERSION = "ses-m2-tercume-baseline-v1-2026-11-03"

SAMPLE_SRT = """1
00:00:01,000 --> 00:00:03,000
Hello world

2
00:00:04,000 --> 00:00:06,500
How are you?
"""


def stage_lang_pair() -> dict[str, Any]:
    from ilim_assistant.motorlar.tercume_faz74 import (
        extract_translate_text,
        parse_language_pair,
    )

    cases = [
        ("bu metni turkceye cevir: Hello", "en", "tr", "Hello"),
        ("ingilizceye cevir: Merhaba", "auto", "en", "Merhaba"),
        ("arapcaya cevir: selam", "auto", "ar", "selam"),
        ("fransizcaya cevir: merhaba", "auto", "fr", "merhaba"),
        ("Hello world turkceye cevir", "en", "tr", "Hello world"),
    ]
    fail = 0
    rows = []
    for msg, es, et, eb in cases:
        src, tgt = parse_language_pair(msg)
        body = extract_translate_text(msg)
        ok = src == es and tgt == et and body == eb
        if not ok:
            fail += 1
        rows.append({"msg": msg[:36], "ok": ok, "src": src, "tgt": tgt, "body": body})
    return {"ok": fail == 0, "fail": fail, "cases": rows}


def stage_srt_mock() -> dict[str, Any]:
    from ilim_assistant.motorlar import altyazi_fabrika as fab
    from ilim_assistant.motorlar.tercume_faz74 import classify_tercume_intent
    from ilim_assistant.motorlar.tercume_srt import translate_srt_text
    from ilim_assistant.ruzgar_motor_kernel import INTENT_DO

    intent = classify_tercume_intent(
        "turkceye cevir:\n" + SAMPLE_SRT, mode_norm="tercume"
    )
    if intent.get("intent") != INTENT_DO or intent.get("reason") != "translate_srt":
        return {"ok": False, "note": f"intent={intent}"}

    def _fake_batch(texts, *, src_lang, tgt_lang):  # noqa: ARG001
        return [f"TR:{t}" for t in texts]

    fab._subtitle_translate_batch = _fake_batch  # type: ignore[attr-defined]
    out = translate_srt_text(SAMPLE_SRT, src_lang="en", tgt_lang="tr")
    ok = bool(out.get("ok")) and "TR:Hello world" in str(out.get("srt") or "")
    return {
        "ok": ok,
        "cue_count": out.get("cue_count"),
        "has_timing": "00:00:01,000 --> 00:00:03,000" in str(out.get("srt") or ""),
    }


def stage_hub() -> dict[str, Any]:
    from ilim_assistant.motorlar.ana_motor_hub_faz76 import resolve_hub_target

    cases = [
        ("bunu turkceye cevir: Hello", "tercume"),
        ("srt cevir: clips/a.srt", "tercume"),
        ("fotosentez nedir", "genel"),
        ("nasilsin", "genel"),
    ]
    fail = 0
    rows = []
    for msg, exp in cases:
        hub, meta = resolve_hub_target(msg)
        ok = hub == exp
        if not ok:
            fail += 1
        rows.append({"msg": msg[:36], "ok": ok, "hub": hub, "reason": meta.get("reason")})
    return {"ok": fail == 0, "fail": fail, "cases": rows}


def stage_api_routes() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[1]
    ds = (root / "desktop_server.py").read_text(encoding="utf-8")
    need = (
        "/api/tercume/srt",
        "/api/tercume/translate-chunk",
        "/api/tercume/pipeline",
        "/api/tercume/config",
        "/api/tercume/readiness",
    )
    missing = [r for r in need if r not in ds]
    return {"ok": not missing, "missing": missing}


def stage_workbench() -> dict[str, Any]:
    from ilim_assistant.motorlar.tercume_atolye import workbench_config

    cfg = workbench_config()
    return {
        "ok": bool(cfg.get("version")) and "book_extensions" in cfg,
        "version": cfg.get("version"),
    }


def run_m2_baseline() -> dict[str, Any]:
    report: dict[str, Any] = {"version": M2_VERSION, "ok": False, "stages": {}}
    report["stages"]["lang_pair"] = stage_lang_pair()
    report["stages"]["srt_mock"] = stage_srt_mock()
    report["stages"]["hub"] = stage_hub()
    report["stages"]["api_routes"] = stage_api_routes()
    report["stages"]["workbench"] = stage_workbench()
    report["ok"] = all(bool((s or {}).get("ok")) for s in report["stages"].values())
    return report
