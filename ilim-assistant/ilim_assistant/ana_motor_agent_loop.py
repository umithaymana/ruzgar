# Created by Ümit & Gökçenur
"""
Ana Motor — Faz 92: çok turlu ajan (plan → oku → @@write → doğrula).

Genel modda Cursor benzeri dosya patch döngüsü (programlama motoruna delege edilmemiş işler).
Kapat: RUZGAR_ANA_AGENT_LOOP=0
"""

from __future__ import annotations

import os
import re
import unicodedata
from typing import Any, Iterator

FAZ92_VERSION = "ana-motor-agent-loop-faz92-v1"

_ACTION_RE = re.compile(
    r"(?:yap|ekle|duzelt|düzelt|yaz|güncelle|guncelle|degistir|değiştir|patch|"
    r"olustur|oluştur|tamamla|bitir|kaydet|dosyaya|dosyasina|@@write|@@read)",
    re.I,
)


def agent_loop_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_AGENT_LOOP", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def max_agent_turns() -> int:
    try:
        return max(1, min(int(os.environ.get("RUZGAR_ANA_AGENT_MAX_TURNS", "3")), 6))
    except ValueError:
        return 3


def _ascii_fold(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def _plan_primary(question_plan: Any | None) -> str:
    if question_plan is None:
        return ""
    if hasattr(question_plan, "primary"):
        return str(question_plan.primary or "")
    if isinstance(question_plan, dict):
        return str(question_plan.get("primary") or "")
    return ""


def _has_file_action_intent(message: str, question_plan: Any | None) -> bool:
    raw = (message or "").strip()
    if not raw:
        return False
    low = _ascii_fold(raw)
    primary = _plan_primary(question_plan)
    if primary in ("islem", "dosya", "programlama"):
        return True
    if "@@write" in low or "@@read" in low:
        return True
    if not _ACTION_RE.search(raw):
        return False
    try:
        from ilim_assistant.local_tools import extract_at_paths
        from ilim_assistant.ana_motor_agent import infer_workspace_rel_paths, _repo_root

        if extract_at_paths(raw):
            return True
        root = _repo_root(None)
        if root and infer_workspace_rel_paths(raw, root):
            return True
    except Exception:
        pass
    if re.search(r"\.(?:py|js|ts|tsx|md|json|html|css|bat|ps1)\b", raw, re.I):
        return True
    return False


def should_run_ana_motor_agent_loop(
    message: str,
    mode_norm: str,
    question_plan: Any | None,
    *,
    workspace_root: str | None = None,
    coding_mode: bool = False,
) -> bool:
    if not agent_loop_enabled() or coding_mode:
        return False
    if mode_norm not in ("genel", "uretim", "gelisim"):
        return False
    if not _has_file_action_intent(message, question_plan):
        try:
            from ilim_assistant.ana_motor_checkpoint import (
                is_resume_message,
                load_checkpoint,
            )

            if is_resume_message(message) and load_checkpoint(workspace_root):
                return True
        except Exception:
            pass
        return False
    try:
        from ilim_assistant.motorlar.programlama_faz10 import should_delegate_to_programlama

        if should_delegate_to_programlama(
            message,
            mode_norm,
            coding_mode=coding_mode,
            motor_flags={},
        ):
            return False
    except Exception:
        pass
    try:
        from ilim_assistant.ruzgar_dogal_sohbet_faz91 import is_natural_conversation_turn

        if is_natural_conversation_turn(
            message, mode_norm, question_plan
        ) and not _has_file_action_intent(message, question_plan):
            return False
    except Exception:
        pass
    return True


def faz92_agent_directive() -> str:
    return (
        "[ANA MOTOR AJAN — Faz 92]\n"
        "Görev: Ümit abi'nin istediği dosya değişikliğini uygula.\n"
        "Sıra: (1) kısa plan 2-3 madde → (2) gerekirse @@read → (3) @@write + kod bloğu → (4) özet.\n"
        "Patch biçimi:\n"
        "@@write ilim-assistant/yol/dosya.py\n"
        "```python\n"
        "# tam dosya veya bölüm\n"
        "```\n"
        "Hassas dosyalara (.env, hafiza, *.db, sağlık) yazma. Gereksiz refaktör yok.\n"
    )


def _build_turn_user(
    message: str,
    *,
    turn: int,
    max_turns: int,
    failure: str = "",
    resume_note: str = "",
) -> str:
    if turn <= 1:
        base = (
            f"[GÖREV — tur {turn}/{max_turns}]\n"
            f"{(message or '').strip()}\n\n"
            "Yanıtta mutlaka gerekli `@@write` patch üret; salt sohbet yeterli değil.\n"
        )
        if resume_note:
            base = resume_note + "\n\n" + base
        return base
    return (
        f"[GÖREV — tur {turn}/{max_turns} — düzeltme]\n"
        f"Önceki tur sorunları:\n{failure[:8000]}\n\n"
        "Yalnızca gerekli `@@write` patch; açıklamayı kısa tut.\n"
    )


def _append_patch_step(
    orch: dict[str, Any],
    patch_meta: dict[str, Any],
) -> None:
    steps = list(orch.get("agent_steps") or [])
    action = str(patch_meta.get("action") or "")
    applied = patch_meta.get("applied") or []
    detail = action
    if applied:
        detail = f"{action}: " + ", ".join(applied[:3])
    steps.append(
        {
            "id": "patch",
            "label": "Patch",
            "status": "done" if action in ("applied", "staged") else "skip",
            "detail": detail[:120],
        }
    )
    orch["agent_steps"] = steps


def iter_ana_motor_agent_events(
    *,
    message: str,
    req: Any,
    system: str,
    user_payload: str,
    model: str,
    prior: list,
    mode_norm: str,
    turn_plan: Any,
    hits: list,
    new_wake: bool,
    orch: dict[str, Any],
) -> Iterator[dict[str, Any]]:
    """Çok turlu genel mod ajan — stream + @@write uygulama."""
    from ilim_assistant.chat_core import finalize_assistant_reply, rag_footer
    from ilim_assistant.llm_brain import stream_chat_with_brain
    from ilim_assistant.motorlar.programlama_faz10 import (
        extract_write_jobs,
        process_assistant_reply_patches,
        resolve_scope_rel,
    )

    max_turns = max_agent_turns()
    sys_full = system.rstrip() + "\n\n" + faz92_agent_directive()
    active_prior = list(prior) if prior else []
    reply_body = ""
    user_msg = (message or "").strip()
    resume_note = ""
    session_id = ""

    try:
        from ilim_assistant.ana_motor_checkpoint import (
            build_resume_context,
            is_resume_message,
            load_checkpoint,
            save_checkpoint,
        )

        if is_resume_message(user_msg):
            cp = load_checkpoint(getattr(req, "workspace_root", None))
            if cp:
                resume_note = build_resume_context(cp)
                session_id = cp.session_id
                user_msg = cp.last_user or user_msg
    except Exception:
        save_checkpoint = None  # type: ignore[assignment]

    try:
        from ilim_assistant.ana_motor_progress import enrich_status_text

        _st = enrich_status_text(
            f"Ana Motor ajan — plan/okuma/yazma (Faz 92, en fazla {max_turns} tur)…",
            phase="ana_agent",
        )
    except Exception:
        _st = f"Ana Motor ajan — plan/okuma/yazma (Faz 92, en fazla {max_turns} tur)…"
    yield {"type": "status", "text": _st, "phase": "ana_agent"}
    yield {"type": "meta", "ana_agent_loop": {"version": FAZ92_VERSION, "max_turns": max_turns}}

    scope = resolve_scope_rel(
        getattr(req, "workspace_root", None),
        active_file=getattr(req, "programlama_active_file", None),
    )
    failure_snippet = ""
    patch_meta: dict[str, Any] = {}

    for turn in range(1, max_turns + 1):
        turn_user = _build_turn_user(
            user_msg,
            turn=turn,
            max_turns=max_turns,
            failure=failure_snippet,
            resume_note=resume_note if turn == 1 else "",
        )
        payload = user_payload + "\n\n---\n" + turn_user
        round_body = ""

        for piece in stream_chat_with_brain(
            sys_full,
            payload,
            model=model,
            prior_messages=active_prior,
            mode_norm=mode_norm,
            coding_mode=False,
            message=user_msg,
            question_plan=turn_plan,
        ):
            round_body += piece
            reply_body += piece
            yield {"type": "token", "text": piece}

        patch_meta = process_assistant_reply_patches(
            round_body,
            getattr(req, "workspace_root", None),
            scope_rel=scope,
        )
        _append_patch_step(orch, patch_meta)

        try:
            if save_checkpoint:
                save_checkpoint(
                    getattr(req, "workspace_root", None),
                    turn_index=turn,
                    last_user=user_msg,
                    last_reply=round_body,
                    plan_primary=_plan_primary(turn_plan),
                    mode_norm=mode_norm,
                    agent_phase="patch" if patch_meta.get("applied") else "planning",
                    agent_steps=orch.get("agent_steps"),
                    patch_applied=list(patch_meta.get("applied") or []),
                    patch_errors=list(patch_meta.get("errors") or []),
                    max_turns=max_turns,
                    session_id=session_id or None,
                )
        except Exception:
            pass

        action = str(patch_meta.get("action") or "")
        if action in ("applied", "staged"):
            pf = str(patch_meta.get("footer") or "")
            if pf and pf not in reply_body:
                reply_body += pf
                yield {"type": "token", "text": pf}
            errors = list(patch_meta.get("errors") or [])
            verify = patch_meta.get("verify") or {}
            if errors or (verify and not verify.get("ok", True)):
                failure_snippet = "\n".join(errors) or str(verify.get("report") or "")[:4000]
                active_prior = active_prior + [
                    {"role": "assistant", "content": round_body},
                    {
                        "role": "user",
                        "content": _build_turn_user(
                            user_msg,
                            turn=turn + 1,
                            max_turns=max_turns,
                            failure=failure_snippet,
                        ),
                    },
                ]
                if turn < max_turns:
                    yield {
                        "type": "status",
                        "text": f"Doğrulama kırmızı — tur {turn + 1}/{max_turns}…",
                    }
                    continue
            break

        if not extract_write_jobs(round_body) or turn >= max_turns:
            break

        failure_snippet = "Model @@write üretmedi veya patch uygulanmadı; tekrar dene."
        active_prior = active_prior + [
            {"role": "assistant", "content": round_body},
            {
                "role": "user",
                "content": _build_turn_user(
                    user_msg,
                    turn=turn + 1,
                    max_turns=max_turns,
                    failure=failure_snippet,
                ),
            },
        ]
        yield {"type": "status", "text": f"Patch bekleniyor — tur {turn + 1}/{max_turns}…"}

    try:
        from ilim_assistant.ana_motor_checkpoint import clear_checkpoint

        if patch_meta.get("action") == "applied" and not patch_meta.get("errors"):
            clear_checkpoint(getattr(req, "workspace_root", None))
        else:
            from ilim_assistant.ana_motor_checkpoint import save_checkpoint as _scp

            _scp(
                getattr(req, "workspace_root", None),
                turn_index=max_turns,
                last_user=user_msg,
                last_reply=reply_body,
                plan_primary=_plan_primary(turn_plan),
                mode_norm=mode_norm,
                agent_phase="done" if patch_meta.get("applied") else "planning",
                agent_steps=orch.get("agent_steps"),
                patch_applied=list(patch_meta.get("applied") or []),
                patch_errors=list(patch_meta.get("errors") or []),
                max_turns=max_turns,
                session_id=session_id or None,
            )
    except Exception:
        pass

    try:
        from ilim_assistant.ana_motor_agent import mark_agent_answer_done

        if orch.get("agent_steps"):
            orch["agent_steps"] = mark_agent_answer_done(orch["agent_steps"])
    except Exception:
        pass

    footer = rag_footer(hits)
    body_fixed = finalize_assistant_reply(reply_body)
    full_out = body_fixed + footer
    done: dict[str, Any] = {
        "type": "done",
        "full_reply": full_out,
        "user_message": user_msg,
        "new_wake_used": new_wake,
        "orchestra": orch,
        "ana_agent_loop": True,
    }
    if patch_meta and patch_meta.get("action") not in ("skip", "none", ""):
        done["code_patch"] = {
            "action": patch_meta.get("action"),
            "applied": list(patch_meta.get("applied") or []),
            "errors": list(patch_meta.get("errors") or []),
            "items": list(patch_meta.get("items") or []),
        }
    yield done
