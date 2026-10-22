# -*- coding: utf-8 -*-
"""C1 — «anlat / daha açık anlat» derinlik: eşleşme + şablon scrub."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _ok(cond: bool, label: str) -> int:
    print(("OK" if cond else "FAIL"), "-", label)
    return 0 if cond else 1


def main() -> int:
    failed = 0
    from ilim_assistant.ruzgar_anlik_niyet_gate import collect_library_llm_context
    from ilim_assistant.ruzgar_bilim_kutuphane import try_bilim_reply
    from ilim_assistant.ruzgar_siyer_kutuphane import try_siyer_reply
    from ilim_assistant.text_encoding import finalize_assistant_reply, strip_answer_scaffold

    failed += _ok(
        try_siyer_reply("hicreti daha açık anlat") is not None,
        "hicreti daha açık anlat → siyer eşleşir",
    )
    failed += _ok(
        try_siyer_reply("hicreti anlat") is not None,
        "hicreti anlat → siyer eşleşir",
    )
    ctx = collect_library_llm_context("hicreti daha açık anlat")
    failed += _ok(
        bool(ctx) and "hicret" in ctx.lower() and "KÜTÜPHANE İPUCU" in ctx,
        "anlat → LLM kütüphane ipucu",
    )
    failed += _ok(
        try_bilim_reply("Fotosentezi biraz daha açık anlat") is not None,
        "fotosentezi anlat → bilim eşleşir",
    )

    bold = (
        "**Niyet:** Hicret hakkında bilgi istemişsin.\n"
        "**Kimlik:** Ben Rüzgar\n"
        "**Üretim:** çalışıyorum\n\n"
        "Hicret, Mekke'den Medine'ye göçtür."
    )
    scrubbed = strip_answer_scaffold(bold)
    failed += _ok(
        "Niyet" not in scrubbed and "Kimlik" not in scrubbed and "Hicret" in scrubbed,
        "bold Niyet/Kimlik scrub",
    )
    echo = (
        "Soru: Fotosentezi biraz daha açık anlat.\n\n"
        "Cevap: Fotosentez, bitkilerin ışıkla besin üretmesidir."
    )
    fin = finalize_assistant_reply(echo)
    failed += _ok(
        not fin.lower().startswith("soru:") and "Fotosentez" in fin,
        "Soru:/Cevap: yankı scrub",
    )
    failed += _ok(
        "Niyet" not in finalize_assistant_reply(bold),
        "finalize bold scaffold",
    )

    total = 7
    print(f"result: {total - failed}/{total} pass")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
