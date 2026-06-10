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


def _is_local_ollama_endpoint(ep: BrainEndpoint) -> bool:
    """Groq OpenAI-uyumlu uç nokta — yerel Ollama sayılmaz."""
    if ep.profile_id == "groq":
        return False
    if ep.provider != "ollama":
        return False
    base = (ep.base_url or "").lower()
    if "groq.com" in base or "openai.azure" in base:
        return False
    return True


def _is_cloud_rate_limit_error(text: str) -> bool:
    low = (text or "").lower()
    if any(
        k in low
        for k in (
            "rate limit",
            "rate_limit",
            "quota",
            "kota",
            "429",
            "too many requests",
            "resource exhausted",
        )
    ):
        return True
    try:
        from ilim_assistant.llm_gemini import is_gemini_quota_or_rate_error

        if is_gemini_quota_or_rate_error(text):
            return True
    except Exception:
        pass
    return False


def _programlama_chain_ids() -> list[str]:
    """Programlama / kod: Faz 26 groq öncelik; kota soğukken gemini atlanır."""
    try:
        from ilim_assistant.motorlar.programlama_faz26 import programming_brain_chain_ids

        f26 = programming_brain_chain_ids()
        if f26:
            ids = list(f26)
        else:
            ids = []
    except Exception:
        ids = []
    if not ids:
        custom = (os.environ.get("RUZGAR_BRAIN_FALLBACK_CHAIN") or "").strip()
        if custom:
            ids = [x.strip() for x in custom.split(",") if x.strip()]
        else:
            ids = ["gemini", "groq", "kod", "denge"]
    try:
        from ilim_assistant.gemini_quota_guard import gemini_cooldown_active

        if gemini_cooldown_active():
            rest = [x for x in ids if x != "gemini"]
            ids = ["groq", "kod", "denge"] + [x for x in rest if x not in ("groq", "kod", "denge")]
    except Exception:
        pass
    try:
        from ilim_assistant.llm_ollama import ollama_reachable

        if ollama_reachable():
            for fallback in ("kod", "denge"):
                if fallback not in ids:
                    ids.append(fallback)
    except Exception:
        pass
    return ids


def _filter_chain_ids_for_quota(chain_ids: list[str]) -> list[str]:
    """Kota soğukken Gemini'yi zincirden çıkar; Groq öne."""
    try:
        from ilim_assistant.gemini_quota_guard import gemini_cooldown_active

        if not gemini_cooldown_active():
            return list(chain_ids)
    except Exception:
        return list(chain_ids)
    out = [x for x in chain_ids if x != "gemini"]
    if "groq" in out:
        out = ["groq"] + [x for x in out if x != "groq"]
    elif _profile_groq() is not None:
        out = ["groq"] + out
    for fb in ("denge", "hizli", "kod"):
        if fb not in out:
            out.append(fb)
    return out


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
    return _filter_chain_ids_for_quota(ids)


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


def _profile_denge70() -> BrainEndpoint | None:
    """Faz D / 8 — yerel 70B denge profili (llama3.1:70b vb.)."""
    model = (
        os.environ.get("RUZGAR_BRAIN_DENGE70_MODEL")
        or os.environ.get("OLLAMA_CHAT_MODEL_70B")
        or "llama3.1:70b"
    ).strip()
    if not model:
        return None
    return BrainEndpoint(
        profile_id="denge70",
        label="Denge 70B (yerel Ollama)",
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


def _normalize_forced_profile(forced: str) -> str:
    alias = {
        "denge-70b": "denge70",
        "denge_70b": "denge70",
        "70b": "denge70",
    }
    return alias.get(forced, forced)


def all_profiles() -> dict[str, BrainEndpoint]:
    out: dict[str, BrainEndpoint] = {}
    for fn in (
        _profile_hizli,
        _profile_denge,
        _profile_denge70,
        _profile_groq,
        _profile_gemini,
        _profile_kod,
    ):
        ep = fn()
        if ep is not None:
            out[ep.profile_id] = ep
    return out


def denge70_readiness() -> dict[str, Any]:
    """Faz E2 — 70B model Ollama'da hazır mı?"""
    ep = _profile_denge70()
    if ep is None:
        return {
            "ready": False,
            "model": "",
            "hint": "denge70 profili tanımlı değil",
        }
    model = ep.model
    try:
        from ilim_assistant.llm_ollama import ollama_model_available, ollama_reachable

        if not ollama_reachable():
            return {
                "ready": False,
                "model": model,
                "hint": "Ollama çalışmıyor — ollama serve",
            }
        if not ollama_model_available(model):
            return {
                "ready": False,
                "model": model,
                "hint": f"Model indirilmedi — ollama pull {model}",
            }
        return {"ready": True, "model": model, "hint": None}
    except Exception as exc:
        return {
            "ready": False,
            "model": model,
            "hint": str(exc)[:120],
        }


def denge70_ready_for_chain() -> bool:
    if os.environ.get("RUZGAR_DENGE70_REQUIRE_PULLED", "1").strip().lower() in (
        "0",
        "false",
        "no",
    ):
        return True
    return bool(denge70_readiness().get("ready"))


def _inject_denge70_chain(
    chain_ids: list[str],
    *,
    question_plan: Any | None,
    message: str,
    mode_norm: str,
    profiles: dict[str, BrainEndpoint],
) -> list[str]:
    """Bilim derin turda 70B profilini zincire ekle."""
    out = list(chain_ids)
    try:
        from ilim_assistant.ana_motor_bilim_derin import (
            bilim_derin_use_70b,
            is_bilim_derin_turn,
        )

        if not (
            bilim_derin_use_70b()
            and is_bilim_derin_turn(question_plan, message, mode_norm)
            and profiles.get("denge70") is not None
            and denge70_ready_for_chain()
            and "denge70" not in out
        ):
            return out
        if "gemini" in out:
            out.insert(out.index("gemini") + 1, "denge70")
        elif "groq" in out:
            out.insert(out.index("groq") + 1, "denge70")
        else:
            out.insert(0, "denge70")
    except Exception:
        pass
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
    try:
        from ilim_assistant.gemini_quota_guard import gemini_cooldown_active

        if gemini_cooldown_active():
            return False
    except Exception:
        pass
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
    forced = _normalize_forced_profile(
        (os.environ.get("RUZGAR_BRAIN_PROFILE") or "auto").strip().lower()
    )

    try:
        from ilim_assistant.ruzgar_umed_cevap_emri import (
            brain_chain_ids_for_emri,
            umed_emri_applies,
        )

        if umed_emri_applies(mode_norm=mode_norm, coding_mode=coding_mode):
            chain_ids = _inject_denge70_chain(
                brain_chain_ids_for_emri(),
                question_plan=question_plan,
                message=message,
                mode_norm=mode_norm,
                profiles=profiles,
            )
            chain_ids = _filter_chain_ids_for_quota(chain_ids)
            chain: list[BrainEndpoint] = []
            seen_u: set[str] = set()
            for pid in chain_ids:
                if pid in seen_u:
                    continue
                ep = profiles.get(pid)
                if ep is not None:
                    seen_u.add(pid)
                    chain.append(ep)
            if chain:
                return BrainSelection(
                    primary=chain[0],
                    chain=chain,
                    reason=f"umed_emri; zincir={[e.profile_id for e in chain]}",
                )
    except Exception:
        pass

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

    if coding_mode or mode_norm == "programlama":
        chain_ids = _programlama_chain_ids()
    elif free_brain_enabled():
        chain_ids = _default_free_chain_ids()
    elif mode_norm in ("hizli",):
        chain_ids = ["hizli", "denge", "gemini"]
    elif primary in ("bilgi", "bilim", "dilbilgisi") or _message_needs_deep_brain(message):
        custom_bilgi = (os.environ.get("RUZGAR_BILGI_BRAIN_CHAIN") or "").strip()
        if custom_bilgi:
            chain_ids = [x.strip() for x in custom_bilgi.split(",") if x.strip()]
        else:
            try:
                from ilim_assistant.config import ollama_only_mode

                if ollama_only_mode():
                    chain_ids = ["denge", "hizli", "kod"]
                elif (
                    os.environ.get("RUZGAR_SUPER_BRAIN", "1").strip().lower()
                    not in ("0", "false", "no")
                    and gemini_configured()
                    and primary in ("bilgi", "bilim")
                ):
                    chain_ids = (
                        ["gemini", "groq", "denge", "hizli"]
                        if _profile_groq() is not None
                        else ["gemini", "denge", "hizli"]
                    )
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

    chain_ids = _inject_denge70_chain(
        chain_ids,
        question_plan=question_plan,
        message=message,
        mode_norm=mode_norm,
        profiles=profiles,
    )
    chain_ids = _filter_chain_ids_for_quota(chain_ids)

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
        if not _is_local_ollama_endpoint(ep):
            seen.add(pid)
            chain.append(ep)
            continue
        if _no_local_ollama:
            continue
        if not ollama_ok:
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


def build_casual_fast_chain_ids() -> list[str]:
    """Kısa sohbet — Groq önce; Ollama yavaşsa hızlı düş."""
    custom = (os.environ.get("RUZGAR_CASUAL_BRAIN_CHAIN") or "").strip()
    if custom:
        ids = [x.strip() for x in custom.split(",") if x.strip()]
    else:
        ids = ["groq", "hizli", "denge", "gemini"]
    return _filter_chain_ids_for_quota(ids)


def _chain_from_ids(chain_ids: list[str]) -> list[BrainEndpoint]:
    profiles = all_profiles()
    chain: list[BrainEndpoint] = []
    seen: set[str] = set()
    for pid in chain_ids:
        if pid in seen:
            continue
        ep = profiles.get(pid)
        if ep is not None:
            seen.add(pid)
            chain.append(ep)
    return chain


def _stream_endpoint(
    ep: BrainEndpoint,
    system: str,
    user: str,
    prior_messages: list | None,
) -> Iterator[str]:
    if ep.provider == "gemini":
        try:
            from ilim_assistant.gemini_quota_guard import gemini_cooldown_active

            if gemini_cooldown_active():
                return
        except Exception:
            pass
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


def stream_chat_casual_fast(
    system: str,
    user: str,
    *,
    prior_messages: list | None = None,
    mode_norm: str = "genel",
    message: str = "",
) -> Iterator[str]:
    """
    Gündelik sohbet — Ümit emri zincirini atla; Groq önce, Ollama kısa timeout.
    «nasılsın» gibi turlarda dakikalarca Ollama ilk token beklemesini keser.
    """
    chain = _chain_from_ids(build_casual_fast_chain_ids())
    if not chain:
        chain = _chain_from_ids(_filter_chain_ids_for_quota(["hizli", "denge", "gemini"]))
    try:
        ollama_cap = os.environ.get("RUZGAR_CASUAL_OLLAMA_READ_TIMEOUT_SEC", "22")
    except Exception:
        ollama_cap = "22"
    old_read = os.environ.get("RUZGAR_OLLAMA_READ_TIMEOUT_SEC")
    os.environ["RUZGAR_OLLAMA_READ_TIMEOUT_SEC"] = str(ollama_cap)
    try:
        yield from _stream_brain_chain_loop(
            chain,
            system,
            user,
            prior_messages=prior_messages,
            mode_norm=mode_norm,
            coding_mode=False,
            message=message,
            use_turn_budget=False,
        )
    finally:
        if old_read is None:
            os.environ.pop("RUZGAR_OLLAMA_READ_TIMEOUT_SEC", None)
        else:
            os.environ["RUZGAR_OLLAMA_READ_TIMEOUT_SEC"] = old_read


def _stream_brain_chain_loop(
    chain: list[BrainEndpoint],
    system: str,
    user: str,
    *,
    prior_messages: list | None,
    mode_norm: str,
    coding_mode: bool,
    message: str,
    use_turn_budget: bool,
) -> Iterator[str]:
    last_err = ""
    last_provider = ""
    any_content = False
    attempted: list[str] = []
    _umed = False
    is_real_user_question = lambda _m: True  # type: ignore[assignment, misc]
    remaining_sec = lambda: 9999.0  # type: ignore[assignment, misc]
    umed_miss_reply = lambda: ""  # type: ignore[assignment, misc]
    if use_turn_budget:
        try:
            from ilim_assistant.ruzgar_umed_cevap_emri import (
                begin_turn_budget,
                remaining_sec as _rem,
                umed_emri_applies,
                umed_miss_reply as _miss,
            )
            from ilim_assistant.ruzgar_egitim import is_real_user_question as _irq

            _umed = umed_emri_applies(mode_norm=mode_norm, coding_mode=coding_mode)
            if _umed:
                begin_turn_budget(message or user, mode_norm=mode_norm)
            is_real_user_question = _irq
            remaining_sec = _rem
            umed_miss_reply = _miss
        except Exception:
            pass

    for ep in chain:
        if _umed and remaining_sec() < 0.8:
            break
        last_provider = ep.profile_id
        attempted.append(ep.profile_id)
        try:
            got_content = False
            for piece in _stream_endpoint(ep, system, user, prior_messages):
                if _umed and remaining_sec() <= 0:
                    if got_content and piece:
                        yield piece
                    break
                if not got_content and _looks_like_error_chunk(piece):
                    last_err = piece.strip()
                    if _is_cloud_rate_limit_error(last_err) and ep.profile_id == "gemini":
                        try:
                            from ilim_assistant.gemini_quota_guard import mark_gemini_quota_hit

                            mark_gemini_quota_hit()
                        except Exception:
                            pass
                    break
                got_content = True
                any_content = True
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

    if _umed and not any_content and is_real_user_question(message or user):
        yield umed_miss_reply()
        return
    if not any_content and (coding_mode or mode_norm == "programlama"):
        chain_hint = ",".join(attempted) or "?"
        yield (
            "Ümit abi, Programlama motoru şu an yanıt üretemedi "
            f"(denenen: {chain_hint}).\n"
        )
        return
    if last_err and not any_content:
        yield last_err
        return
    if not any_content:
        yield (
            "Ümit abi, şu an yanıt üretemedim — `ollama serve` veya GROQ_API_KEY kontrol et; "
            "biraz sonra tekrar dene."
        )


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
    any_content = False
    attempted: list[str] = []
    _umed = False
    is_real_user_question = lambda _m: True  # type: ignore[assignment, misc]
    remaining_sec = lambda: 9999.0  # type: ignore[assignment, misc]
    umed_miss_reply = lambda: ""  # type: ignore[assignment, misc]
    try:
        from ilim_assistant.ruzgar_umed_cevap_emri import (
            begin_turn_budget,
            remaining_sec as _rem,
            umed_emri_applies,
            umed_miss_reply as _miss,
        )
        from ilim_assistant.ruzgar_egitim import is_real_user_question as _irq

        _umed = umed_emri_applies(mode_norm=mode_norm, coding_mode=coding_mode)
        if _umed:
            begin_turn_budget(message or user, mode_norm=mode_norm)
        is_real_user_question = _irq
        remaining_sec = _rem
        umed_miss_reply = _miss
    except Exception:
        pass

    for ep in sel.chain:
        if _umed and remaining_sec() < 0.8:
            break
        last_provider = ep.profile_id
        attempted.append(ep.profile_id)
        try:
            got_content = False
            for piece in _stream_endpoint(ep, system, user, prior_messages):
                if _umed and remaining_sec() <= 0:
                    if got_content and piece:
                        yield piece
                    break
                if not got_content and _looks_like_error_chunk(piece):
                    last_err = piece.strip()
                    if _is_cloud_rate_limit_error(last_err):
                        if ep.profile_id == "gemini":
                            try:
                                from ilim_assistant.gemini_quota_guard import (
                                    mark_gemini_quota_hit,
                                )

                                mark_gemini_quota_hit()
                            except Exception:
                                pass
                    break
                got_content = True
                any_content = True
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

    if _umed and not any_content and is_real_user_question(message or user):
        yield umed_miss_reply()
        return

    if not any_content and (coding_mode or mode_norm == "programlama"):
        chain_hint = ",".join(attempted) or ",".join(
            e.profile_id for e in sel.chain[:6]
        ) or "?"
        order_hint = " -> ".join(e.profile_id for e in sel.chain[:5]) or chain_hint
        err_hint = f" Son hata ({last_provider}): {last_err[:240]}" if last_err else ""
        yield (
            "Ümit abi, Programlama motoru şu an yanıt üretemedi "
            f"(denenen: {chain_hint}). "
            f"Sıra: {order_hint}. "
            "Kontrol: `RUZGAR_BRAIN.env`, `ollama serve`, `Ruzgar.ps1 -ForceRestart`.\n"
            f"{err_hint}"
        )
        return

    if last_err:
        try:
            from ilim_assistant.llm_gemini import is_gemini_quota_or_rate_error

            if is_gemini_quota_or_rate_error(last_err):
                try:
                    from ilim_assistant.gemini_quota_guard import (
                        gemini_cooldown_active,
                        mark_gemini_quota_hit,
                    )

                    mark_gemini_quota_hit()
                    if not gemini_cooldown_active():
                        pass
                except Exception:
                    pass
                if _umed:
                    yield umed_miss_reply()
                    return
                yield (
                    "Gemini kotası dolu — Ollama/Groq denendi ama yanıt üretilemedi. "
                    "Bir süre bekleyin, `GROQ_API_KEY` ekleyin veya `ollama serve` + daha güçlü model deneyin."
                )
                return
        except Exception:
            pass
        if _umed and is_real_user_question(message or user):
            yield umed_miss_reply()
            return
        yield last_err
        return
    if _umed and is_real_user_question(message or user):
        yield umed_miss_reply()
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
