# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 42: LSP v2 (referanslar, yeniden adlandırma, import grafı).

Faz 36 goto üzerine: find references, güvenli rename (tek dosya / tanım dosyası).
"""

from __future__ import annotations

import os
import re
import unicodedata
from pathlib import Path
from typing import Any

FAZ42_VERSION = "programlama-faz42-v1-2026-05-25"

_REFS_RE = re.compile(
    r"(?:referanslar|referans|refs|kullanimlar|kullanımlar)\s*[:\"]?\s*([\w.\-$]{1,80})",
    re.I,
)
_RENAME_RE = re.compile(
    r"(?:yeniden\s+adlandir|yeniden\s+adlandır|rename|adlandir)\s+"
    r"([\w.\-$]{1,80})\s*(?:->|→|,|to)\s*([\w.\-$]{1,80})",
    re.I,
)
_IMPORT_GRAPH_RE = re.compile(
    r"(?:import\s+graf|import\s+graph|bagimlilik\s+graf|bağımlılık\s+graf)",
    re.I,
)
_PY_IMPORT_RE = re.compile(
    r"^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))",
    re.M,
)
_IDENT_RE = re.compile(r"^[A-Za-z_][\w$]{0,79}$")


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ42", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def lsp_v2_enabled() -> bool:
    return _enabled()


def _ascii_fold(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def parse_refs_query(message: str) -> str | None:
    m = _REFS_RE.search(message or "")
    if m:
        return m.group(1).strip()
    low = _ascii_fold(message)
    if low.startswith("refs "):
        parts = (message or "").strip().split(None, 1)
        if len(parts) >= 2:
            return parts[1].strip()
    return None


def parse_rename_query(message: str) -> tuple[str, str] | None:
    m = _RENAME_RE.search(message or "")
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return None


def wants_find_references(message: str) -> bool:
    if not lsp_v2_enabled():
        return False
    return bool(parse_refs_query(message))


def wants_rename_symbol(message: str) -> bool:
    if not lsp_v2_enabled():
        return False
    return bool(parse_rename_query(message))


def wants_import_graph(message: str) -> bool:
    if not lsp_v2_enabled():
        return False
    return bool(_IMPORT_GRAPH_RE.search(message or ""))


def find_references(
    workspace_root: str | Path | None,
    scope_rel: str,
    symbol_name: str,
    *,
    max_hits: int = 40,
) -> dict[str, Any]:
    """Proje içinde sembol kullanım satırları."""
    name = (symbol_name or "").strip()
    scope = (scope_rel or "").strip().replace("\\", "/")
    if not name or not scope:
        return {"ok": False, "error": "scope veya sembol eksik"}

    try:
        from ilim_assistant.motorlar.programlama_faz22 import (
            _iter_code_files,
            build_symbol_index,
        )

        build_symbol_index(workspace_root, scope)
        word = re.compile(rf"\b{re.escape(name)}\b")
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:200]}

    hits: list[dict[str, Any]] = []
    try:
        from ilim_assistant.motorlar.programlama_motoru import ProgramlamaAraclari, repo_root

        root = repo_root(workspace_root)
        if root is None:
            return {"ok": False, "error": "workspace yok"}
        for rel in _iter_code_files(workspace_root, scope, max_files=60):
            fp = root / rel.replace("/", os.sep)
            try:
                body = fp.read_text(encoding="utf-8", errors="replace")[:80_000]
            except OSError:
                continue
            for i, line in enumerate(body.splitlines(), 1):
                if word.search(line):
                    hits.append(
                        {
                            "rel": rel,
                            "line": i,
                            "text": line.strip()[:160],
                            "name": name,
                        }
                    )
                    if len(hits) >= max_hits:
                        break
            if len(hits) >= max_hits:
                break
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:200]}

    return {
        "ok": True,
        "scope_rel": scope,
        "query": name,
        "hits": hits,
        "count": len(hits),
        "version": FAZ42_VERSION,
    }


def rename_symbol(
    workspace_root: str | Path | None,
    scope_rel: str,
    old_name: str,
    new_name: str,
    *,
    rel_path: str | None = None,
    max_replacements: int = 40,
) -> dict[str, Any]:
    """Güvenli yeniden adlandırma — varsayılan: tanım dosyası veya tek rel."""
    old = (old_name or "").strip()
    new = (new_name or "").strip()
    scope = (scope_rel or "").strip().replace("\\", "/")
    if not old or not new or not scope:
        return {"ok": False, "error": "eski/yeni ad veya scope eksik"}
    if not _IDENT_RE.match(old) or not _IDENT_RE.match(new):
        return {"ok": False, "error": "geçersiz tanımlayıcı adı"}

    target_rel = (rel_path or "").strip().replace("\\", "/")
    if not target_rel:
        try:
            from ilim_assistant.motorlar.programlama_faz36 import goto_definition

            g = goto_definition(workspace_root, scope, old)
            if g.get("ok"):
                target_rel = str(g.get("focus_path") or (g.get("primary") or {}).get("rel") or "")
        except Exception:
            target_rel = ""
    if not target_rel:
        return {"ok": False, "error": "hedef dosya bulunamadı — `rel:` ile belirtin"}

    try:
        from ilim_assistant.motorlar.programlama_motoru import ProgramlamaAraclari

        tools = ProgramlamaAraclari(workspace_root)
        rep = tools.read(target_rel, max_chars=120_000)
        if not rep.ok or not rep.content:
            return {"ok": False, "error": rep.error or "dosya okunamadı"}
        word = re.compile(rf"\b{re.escape(old)}\b")
        lines = rep.content.splitlines(keepends=True)
        count = 0
        new_lines: list[str] = []
        for line in lines:
            if count < max_replacements and word.search(line):
                new_line, n = word.subn(new, line, max_replacements - count)
                count += n
                new_lines.append(new_line)
            else:
                new_lines.append(line)
        new_body = "".join(new_lines)
        if count == 0:
            return {
                "ok": False,
                "error": f"`{old}` bu dosyada bulunamadı",
                "rel": target_rel,
            }
        wrep = tools.write(target_rel, new_body)
        return {
            "ok": wrep.ok,
            "rel": target_rel,
            "old": old,
            "new": new,
            "replacements": count,
            "detail": wrep.detail,
            "version": FAZ42_VERSION,
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:200]}


def build_import_graph(
    workspace_root: str | Path | None,
    scope_rel: str,
    *,
    max_files: int = 25,
) -> dict[str, Any]:
    """Hafif import listesi (Python öncelikli)."""
    scope = (scope_rel or "").strip().replace("\\", "/")
    try:
        from ilim_assistant.motorlar.programlama_faz22 import _iter_code_files, build_symbol_index
        from ilim_assistant.motorlar.programlama_motoru import repo_root

        build_symbol_index(workspace_root, scope)
        root = repo_root(workspace_root)
        if root is None:
            return {"ok": False, "error": "workspace yok"}
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:200]}

    edges: list[dict[str, Any]] = []
    for rel in _iter_code_files(workspace_root, scope, max_files=max_files):
        if not rel.endswith(".py"):
            continue
        fp = root / rel.replace("/", os.sep)
        try:
            body = fp.read_text(encoding="utf-8", errors="replace")[:40_000]
        except OSError:
            continue
        imports: list[str] = []
        for m in _PY_IMPORT_RE.finditer(body):
            mod = (m.group(1) or m.group(2) or "").strip()
            if mod and mod not in imports:
                imports.append(mod)
        if imports:
            edges.append({"rel": rel, "imports": imports[:12]})

    return {
        "ok": True,
        "scope_rel": scope,
        "files": len(edges),
        "edges": edges,
        "version": FAZ42_VERSION,
    }


def format_refs_report(result: dict[str, Any]) -> str:
    if not result.get("ok"):
        return f"Referans araması başarısız: {result.get('error')} ({FAZ42_VERSION})"
    name = result.get("query")
    hits = result.get("hits") or []
    lines = [
        f"Ümit abi, **referanslar** — `{name}` ({len(hits)} kullanım):",
        "",
    ]
    for h in hits[:20]:
        lines.append(f"· `{h.get('rel')}`:{h.get('line')} — `{h.get('text', '')[:80]}`")
    if len(hits) > 20:
        lines.append(f"… +{len(hits) - 20} satır")
    lines.append(f"\n({FAZ42_VERSION})")
    return "\n".join(lines)


def format_rename_report(result: dict[str, Any]) -> str:
    if not result.get("ok"):
        return f"Yeniden adlandırma başarısız: {result.get('error')} ({FAZ42_VERSION})"
    return (
        f"Ümit abi, **rename** `{result.get('old')}` → `{result.get('new')}`\n"
        f"Dosya: `{result.get('rel')}` · {result.get('replacements')} değişiklik\n"
        f"({FAZ42_VERSION})"
    )


def format_import_graph_report(result: dict[str, Any]) -> str:
    if not result.get("ok"):
        return f"Import grafı alınamadı: {result.get('error')}"
    lines = [
        f"Ümit abi, **import grafı** — `{result.get('scope_rel')}` ({result.get('files')} dosya):",
        "",
    ]
    for e in (result.get("edges") or [])[:15]:
        imps = ", ".join(e.get("imports") or [])[:100]
        lines.append(f"· `{e.get('rel')}` → {imps}")
    lines.append(f"\n({FAZ42_VERSION})")
    return "\n".join(lines)


def execute_refs_tool(
    workspace_root: str | Path | None,
    scope_rel: str,
    symbol_name: str,
) -> dict[str, Any]:
    res = find_references(workspace_root, scope_rel, symbol_name)
    return {
        "ok": bool(res.get("ok")),
        "tool": "refs",
        "output": format_refs_report(res)[:8000],
        "count": res.get("count", 0),
    }


def execute_rename_tool(
    workspace_root: str | Path | None,
    scope_rel: str,
    old_name: str,
    new_name: str,
    *,
    rel_path: str | None = None,
) -> dict[str, Any]:
    res = rename_symbol(
        workspace_root,
        scope_rel,
        old_name,
        new_name,
        rel_path=rel_path,
    )
    return {
        "ok": bool(res.get("ok")),
        "tool": "rename",
        "output": format_rename_report(res)[:8000],
        "rel": res.get("rel"),
    }


def maybe_instant_faz42(
    message: str,
    workspace_root: str | Path | None,
    *,
    active_file: str | None = None,
) -> str | None:
    if not _enabled():
        return None
    try:
        from ilim_assistant.motorlar.programlama_faz13 import resolve_scope_rel

        scope = resolve_scope_rel(
            workspace_root, active_file=active_file, message=message
        )
    except Exception:
        scope = None
    if not scope:
        return None

    if wants_import_graph(message):
        return format_import_graph_report(build_import_graph(workspace_root, scope))

    if wants_find_references(message):
        q = parse_refs_query(message)
        if q:
            return format_refs_report(find_references(workspace_root, scope, q))

    if wants_rename_symbol(message):
        pair = parse_rename_query(message)
        if pair:
            old, new = pair
            return format_rename_report(
                rename_symbol(workspace_root, scope, old, new)
            )
    return None


def faz42_directive() -> str:
    return (
        "[LSP v2 — Faz 42]\n"
        "`referanslar health` · `rename eski -> yeni` · `import graf`\n"
        "ruzgar-tool: refs, rename, import_graph\n"
        "Kapat: RUZGAR_FAZ42=0\n"
    )
