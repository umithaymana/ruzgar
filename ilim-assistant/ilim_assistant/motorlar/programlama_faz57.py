# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 57: Model yedek zinciri (Groq'suz Gemini FC).

- Groq yoksa / hata verirse Gemini function calling (Faz 40 yedek)
- Canlı metin-only oranı <%3 (`.ruzgar/text_only_stats.json`)
- Parity: `--groq-e2e` → Groq veya Gemini FC ping
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

FAZ57_VERSION = "programlama-faz57-v1-2026-05-26"
_STATS_FILE = "text_only_stats.json"
_MAX_EVENTS = 400
_TARGET_TEXT_ONLY_RATE = 0.03


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ57", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz57_enabled() -> bool:
    return _enabled()


def gemini_fc_fallback_enabled() -> bool:
    if not _enabled():
        return False
    return os.environ.get("RUZGAR_FAZ57_GEMINI_FC", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def target_text_only_rate() -> float:
    try:
        return max(
            0.01,
            min(0.15, float(os.environ.get("RUZGAR_FAZ57_TEXT_ONLY_TARGET", "0.03"))),
        )
    except ValueError:
        return _TARGET_TEXT_ONLY_RATE


def groq_fc_available() -> bool:
    try:
        from ilim_assistant.motorlar.programlama_faz40 import _groq_endpoint

        return _groq_endpoint() is not None
    except Exception:
        return bool(os.environ.get("GROQ_API_KEY", "").strip())


def gemini_fc_available() -> bool:
    if not gemini_fc_fallback_enabled():
        return False
    try:
        from ilim_assistant.llm_gemini import gemini_configured

        return gemini_configured()
    except Exception:
        return False


def select_fc_provider() -> str:
    """Birincil FC sağlayıcı: groq | gemini | none."""
    prefer = (os.environ.get("RUZGAR_FAZ57_FC_PROVIDER", "auto") or "auto").strip().lower()
    if prefer == "gemini" and gemini_fc_available():
        return "gemini"
    if prefer == "groq" and groq_fc_available():
        return "groq"
    if groq_fc_available():
        return "groq"
    if gemini_fc_available():
        return "gemini"
    return "none"


def reorder_brain_chain_for_fc(chain: list[str]) -> list[str]:
    """Groq yokken gemini öne — görev LLM zinciri."""
    if groq_fc_available():
        return chain
    if not gemini_fc_available():
        return chain
    out: list[str] = []
    for p in ("gemini", "kod", "groq"):
        if p in chain and p not in out:
            out.append(p)
    for x in chain:
        if x not in out:
            out.append(x)
    return out or chain


def task_brain_profile_when_no_groq() -> str | None:
    if groq_fc_available():
        return None
    if gemini_fc_available():
        return "gemini"
    return None


def gemini_function_declarations() -> list[dict[str, Any]]:
    try:
        from ilim_assistant.motorlar.programlama_faz40 import openai_tools_schema

        decls: list[dict[str, Any]] = []
        for tool in openai_tools_schema():
            fn = (tool.get("function") or {}) if isinstance(tool, dict) else {}
            name = str(fn.get("name") or "").strip()
            if not name:
                continue
            decls.append(
                {
                    "name": name,
                    "description": str(fn.get("description") or "")[:500],
                    "parameters": fn.get("parameters")
                    or {"type": "object", "properties": {}},
                }
            )
        return decls
    except Exception:
        return []


def _gemini_fc_mode(tool_choice: str) -> str:
    tc = (tool_choice or "auto").strip().lower()
    if tc == "required":
        return "ANY"
    if tc == "none":
        return "NONE"
    return "AUTO"


def _spec_from_gemini_call(part: dict[str, Any]) -> dict[str, Any] | None:
    fc = part.get("functionCall") or part.get("function_call") or {}
    if not isinstance(fc, dict):
        return None
    name = str(fc.get("name") or "").strip().lower()
    if not name:
        return None
    args = fc.get("args") or fc.get("arguments") or {}
    if not isinstance(args, dict):
        args = {}
    return {"tool": name, **args}


def gemini_chat_completion_with_tools(
    system: str,
    user: str,
    *,
    prior_messages: list | None = None,
    scope_rel: str = "",
    tool_choice: str = "auto",
) -> tuple[str, list[dict[str, Any]]]:
    """Gemini generateContent + functionDeclarations."""
    if not gemini_fc_available():
        return "", []
    try:
        import requests
        from ilim_assistant.llm_gemini import (
            _build_gemini_contents,
            _gemini_timeout,
            gemini_active_model,
            gemini_api_key,
        )
        from ilim_assistant.motorlar.programlama_motoru import repo_root

        key = gemini_api_key().strip()
        if not key:
            return "", []
        model = gemini_active_model()
        decls = gemini_function_declarations()
        if not decls:
            return "[Gemini FC: araç şeması yok]", []

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent"
        )
        contents = _build_gemini_contents(user, prior_messages)
        payload: dict[str, Any] = {
            "systemInstruction": {"parts": [{"text": (system or "").strip()[:12000]}]},
            "contents": contents,
            "tools": [{"functionDeclarations": decls}],
            "toolConfig": {
                "functionCallingConfig": {"mode": _gemini_fc_mode(tool_choice)},
            },
            "generationConfig": {"temperature": 0.2},
        }
        conn_t, read_t = _gemini_timeout()
        resp = requests.post(
            url,
            json=payload,
            headers={
                "x-goog-api-key": key,
                "Content-Type": "application/json",
            },
            timeout=(conn_t, min(read_t, 90.0)),
        )
        if resp.status_code >= 400:
            return f"[Gemini FC HTTP {resp.status_code}]", []
        data = resp.json()
        candidates = data.get("candidates") or []
        if not candidates:
            return "", []
        content = (candidates[0] or {}).get("content") or {}
        parts = content.get("parts") or []
        texts: list[str] = []
        specs: list[dict[str, Any]] = []
        for part in parts:
            if not isinstance(part, dict):
                continue
            if part.get("text"):
                texts.append(str(part["text"]))
            spec = _spec_from_gemini_call(part)
            if spec:
                specs.append(spec)
        from ilim_assistant.motorlar.programlama_faz40 import run_tool_specs

        root = repo_root(None)
        results = run_tool_specs(specs, root, scope_rel=scope_rel or None) if specs else []
        return "\n".join(texts).strip(), results
    except Exception as exc:
        return f"[Gemini FC: {str(exc)[:200]}]", []


def _groq_chat_completion_with_tools(
    system: str,
    user: str,
    *,
    prior_messages: list | None = None,
    scope_rel: str = "",
    tool_choice: str = "auto",
) -> tuple[str, list[dict[str, Any]]]:
    """Doğrudan Groq (faz40 iç kodu — döngüsel import önleme)."""
    try:
        from ilim_assistant.motorlar.programlama_faz40 import (
            _groq_endpoint,
            _spec_from_openai_call,
            openai_tools_schema,
            run_tool_specs,
        )
        from ilim_assistant.llm_ollama import _build_chat_messages

        ep = _groq_endpoint()
        if ep is None:
            return "", []
        import requests

        base, key, model = ep
        messages = _build_chat_messages(system, user, prior_messages)
        tc = (tool_choice or "auto").strip().lower()
        if tc not in ("auto", "required", "none"):
            tc = "auto"
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "tools": openai_tools_schema(),
            "tool_choice": tc,
            "temperature": 0.2,
            "stream": False,
        }
        resp = requests.post(
            f"{base}/chat/completions",
            json=payload,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            timeout=90,
        )
        if resp.status_code >= 400:
            return f"[Groq tools HTTP {resp.status_code}]", []
        data = resp.json()
        msg = (data.get("choices") or [{}])[0].get("message") or {}
        content = str(msg.get("content") or "").strip()
        specs: list[dict[str, Any]] = []
        for c in msg.get("tool_calls") or []:
            if isinstance(c, dict):
                spec = _spec_from_openai_call(c)
                if spec:
                    specs.append(spec)
        from ilim_assistant.motorlar.programlama_motoru import repo_root

        root = repo_root(None)
        results = run_tool_specs(specs, root, scope_rel=scope_rel or None) if specs else []
        return content, results
    except Exception as exc:
        return f"[Groq FC: {str(exc)[:200]}]", []


def _groq_failed(text: str, batch: list[dict[str, Any]]) -> bool:
    if batch:
        return False
    raw = (text or "").strip()
    if not raw:
        return True
    low = raw.lower()
    return raw.startswith("[") and ("groq" in low or "http" in low)


def route_fc_completion(
    system: str,
    user: str,
    *,
    prior_messages: list | None = None,
    scope_rel: str = "",
    tool_choice: str = "auto",
) -> tuple[str, list[dict[str, Any]]]:
    """Faz 57 yönlendirme: Groq → Gemini yedek."""
    provider = select_fc_provider()
    if provider == "gemini":
        return gemini_chat_completion_with_tools(
            system,
            user,
            prior_messages=prior_messages,
            scope_rel=scope_rel,
            tool_choice=tool_choice,
        )
    if provider == "groq":
        text, batch = _groq_chat_completion_with_tools(
            system,
            user,
            prior_messages=prior_messages,
            scope_rel=scope_rel,
            tool_choice=tool_choice,
        )
        if gemini_fc_fallback_enabled() and _groq_failed(text, batch):
            g_text, g_batch = gemini_chat_completion_with_tools(
                system,
                user,
                prior_messages=prior_messages,
                scope_rel=scope_rel,
                tool_choice=tool_choice,
            )
            if g_batch or (g_text and not _groq_failed(g_text, g_batch)):
                return g_text, g_batch
        return text, batch
    return "", []


def _stats_path(workspace_root: str | Path | None) -> Path | None:
    try:
        from ilim_assistant.motorlar.programlama_motoru import repo_root

        root = repo_root(workspace_root)
        if root is None:
            return None
        cache = root / ".ruzgar"
        cache.mkdir(parents=True, exist_ok=True)
        return cache / _STATS_FILE
    except Exception:
        return None


def _load_stats(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {"events": [], "version": FAZ57_VERSION}


def _save_stats(path: Path, store: dict[str, Any]) -> None:
    store["version"] = FAZ57_VERSION
    store["saved_at"] = time.time()
    events = list(store.get("events") or [])
    if len(events) > _MAX_EVENTS:
        store["events"] = events[-_MAX_EVENTS:]
    path.write_text(json.dumps(store, ensure_ascii=False, indent=2), encoding="utf-8")


def record_agent_turn_fc(
    workspace_root: str | Path | None,
    *,
    scope_rel: str = "",
    turn: int = 0,
    text_only: bool = False,
    provider: str = "",
    recovery_attempted: bool = False,
) -> dict[str, Any]:
    """Tur sonu FC metrik — metin-only oranı için."""
    if not _enabled():
        return {"ok": False, "skipped": True}
    path = _stats_path(workspace_root)
    if path is None:
        return {"ok": False, "error": "no_workspace"}
    store = _load_stats(path)
    events = list(store.get("events") or [])
    events.append(
        {
            "ts": time.time(),
            "scope_rel": scope_rel,
            "turn": turn,
            "text_only": bool(text_only),
            "provider": provider or select_fc_provider(),
            "recovery_attempted": bool(recovery_attempted),
        }
    )
    store["events"] = events
    _recompute_summary(store)
    _save_stats(path, store)
    return {"ok": True, "stats": store.get("summary") or {}}


def _recompute_summary(store: dict[str, Any]) -> None:
    events = list(store.get("events") or [])
    total = len(events)
    text_only = sum(1 for e in events if e.get("text_only"))
    recovery = sum(1 for e in events if e.get("recovery_attempted"))
    rate = (text_only / total) if total else 0.0
    store["summary"] = {
        "total_turns": total,
        "text_only_turns": text_only,
        "text_only_rate": round(rate, 4),
        "recovery_attempts": recovery,
        "target_rate": target_text_only_rate(),
        "meets_target": rate <= target_text_only_rate() if total >= 5 else True,
    }


def compute_text_only_stats(
    workspace_root: str | Path | None,
    *,
    window_days: int = 7,
) -> dict[str, Any]:
    path = _stats_path(workspace_root)
    if path is None or not path.is_file():
        return {
            "ok": True,
            "total_turns": 0,
            "text_only_turns": 0,
            "text_only_rate": 0.0,
            "meets_target": True,
            "target_rate": target_text_only_rate(),
            "version": FAZ57_VERSION,
        }
    store = _load_stats(path)
    cutoff = time.time() - max(1, window_days) * 86400
    events = [e for e in (store.get("events") or []) if float(e.get("ts") or 0) >= cutoff]
    total = len(events)
    text_only = sum(1 for e in events if e.get("text_only"))
    rate = (text_only / total) if total else 0.0
    return {
        "ok": True,
        "total_turns": total,
        "text_only_turns": text_only,
        "text_only_rate": round(rate, 4),
        "recovery_attempts": sum(1 for e in events if e.get("recovery_attempted")),
        "meets_target": rate <= target_text_only_rate() if total >= 5 else True,
        "target_rate": target_text_only_rate(),
        "fc_provider": select_fc_provider(),
        "groq_available": groq_fc_available(),
        "gemini_fc_available": gemini_fc_available(),
        "version": FAZ57_VERSION,
    }


def format_text_only_report(stats: dict[str, Any]) -> str:
    rate = float(stats.get("text_only_rate") or 0) * 100
    target = float(stats.get("target_rate") or target_text_only_rate()) * 100
    mark = "OK" if stats.get("meets_target") else "KIRMIZI"
    return (
        f"**Metin-only (Faz 57):** {rate:.1f}% / hedef <{target:.0f}% · {mark}\n"
        f"Tur: {stats.get('total_turns', 0)} · metin-only: {stats.get('text_only_turns', 0)} · "
        f"FC: `{stats.get('fc_provider', select_fc_provider())}`"
    )


def faz57_directive() -> str:
    return (
        "[MODEL YEDEK — Faz 57]\n"
        f"FC: {select_fc_provider()} (Groq yoksa Gemini function calling).\n"
        f"Metin-only hedef: <{int(target_text_only_rate() * 100)}% · log: .ruzgar/text_only_stats.json\n"
        "Kapat: RUZGAR_FAZ57=0 · Gemini FC: RUZGAR_FAZ57_GEMINI_FC=0\n"
    )
