# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 36: LSP hafif (tanıma git / goto).

Sembol indeksinden tanım konumuna atlama + satır önizlemesi.
"""

from __future__ import annotations

import os
import re
import unicodedata
from pathlib import Path
from typing import Any

FAZ36_VERSION = "programlama-faz36-v1-2026-05-25"

_GOTO_RE = re.compile(
    r"(?:tanima\s+git|tanıma\s+git|goto|definisyona\s+git|definition\s+goto)\s*[:\"]?\s*([\w.\-$]{1,80})",
    re.I,
)


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ36", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def lsp_goto_enabled() -> bool:
    return _enabled()


def _ascii_fold(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def parse_goto_query(message: str) -> str | None:
    m = _GOTO_RE.search(message or "")
    if m:
        return m.group(1).strip()
    low = _ascii_fold(message)
    if low.startswith("goto "):
        parts = (message or "").strip().split(None, 1)
        if len(parts) >= 2:
            return parts[1].strip().strip(":").strip('"')
    return None


def wants_goto_definition(message: str) -> bool:
    if not lsp_goto_enabled():
        return False
    return bool(parse_goto_query(message))


def goto_definition(
    workspace_root: str | Path | None,
    scope_rel: str,
    symbol_name: str,
    *,
    context_lines: int = 8,
) -> dict[str, Any]:
    """İlk tanım + çevre satırlar."""
    name = (symbol_name or "").strip()
    scope = (scope_rel or "").strip().replace("\\", "/")
    if not name or not scope:
        return {"ok": False, "error": "scope veya sembol eksik"}

    try:
        from ilim_assistant.motorlar.programlama_faz22 import lookup_symbols

        res = lookup_symbols(workspace_root, scope, name, max_hits=4)
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:200]}

    hits = res.get("hits") or []
    if not hits:
        return {
            "ok": False,
            "error": "tanım bulunamadı",
            "scope_rel": scope,
            "query": name,
        }

    primary = hits[0]
    rel = str(primary.get("rel") or "")
    line_no = int(primary.get("line") or 1)
    preview = ""
    try:
        from ilim_assistant.motorlar.programlama_motoru import ProgramlamaAraclari

        tools = ProgramlamaAraclari(workspace_root)
        rep = tools.read(rel, max_chars=12000)
        if rep.ok and rep.content:
            lines = rep.content.splitlines()
            start = max(0, line_no - 1 - context_lines)
            end = min(len(lines), line_no + context_lines)
            snippet_lines = []
            for i in range(start, end):
                mark = ">>>" if i == line_no - 1 else "   "
                snippet_lines.append(f"{mark} {i + 1:4d}| {lines[i]}")
            preview = "\n".join(snippet_lines)
    except Exception:
        preview = ""

    return {
        "ok": True,
        "scope_rel": scope,
        "query": name,
        "primary": primary,
        "hits": hits,
        "preview": preview,
        "focus_path": rel,
        "line": line_no,
        "version": FAZ36_VERSION,
    }


def format_goto_report(result: dict[str, Any]) -> str:
    if not result.get("ok"):
        return (
            f"Ümit abi, tanım bulunamadı: `{result.get('query')}` "
            f"({result.get('error')}). `sembol indeks yenile` deneyin.\n"
            f"({FAZ36_VERSION})"
        )
    p = result.get("primary") or {}
    rel = p.get("rel") or result.get("focus_path") or "?"
    line = int(result.get("line") or p.get("line") or 0)
    kind = p.get("kind") or "symbol"
    name = p.get("name") or result.get("query")
    lines = [
        f"Ümit abi, **tanıma git** — `{name}` ({kind}):",
        "",
        f"Konum: `{rel}` satır **{line}**",
        "",
    ]
    prev = (result.get("preview") or "").strip()
    if prev:
        lines.append("```\n" + prev[:6000] + "\n```")
    extra = result.get("hits") or []
    if len(extra) > 1:
        lines.append("")
        lines.append("Diğer eşleşmeler:")
        for h in extra[1:4]:
            lines.append(
                f"· `{h.get('rel')}`:{h.get('line')} — {h.get('name')} ({h.get('kind')})"
            )
    lines.append(f"\n({FAZ36_VERSION})")
    return "\n".join(lines)


def execute_goto_tool(
    workspace_root: str | Path | None,
    scope_rel: str,
    symbol_name: str,
) -> dict[str, Any]:
    res = goto_definition(workspace_root, scope_rel, symbol_name)
    return {
        "ok": bool(res.get("ok")),
        "tool": "goto",
        "output": format_goto_report(res)[:8000],
        "focus_path": res.get("focus_path"),
        "line": res.get("line"),
    }


def maybe_instant_faz36(
    message: str,
    workspace_root: str | Path | None,
    *,
    active_file: str | None = None,
) -> str | None:
    if not _enabled() or not wants_goto_definition(message):
        return None
    q = parse_goto_query(message)
    if not q:
        return "Ümit abi, `tanıma git health` veya `goto health` yazın."
    try:
        from ilim_assistant.motorlar.programlama_faz13 import resolve_scope_rel

        scope = resolve_scope_rel(
            workspace_root, active_file=active_file, message=message
        )
    except Exception:
        scope = None
    if not scope:
        return "Ümit abi, `projects/<proje>/` açın veya yol yazın."
    return format_goto_report(goto_definition(workspace_root, scope, q))


def faz36_directive() -> str:
    return (
        "[LSP HAFİF — Faz 36]\n"
        "`tanıma git <sembol>` · `goto <ad>` — tanım satırı + önizleme.\n"
        "ruzgar-tool: `{\"tool\":\"goto\",\"scope\":\"projects/x\",\"name\":\"health\"}`\n"
    )
