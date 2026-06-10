# Created by Ümit & Gökçenur
"""
Ana Motor v2 — Faz 59: Kod niyeti sınıflandırıcı + delege özeti + bütçe aktarımı.

- Hafif niyet sınıflandırması (~50ms, kural tabanlı)
- Genel → Programlama delege: Ümit 15sn yerine kısa yönlendirme; kod bütçesi programlama motorunda
- İlim ağırlıklı sorularda 22 sn (Ümit emri ile uyumlu)
- Delege bitişinde Ana Motor'a kısa özet (yazım + test)
"""

from __future__ import annotations

import json
import os
import re
import time
import unicodedata
from pathlib import Path
from typing import Any

FAZ59_VERSION = "ana-motor-faz59-v1-2026-05-26"
_SUMMARY_FILE = "delegation_summaries.json"
_ROUTER_BUDGET_DEFAULT = 3.0
_MAX_SUMMARIES = 40

_CODE_STRONG = (
    r"\b(refactor|pytest|traceback|@@write|@@read|fastapi|uvicorn|npm test)\b",
    r"\b(main\.py|app\.py|\.py\b|\.tsx?\b|github|pull request|pr\b)",
    r"\b(proje üret|proje uret|web sitesi yap|api yaz|bugfix|hata ayikla)\b",
    r"projects/[\w.\-]+",
    r"\b(gorev:|görev:)\s*",
)

_CODE_SOFT = (
    "kod",
    "dosya",
    "patch",
    "test et",
    "calistir",
    "çalıştır",
    "uygula",
    "ekle",
    "duzelt",
    "düzelt",
)

_ILIM_MARKERS = (
    "nedir",
    "kimdir",
    "nasıl",
    "neden",
    "tarih",
    "hadis",
    "ayet",
    "kuran",
    "mektubat",
    "tasavvuf",
    "felsefe",
    "açıkla",
    "acikla",
    "anlat",
    "ilim",
    "mana",
)


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ59", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz59_enabled() -> bool:
    return _enabled()


def _ascii_fold(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def classify_turn_intent(
    message: str,
    *,
    mode_norm: str = "genel",
    coding_mode: bool = False,
    motor_flags: dict[str, bool] | None = None,
) -> dict[str, Any]:
    """
    Hafif niyet — code | ilim | general | mixed.
    delegate_programming: genel modda programlamaya aktar.
    use_ilim_budget: 22 sn Ümit bütçesi.
    """
    t0 = time.perf_counter()
    flags = motor_flags or {}
    low = _ascii_fold(message)
    msg = (message or "").strip()

    code_score = 0
    ilim_score = 0
    if flags.get("programlama"):
        code_score += 3
    for pat in _CODE_STRONG:
        if re.search(pat, low, re.I):
            code_score += 2
    for w in _CODE_SOFT:
        if w in low:
            code_score += 1
    for m in _ILIM_MARKERS:
        if m in low:
            ilim_score += 1
    try:
        from ilim_assistant.ruzgar_umed_cevap_emri import is_ilim_heavy_question

        if is_ilim_heavy_question(msg):
            ilim_score += 3
    except Exception:
        pass

    if coding_mode or mode_norm == "programlama":
        intent = "code"
    elif code_score >= 2 and code_score > ilim_score:
        intent = "code"
    elif ilim_score >= 2 and ilim_score > code_score:
        intent = "ilim"
    elif code_score >= 1 and ilim_score >= 1:
        intent = "mixed"
    else:
        intent = "general"

    delegate = False
    if _enabled() and mode_norm in ("genel", "gelisim", "uretim", "") and not coding_mode:
        if intent in ("code", "mixed") and code_score >= ilim_score:
            try:
                from ilim_assistant.motorlar.programlama_faz10 import (
                    should_delegate_to_programlama,
                )

                delegate = should_delegate_to_programlama(
                    msg,
                    mode_norm,
                    coding_mode=coding_mode,
                    motor_flags=flags,
                )
            except Exception:
                delegate = code_score >= 2
        elif intent == "code":
            delegate = code_score >= 2

    use_ilim = intent in ("ilim", "mixed") and ilim_score >= code_score

    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    return {
        "ok": True,
        "intent": intent,
        "code_score": code_score,
        "ilim_score": ilim_score,
        "delegate_programming": delegate,
        "use_ilim_budget": use_ilim and not delegate,
        "programming_budget_transferred": delegate,
        "elapsed_ms": round(elapsed_ms, 2),
        "version": FAZ59_VERSION,
    }


def router_budget_sec() -> float:
    try:
        return max(
            1.0,
            float(os.environ.get("RUZGAR_FAZ59_ROUTER_BUDGET_SEC", str(_ROUTER_BUDGET_DEFAULT))),
        )
    except ValueError:
        return _ROUTER_BUDGET_DEFAULT


def resolve_umed_budget_sec(
    message: str,
    *,
    mode_norm: str = "genel",
    coding_mode: bool = False,
    motor_flags: dict[str, bool] | None = None,
) -> float:
    """Delege varsa kısa yönlendirme; ilimde 22sn; doğal sohbet 32sn; yoksa 15sn."""
    try:
        from ilim_assistant.ruzgar_dogal_sohbet_faz91 import turn_budget_for_message

        ext = turn_budget_for_message(message, mode_norm)
        if ext is not None:
            return ext
    except Exception:
        pass
    if not _enabled():
        try:
            from ilim_assistant.ruzgar_umed_cevap_emri import turn_budget_sec

            return turn_budget_sec(message, mode_norm=mode_norm)
        except Exception:
            return 15.0
    intent = classify_turn_intent(
        message,
        mode_norm=mode_norm,
        coding_mode=coding_mode,
        motor_flags=motor_flags,
    )
    if intent.get("delegate_programming"):
        return router_budget_sec()
    if intent.get("use_ilim_budget"):
        try:
            return float(os.environ.get("RUZGAR_UMED_ILIM_BUDGET_SEC", "22"))
        except ValueError:
            return 22.0
    try:
        return float(os.environ.get("RUZGAR_UMED_BUDGET_SEC", "15"))
    except ValueError:
        return 15.0


def begin_umed_turn_budget(
    message: str,
    *,
    mode_norm: str = "genel",
    coding_mode: bool = False,
    motor_flags: dict[str, bool] | None = None,
) -> float:
    """Ümit emri deadline — Faz 59 bütçe çözümü."""
    budget = resolve_umed_budget_sec(
        message,
        mode_norm=mode_norm,
        coding_mode=coding_mode,
        motor_flags=motor_flags,
    )
    try:
        from ilim_assistant.ruzgar_umed_cevap_emri import set_turn_deadline

        set_turn_deadline(time.monotonic() + budget)
    except Exception:
        pass
    return budget


def build_delegation_summary(
    *,
    scope_rel: str = "",
    success: bool = False,
    verify_ok: bool | None = None,
    turns_used: int = 0,
    writes_count: int = 0,
    elapsed_sec: float = 0.0,
    goal: str = "",
    detail: str = "",
) -> dict[str, Any]:
    v_ok = verify_ok if verify_ok is not None else success
    return {
        "ok": True,
        "scope_rel": scope_rel,
        "success": success,
        "verify_ok": v_ok,
        "turns_used": turns_used,
        "writes_count": writes_count,
        "elapsed_sec": round(elapsed_sec, 1),
        "goal": (goal or "")[:300],
        "detail": (detail or "")[:400],
        "ts": time.time(),
        "version": FAZ59_VERSION,
    }


def summary_from_agent_state(
    workspace_root: str | Path | None,
    *,
    success: bool,
    turns_used: int,
    elapsed_sec: float,
    scope_rel: str = "",
    goal: str = "",
) -> dict[str, Any]:
    verify_ok = None
    writes = 0
    try:
        from ilim_assistant.motorlar.programlama_faz14 import load_agent_state

        st = load_agent_state(workspace_root)
        verify_ok = st.get("last_verify_ok")
        writes = int(st.get("total_writes") or 0)
        scope_rel = scope_rel or str(st.get("scope_rel") or "")
        goal = goal or str(st.get("goal") or "")
    except Exception:
        pass
    return build_delegation_summary(
        scope_rel=scope_rel,
        success=success,
        verify_ok=bool(verify_ok) if verify_ok is not None else success,
        turns_used=turns_used,
        writes_count=writes,
        elapsed_sec=elapsed_sec,
        goal=goal,
    )


def format_delegation_summary_text(summary: dict[str, Any]) -> str:
    if not summary.get("ok"):
        return ""
    scope = summary.get("scope_rel") or "?"
    turns = int(summary.get("turns_used") or 0)
    writes = int(summary.get("writes_count") or 0)
    sec = float(summary.get("elapsed_sec") or 0)
    v_ok = summary.get("verify_ok")
    test_txt = (
        "pytest yeşil"
        if v_ok
        else ("test kırmızı" if v_ok is False else "test bilinmiyor")
    )
    ok_txt = "tamamlandı" if summary.get("success") else "kısmi"
    return (
        f"\n\n---\n**Ana Motor özeti (Faz 59)** — delege {ok_txt}\n"
        f"· Kapsam: `{scope}` · {turns} tur · {writes} yazım · {sec:.0f} sn\n"
        f"· Test: **{test_txt}**\n"
        f"({FAZ59_VERSION})"
    )


def _summary_path(workspace_root: str | Path | None) -> Path | None:
    try:
        from ilim_assistant.motorlar.programlama_motoru import repo_root

        root = repo_root(workspace_root)
        if root is None:
            return None
        cache = root / ".ruzgar"
        cache.mkdir(parents=True, exist_ok=True)
        return cache / _SUMMARY_FILE
    except Exception:
        return None


def persist_delegation_summary(
    workspace_root: str | Path | None,
    summary: dict[str, Any],
) -> None:
    path = _summary_path(workspace_root)
    if path is None:
        return
    store: dict[str, Any] = {"items": [], "version": FAZ59_VERSION}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            store = data
    except (OSError, json.JSONDecodeError):
        pass
    items = list(store.get("items") or [])
    items.append(summary)
    store["items"] = items[-_MAX_SUMMARIES:]
    store["saved_at"] = time.time()
    path.write_text(json.dumps(store, ensure_ascii=False, indent=2), encoding="utf-8")


def load_last_delegation_summary(
    workspace_root: str | Path | None,
) -> dict[str, Any] | None:
    path = _summary_path(workspace_root)
    if path is None or not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        items = list((data or {}).get("items") or [])
        return items[-1] if items else None
    except (OSError, json.JSONDecodeError):
        return None


def append_delegation_footer_to_reply(
    reply_body: str,
    workspace_root: str | Path | None,
    *,
    success: bool,
    turns_used: int,
    elapsed_sec: float,
    scope_rel: str = "",
    goal: str = "",
) -> str:
    if not _enabled():
        return reply_body
    summ = summary_from_agent_state(
        workspace_root,
        success=success,
        turns_used=turns_used,
        elapsed_sec=elapsed_sec,
        scope_rel=scope_rel,
        goal=goal,
    )
    persist_delegation_summary(workspace_root, summ)
    footer = format_delegation_summary_text(summ)
    if footer and footer not in (reply_body or ""):
        return (reply_body or "").rstrip() + footer
    return reply_body or ""


def enrich_handoff_with_intent(
    packet_text: str,
    message: str,
    *,
    mode_norm: str = "genel",
    motor_flags: dict[str, bool] | None = None,
) -> str:
    if not _enabled():
        return packet_text
    intent = classify_turn_intent(
        message, mode_norm=mode_norm, motor_flags=motor_flags
    )
    line = (
        f"[Niyet — Faz 59] `{intent.get('intent')}` · "
        f"delege={'evet' if intent.get('delegate_programming') else 'hayır'} · "
        f"{intent.get('elapsed_ms', 0):.1f}ms"
    )
    if intent.get("programming_budget_transferred"):
        line += " · kod bütçesi programlama motorunda"
    return (packet_text or "").rstrip() + "\n\n" + line


def faz59_directive() -> str:
    return (
        "[ANA MOTOR v2 — Faz 59]\n"
        "Kod niyeti → programlama delege · ilim 22sn · delege özeti.\n"
        "Kapat: RUZGAR_FAZ59=0\n"
    )
