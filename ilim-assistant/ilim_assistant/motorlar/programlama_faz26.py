# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 26: tüm programlama turlarında kod beyin önceliği.

Görev dışı sohbetlerde de Groq/kod öncelikli zincir (env ile).
"""

from __future__ import annotations

import os

FAZ26_VERSION = "programlama-faz26-v1-2026-05-25"
_DEFAULT_CHAIN = "kod,groq,gemini"


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ26", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def programming_brain_chain_ids() -> list[str]:
    """Programlama modu LLM zinciri — Faz 19/26 birleşik."""
    if not _enabled():
        return []
    raw = (
        os.environ.get("RUZGAR_PROG_BRAIN_CHAIN", "").strip()
        or os.environ.get("RUZGAR_CODE_AGENT_BRAIN", "").strip()
        or _DEFAULT_CHAIN
    )
    ids = [x.strip() for x in raw.split(",") if x.strip()]
    if not ids:
        ids = [x.strip() for x in _DEFAULT_CHAIN.split(",")]
    try:
        from ilim_assistant.gemini_quota_guard import gemini_cooldown_active

        if gemini_cooldown_active() and "gemini" in ids:
            rest = [x for x in ids if x != "gemini"]
            ids = ["groq", "kod"] + [x for x in rest if x not in ("groq", "kod")]
    except Exception:
        pass
    try:
        from ilim_assistant.llm_ollama import ollama_reachable

        if ollama_reachable():
            for fb in ("kod", "denge"):
                if fb not in ids:
                    ids.append(fb)
    except Exception:
        pass
    seen: set[str] = set()
    out: list[str] = []
    for i in ids:
        if i not in seen:
            seen.add(i)
            out.append(i)
    try:
        from ilim_assistant.motorlar.programlama_faz85 import local_first_brain_chain

        out = local_first_brain_chain(out)
    except Exception:
        pass
    return out


def faz26_directive() -> str:
    chain = ",".join(programming_brain_chain_ids()[:4]) or _DEFAULT_CHAIN
    return (
        "[BEYİN — Faz 26]\n"
        f"Programlama modu zinciri: {chain}\n"
        "Env: RUZGAR_PROG_BRAIN_CHAIN=groq,kod,gemini\n"
    )
