"""
Tercüme motoru — çeviri için LLM zinciri (Ollama öncelik, net hatalar).
"""

from __future__ import annotations

import os
from typing import Any

TERCUME_LLM_VERSION = "tercume-llm-v13-2026-06-01"


def translation_brain_status() -> dict[str, Any]:
    """Çeviri için hangi beyinler hazır."""
    from ilim_assistant.config import gemini_disabled, groq_disabled, ollama_only_mode

    ollama = False
    ollama_detail = ""
    try:
        from ilim_assistant.llm_ollama import ollama_reachable

        ollama = bool(ollama_reachable())
        ollama_detail = (
            os.environ.get("OLLAMA_CHAT_MODEL", "llama3.1:8b")
            if ollama
            else "ollama serve çalışmıyor"
        )
    except Exception as exc:
        ollama_detail = str(exc)[:120]

    groq = False
    if not groq_disabled():
        groq = bool((os.environ.get("GROQ_API_KEY") or "").strip())

    gemini = False
    if not gemini_disabled():
        try:
            from ilim_assistant.llm_gemini import gemini_configured

            gemini = bool(gemini_configured())
        except Exception:
            pass

    only = ollama_only_mode()
    ready = ollama if only else (ollama or groq or gemini)
    chain: list[str] = []
    if ollama:
        chain.append("Ollama")
    if not only:
        if groq:
            chain.append("Groq")
        if gemini:
            chain.append("Gemini")

    return {
        "ollama_only": only,
        "ready": ready,
        "ollama": ollama,
        "ollama_model": ollama_detail,
        "groq": groq,
        "gemini": gemini,
        "chain": chain,
    }


def _cloud_translate_attempt(system: str, user: str) -> dict[str, Any] | None:
    try:
        from ilim_assistant.config import groq_disabled

        if not groq_disabled():
            from ilim_assistant.llm_brain import chat_completion_groq

            out = chat_completion_groq(system, user)
            if out and not out.strip().startswith("["):
                return {"ok": True, "text": out.strip(), "provider": "groq"}
    except Exception:
        pass
    try:
        from ilim_assistant.config import gemini_disabled
        from ilim_assistant.gemini_quota_guard import gemini_cooldown_active
        from ilim_assistant.llm_gemini import chat_completion_gemini, gemini_configured

        if (
            not gemini_disabled()
            and gemini_configured()
            and not gemini_cooldown_active()
        ):
            out = chat_completion_gemini(system, user)
            if out and not out.strip().startswith("["):
                return {"ok": True, "text": out.strip(), "provider": "gemini"}
    except Exception:
        pass
    return None


def translate_completion(
    system: str,
    user: str,
    *,
    max_tokens: int = 4000,
    cloud_first: bool = False,
) -> dict[str, Any]:
    """
    Çeviri LLM çağrısı.
    Dönüş: { ok, text?, error?, error_code?, hint_tr?, provider? }
    """
    st = translation_brain_status()
    if not st.get("ready"):
        if st.get("ollama_only"):
            return {
                "ok": False,
                "error_code": "ollama_offline",
                "error": "Yerel Ollama kapalı veya erişilemiyor.",
                "hint_tr": (
                    "Ümit abi, çeviri için Ollama gerekli: terminalde `ollama serve`, "
                    "sonra `ollama pull llama3.1:8b`. .env: RUZGAR_OLLAMA_ONLY=1 ve "
                    "RUZGAR_DISABLE_LOCAL_OLLAMA=0."
                ),
            }
        return {
            "ok": False,
            "error_code": "no_brain",
            "error": "Çeviri beyni yok.",
            "hint_tr": "Ollama açın veya GEMINI_API_KEY / GROQ_API_KEY tanımlayın.",
        }

    sys_txt = (system or "").strip()
    usr_txt = (user or "").strip()

    if cloud_first and not st.get("ollama_only"):
        hit = _cloud_translate_attempt(sys_txt, usr_txt)
        if hit:
            return hit

    if st.get("ollama") or st.get("ollama_only"):
        try:
            from ilim_assistant.llm_ollama import chat_completion

            out = (chat_completion(sys_txt, usr_txt, max_tokens=max_tokens) or "").strip()
            if out and not out.startswith("["):
                return {"ok": True, "text": out, "provider": "ollama"}
        except Exception as exc:
            if st.get("ollama_only"):
                return {
                    "ok": False,
                    "error_code": "ollama_error",
                    "error": str(exc)[:200],
                    "hint_tr": "Ollama yanıt vermedi — model indirildi mi? `ollama pull llama3.1:8b`",
                }

    if not st.get("ollama_only"):
        hit = _cloud_translate_attempt(sys_txt, usr_txt)
        if hit:
            return hit

    return {
        "ok": False,
        "error_code": "empty_response",
        "error": "LLM boş veya hata döndü.",
        "hint_tr": (
            "Çeviri üretilemedi. Ollama çalışıyorsa modeli kontrol edin; "
            "bulut kapalıysa yalnızca yerel model kullanılır."
        ),
    }
