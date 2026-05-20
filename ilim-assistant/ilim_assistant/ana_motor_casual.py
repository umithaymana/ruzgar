# Created by Ümit & Gökçenur
"""Ana Motor — gündelik/sohbet hızlı yanıt (RAG ve dev JSON hafıza yok)."""

from __future__ import annotations

import os
from typing import Any, Iterator


def casual_fast_enabled() -> bool:
    return os.environ.get("RUZGAR_CASUAL_FAST_GEMINI", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _casual_max_tokens() -> int:
    try:
        return max(80, min(int(os.environ.get("RUZGAR_CASUAL_MAX_TOKENS", "420")), 900))
    except ValueError:
        return 420


def iter_casual_gemini_reply(
    message: str,
    history: list,
    *,
    mode_norm: str = "genel",
) -> Iterator[str]:
    """Kısa sohbet: yalnızca Gemini, minimal istem."""
    from ilim_assistant.chat_core import pick_system, prior_messages_for_turn
    from ilim_assistant.config import apply_global_api_key_to_runtime, gemini_ready
    from ilim_assistant.llm_gemini import chat_completion_stream_gemini

    apply_global_api_key_to_runtime()
    if not gemini_ready():
        yield (
            "Şu an bulut beyin (Gemini) bağlı değil; `.env` içinde GLOBAL_API_KEY kontrol edin "
            "veya Ruzgar.ps1 ile yeniden başlatın."
        )
        return

    system = (
        pick_system(False, mode_norm)
        + "\n\n[TALİMAT — KISA SOHBET]\n"
        "Ümit abi ile doğal, sıcak sohbet. 2–4 cümle, Türkçe. "
        "Liste veya uzun ders anlatımı yok; soruya doğrudan yanıt ver.\n"
    )
    user = (
        f"Kullanıcı mesajı:\n{(message or '').strip()}\n\n"
        "Bu bir sohbet veya günlük konuşma turudur; soruya **doğrudan**, samimi ve "
        "kısa yanıt ver. Konu dışına çıkma; ders anlatımı veya kaynak listesi verme."
    )
    prior = prior_messages_for_turn(history, mode_norm)
    for piece in chat_completion_stream_gemini(
        system,
        user,
        prior_messages=prior[-6:] if prior else None,
        max_output_tokens=_casual_max_tokens(),
        temperature=0.55,
    ):
        if piece:
            yield piece


def iter_casual_fast_reply(
    message: str,
    history: list,
    *,
    mode_norm: str = "genel",
) -> Iterator[str]:
    """
    Kısa sohbet: RUZGAR_FREE_BRAIN=1 ise Ollama → Groq → Gemini zinciri;
    aksi halde yalnızca Gemini (eski davranış).
    """
    from ilim_assistant.chat_core import pick_system, prior_messages_for_turn
    from ilim_assistant.llm_brain import free_brain_enabled, stream_chat_with_brain

    use_gemini_only = casual_fast_enabled() and not free_brain_enabled()
    if use_gemini_only:
        yield from iter_casual_gemini_reply(message, history, mode_norm=mode_norm)
        return

    system = (
        pick_system(False, mode_norm)
        + "\n\n[TALİMAT — KISA SOHBET]\n"
        "Ümit abi ile doğal, sıcak sohbet. 2–4 cümle, Türkçe. "
        "Liste veya uzun ders anlatımı yok; soruya doğrudan yanıt ver.\n"
    )
    user = (
        f"Kullanıcı mesajı:\n{(message or '').strip()}\n\n"
        "Bu bir sohbet veya günlük konuşma turudur; soruya **doğrudan**, samimi ve "
        "kısa yanıt ver."
    )
    prior = prior_messages_for_turn(history, mode_norm)
    for piece in stream_chat_with_brain(
        system,
        user,
        prior_messages=prior[-6:] if prior else None,
        mode_norm=mode_norm,
        message=message,
    ):
        if piece:
            yield piece
