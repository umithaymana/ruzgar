# Created by Ümit & Gökçenur
"""Blok I — yerel öncelik zinciri workbench (Groq'suz / ollama-only)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

LOCAL_WORKBENCH_VERSION = "programlama-local-workbench-v1-2026-05-29"
_E3_TEXT_ONLY_TARGET = 0.01


def e3_text_only_target() -> float:
    try:
        return max(
            0.005,
            min(0.05, float(os.environ.get("RUZGAR_E3_TEXT_ONLY_TARGET", str(_E3_TEXT_ONLY_TARGET)))),
        )
    except ValueError:
        return _E3_TEXT_ONLY_TARGET


def ollama_only_chain_ids() -> list[str]:
    """RUZGAR_OLLAMA_ONLY=1 iken beklenen programlama zinciri."""
    return ["kod", "denge", "hizli"]


def rural_fallback_message(*, ollama_up: bool, ollama_only: bool) -> str:
    if ollama_only and not ollama_up:
        return (
            "Ümit abi, yerel Ollama modu açık ama Ollama yanıt vermiyor. "
            "`ollama serve` çalıştırın veya RUZGAR_OLLAMA_ONLY=0 ile bulut yedek açın."
        )
    if ollama_only:
        return "Kırsal/yerel mod: yalnızca Ollama (kod/denge/hizli) — Gemini/Groq kapalı."
    if not ollama_up:
        return (
            "Ollama kapalı — programlama Groq/Gemini yedek zincirine düşer. "
            "Yerel öncelik için Ollama'yı başlatın."
        )
    return "Yerel öncelik aktif: kod → denge → hizli, sonra bulut yedek."


def _gemini_fc_stress() -> dict[str, Any]:
    try:
        from ilim_assistant.motorlar.programlama_faz57 import (
            gemini_fc_available,
            groq_fc_available,
            reorder_brain_chain_for_fc,
            select_fc_provider,
        )

        base = ["groq", "kod", "gemini"]
        reordered = reorder_brain_chain_for_fc(list(base))
        groq = groq_fc_available()
        gem = gemini_fc_available()
        ok = True
        if not groq and gem:
            ok = reordered and reordered[0] == "gemini"
        elif groq:
            ok = reordered and reordered[0] in ("groq", "kod")
        return {
            "ok": ok,
            "groq_fc": groq,
            "gemini_fc": gem,
            "provider": select_fc_provider(),
            "chain_without_groq": reordered if not groq else base,
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:120]}


def _ollama_only_self_test() -> dict[str, Any]:
    expected = ollama_only_chain_ids()
    forbidden = {"groq", "gemini"}
    leaked = [x for x in expected if x in forbidden]
    return {
        "ok": not leaked and expected[0] == "kod",
        "expected_chain": expected,
        "cloud_blocked": list(forbidden),
    }


def build_local_workbench_payload(workspace_root: str | Path | None) -> dict[str, Any]:
    from ilim_assistant.config import gemini_disabled, groq_disabled, ollama_only_mode
    from ilim_assistant.motorlar.programlama_faz26 import (
        p9_strict_local_first,
        programming_brain_chain_ids,
    )
    from ilim_assistant.motorlar.programlama_faz57 import compute_text_only_stats
    from ilim_assistant.motorlar.programlama_faz85 import (
        local_first_brain_chain,
        local_first_enabled,
        ollama_available,
    )
    from ilim_assistant.ruzgar_ui_manifest import build_ui_manifest

    ollama_up = ollama_available()
    ollama_only = ollama_only_mode()
    chain = programming_brain_chain_ids()
    raw_chain = list(chain)
    if local_first_enabled() and ollama_up:
        chain = local_first_brain_chain(chain)

    text_stats = compute_text_only_stats(workspace_root, window_days=7)
    e3_target = e3_text_only_target()
    rate = float(text_stats.get("text_only_rate") or 0)
    total = int(text_stats.get("total_turns") or 0)
    e3_ok = total < 5 or rate <= e3_target

    manifest = build_ui_manifest()
    prog_tag = str((manifest.get("motors") or {}).get("programlama", {}).get("tag") or "")

    cloud_in_chain = [x for x in chain if x in ("groq", "gemini")]
    local_leads = bool(chain and chain[0] in ("kod", "denge", "hizli"))

    return {
        "ok": True,
        "version": LOCAL_WORKBENCH_VERSION,
        "modes": {
            "ollama_only": ollama_only,
            "gemini_disabled": gemini_disabled(),
            "groq_disabled": groq_disabled(),
            "prog_local_first": local_first_enabled(),
            "p9_strict_local_first": p9_strict_local_first(),
            "ollama_available": ollama_up,
        },
        "chain": {
            "effective": chain[:8],
            "raw": raw_chain[:8],
            "local_first_active": local_leads,
            "cloud_tail": cloud_in_chain,
            "ollama_only_preview": ollama_only_chain_ids(),
        },
        "e3": {
            "target_text_only_rate": e3_target,
            "current_rate": rate,
            "sample_total": total,
            "meets_target": e3_ok,
            "faz57_target": float(text_stats.get("target_rate") or 0.03),
            "faz57_meets": bool(text_stats.get("meets_target")),
        },
        "text_only": text_stats,
        "fc_stress": _gemini_fc_stress(),
        "ollama_only_test": _ollama_only_self_test(),
        "rural": {
            "fallback_message": rural_fallback_message(
                ollama_up=ollama_up,
                ollama_only=ollama_only,
            ),
            "offline_smoke_hint": (
                "API'siz: python scripts/programlama_local_smoke.py"
            ),
        },
        "manifest": {
            "programlama_tag": prog_tag,
            "ok": bool(prog_tag),
        },
        "report_hint": "docs/PROGRAMLAMA_E3_YEREL_ZINCIR.md",
    }
