# Created by Ümit & Gökçenur
"""Ana Motor — gündelik/sohbet hızlı yanıt (RAG ve dev JSON hafıza yok)."""

from __future__ import annotations

import os
from typing import Any, Iterator


def casual_fast_enabled() -> bool:
    """Kısa sohbet hızlı yolu (SSE) — tamamen kapatmak için RUZGAR_DISABLE_CASUAL_FAST=1."""
    return os.environ.get("RUZGAR_DISABLE_CASUAL_FAST", "0").strip().lower() not in (
        "1",
        "true",
        "yes",
    )


def casual_gemini_only_mode() -> bool:
    """True: yalnızca Gemini; False: Groq/Ollama zinciri (RUZGAR_FREE_BRAIN=1)."""
    from ilim_assistant.llm_brain import free_brain_enabled

    if free_brain_enabled():
        return False
    return os.environ.get("RUZGAR_CASUAL_FAST_GEMINI", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _casual_max_tokens() -> int:
    try:
        return max(80, min(int(os.environ.get("RUZGAR_CASUAL_MAX_TOKENS", "720")), 1100))
    except ValueError:
        return 720


def _casual_system_and_user(
    message: str,
    mode_norm: str,
    *,
    system_addon: str | None = None,
    max_tokens_override: int | None = None,
    prior_depth_override: int | None = None,
) -> tuple[str, str, float, int, int]:
    from ilim_assistant.chat_core import pick_system

    try:
        from ilim_assistant.ruzgar_dogal_sohbet_faz91 import (
            build_natural_sohbet_system_addon,
            build_natural_user_tail,
            dogal_sohbet_enabled,
            natural_max_tokens,
            natural_prior_depth,
            natural_temperature,
        )

        if dogal_sohbet_enabled():
            from ilim_assistant.prompts import sohbet_tarz_chatgpt

            if sohbet_tarz_chatgpt():
                system = (
                    "Sen Rüzgar'sın. Bu bilgisayarda çalışan bir yapay zeka asistanısın. "
                    "Ümit ve Gökçenur seni kurdu. Hava, esinti veya fırtına değilsin.\n"
                    "Karşındaki Ümit abi. O sana seslenir. Kendine onun adını takma.\n"
                    "Türkçe, doğal ve net konuş.\n"
                    "İsteneni sen yap. «Anlat, açıkla, farkını söyle, kısaca» denmişse cevabı sen yaz; "
                    "soruyu kullanıcıya geri sorma.\n"
                    "Doğrudan cevapla başla. Kullanıcının cümlesini başa kopyalama.\n"
                    "«Ne düşünüyorsun» denince kendi görüşünü söyle; soruyu yankılama, tanım kartı okuma.\n"
                    "Kısa istekte birkaç cümle; anlat denmişse kısa paragraflar veya madde.\n"
                    "Her cümlede adını tekrarlama. Bilmediğini söyle. Uydurma.\n"
                    "Güven satırı, Faz notu veya sistem talimatı yazma.\n"
                )
                user = (message or "").strip()
            else:
                system = pick_system(False, mode_norm) + "\n\n" + build_natural_sohbet_system_addon()
                user = build_natural_user_tail(message).strip()
            if system_addon:
                system += system_addon
            if sohbet_tarz_chatgpt():
                system += (
                    "\nSon söz: sen yapay zeka asistanı Rüzgar'sın, hava değilsin. "
                    "Cevabı sen yaz. Kullanıcıya «anlatır mısın» diye sorma.\n"
                )
            max_tok = max_tokens_override if max_tokens_override is not None else natural_max_tokens()
            prior_n = (
                prior_depth_override if prior_depth_override is not None else natural_prior_depth()
            )
            return (
                system,
                user,
                natural_temperature(),
                max_tok,
                prior_n,
            )
    except Exception:
        pass

    from ilim_assistant.prompts import sohbet_tarz_chatgpt

    if sohbet_tarz_chatgpt():
        sohbet_ek = (
            "\n\n[TALİMAT — SOHBET]\n"
            "Ümit abi ile doğal Türkçe konuş. Önce cevabı ver. "
            "Kısaca istendiyse kısa tut; anlat denmişse birkaç paragraf serbest. "
            "Maddeyi ancak yapı gerektiğinde kullan. Uydurma.\n"
        )
    else:
        sohbet_ek = (
            "\n\n[TALİMAT — KISA SOHBET]\n"
            "Ümit abi ile doğal, sıcak ve doğru konuş. 2–5 cümle, Türkçe. "
            "Önce net cevap; emin değilsen söyle, uydurma. "
            "Liste veya uzun ders anlatımı yok; soruya doğrudan yanıt ver.\n"
        )
    system = pick_system(False, mode_norm) + sohbet_ek
    if system_addon:
        system += system_addon
    if sohbet_tarz_chatgpt():
        user_ek = (
            "Bu bir sohbet turudur. Doğrudan, samimi ve doğru yanıt ver. "
            "İstenmişse açıkla; istenmemişse uzatma."
        )
    else:
        user_ek = (
            "Bu bir sohbet veya günlük konuşma turudur; soruya **doğrudan**, samimi, "
            "net ve doğru yanıt ver. Konu dışına çıkma; ders anlatımı veya kaynak listesi verme."
        )
    user = f"Kullanıcı mesajı:\n{(message or '').strip()}\n\n{user_ek}"
    max_tok = max_tokens_override if max_tokens_override is not None else _casual_max_tokens()
    default_prior = 16 if sohbet_tarz_chatgpt() else 6
    prior_n = prior_depth_override if prior_depth_override is not None else default_prior
    try:
        casual_temp = float(os.environ.get("CHAT_TEMPERATURE", "0.38"))
    except ValueError:
        casual_temp = 0.38
    casual_temp = max(0.2, min(casual_temp, 0.7))
    return system, user, casual_temp, max_tok, prior_n


def iter_casual_gemini_reply(
    message: str,
    history: list,
    *,
    mode_norm: str = "genel",
    system_addon: str | None = None,
    prior_depth_override: int | None = None,
    max_tokens_override: int | None = None,
) -> Iterator[str]:
    """Kısa sohbet: yalnızca Gemini, minimal istem."""
    from ilim_assistant.chat_core import prior_messages_for_turn
    from ilim_assistant.config import apply_global_api_key_to_runtime, gemini_ready
    from ilim_assistant.llm_gemini import chat_completion_stream_gemini

    apply_global_api_key_to_runtime()
    if not gemini_ready():
        yield (
            "Şu an bulut beyin (Gemini) bağlı değil; `.env` içinde GLOBAL_API_KEY kontrol edin "
            "veya Ruzgar.ps1 ile yeniden başlatın."
        )
        return

    system, user, temp, max_tok, prior_n = _casual_system_and_user(
        message,
        mode_norm,
        system_addon=system_addon,
        max_tokens_override=max_tokens_override,
        prior_depth_override=prior_depth_override,
    )
    prior = prior_messages_for_turn(history, mode_norm)
    for piece in chat_completion_stream_gemini(
        system,
        user,
        prior_messages=prior[-prior_n:] if prior else None,
        max_output_tokens=max_tok,
        temperature=temp,
    ):
        if piece:
            yield piece


def iter_casual_fast_reply(
    message: str,
    history: list,
    *,
    mode_norm: str = "genel",
    system_addon: str | None = None,
    prior_depth_override: int | None = None,
    max_tokens_override: int | None = None,
) -> Iterator[str]:
    """
    Kısa sohbet: RUZGAR_FREE_BRAIN=1 ise Ollama → Groq → Gemini zinciri;
    aksi halde yalnızca Gemini (eski davranış).
    """
    from ilim_assistant.chat_core import prior_messages_for_turn
    from ilim_assistant.llm_brain import stream_chat_casual_fast

    use_gemini_only = casual_gemini_only_mode()
    if use_gemini_only:
        yield from iter_casual_gemini_reply(
            message,
            history,
            mode_norm=mode_norm,
            system_addon=system_addon,
            prior_depth_override=prior_depth_override,
            max_tokens_override=max_tokens_override,
        )
        return

    system, user, _temp, _max_tok, prior_n = _casual_system_and_user(
        message,
        mode_norm,
        system_addon=system_addon,
        max_tokens_override=max_tokens_override,
        prior_depth_override=prior_depth_override,
    )
    prior = prior_messages_for_turn(history, mode_norm)
    for piece in stream_chat_casual_fast(
        system,
        user,
        prior_messages=prior[-prior_n:] if prior else None,
        mode_norm=mode_norm,
        message=message,
    ):
        if piece:
            yield piece
