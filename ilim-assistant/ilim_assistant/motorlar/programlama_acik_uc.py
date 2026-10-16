# Created by Ümit & Gökçenur
"""Açık uç — tarif ve incelemenin yerine geçmez.

Sıra: yerel Ollama (kod, denge, hizli), gerekirse web.
"""

from __future__ import annotations

import unicodedata

ACIK_UC_VERSION = "programlama-acik-uc-v1-2026-10-16"
LOCAL_CHAIN = ("kod", "denge", "hizli")
AFTER_LOCAL = ("web",)


def _fold(text: str) -> str:
    raw = unicodedata.normalize("NFKD", text or "")
    raw = "".join(c for c in raw if not unicodedata.combining(c))
    raw = raw.replace("ı", "i").replace("İ", "I").lower()
    return " ".join(raw.split())


def open_end_chain() -> list[str]:
    return list(LOCAL_CHAIN) + list(AFTER_LOCAL)


def wants_acik_uc(message: str) -> bool:
    low = _fold(message)
    return any(
        cue in low
        for cue in (
            "acik uc",
            "beyin sirasi",
            "beyin zinciri",
        )
    )


def format_acik_uc_report(*, ollama_up: bool | None = None) -> str:
    if ollama_up is None:
        try:
            from ilim_assistant.motorlar.programlama_faz85 import ollama_available

            ollama_up = ollama_available()
        except Exception:
            ollama_up = False
    chain = " → ".join(open_end_chain())
    local = "Yerel Ollama dinliyor." if ollama_up else "Yerel Ollama yanıt vermiyor; sıra web'e gelir."
    return "\n".join(
        [
            "Ümit abi, açık uç sırası tarifin ve incelemenin yerine geçmez.",
            "",
            f"Sıra: {chain}",
            local,
            "Tarif eşleşirse dosya yerelden yazılır, model çağrılmaz.",
            "Tarif yoksa dosya uydurulmaz.",
            "Açık soru bu sıraya kalır: önce kod, denge, hizli; gerekirse web.",
            f"({ACIK_UC_VERSION})",
        ]
    )


def acik_uc_directive() -> str:
    chain = ",".join(open_end_chain())
    return (
        "[AÇIK UÇ]\n"
        f"Tarif, kütüphane envanteri ve derin inceleme bu sıranın önündedir: {chain}.\n"
        "Tarifi olmayan iş için dosya uydurma. Açık soruda önce yerel Ollama, gerekirse web.\n"
    )
