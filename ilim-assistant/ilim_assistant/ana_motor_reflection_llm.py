# Created by Ümit & Gökçenur
"""Ana Motor Faz Y1 — opsiyonel LLM reflection (factual sorularda ikinci tur)."""

from __future__ import annotations

import os
import re
import time
from typing import Any

FAZ_Y_LLM_VERSION = "ana-motor-reflection-llm-y1-2026-06-10"

_GUVEN_RE = re.compile(
    r"\*\*Güven:\s*(yüksek|orta|düşük|dusuk)\*\*[^.\n]*",
    re.I,
)


def llm_reflection_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_LLM_REFLECTION", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _budget_sec() -> float:
    try:
        return max(3.0, min(float(os.environ.get("RUZGAR_ANA_LLM_REFLECTION_BUDGET_SEC", "8")), 20.0))
    except ValueError:
        return 8.0


def _max_tokens() -> int:
    try:
        return max(80, min(int(os.environ.get("RUZGAR_ANA_LLM_REFLECTION_MAX_TOKENS", "280")), 600))
    except ValueError:
        return 280


def should_run_llm_reflection(
    reply: str,
    user_message: str,
    *,
    hits: list | None = None,
    question_plan: Any | None = None,
    web_was_used: bool = False,
    mismatch: bool = False,
) -> bool:
    if not llm_reflection_enabled():
        return False
    from ilim_assistant.ana_motor_reflection import _has_guven_line, _looks_factual_question, _plan_primary

    if not _looks_factual_question(user_message):
        return False
    primary = _plan_primary(question_plan)
    if primary not in ("bilgi", "bilim", "dilbilgisi"):
        return False
    body = (reply or "").strip()
    if not body or len(body) < 20:
        return False
    n_src = len(hits or [])
    if mismatch:
        return True
    if not _has_guven_line(body):
        return True
    from ilim_assistant.ana_motor_kaynak_rozet import parse_guven_level

    if parse_guven_level(body) == "düşük" and n_src >= 1:
        return True
    if n_src == 0 and not web_was_used:
        return True
    return False


def _merge_reflection_note(reply: str, llm_out: str) -> str:
    body = (reply or "").strip()
    note = (llm_out or "").strip()
    if not note:
        return body
    guven_match = _GUVEN_RE.search(note)
    if guven_match:
        new_guven = guven_match.group(0)
        if _GUVEN_RE.search(body):
            body = _GUVEN_RE.sub(new_guven, body, count=1)
        else:
            body = body.rstrip() + f"\n\n{new_guven}"
        note = _GUVEN_RE.sub("", note).strip()
    if note and note.lower() not in body.lower():
        body = body.rstrip() + f"\n\n*Not (Faz Y): {note[:400]}*"
    return body


def run_llm_reflection_pass(
    reply: str,
    user_message: str,
    *,
    hits: list | None = None,
    question_plan: Any | None = None,
    web_was_used: bool = False,
    mismatch_note: str = "",
) -> dict[str, Any]:
    if not llm_reflection_enabled():
        return {"ok": True, "applied": False, "reason": "disabled"}

    from ilim_assistant.ana_motor_reflection import detect_source_answer_mismatch

    mis, mis_note = detect_source_answer_mismatch(
        reply,
        hits=hits,
        web_was_used=web_was_used,
    )
    note = mismatch_note or mis_note or ""
    if not should_run_llm_reflection(
        reply,
        user_message,
        hits=hits,
        question_plan=question_plan,
        web_was_used=web_was_used,
        mismatch=mis,
    ):
        return {"ok": True, "applied": False, "reason": "not_needed"}

    n_src = len(hits or [])
    src_hint = ""
    if hits:
        src_hint = "\n".join(
            f"- [{i}] {str(h[1] if len(h) > 1 else '')[:80]}"
            for i, h in enumerate(hits[:4], start=1)
            if isinstance(h, (list, tuple))
        )

    system = (
        "Sen Rüzgar Ana Motor kalite denetçisisin (Ümit & Gökçenur). "
        "Görev: YALNIZCA **Güven:** satırını ve gerekirse tek cümlelik kaynak uyarısını düzelt. "
        "Tam cevabı yeniden yazma. Türkçe, kısa.\n"
        "Format örneği:\n**Güven: orta** — kaynak sayısı sınırlı.\n"
        "veya tek satır: Kaynaklarda tarih çelişkisi olabilir; emin değilim."
    )
    user = (
        f"Soru: {(user_message or '')[:500]}\n\n"
        f"Cevap özeti (ilk 1200 kr):\n{(reply or '')[:1200]}\n\n"
        f"Yerel kaynak sayısı: {n_src}\n"
        f"Web kullanıldı: {'evet' if web_was_used else 'hayır'}\n"
    )
    if src_hint:
        user += f"Kaynaklar:\n{src_hint}\n"
    if note:
        user += f"Kural denetimi notu: {note[:400]}\n"

    started = time.monotonic()
    out_text = ""
    try:
        fast_model = os.environ.get("OLLAMA_FAST_MODEL") or os.environ.get(
            "OLLAMA_CHAT_MODEL", "llama3.2:3b"
        )
        from ilim_assistant.llm_ollama import chat_completion, ollama_reachable

        if not ollama_reachable():
            return {"ok": True, "applied": False, "reason": "ollama_offline"}
        out_text = (
            chat_completion(
                system,
                user,
                model=fast_model,
            )
            or ""
        ).strip()
    except Exception as exc:
        return {"ok": False, "applied": False, "error": str(exc)[:200]}

    elapsed = time.monotonic() - started
    if elapsed > _budget_sec() or not out_text or out_text.startswith("["):
        return {
            "ok": True,
            "applied": False,
            "reason": "timeout_or_empty",
            "elapsed_sec": round(elapsed, 2),
        }

    merged = _merge_reflection_note(reply, out_text)
    return {
        "ok": True,
        "applied": True,
        "reply": merged,
        "elapsed_sec": round(elapsed, 2),
        "version": FAZ_Y_LLM_VERSION,
    }


def apply_bilgi_kalite_pass(
    reply: str,
    user_message: str,
    *,
    hits: list | None = None,
    question_plan: Any | None = None,
    web_was_used: bool = False,
) -> tuple[str, dict[str, Any], dict[str, Any] | None]:
    """
    Faz Y boru hattı: kural reflection → LLM reflection → kaynak rozeti.
    Dönüş: (cevap, reflection_meta, source_trust_card)
    """
    from ilim_assistant.ana_motor_kaynak_rozet import build_source_trust_card
    from ilim_assistant.ana_motor_reflection import (
        apply_answer_quality_pass,
        detect_source_answer_mismatch,
    )

    body = apply_answer_quality_pass(
        reply,
        user_message,
        hits=hits,
        question_plan=question_plan,
        web_was_used=web_was_used,
    )
    mismatch, mismatch_note = detect_source_answer_mismatch(
        body,
        hits=hits,
        web_was_used=web_was_used,
    )
    reflection_meta: dict[str, Any] = {
        "mismatch": mismatch,
        "mismatch_note": mismatch_note,
        "llm_reflection_applied": False,
    }

    llm_result = run_llm_reflection_pass(
        body,
        user_message,
        hits=hits,
        question_plan=question_plan,
        web_was_used=web_was_used,
        mismatch_note=mismatch_note,
    )
    if llm_result.get("applied") and llm_result.get("reply"):
        body = str(llm_result["reply"])
        reflection_meta["llm_reflection_applied"] = True
        reflection_meta["llm_elapsed_sec"] = llm_result.get("elapsed_sec")

    card = build_source_trust_card(
        body,
        user_message,
        hits=hits,
        question_plan=question_plan,
        web_was_used=web_was_used,
        reflection_meta=reflection_meta,
    )
    return body, reflection_meta, card if card.get("ok") else None
