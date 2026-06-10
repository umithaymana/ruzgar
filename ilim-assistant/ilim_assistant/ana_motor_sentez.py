# Created by Ümit & Gökçenur
"""Ana Motor Faz B1 — çok kaynaklı araştırma özeti (hızlı model, tek tur)."""

from __future__ import annotations

import os
import re
from typing import Any

_SENTEZ_SYSTEM = (
    "Sen Rüzgar asistanının araştırma özetleyicisisin (Ümit & Gökçenur). "
    "Verilen yerel parçalar ve web metninden **tek Türkçe özet** üret. "
    "Çelişkileri açıkça belirt; uydurma ekleme. En fazla 6 madde veya 2 kısa paragraf."
)


def sentez_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_MOTOR_SENTEZ", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _plan_primary(question_plan: Any | None) -> str:
    if question_plan is None:
        return ""
    if hasattr(question_plan, "primary"):
        return str(getattr(question_plan, "primary", "") or "").strip().lower()
    if isinstance(question_plan, dict):
        return str(question_plan.get("primary") or "").strip().lower()
    return ""


def _distinct_source_kinds(hits: list[tuple[str, str, float]]) -> set[str]:
    kinds: set[str] = set()
    for _t, src, _s in hits or []:
        sl = (src or "").replace("\\", "/").lower()
        if "arsiv" in sl or "mektubat" in sl or "kulliyat" in sl:
            kinds.add("arsiv")
        elif "tarih" in sl or "kultur" in sl:
            kinds.add("tarih")
        elif "nebula" in sl:
            kinds.add("nebula")
        elif "tdk" in sl:
            kinds.add("tdk")
        else:
            kinds.add("indeks")
    return kinds


def should_synthesize_turn(
    *,
    question_plan: Any | None,
    hits: list[tuple[str, str, float]] | None,
    web_extra: str,
    mode_norm: str,
) -> bool:
    """Yerel + web birlikteyken tek özet turu."""
    if not sentez_enabled():
        return False
    if mode_norm not in ("genel", "uretim", "gelisim", "okuma", "hafiza"):
        return False
    primary = _plan_primary(question_plan)
    if primary not in ("bilgi", "bilim"):
        return False
    n_local = len(hits or [])
    has_web = bool((web_extra or "").strip())
    if n_local < 1 or not has_web:
        return False
    kinds = _distinct_source_kinds(hits or [])
    # En az iki kaynak türü veya yerel+web
    if len(kinds) >= 2:
        return True
    return n_local >= 2 and has_web


def _pack_sources(
    hits: list[tuple[str, str, float]],
    web_extra: str,
    *,
    max_chars: int,
) -> str:
    lines: list[str] = []
    budget = max_chars
    for i, (text, src, score) in enumerate((hits or [])[:6], 1):
        body = (text or "").strip().replace("\r\n", "\n")
        if len(body) > 900:
            body = body[:900] + "…"
        chunk = f"[Y{i}] {src} (skor~{float(score):.2f})\n{body}\n"
        if len(chunk) > budget:
            break
        lines.append(chunk)
        budget -= len(chunk)
    web = (web_extra or "").strip()
    if web and budget > 200:
        if len(web) > budget:
            web = web[:budget] + "…"
        lines.append(f"[WEB]\n{web}\n")
    return "\n".join(lines).strip()


def _call_fast_summary(system: str, user: str) -> str:
    """Hızlı yerel model; yoksa Gemini; hata → boş."""
    try:
        from ilim_assistant.llm_brain import _profile_hizli

        ep = _profile_hizli()
        if ep is not None:
            from ilim_assistant.llm_ollama import chat_completion

            out = chat_completion(
                system,
                user,
                model=ep.model,
                base_url=ep.base_url,
                api_key=ep.api_key,
            )
            if out and not out.startswith("["):
                return out.strip()
    except Exception:
        pass
    try:
        from ilim_assistant.llm_gemini import chat_completion_gemini, gemini_configured

        if gemini_configured():
            out = chat_completion_gemini(system, user)
            if out and not out.startswith("["):
                return out.strip()
    except Exception:
        pass
    return ""


def build_research_summary(
    user_message: str,
    *,
    hits: list[tuple[str, str, float]] | None,
    web_extra: str,
    question_plan: Any | None = None,
    mode_norm: str = "genel",
) -> str:
    """
    Arşiv/indeks + web → tek araştırma özeti bloğu (model bağlamına eklenir).
    Başarısızsa boş string.
    """
    if not should_synthesize_turn(
        question_plan=question_plan,
        hits=hits,
        web_extra=web_extra,
        mode_norm=mode_norm,
    ):
        return ""
    try:
        cap = max(2000, int(os.environ.get("RUZGAR_SENTEZ_SOURCE_MAX", "6000")))
    except ValueError:
        cap = 6000
    packed = _pack_sources(hits or [], web_extra, max_chars=cap)
    if not packed:
        return ""
    q = (user_message or "").strip()[:400]
    prompt = (
        f"Soru: {q}\n\n"
        "Kaynaklar:\n"
        f"{packed}\n\n"
        "Görev: Yukarıdaki kaynaklardan **araştırma özeti** yaz. "
        "Çelişen bilgi varsa «kaynaklar farklı söylüyor» de."
    )
    summary = _call_fast_summary(_SENTEZ_SYSTEM, prompt)
    if not summary or len(summary) < 24:
        return ""
    if summary.startswith("[HTTP"):
        return ""
    return (
        "\n\n[ARAŞTIRMA ÖZETİ — Ana Motor Faz B1 — Ümit & Gökçenur]\n"
        "Aşağıdaki özet yerel indeks + web taramasından **hızlı model** ile üretildi; "
        "asıl yanıtında bunu kaynaklarla birlikte kullan.\n\n"
        f"{summary.strip()}\n"
        "[/ARAŞTIRMA ÖZETİ]\n"
    )


def maybe_build_research_summary(
    user_message: str,
    *,
    hits: list[tuple[str, str, float]] | None,
    web_extra: str,
    question_plan: Any | None = None,
    mode_norm: str = "genel",
) -> str:
    """Güvenli sarmalayıcı — hata yutar."""
    try:
        return build_research_summary(
            user_message,
            hits=hits,
            web_extra=web_extra,
            question_plan=question_plan,
            mode_norm=mode_norm,
        )
    except Exception:
        return ""
