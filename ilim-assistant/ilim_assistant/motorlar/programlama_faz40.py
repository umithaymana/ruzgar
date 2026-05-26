# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 40: Yapılandırılmış araç API (OpenAI tools).

Birincil yol: Groq/OpenAI function calling → sunucu execute_tool.
Yedek: ruzgar-tool blokları ve @@write (Faz 20).
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Callable

FAZ40_VERSION = "programlama-faz40-v1-2026-05-25"

_TOOL_CALLS_JSON_RE = re.compile(
    r"```(?:ruzgar-tools|json)\s*\r?\n(\{.*?\})\r?\n```",
    re.DOTALL | re.IGNORECASE,
)


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ40", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def structured_tools_enabled() -> bool:
    return _enabled()


def tool_api_mode() -> str:
    return (os.environ.get("RUZGAR_TOOL_API", "openai") or "openai").strip().lower()


def max_tool_api_rounds() -> int:
    try:
        return max(1, min(int(os.environ.get("RUZGAR_FAZ40_MAX_ROUNDS", "6")), 8))
    except ValueError:
        return 6


def openai_tools_schema() -> list[dict[str, Any]]:
    """OpenAI / Groq tools dizisi."""
    return [
        {
            "type": "function",
            "function": {
                "name": "read",
                "description": "Proje dosyası oku (projects/... yolu)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "projects/foo/app/main.py"},
                    },
                    "required": ["path"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "write",
                "description": "Dosya yaz veya güncelle",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "content": {"type": "string"},
                    },
                    "required": ["path", "content"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "grep",
                "description": "Proje içi metin ara",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "scope": {"type": "string"},
                        "pattern": {"type": "string"},
                    },
                    "required": ["scope", "pattern"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "verify",
                "description": "pytest veya npm test çalıştır",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "scope": {"type": "string"},
                    },
                    "required": ["scope"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "run",
                "description": "Terminal preset (npm_build, npm_test, git_status)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "scope": {"type": "string"},
                        "preset": {"type": "string"},
                    },
                    "required": ["scope", "preset"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "goto",
                "description": "Sembol tanımına git",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "scope": {"type": "string"},
                        "name": {"type": "string"},
                    },
                    "required": ["scope", "name"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "refs",
                "description": "Sembol referanslarını bul",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "scope": {"type": "string"},
                        "name": {"type": "string"},
                    },
                    "required": ["scope", "name"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "rename",
                "description": "Sembolü yeniden adlandır (tek dosya)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "scope": {"type": "string"},
                        "old": {"type": "string"},
                        "new": {"type": "string"},
                        "path": {"type": "string"},
                    },
                    "required": ["scope", "old", "new"],
                },
            },
        },
    ]


def _spec_from_openai_call(call: dict[str, Any]) -> dict[str, Any] | None:
    fn = call.get("function") or {}
    name = str(fn.get("name") or call.get("name") or "").strip().lower()
    if not name:
        return None
    raw_args = fn.get("arguments") or call.get("arguments") or "{}"
    if isinstance(raw_args, dict):
        args = raw_args
    else:
        try:
            args = json.loads(str(raw_args))
        except json.JSONDecodeError:
            args = {}
    if not isinstance(args, dict):
        args = {}
    spec: dict[str, Any] = {"tool": name, **args}
    return spec


def extract_tool_invocations(text: str) -> list[dict[str, Any]]:
    """ruzgar-tool + ruzgar-tools JSON + OpenAI tool_calls satırları."""
    from ilim_assistant.motorlar.programlama_faz20 import extract_tool_calls

    out: list[dict[str, Any]] = []
    seen: set[str] = set()

    def _add(spec: dict[str, Any] | None) -> None:
        if not spec or not spec.get("tool"):
            return
        key = json.dumps(spec, sort_keys=True, ensure_ascii=False)[:200]
        if key in seen:
            return
        seen.add(key)
        out.append(spec)

    for spec in extract_tool_calls(text or ""):
        _add(spec)

    for m in _TOOL_CALLS_JSON_RE.finditer(text or ""):
        try:
            data = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            calls = data.get("tool_calls") or data.get("calls") or []
            if isinstance(calls, list):
                for c in calls:
                    if isinstance(c, dict):
                        _add(_spec_from_openai_call(c))

    return out


def _format_tool_block(results: list[dict[str, Any]], *, tag: str = "") -> str:
    if not results:
        return ""
    lines = [f"[ARAÇ SONUÇLARI — Faz 40{(' ' + tag) if tag else ''}]"]
    for i, res in enumerate(results, 1):
        mark = "OK" if res.get("ok") else "HATA"
        lines.append(
            f"{i}. {res.get('tool')} [{mark}]\n```text\n"
            f"{str(res.get('output') or '')[:4000]}\n```"
        )
    return "\n\n".join(lines)


def run_tool_specs(
    specs: list[dict[str, Any]],
    workspace_root: Any,
    *,
    scope_rel: str | None = None,
) -> list[dict[str, Any]]:
    from ilim_assistant.motorlar.programlama_faz20 import execute_tool

    results: list[dict[str, Any]] = []
    for spec in specs:
        results.append(execute_tool(spec, workspace_root, scope_rel=scope_rel))
    return results


def process_llm_tools(
    reply: str,
    workspace_root: Any,
    *,
    scope_rel: str | None = None,
    goal: str = "",
) -> tuple[list[dict[str, Any]], str]:
    """
    Tüm formatlardan araç çıkar ve çalıştır.
    Hiç araç yoksa Faz 34 keşif specs (hedef varsa).
    """
    specs = extract_tool_invocations(reply)
    if not specs and goal.strip():
        try:
            from ilim_assistant.motorlar.programlama_faz34 import discovery_tool_specs

            specs = discovery_tool_specs(
                workspace_root,
                scope_rel or "",
                goal=goal,
            )[:4]
        except Exception:
            pass
    results = run_tool_specs(specs, workspace_root, scope_rel=scope_rel)
    block = _format_tool_block(results)
    return results, block


def _groq_endpoint() -> tuple[str, str, str] | None:
    key = (os.environ.get("GROQ_API_KEY") or "").strip()
    if not key:
        return None
    base = (os.environ.get("GROQ_API_BASE") or "https://api.groq.com/openai/v1").rstrip("/")
    model = (os.environ.get("GROQ_MODEL") or "llama-3.3-70b-versatile").strip()
    return base, key, model


def chat_completion_with_tools(
    system: str,
    user: str,
    *,
    prior_messages: list | None = None,
    scope_rel: str = "",
    tool_choice: str = "auto",
) -> tuple[str, list[dict[str, Any]]]:
    """
    Groq OpenAI tools — tek tur completion + tool_calls parse.
    Dönüş: (assistant_text, tool_results_executed)
    """
    ep = _groq_endpoint()
    if ep is None or tool_api_mode() != "openai":
        return "", []
    base, key, model = ep
    try:
        import requests
        from ilim_assistant.llm_ollama import _build_chat_messages

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
        raw_calls = msg.get("tool_calls") or []
        specs: list[dict[str, Any]] = []
        for c in raw_calls:
            if isinstance(c, dict):
                spec = _spec_from_openai_call(c)
                if spec:
                    specs.append(spec)
        results: list[dict[str, Any]] = []
        if specs:
            from ilim_assistant.motorlar.programlama_motoru import repo_root

            root = repo_root(None)
            results = run_tool_specs(specs, root, scope_rel=scope_rel or None)
        return content, results
    except Exception as exc:
        return f"[Faz 40 tools: {str(exc)[:200]}]", []


def run_structured_tool_loop(
    *,
    system: str,
    user: str,
    workspace_root: Any,
    scope_rel: str,
    goal: str,
    prior_messages: list | None = None,
    has_write_fn: Callable[[str, list[dict[str, Any]]], bool] | None = None,
    tool_choice: str = "auto",
) -> tuple[str, list[dict[str, Any]], str]:
    """
    LLM ↔ araç döngüsü (max RUZGAR_FAZ40_MAX_ROUNDS).
    Dönüş: (combined_text, all_tool_results, tool_block)
    """
    if not structured_tools_enabled():
        results, block = process_llm_tools("", workspace_root, scope_rel=scope_rel, goal=goal)
        return "", results, block

    def _has_write(body: str, tools: list[dict[str, Any]]) -> bool:
        if has_write_fn:
            return has_write_fn(body, tools)
        if any(str(t.get("tool")) == "write" and t.get("ok") for t in tools):
            return True
        return "@@write" in (body or "").lower()

    all_results: list[dict[str, Any]] = []
    texts: list[str] = []
    cur_user = user
    extra_prior = list(prior_messages or [])

    tc = (tool_choice or "auto").strip().lower()
    if tc not in ("auto", "required", "none"):
        tc = "auto"

    for rnd in range(max_tool_api_rounds()):
        round_tc = tc
        if rnd > 0 and tc == "auto":
            try:
                from ilim_assistant.motorlar.programlama_faz52 import (
                    faz52_enabled,
                    tool_choice_for_task,
                )

                if faz52_enabled() and not _has_write("\n".join(texts), all_results):
                    round_tc = tool_choice_for_task(recovery=True)
            except Exception:
                pass
        text, batch = chat_completion_with_tools(
            system,
            cur_user,
            prior_messages=extra_prior if rnd == 0 else extra_prior,
            scope_rel=scope_rel,
            tool_choice=round_tc,
        )
        if text:
            texts.append(text)
        if batch:
            all_results.extend(batch)
            extra_prior = extra_prior + [
                {"role": "assistant", "content": text or "(araç çağrısı)"},
                {
                    "role": "user",
                    "content": _format_tool_block(batch, tag=f"round {rnd + 1}")
                    + "\nDevam: hedefe uygun write/verify.",
                },
            ]
        inv = extract_tool_invocations(text or "")
        if inv:
            more = run_tool_specs(inv, workspace_root, scope_rel=scope_rel)
            all_results.extend(more)
        if _has_write("\n".join(texts), all_results):
            break
        if not batch and not inv:
            break
        cur_user = (
            f"[Faz 40 tur {rnd + 2}] Hedef: {goal}\n"
            "Son araç sonuçlarına göre write ve verify yap."
        )

    block = _format_tool_block(all_results, tag="structured")
    combined = "\n\n".join(t for t in texts if t.strip())
    if block and block not in combined:
        combined = (combined.rstrip() + "\n\n" + block) if combined else block
    return combined, all_results, block


def augment_reply_tools(
    reply: str,
    workspace_root: Any,
    *,
    scope_rel: str | None = None,
    goal: str = "",
) -> tuple[str, list[dict[str, Any]], str]:
    """
    Faz 20 run_tools_from_reply yerine / üzerine — tüm formatlar + keşif.
    """
    results, block = process_llm_tools(
        reply, workspace_root, scope_rel=scope_rel, goal=goal
    )
    merged_reply = reply
    if block and block not in (reply or ""):
        merged_reply = (reply or "").rstrip() + "\n\n" + block
    return merged_reply, results, block


def faz40_directive() -> str:
    return (
        "[YAPILANDIRILMIŞ ARAÇ — Faz 40]\n"
        "Birincil: model function calling (read/write/grep/verify/run/goto).\n"
        "Yedek: ```ruzgar-tool``` veya ```ruzgar-tools\\n"
        '{"tool_calls":[{"name":"write",...}]}\n```\n'
        "Kapat: RUZGAR_FAZ40=0 · API: RUZGAR_TOOL_API=openai\n"
    )
