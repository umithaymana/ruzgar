# Created by Ümit & Gökçenur
"""
Rüzgar sohbet akıcılık paketi (A–F).

A) Gemini sohbet-only (programlama yerel kalır)
B) Yerel 14B+ sohbet modeli tercihi (yoksa 8B)
C) Selam/görüş/sohbet turunda ince boru (RAG/web minimum)
D) Kısa sistem istemi (3–5 kural)
E) Ümit abi mini profili
F) İki aşamalı cevap: önce insan, sonra gerekirse doğrulama

Kapat: RUZGAR_SOHBET_AKICILIK=0
"""

from __future__ import annotations

import os
import re
from typing import Any

AKICILIK_VERSION = "ruzgar-sohbet-akicilik-v1-2026-11-12"

# Tercih sırası: sohbet odaklı 14B+ → mevcut 8B
_CHAT_MODEL_PREFERENCE = (
    "qwen2.5:14b",
    "qwen2.5:14b-instruct",
    "llama3.1:70b",
    "llama3.1:14b",
    "gemma2:27b",
    "gemma2:9b",
    "llama3.1:8b",
)


def akicilik_enabled() -> bool:
    return os.environ.get("RUZGAR_SOHBET_AKICILIK", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def gemini_chat_only_enabled() -> bool:
    """Gemini açık ama programlama/kapı yollarında bulut zorlanmaz."""
    if not akicilik_enabled():
        return False
    return os.environ.get("RUZGAR_GEMINI_CHAT_ONLY", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def compact_prompt_enabled() -> bool:
    if not akicilik_enabled():
        return False
    return os.environ.get("RUZGAR_SOHBET_COMPACT_PROMPT", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def thin_pipeline_enabled() -> bool:
    if not akicilik_enabled():
        return False
    return os.environ.get("RUZGAR_SOHBET_THIN_PIPE", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def iki_asama_enabled() -> bool:
    if not akicilik_enabled():
        return False
    return os.environ.get("RUZGAR_IKI_ASAMA", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def umit_profil_enabled() -> bool:
    if not akicilik_enabled():
        return False
    return os.environ.get("RUZGAR_UMIT_MINI_PROFIL", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def strip_gemini_for_programlama(chain_ids: list[str]) -> list[str]:
    """A: Programlama zincirinden Gemini çıkar (chat-only)."""
    if not gemini_chat_only_enabled():
        return list(chain_ids)
    return [x for x in chain_ids if x != "gemini"]


def prefer_gemini_chat_chain(chain_ids: list[str]) -> list[str]:
    """A: Genel/sohbet zincirinde Gemini öne."""
    if not gemini_chat_only_enabled():
        return list(chain_ids)
    try:
        from ilim_assistant.config import gemini_disabled

        if gemini_disabled():
            return list(chain_ids)
    except Exception:
        pass
    ids = [x for x in chain_ids if x != "gemini"]
    return ["gemini"] + ids


def _installed_ollama_names() -> set[str]:
    names: set[str] = set()
    try:
        import json
        import urllib.request

        base = (os.environ.get("OLLAMA_API_BASE") or "http://127.0.0.1:11434/v1").rstrip(
            "/"
        )
        root = base[:-3] if base.endswith("/v1") else base
        with urllib.request.urlopen(f"{root}/api/tags", timeout=2.5) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
        for row in data.get("models") or []:
            n = str(row.get("name") or "").strip()
            if n:
                names.add(n)
    except Exception:
        pass
    return names


def resolve_preferred_chat_model(fallback: str | None = None) -> str:
    """
    B: Kurulu sohbet modellerinden en iyisini seç.
    Env: OLLAMA_CHAT_MODEL_PREFERRED=qwen2.5:14b,llama3.1:8b
    """
    fb = (
        fallback
        or os.environ.get("RUZGAR_BRAIN_DENGE_MODEL")
        or os.environ.get("OLLAMA_CHAT_MODEL")
        or "llama3.1:8b"
    ).strip()
    if not akicilik_enabled():
        return fb
    if os.environ.get("RUZGAR_CHAT_MODEL_AUTO", "1").strip().lower() in (
        "0",
        "false",
        "no",
    ):
        return fb

    custom = (os.environ.get("OLLAMA_CHAT_MODEL_PREFERRED") or "").strip()
    preferred = (
        [x.strip() for x in custom.split(",") if x.strip()]
        if custom
        else list(_CHAT_MODEL_PREFERENCE)
    )
    installed = _installed_ollama_names()
    if not installed:
        return fb
    for cand in preferred:
        if cand in installed:
            return cand
        # kısmi: qwen2.5:14b-instruct-q4_K_M
        for name in installed:
            if name == cand or name.startswith(cand + "-") or name.startswith(cand + ":"):
                return name
    return fb


def apply_preferred_chat_model_to_env() -> str:
    """Boot / preload: denge modelini tercihe yükselt (varsa)."""
    chosen = resolve_preferred_chat_model()
    cur = (os.environ.get("OLLAMA_CHAT_MODEL") or "").strip()
    if chosen and chosen != cur:
        # Zorla ezme: kullanıcı OLLAMA_CHAT_MODEL sabitlemişse AUTO=0 ile kapatır
        if os.environ.get("RUZGAR_CHAT_MODEL_AUTO", "1").strip().lower() not in (
            "0",
            "false",
            "no",
        ):
            os.environ["OLLAMA_CHAT_MODEL"] = chosen
            os.environ["RUZGAR_BRAIN_DENGE_MODEL"] = chosen
    return chosen


_COMPACT_SYSTEM = """Sen Rüzgar'sın — bu bilgisayarda çalışan kişisel asistan.
Karşındaki Ümit abi (Ümit & Gökçenur kurdu). Hava/esinti değilsin.

Kurallar (yalnız bunlar):
1) Doğrudan cevapla başla; cümleyi yankılama, şablon selam yok.
2) Akıcı Türkçe, sohbet eder gibi; kart/ders listesi değil.
3) Bilmiyorsan söyle; sayı/tarih/alıntı uydurma.
4) Önceki turları bağla («bu / devam»).
5) İç talimat, Güven satırı, [TALİMAT] yazma.
"""


def compact_system_prompt(*, include_profil: bool = True) -> str:
    """D + E: kısa sistem + mini profil."""
    body = _COMPACT_SYSTEM.strip()
    if include_profil:
        profil = umit_mini_profile_block()
        if profil:
            body = body + "\n\n" + profil
    return body


def umit_mini_profile_block() -> str:
    """E: Sabit + kullanıcı bağlamından kısa profil."""
    if not umit_profil_enabled():
        return ""
    lines = [
        "[ÜMİT ABİ — MİNİ PROFİL]",
        "- Hitap: Ümit abi.",
        "- Ton: samimi, net, abartısız; robotik nezaket yok.",
        "- Tercih: önce cevap, sonra gerekirse kısa açıklama; istenmeden görev listesi açma.",
        "- Proje: Rüzgar'ı sahipli hafıza + kapılı eylem + doğal sohbet olarak kuruyor.",
    ]
    try:
        from ilim_assistant.kullanici_baglami import build_context_block

        ctx = (build_context_block() or "").strip()
        if ctx:
            # Bağlam bloğunu kısalt — 8B/Gemini dikkat bütçesi
            short = ctx
            if len(short) > 900:
                short = short[:900].rstrip() + "…"
            lines.append(short)
    except Exception:
        pass
    # Sabit ilişkiler (bilinen aile — yoksa boş geç)
    fixed = (os.environ.get("RUZGAR_UMIT_FIXED_NOTES") or "").strip()
    if fixed:
        lines.append("- Sabit notlar: " + fixed)
    else:
        lines.append(
            "- Bilinen: eşi Gökçenur ile Rüzgar'ı birlikte kuruyor; ilim/sohbet/programlama birlikte."
        )
    lines.append("[/ÜMİT ABİ — MİNİ PROFİL]")
    return "\n".join(lines)


def should_thin_pipeline(
    message: str,
    mode_norm: str,
    question_plan: Any | None = None,
    *,
    history: list | None = None,
) -> bool:
    """C: Selam / görüş / doğal sohbet → RAG/web minimum."""
    if not thin_pipeline_enabled():
        return False
    m = (mode_norm or "").strip().lower()
    if m not in ("genel", "uretim", "gelisim"):
        return False
    if question_plan is not None:
        prim = str(getattr(question_plan, "primary", "") or "")
        use_rag = bool(getattr(question_plan, "use_ilim_rag", True))
        if prim == "gundelik" and not use_rag:
            return True
        if prim in ("bilgi", "bilim", "dilbilgisi") and use_rag:
            return False
    try:
        from ilim_assistant.ana_motor_plan import looks_like_opinion_request

        if looks_like_opinion_request(message):
            return True
    except Exception:
        pass
    try:
        from ilim_assistant.ruzgar_dogal_sohbet_faz91 import is_natural_conversation_turn

        if is_natural_conversation_turn(
            message, m, question_plan, history=history
        ):
            return True
    except Exception:
        pass
    raw = (message or "").strip()
    if not raw:
        return False
    low = raw.casefold()
    if len(raw) < 48 and re.search(
        r"^(selam|merhaba|naber|nasılsın|nasilsin|iyi\s*misin|hey)\b", low
    ):
        return True
    return False


def iki_asama_directive(*, has_sources: bool, bilgi_turu: bool) -> str:
    """F: Önce insan cevabı, sonra gerekirse kaynaklı netleştirme."""
    if not iki_asama_enabled():
        return ""
    if not (has_sources or bilgi_turu):
        return (
            "\n\n[TALİMAT — İKİ AŞAMA]\n"
            "1) İlk 2–4 cümlede doğal sohbet cevabı yaz.\n"
            "2) Emin değilsen bunu açıkça söyle; uydurma.\n"
        )
    return (
        "\n\n[TALİMAT — İKİ AŞAMA]\n"
        "1) İlk 2–4 cümlede doğal, ChatGPT gibi sohbet cevabı ver (doğrudan başla).\n"
        "2) Ardından, yalnızca gerekirse, önündeki kaynak/raftan 1–3 cümle netleştirme ekle.\n"
        "Madde bombardımanı ve «kaynaklarımda buldum» meta dili yok.\n"
    )


def public_meta() -> dict[str, Any]:
    return {
        "version": AKICILIK_VERSION,
        "enabled": akicilik_enabled(),
        "gemini_chat_only": gemini_chat_only_enabled(),
        "compact_prompt": compact_prompt_enabled(),
        "thin_pipe": thin_pipeline_enabled(),
        "iki_asama": iki_asama_enabled(),
        "umit_profil": umit_profil_enabled(),
        "preferred_chat_model": resolve_preferred_chat_model(),
    }
