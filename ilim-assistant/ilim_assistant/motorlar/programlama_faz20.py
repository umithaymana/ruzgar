# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 20: Cursor yolu — birleşik ajan + ruzgar-tool protokolü.

Tek sohbetten çok tur: read / write / grep / verify / run.
"""

from __future__ import annotations

import json
import os
import re
import unicodedata
from pathlib import Path
from typing import Any, Iterator

FAZ20_VERSION = "programlama-faz20-v1-2026-05-25"

_TOOL_BLOCK_RE = re.compile(
    r"```(?:ruzgar-tool|json)\s*\r?\n(\{.*?\})\r?\n```",
    re.DOTALL | re.IGNORECASE,
)
_IMPLEMENTATION_RE = re.compile(
    r"(?:yap|olustur|oluştur|ekle|duzelt|düzelt|geçir|gecir|bitir|tamamla|yaz|güncelle|guncelle|"
    r"implement|fix|add|create|build|refactor|test|pytest|calistir|çalıştır|scaffold|"
    r"endpoint|versiyon|version|patch|görev|gorev|iş:|is:|yap:)",
    re.I,
)
_QUESTION_ONLY_RE = re.compile(
    r"^(?:nedir|nasıl|nasil|ne\s+demek|açıkla|acikla|anlat|why|what\s+is)\b",
    re.I,
)


def _enabled() -> bool:
    return os.environ.get("RUZGAR_PROG_UNIFIED_AGENT", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _ascii_fold(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def unified_agent_enabled() -> bool:
    return _enabled()


def agent_auto_apply_writes() -> bool:
    """Görev döngüsünde patch doğrudan diske (Cursor gibi)."""
    return os.environ.get("RUZGAR_AGENT_AUTO_APPLY", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def tool_catalog() -> list[dict[str, str]]:
    return [
        {"id": "read", "desc": "Dosya oku — path: projects/.../dosya"},
        {"id": "write", "desc": "Dosya yaz — path, content"},
        {"id": "grep", "desc": "Proje içi ara — scope, pattern"},
        {"id": "verify", "desc": "pytest/npm — scope (proje kökü)"},
        {"id": "run", "desc": "Terminal preset — scope, preset: npm_test|npm_build|git_status"},
        {"id": "goto", "desc": "Tanıma git (LSP hafif) — scope, name"},
    ]


def faz20_tool_directive() -> str:
    lines = [
        "[RUZGAR-TOOL — Faz 20 — Cursor yolu]",
        "İş yaparken her turda bir veya daha fazla araç bloğu kullan:",
        "",
        "```ruzgar-tool",
        '{"tool":"read","path":"projects/foo/app/main.py"}',
        "```",
        "",
        "İzinli tool: read, write, grep, symbol, verify, run, goto, refs, rename",
        "write için content alanı zorunlu. grep: scope + pattern. run: preset.",
        "Plan 3 madde; sonra araçlar; gereksiz sohbet yok.",
    ]
    return "\n".join(lines)


def wants_implementation_agent(message: str, mode_norm: str = "") -> bool:
    """Kod/iş niyeti — birleşik ajan devreye girsin."""
    if not _enabled() or mode_norm != "programlama":
        return False
    raw = (message or "").strip()
    if len(raw) < 8:
        return False
    if _QUESTION_ONLY_RE.search(raw) and "@@write" not in raw.lower():
        return False
    try:
        from ilim_assistant.motorlar.programlama_faz14 import (
            wants_code_agent_status,
            wants_code_agent_stop,
        )

        if wants_code_agent_stop(raw) or wants_code_agent_status(raw):
            return False
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_motoru import is_programlama_reserved_command

        if is_programlama_reserved_command(raw):
            low = _ascii_fold(raw)
            if not any(
                k in low
                for k in (
                    "gorev:",
                    "görev:",
                    "iş:",
                    "is:",
                    "yap:",
                    "@@write",
                    "@@find",
                    "sembol",
                    "@@symbol",
                )
            ):
                return False
    except Exception:
        pass
    if "@@write" in raw.lower():
        return True
    if _IMPLEMENTATION_RE.search(raw):
        return True
    try:
        from ilim_assistant.motorlar.programlama_faz19 import parse_implicit_programming_task

        if parse_implicit_programming_task(raw):
            return True
    except Exception:
        pass
    return False


def should_run_unified_programming_agent(
    message: str,
    mode_norm: str = "",
    *,
    workspace_root: str | Path | None = None,
    active_file: str | None = None,
) -> bool:
    """Faz 33 — görev: şart değil; aktif proje + resolve_agent_task."""
    try:
        from ilim_assistant.motorlar.programlama_faz33 import should_auto_programming_agent

        return should_auto_programming_agent(
            message,
            mode_norm,
            workspace_root=workspace_root,
            active_file=active_file,
        )
    except Exception:
        if not wants_implementation_agent(message, mode_norm):
            return False
        return resolve_agent_task(
            message,
            workspace_root,
            active_file=active_file,
            mode_norm=mode_norm,
        ) is not None


def resolve_agent_task(
    message: str,
    workspace_root: str | Path | None,
    *,
    active_file: str | None = None,
    mode_norm: str = "programlama",
) -> Any | None:
    from ilim_assistant.motorlar.programlama_faz19 import normalize_agent_message
    from ilim_assistant.motorlar.programlama_faz14 import CodeAgentTask, parse_code_agent_task
    from ilim_assistant.motorlar.programlama_faz13 import resolve_scope_rel

    msg = normalize_agent_message(message, mode_norm=mode_norm)
    task = parse_code_agent_task(msg)
    if task:
        return task
    scope = resolve_scope_rel(workspace_root, active_file=active_file, message=message)
    if not scope:
        return None
    slug = scope.split("/")[-1] if "/" in scope else scope
    goal = (message or "").strip()
    return CodeAgentTask(scope_rel=scope, goal=goal, project_slug=slug)


def _parse_tool_obj(raw: str) -> dict[str, Any] | None:
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None


def extract_tool_calls(text: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for m in _TOOL_BLOCK_RE.finditer(text or ""):
        data = _parse_tool_obj(m.group(1))
        if data and data.get("tool"):
            out.append(data)
    return out


def execute_tool(
    spec: dict[str, Any],
    workspace_root: str | Path | None,
    *,
    scope_rel: str | None = None,
) -> dict[str, Any]:
    """Tek araç çağrısı — sonuç LLM'e geri beslenir."""
    tool = str(spec.get("tool") or "").strip().lower()
    try:
        if tool == "read":
            from ilim_assistant.motorlar.programlama_motoru import ProgramlamaAraclari

            path = str(spec.get("path") or "")
            rep = ProgramlamaAraclari(workspace_root).read(path, max_chars=14000)
            return {
                "ok": rep.ok,
                "tool": tool,
                "output": rep.content if rep.ok else rep.error or "",
            }

        if tool == "write":
            from ilim_assistant.motorlar.programlama_motoru import ProgramlamaAraclari

            path = str(spec.get("path") or "")
            content = str(spec.get("content") or "")
            rep = ProgramlamaAraclari(workspace_root).write(path, content)
            return {
                "ok": rep.ok,
                "tool": tool,
                "path": path,
                "output": rep.detail,
            }

        if tool == "grep":
            from ilim_assistant.motorlar.programlama_faz13 import search_in_project

            scope = str(spec.get("scope") or scope_rel or "")
            pat = str(spec.get("pattern") or spec.get("query") or "")
            res = search_in_project(workspace_root, scope, pat, max_hits=12)
            lines = []
            for h in res.get("hits") or []:
                rel = h.get("rel") or h.get("path") or "?"
                lines.append(f"{rel}:{h.get('line')}: {str(h.get('text') or '')[:120]}")
            return {
                "ok": bool(res.get("ok")),
                "tool": tool,
                "output": "\n".join(lines) or str(res.get("error") or "sonuç yok"),
            }

        if tool == "symbol":
            from ilim_assistant.motorlar.programlama_faz22 import (
                format_symbol_report,
                lookup_symbols,
            )

            scope = str(spec.get("scope") or scope_rel or "")
            name = str(spec.get("name") or spec.get("query") or spec.get("pattern") or "")
            res = lookup_symbols(workspace_root, scope, name, max_hits=16)
            return {
                "ok": bool(res.get("ok")),
                "tool": tool,
                "output": format_symbol_report(res)[:8000],
            }

        if tool == "verify":
            from ilim_assistant.motorlar.programlama_faz14 import run_project_verify

            scope = str(spec.get("scope") or scope_rel or "")
            rep = run_project_verify(workspace_root, scope, goal=str(spec.get("goal") or ""))
            if rep is None:
                return {"ok": False, "tool": tool, "output": "verify atlanamadı"}
            return {
                "ok": rep.ok,
                "tool": tool,
                "output": (rep.output or "")[:8000],
                "exit_code": rep.exit_code,
            }

        if tool == "run":
            scope = str(spec.get("scope") or scope_rel or "")
            preset = str(spec.get("preset") or spec.get("cmd") or "npm_test")
            try:
                from ilim_assistant.motorlar.programlama_faz43 import run_terminal_v3

                res = run_terminal_v3(workspace_root, preset, scope_rel=scope)
            except Exception:
                from ilim_assistant.motorlar.programlama_faz15 import run_terminal_preset

                res = run_terminal_preset(workspace_root, preset, scope_rel=scope)
            return {
                "ok": bool(res.get("ok")),
                "tool": tool,
                "output": str(res.get("output") or res.get("error") or "")[:8000],
            }

        if tool == "goto":
            from ilim_assistant.motorlar.programlama_faz36 import execute_goto_tool

            scope = str(spec.get("scope") or scope_rel or "")
            name = str(spec.get("name") or spec.get("query") or spec.get("pattern") or "")
            return execute_goto_tool(workspace_root, scope, name)

        if tool == "refs":
            from ilim_assistant.motorlar.programlama_faz42 import execute_refs_tool

            scope = str(spec.get("scope") or scope_rel or "")
            name = str(spec.get("name") or spec.get("query") or "")
            return execute_refs_tool(workspace_root, scope, name)

        if tool == "rename":
            from ilim_assistant.motorlar.programlama_faz42 import execute_rename_tool

            scope = str(spec.get("scope") or scope_rel or "")
            old = str(spec.get("old") or spec.get("name") or "")
            new = str(spec.get("new") or spec.get("to") or "")
            rel = str(spec.get("path") or spec.get("rel") or "") or None
            return execute_rename_tool(
                workspace_root, scope, old, new, rel_path=rel
            )

        if tool in ("import_graph", "importgraph"):
            from ilim_assistant.motorlar.programlama_faz42 import (
                build_import_graph,
                format_import_graph_report,
            )

            scope = str(spec.get("scope") or scope_rel or "")
            return {
                "ok": True,
                "tool": "import_graph",
                "output": format_import_graph_report(
                    build_import_graph(workspace_root, scope)
                )[:8000],
            }

        return {"ok": False, "tool": tool, "output": f"Bilinmeyen araç: {tool}"}
    except Exception as exc:
        return {"ok": False, "tool": tool, "output": str(exc)[:500]}


def run_tools_from_reply(
    reply: str,
    workspace_root: str | Path | None,
    *,
    scope_rel: str | None = None,
) -> tuple[list[dict[str, Any]], str]:
    """Tüm tool bloklarını çalıştır; özet metin döner."""
    calls = extract_tool_calls(reply)
    if not calls:
        return [], ""
    results: list[dict[str, Any]] = []
    blocks: list[str] = ["[ARAÇ SONUÇLARI]"]
    for i, spec in enumerate(calls, 1):
        res = execute_tool(spec, workspace_root, scope_rel=scope_rel)
        results.append(res)
        mark = "OK" if res.get("ok") else "HATA"
        blocks.append(
            f"{i}. {res.get('tool')} [{mark}]\n```text\n{str(res.get('output') or '')[:4000]}\n```"
        )
    return results, "\n\n".join(blocks)


def augment_agent_system(system: str) -> str:
    out = (system or "").rstrip() + "\n\n" + faz20_tool_directive() + "\n"
    try:
        from ilim_assistant.motorlar.programlama_faz40 import faz40_directive

        out = out.rstrip() + "\n\n" + faz40_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz34 import augment_agent_system as _f34

        out = _f34(out)
    except Exception:
        pass
    return out


def iter_unified_programming_agent_events(
    *,
    message: str,
    req: Any,
    system: str,
    user_payload: str,
    model: str,
    prior: list,
    mode_norm: str,
    coding: bool,
    turn_plan: Any | None,
    hits: list,
    new_wake: bool,
    orch: dict[str, Any] | None,
    delegated_from_genel: bool = False,
) -> Iterator[dict[str, Any]]:
    """
    Faz 20 giriş — Faz 14 döngüsünü birleşik ajan + araç sonuçları ile sarar.
    """
    from ilim_assistant.motorlar.programlama_faz14 import (
        build_compact_agent_system,
        iter_code_agent_turn_events,
    )

    task = resolve_agent_task(
        message,
        req.workspace_root,
        active_file=getattr(req, "programlama_active_file", None),
        mode_norm=mode_norm,
    )
    if task is None:
        yield {"type": "error", "text": "Proje odakı yok — `projects/<ad>/` açın veya yol yazın."}
        return

    try:
        from ilim_assistant.motorlar.programlama_faz23 import (
            code_agent_budget_sec,
            enter_task_mode,
            exit_task_mode,
            format_task_mode_status,
        )

        enter_task_mode()
        yield {
            "type": "status",
            "text": format_task_mode_status(task.scope_rel, code_agent_budget_sec()),
        }
    except Exception:
        enter_task_mode = exit_task_mode = None  # type: ignore

    if agent_auto_apply_writes():
        os.environ["RUZGAR_FAZ10_AUTO_PATCH"] = "1"

    norm_msg = message
    try:
        from ilim_assistant.motorlar.programlama_faz33 import normalize_for_agent

        norm_msg = normalize_for_agent(
            message,
            mode_norm,
            workspace_root=req.workspace_root,
            active_file=getattr(req, "programlama_active_file", None),
        )
    except Exception:
        try:
            from ilim_assistant.motorlar.programlama_faz19 import normalize_agent_message

            norm_msg = normalize_agent_message(message, mode_norm=mode_norm)
        except Exception:
            pass

    yield {
        "type": "status",
        "text": (
            f"Cursor yolu ajan (Faz 20) — `{task.scope_rel}` — "
            "araçlar: read/write/grep/verify/run…"
        ),
    }
    yield {
        "type": "meta",
        "code_agent": {
            "phase": "unified_faz20",
            "scope_rel": task.scope_rel,
            "goal": task.goal,
            "version": FAZ20_VERSION,
        },
    }

    agent_system = augment_agent_system(build_compact_agent_system(req.workspace_root, task))

    try:
        for ev in iter_code_agent_turn_events(
            message=norm_msg,
            req=req,
            system=agent_system,
            user_payload=user_payload,
            model=model,
            prior=prior,
            mode_norm=mode_norm,
            coding=coding,
            turn_plan=turn_plan,
            hits=hits,
            new_wake=new_wake,
            orch=orch,
            delegated_from_genel=delegated_from_genel,
        ):
            if ev.get("type") == "token":
                body = str(ev.get("text") or "")
                if body:
                    yield ev
                continue
            if ev.get("type") == "done":
                full = str(ev.get("full_reply") or "")
                tool_results, tool_block = run_tools_from_reply(
                    full,
                    req.workspace_root,
                    scope_rel=task.scope_rel,
                )
                try:
                    from ilim_assistant.motorlar.programlama_faz34 import apply_turn_tool_first

                    tool_results, faz34_block, _ = apply_turn_tool_first(
                        tool_results,
                        full,
                        req.workspace_root,
                        task.scope_rel,
                        task.goal,
                        1,
                    )
                    if faz34_block:
                        tool_block = (tool_block or "").rstrip() + "\n\n" + faz34_block
                except Exception:
                    pass
                if tool_block and tool_results:
                    extra_tools = sum(
                        1 for r in tool_results if r.get("tool") == "write" and r.get("ok")
                    )
                    ev = dict(ev)
                    ev["full_reply"] = full.rstrip() + "\n\n" + tool_block
                    ev.setdefault("meta", {})["faz20_tools"] = len(tool_results)
                    if extra_tools:
                        ev["code_agent"] = dict(ev.get("code_agent") or {})
                        ev["code_agent"]["faz20_tool_writes"] = extra_tools
                yield ev
                continue
            yield ev
    finally:
        try:
            from ilim_assistant.motorlar.programlama_faz23 import exit_task_mode

            exit_task_mode()
        except Exception:
            pass
