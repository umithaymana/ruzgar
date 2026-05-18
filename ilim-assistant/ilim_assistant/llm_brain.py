# Created by Ümit & Gökçenur
"""
Rüzgar Süper Beyin — çoklu model profili ve yedekli LLM akışı (Faz 8).

Profiller:
  - hizli / denge / kod → yerel Ollama (OpenAI uyumlu /v1)
  - gemini → Google Gemini API (ücretsiz geliştirici kotası)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Iterator, Literal

from ilim_assistant.defaults import DEFAULT_GEMINI_MODEL, DEFAULT_OLLAMA_CHAT_MODEL
from ilim_assistant.llm_gemini import (
    chat_completion_stream_gemini,
    format_gemini_user_error,
    gemini_api_key,
    gemini_configured,
)
from ilim_assistant.llm_ollama import chat_completion_stream, format_llm_user_error

MIMAR_IMZA = "Ümit & Gökçenur"

ProviderKind = Literal["ollama", "gemini"]

_PROFILE_ORDER_DEFAULT = ("gemini", "denge", "hizli", "kod")

_ERROR_PREFIXES = (
    "[HTTP",
    "Ollama",
    "Gemini",
    "LLM hatası",
    "LLM isteği",
    "Model bulunamadı",
    "API anahtarı",
)


@dataclass(frozen=True)
class BrainEndpoint:
    profile_id: str
    label: str
    model: str
    provider: ProviderKind
    base_url: str = ""
    api_key: str = ""
    max_tokens: int | None = None
    temperature: float | None = None

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "label": self.label,
            "model": self.model,
            "provider": self.provider,
            "endpoint": self._endpoint_hint(),
            "configured": bool(self.model.strip()),
        }

    def _endpoint_hint(self) -> str:
        if self.provider == "gemini":
            return "generativelanguage.googleapis.com/v1beta"
        b = (self.base_url or "").rstrip("/")
        if len(b) > 48:
            return b[:24] + "…" + b[-12:]
        return b or "ollama-local"


@dataclass
class BrainSelection:
    primary: BrainEndpoint
    chain: list[BrainEndpoint] = field(default_factory=list)
    reason: str = ""

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "primary": self.primary.to_public_dict(),
            "chain": [e.to_public_dict() for e in self.chain],
            "reason": self.reason,
        }


def super_brain_enabled() -> bool:
    return os.environ.get("RUZGAR_SUPER_BRAIN", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _ollama_base() -> str:
    return (os.environ.get("OLLAMA_API_BASE") or "http://127.0.0.1:11434/v1").rstrip("/")


def _ollama_key() -> str:
    return os.environ.get("OLLAMA_API_KEY", "ollama") or "ollama"


def _profile_hizli() -> BrainEndpoint | None:
    model = (
        os.environ.get("RUZGAR_BRAIN_HIZLI_MODEL")
        or os.environ.get("OLLAMA_CHAT_MODEL_FAST")
        or "llama3.2:3b"
    ).strip()
    if not model:
        return None
    return BrainEndpoint(
        profile_id="hizli",
        label="Hızlı (yerel Ollama)",
        model=model,
        provider="ollama",
        base_url=_ollama_base(),
        api_key=_ollama_key(),
    )


def _profile_denge() -> BrainEndpoint | None:
    model = (
        os.environ.get("RUZGAR_BRAIN_DENGE_MODEL")
        or os.environ.get("OLLAMA_CHAT_MODEL")
        or DEFAULT_OLLAMA_CHAT_MODEL
    ).strip()
    if not model:
        return None
    return BrainEndpoint(
        profile_id="denge",
        label="Denge (yerel Ollama)",
        model=model,
        provider="ollama",
        base_url=_ollama_base(),
        api_key=_ollama_key(),
    )


def _profile_gemini() -> BrainEndpoint | None:
    if not gemini_configured():
        return None
    model = (
        os.environ.get("RUZGAR_GEMINI_MODEL")
        or os.environ.get("GEMINI_MODEL")
        or DEFAULT_GEMINI_MODEL
    ).strip()
    if not model:
        return None
    try:
        mt = int(os.environ.get("RUZGAR_GEMINI_MAX_OUTPUT_TOKENS", "4096"))
    except ValueError:
        mt = 4096
    try:
        temp = float(os.environ.get("RUZGAR_GEMINI_TEMPERATURE", "0.35"))
    except ValueError:
        temp = 0.35
    return BrainEndpoint(
        profile_id="gemini",
        label="Gemini (Google AI Studio)",
        model=model,
        provider="gemini",
        api_key=gemini_api_key(),
        max_tokens=mt,
        temperature=temp,
    )


def _profile_kod() -> BrainEndpoint | None:
    use_gemini = os.environ.get("RUZGAR_BRAIN_KOD_USE_GEMINI", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )
    if use_gemini:
        g = _profile_gemini()
        if g is not None:
            kod_model = (os.environ.get("RUZGAR_BRAIN_KOD_MODEL") or g.model).strip()
            return BrainEndpoint(
                profile_id="kod",
                label="Kod (Gemini)",
                model=kod_model or g.model,
                provider="gemini",
                api_key=g.api_key,
                max_tokens=g.max_tokens,
                temperature=float(os.environ.get("RUZGAR_BRAIN_KOD_TEMPERATURE", "0.2")),
            )
    model = (
        os.environ.get("RUZGAR_BRAIN_KOD_MODEL")
        or os.environ.get("OLLAMA_CHAT_MODEL_CODING")
        or os.environ.get("OLLAMA_CHAT_MODEL")
        or DEFAULT_OLLAMA_CHAT_MODEL
    ).strip()
    if not model:
        return None
    return BrainEndpoint(
        profile_id="kod",
        label="Kod (yerel Ollama)",
        model=model,
        provider="ollama",
        base_url=_ollama_base(),
        api_key=_ollama_key(),
    )


def all_profiles() -> dict[str, BrainEndpoint]:
    out: dict[str, BrainEndpoint] = {}
    for fn in (_profile_hizli, _profile_denge, _profile_gemini, _profile_kod):
        ep = fn()
        if ep is not None:
            out[ep.profile_id] = ep
    return out


def _plan_primary(question_plan: Any | None) -> str:
    if question_plan is None:
        return ""
    if hasattr(question_plan, "primary"):
        return str(getattr(question_plan, "primary", "") or "").strip().lower()
    if isinstance(question_plan, dict):
        return str(question_plan.get("primary") or "").strip().lower()
    return ""


def _message_needs_deep_brain(message: str) -> bool:
    m = (message or "").strip().lower()
    if len(m) < 12:
        return False
    cues = (
        "nedir",
        "nasıl",
        "niçin",
        "niye",
        "açıkla",
        "acikla",
        "karşılaştır",
        "karsilastir",
        "tarih",
        "hadis",
        "ayet",
        "tefsir",
        "kaynak",
        "kanıt",
        "kanit",
        "detaylı",
        "detayli",
        "analiz",
        "özetle",
        "ozetle",
        "araştır",
        "arastir",
        "güncel",
        "guncel",
        "bugün",
        "bugun",
    )
    return any(c in m for c in cues)


def select_brain_chain(
    *,
    message: str,
    mode_norm: str,
    coding_mode: bool = False,
    question_plan: Any | None = None,
    legacy_model: str | None = None,
) -> BrainSelection:
    profiles = all_profiles()
    forced = (os.environ.get("RUZGAR_BRAIN_PROFILE") or "auto").strip().lower()

    if forced not in ("", "auto"):
        if forced in profiles:
            ep = profiles[forced]
            return BrainSelection(primary=ep, chain=[ep], reason=f"zorunlu profil={forced}")
        if legacy_model:
            ep = BrainEndpoint(
                profile_id="legacy",
                label="Legacy Ollama",
                model=legacy_model,
                provider="ollama",
                base_url=_ollama_base(),
                api_key=_ollama_key(),
            )
            return BrainSelection(primary=ep, chain=[ep], reason="bilinmeyen profil, legacy")

    chain_ids: list[str] = []
    primary = _plan_primary(question_plan)

    if coding_mode or mode_norm == "programlama":
        chain_ids = ["kod", "gemini", "denge", "hizli"]
    elif mode_norm in ("hizli",):
        chain_ids = ["hizli", "denge", "gemini"]
    elif primary in ("bilgi", "bilim", "dilbilgisi") or _message_needs_deep_brain(message):
        chain_ids = ["gemini", "denge", "hizli"]
    elif primary in ("gundelik", "islem", "hava", "dosya"):
        chain_ids = ["hizli", "denge", "gemini"]
    else:
        chain_ids = list(_PROFILE_ORDER_DEFAULT)

    custom = (os.environ.get("RUZGAR_BRAIN_FALLBACK_CHAIN") or "").strip()
    if custom:
        chain_ids = [x.strip() for x in custom.split(",") if x.strip()]

    chain: list[BrainEndpoint] = []
    seen: set[str] = set()
    for pid in chain_ids:
        if pid in seen:
            continue
        ep = profiles.get(pid)
        if ep is None:
            continue
        seen.add(pid)
        chain.append(ep)

    if not chain and legacy_model:
        chain = [
            BrainEndpoint(
                profile_id="legacy",
                label="Legacy",
                model=legacy_model,
                provider="ollama",
                base_url=_ollama_base(),
                api_key=_ollama_key(),
            )
        ]

    if not chain:
        ep = _profile_gemini() or _profile_denge() or _profile_hizli()
        if ep is not None:
            chain = [ep]

    if not chain:
        chain = [
            BrainEndpoint(
                profile_id="fallback",
                label="Fallback",
                model=DEFAULT_OLLAMA_CHAT_MODEL,
                provider="ollama",
                base_url=_ollama_base(),
                api_key=_ollama_key(),
            )
        ]

    reason = f"mod={mode_norm}; plan={primary or '—'}; zincir={[e.profile_id for e in chain]}"
    return BrainSelection(primary=chain[0], chain=chain, reason=reason)


def _looks_like_error_chunk(piece: str) -> bool:
    p = (piece or "").strip()
    if not p:
        return False
    return any(p.startswith(pref) for pref in _ERROR_PREFIXES)


def _stream_endpoint(
    ep: BrainEndpoint,
    system: str,
    user: str,
    prior_messages: list | None,
) -> Iterator[str]:
    if ep.provider == "gemini":
        yield from chat_completion_stream_gemini(
            system,
            user,
            model=ep.model,
            api_key=ep.api_key,
            prior_messages=prior_messages,
            max_output_tokens=ep.max_tokens,
            temperature=ep.temperature,
        )
        return
    yield from chat_completion_stream(
        system,
        user,
        model=ep.model,
        base_url=ep.base_url,
        api_key=ep.api_key,
        prior_messages=prior_messages,
    )


def super_brain_system_directive(*, profile_id: str) -> str:
    if not super_brain_enabled():
        return ""
    depth = (
        "Bu turda **Süper Beyin** profili etkindir. "
        "Kullanıcının sorusunu eksiksiz anla; mümkün olduğunca **doğrudan, net ve yapılandırılmış** yanıt ver. "
        "Bilmediğin konuda uydurma; emin değilsen dürüstçe söyle. "
        "Yerel bağlam (RAG/arşiv/web) varsa onu önceliklendir.\n"
    )
    if profile_id == "gemini":
        depth += (
            "Gemini profili: derin ve güncel bilgi; madde madde yapı + kısa sonuç cümlesi.\n"
        )
    elif profile_id == "kod":
        depth += "Kod profili: çalışır örnek, dosya yolu ve test adımı ver.\n"
    return f"\n\n[TALİMAT — RÜZGAR Süper Beyin — {MIMAR_IMZA}]\n{depth}"


def enrich_system_for_brain(
    system: str,
    *,
    mode_norm: str,
    message: str,
    question_plan: Any | None = None,
    coding_mode: bool = False,
    selection: BrainSelection | None = None,
) -> str:
    sel = selection or select_brain_chain(
        message=message,
        mode_norm=mode_norm,
        coding_mode=coding_mode,
        question_plan=question_plan,
    )
    extra = super_brain_system_directive(profile_id=sel.primary.profile_id)
    if not extra:
        return system
    return (system or "").rstrip() + extra


def resolve_brain_model(
    coding_mode: bool,
    *,
    message: str = "",
    mode_norm: str = "genel",
    question_plan: Any | None = None,
) -> str:
    sel = select_brain_chain(
        message=message,
        mode_norm=mode_norm,
        coding_mode=coding_mode,
        question_plan=question_plan,
    )
    return sel.primary.model


def stream_chat_with_brain(
    system: str,
    user: str,
    *,
    model: str | None = None,
    prior_messages: list | None = None,
    mode_norm: str = "genel",
    coding_mode: bool = False,
    message: str = "",
    question_plan: Any | None = None,
) -> Iterator[str]:
    system = enrich_system_for_brain(
        system,
        mode_norm=mode_norm,
        message=message or user,
        question_plan=question_plan,
        coding_mode=coding_mode,
    )
    sel = select_brain_chain(
        message=message or user,
        mode_norm=mode_norm,
        coding_mode=coding_mode,
        question_plan=question_plan,
        legacy_model=model,
    )
    last_err = ""
    for ep in sel.chain:
        try:
            got_content = False
            for piece in _stream_endpoint(ep, system, user, prior_messages):
                if not got_content and _looks_like_error_chunk(piece):
                    last_err = piece.strip()
                    break
                got_content = True
                yield piece
            if got_content:
                return
        except Exception as e:
            if ep.provider == "gemini":
                last_err = format_gemini_user_error(e)
            else:
                last_err = format_llm_user_error(e)
            continue

    yield last_err or (
        "Hiçbir beyin profili yanıt üretemedi. Yerel için Ollama'yı başlatın; "
        "bulut için GOOGLE_GEMINI_API_KEY tanımlayın (https://aistudio.google.com/apikey)."
    )


def brain_health_snapshot() -> dict[str, Any]:
    profiles = all_profiles()
    sel = select_brain_chain(message="ping", mode_norm="genel")
    return {
        "super_brain_enabled": super_brain_enabled(),
        "forced_profile": (os.environ.get("RUZGAR_BRAIN_PROFILE") or "auto").strip(),
        "cloud_provider": "google_gemini",
        "gemini_configured": gemini_configured(),
        "gemini_model_default": os.environ.get("RUZGAR_GEMINI_MODEL") or DEFAULT_GEMINI_MODEL,
        "profiles": {k: v.to_public_dict() for k, v in profiles.items()},
        "default_chain": [e.profile_id for e in sel.chain],
    }
