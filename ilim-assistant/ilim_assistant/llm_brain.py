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

from ilim_assistant.defaults import (
    DEFAULT_GEMINI_MODEL,
    DEFAULT_OLLAMA_CHAT_MODEL,
    DEFAULT_OLLAMA_FAST_MODEL,
)
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
    "kotası",
    "kota",
)


def free_brain_enabled() -> bool:
    """Ücretsiz öncelik: yerel Ollama (+ isteğe Groq), Gemini yedek."""
    return os.environ.get("RUZGAR_FREE_BRAIN", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _default_free_chain_ids() -> list[str]:
    """Yerel Ollama birincil; bulut isteğe bağlı."""
    try:
        from ilim_assistant.config import ollama_only_mode

        if ollama_only_mode():
            return ["denge", "hizli", "kod"]
    except Exception:
        pass
    ids: list[str] = []
    if _profile_groq() is not None:
        ids.append("groq")
    ids.extend(["denge", "hizli"])
    if gemini_configured():
        ids.append("gemini")
    return ids


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
    try:
        from ilim_assistant.gemini_quota_guard import gemini_cooldown_active

        if gemini_cooldown_active():
            return None
    except Exception:
        pass
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


def _profile_groq() -> BrainEndpoint | None:
    try:
        from ilim_assistant.config import groq_disabled

        if groq_disabled():
            return None
    except Exception:
        pass
    key = os.environ.get("GROQ_API_KEY", "").strip()
    if not key:
        return None
    base = os.environ.get("GROQ_API_BASE", "").strip() or "https://api.groq.com/openai/v1"
    model = (
        os.environ.get("GROQ_MODEL", "").strip()
        or os.environ.get("OLLAMA_CHAT_MODEL", "llama-3.1-8b-instant")
    ).strip()
    if not model:
        return None
    return BrainEndpoint(
        profile_id="groq",
        label="Groq (ücretsiz bulut)",
        model=model,
        provider="ollama",
        base_url=base.rstrip("/"),
        api_key=key,
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
    for fn in (
        _profile_hizli,
        _profile_denge,
        _profile_groq,
        _profile_gemini,
        _profile_kod,
    ):
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


def _ollama_reachable_safe() -> bool:
    try:
        from ilim_assistant.llm_ollama import ollama_reachable

        return ollama_reachable()
    except Exception:
        return False


def _gemini_only_when_configured() -> bool:
    """GLOBAL_API_KEY varken yalnızca Gemini (RUZGAR_FREE_BRAIN=1 ise kapalı)."""
    if free_brain_enabled():
        return False
    raw = (os.environ.get("RUZGAR_GEMINI_ONLY") or "auto").strip().lower()
    if raw in ("0", "false", "no"):
        return False
    if raw in ("1", "true", "yes", "on"):
        return gemini_configured()
    return gemini_configured()


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

    if _gemini_only_when_configured() and not coding_mode and mode_norm != "programlama":
        ep = profiles.get("gemini")
        if ep is not None:
            return BrainSelection(
                primary=ep,
                chain=[ep],
                reason="gemini_only (GLOBAL_API_KEY)",
            )

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

    if free_brain_enabled():
        chain_ids = _default_free_chain_ids()
    elif coding_mode or mode_norm == "programlama":
        chain_ids = ["kod", "gemini", "denge", "hizli"]
    elif mode_norm in ("hizli",):
        chain_ids = ["hizli", "denge", "gemini"]
    elif primary in ("bilgi", "bilim", "dilbilgisi") or _message_needs_deep_brain(message):
        try:
            from ilim_assistant.config import ollama_only_mode

            if ollama_only_mode():
                chain_ids = ["denge", "hizli", "kod"]
            else:
                chain_ids = (
                    ["groq", "denge", "hizli", "gemini"]
                    if _profile_groq() is not None
                    else ["denge", "hizli", "gemini"]
                )
        except Exception:
            chain_ids = ["denge", "hizli", "gemini"]
    elif primary in ("gundelik", "islem", "hava", "dosya"):
        chain_ids = (
            ["gemini", "hizli", "denge"]
            if gemini_configured()
            else ["hizli", "denge", "gemini"]
        )
    elif mode_norm in ("genel", "uretim", "gelisim") and gemini_configured():
        chain_ids = ["gemini", "denge", "hizli"]
    else:
        chain_ids = list(_PROFILE_ORDER_DEFAULT)

    custom = (os.environ.get("RUZGAR_BRAIN_FALLBACK_CHAIN") or "").strip()
    if custom:
        chain_ids = [x.strip() for x in custom.split(",") if x.strip()]

    chain: list[BrainEndpoint] = []
    seen: set[str] = set()
    ollama_ok = True
    try:
        from ilim_assistant.llm_ollama import ollama_reachable

        ollama_ok = ollama_reachable()
    except Exception:
        ollama_ok = True

    try:
        from ilim_assistant.config import local_ollama_disabled

        _no_local_ollama = local_ollama_disabled()
    except Exception:
        _no_local_ollama = False

    for pid in chain_ids:
        if pid in seen:
            continue
        ep = profiles.get(pid)
        if ep is None:
            continue
        if _no_local_ollama and ep.provider == "ollama":
            continue
        if ep.provider == "ollama" and not ollama_ok and gemini_configured():
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
    if any(p.startswith(pref) for pref in _ERROR_PREFIXES):
        return True
    try:
        from ilim_assistant.llm_gemini import is_gemini_quota_or_rate_error

        if is_gemini_quota_or_rate_error(p):
            return True
    except Exception:
        pass
    return False


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
    last_provider = ""
    for ep in sel.chain:
        last_provider = ep.provider
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
                try:
                    from ilim_assistant.llm_gemini import is_gemini_quota_or_rate_error
                    from ilim_assistant.gemini_quota_guard import mark_gemini_quota_hit

                    if is_gemini_quota_or_rate_error(last_err):
                        mark_gemini_quota_hit()
                except Exception:
                    pass
            else:
                last_err = format_llm_user_error(e)
            continue

    if last_err:
        try:
            from ilim_assistant.llm_gemini import is_gemini_quota_or_rate_error

            if is_gemini_quota_or_rate_error(last_err):
                yield (
                    "Gemini kotası dolu — yerel Ollama ile yanıt denendi ama sonuç üretilemedi. "
                    "Bir süre sonra tekrar deneyin veya `ollama serve` + `ollama pull llama3.2:3b` kontrol edin."
                )
                return
        except Exception:
            pass
        yield last_err
        return
    yield (
        "Hiçbir beyin profili yanıt üretemedi. "
        "Ollama: `ollama serve` + `ollama pull llama3.2:3b` — veya `.env` içinde GROQ_API_KEY / GLOBAL_API_KEY."
    )


def brain_health_snapshot() -> dict[str, Any]:
    profiles = all_profiles()
    sel = select_brain_chain(message="ping", mode_norm="genel")
    gemini_ping: dict[str, Any] = {}
    if gemini_configured():
        try:
            from ilim_assistant.llm_gemini import gemini_model_ping

            gemini_ping = gemini_model_ping()
        except Exception as exc:
            gemini_ping = {"ok": False, "reason": str(exc)[:200]}
    gemini_daemon: dict[str, Any] = {}
    try:
        from ilim_assistant.gemini_daemon import daemon_status

        gemini_daemon = daemon_status()
    except Exception:
        pass
    global_key_set = False
    try:
        from ilim_assistant.config import global_api_key

        global_key_set = bool(global_api_key())
    except Exception:
        pass
    groq_ep = _profile_groq()
    gemini_off = False
    try:
        from ilim_assistant.config import gemini_disabled

        gemini_off = gemini_disabled()
    except Exception:
        pass
    gemini_cd = False
    try:
        from ilim_assistant.gemini_quota_guard import gemini_cooldown_active

        gemini_cd = gemini_cooldown_active()
    except Exception:
        pass
    return {
        "super_brain_enabled": super_brain_enabled(),
        "free_brain_mode": free_brain_enabled(),
        "gemini_cooldown_active": gemini_cd,
        "forced_profile": (os.environ.get("RUZGAR_BRAIN_PROFILE") or "auto").strip(),
        "cloud_provider": (
            "ollama_local"
            if gemini_off and groq_ep is None
            else ("groq" if groq_ep is not None else "google_gemini")
        ),
        "ollama_only": gemini_off and groq_ep is None,
        "gemini_disabled": gemini_off,
        "groq_configured": groq_ep is not None,
        "groq_model": groq_ep.model if groq_ep else "",
        "gemini_configured": gemini_configured(),
        "gemini_model_default": os.environ.get("RUZGAR_GEMINI_MODEL") or DEFAULT_GEMINI_MODEL,
        "gemini_model_ping": gemini_ping,
        "global_api_key_set": global_key_set,
        "gemini_daemon": gemini_daemon,
        "gemini_only": _gemini_only_when_configured(),
        "ollama_reachable": _ollama_reachable_safe(),
        "env_loaded_from": os.environ.get("RUZGAR_ENV_LOADED_FROM", ""),
        "profiles": {k: v.to_public_dict() for k, v in profiles.items()},
        "default_chain": [e.profile_id for e in sel.chain],
    }


def chat_completion_groq(system: str, user: str) -> str:
    """Groq bulut tamamlama (OpenAI uyumlu API)."""
    ep = _profile_groq()
    if ep is None:
        return ""
    try:
        from ilim_assistant.llm_ollama import chat_completion

        return (
            chat_completion(
                system,
                user,
                model=ep.model,
                base_url=ep.base_url,
                api_key=ep.api_key,
            )
            or ""
        ).strip()
    except Exception:
        return ""
