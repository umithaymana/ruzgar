# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 44: Bağlam v3 (repo haritası, @dosya, ilgili dosyalar).

Görev/LLM turu başında kompakt ağaç + son değişenler + anahtar kelime dosya seçimi.
"""

from __future__ import annotations

import os
import re
import time
import unicodedata
from pathlib import Path
from typing import Any

FAZ44_VERSION = "programlama-faz44-v1-2026-05-25"

_AT_REF_RE = re.compile(
    r"@(?:dosya|klasor|klasör|file|folder)\s*[:\"]?\s*([^\s\n,;]+)",
    re.I,
)
_AT_PATH_RE = re.compile(
    r"@((?:projects/)[\w.\-/\\]+(?:\.[a-zA-Z0-9]{1,8})?/?)",
    re.I,
)
_MAP_CMD_RE = re.compile(
    r"(?:repo\s+harita|proje\s+harita|baglam\s+v3|context\s+map|baglam\s+harita)",
    re.I,
)
_SKIP = frozenset(
    {
        ".git",
        ".cursor",
        ".ruzgar",
        ".venv",
        "venv",
        "__pycache__",
        "node_modules",
        "dist",
        "build",
        ".pytest_cache",
    }
)


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ44", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def context_v3_enabled() -> bool:
    return _enabled()


def _ascii_fold(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def _norm_rel(rel: str) -> str:
    return (rel or "").strip().replace("\\", "/").lstrip("/")


def build_project_tree_map(
    workspace_root: str | Path | None,
    scope_rel: str,
    *,
    max_depth: int = 3,
    max_lines: int = 55,
) -> str:
    """projects/<ad>/ dizin ağacı (sığ)."""
    from ilim_assistant.motorlar.programlama_motoru import repo_root

    root = repo_root(workspace_root)
    scope = _norm_rel(scope_rel)
    if root is None or not scope:
        return ""
    base = root / scope.replace("/", os.sep)
    if not base.is_dir():
        return ""

    lines: list[str] = [f"[REPO HARİTASI — {scope}]"]

    def walk(dir_path: Path, prefix: str, depth: int) -> None:
        if depth > max_depth or len(lines) >= max_lines:
            return
        try:
            entries = sorted(
                dir_path.iterdir(),
                key=lambda p: (not p.is_dir(), p.name.lower()),
            )
        except OSError:
            return
        for i, child in enumerate(entries):
            if len(lines) >= max_lines:
                lines.append(f"{prefix}…")
                return
            if child.name in _SKIP or child.name.startswith("."):
                continue
            is_last = i == len(entries) - 1
            branch = "└── " if is_last else "├── "
            tag = "/" if child.is_dir() else ""
            lines.append(f"{prefix}{branch}{child.name}{tag}")
            if child.is_dir():
                ext = "    " if is_last else "│   "
                walk(child, prefix + ext, depth + 1)

    walk(base, "", 0)
    return "\n".join(lines)


def recent_changed_files(
    workspace_root: str | Path | None,
    scope_rel: str,
    *,
    limit: int = 12,
    within_sec: float = 86400 * 7,
) -> list[dict[str, Any]]:
    from ilim_assistant.motorlar.programlama_motoru import repo_root

    root = repo_root(workspace_root)
    scope = _norm_rel(scope_rel)
    if root is None:
        return []
    base = root / scope.replace("/", os.sep)
    if not base.is_dir():
        return []
    now = time.time()
    rows: list[dict[str, Any]] = []
    for fp in base.rglob("*"):
        if len(rows) > 400:
            break
        if not fp.is_file():
            continue
        parts = fp.relative_to(root).parts
        if any(p in _SKIP for p in parts):
            continue
        try:
            mt = fp.stat().st_mtime
        except OSError:
            continue
        if now - mt > within_sec:
            continue
        rel = _norm_rel(str(fp.relative_to(root)).replace("\\", "/"))
        rows.append({"rel": rel, "mtime": mt, "size": fp.stat().st_size})
    rows.sort(key=lambda x: -float(x["mtime"]))
    return rows[:limit]


def format_recent_block(files: list[dict[str, Any]]) -> str:
    if not files:
        return "[SON DEĞİŞEN] (kayıt yok)"
    lines = ["[SON DEĞİŞEN DOSYALAR]"]
    for f in files:
        age_h = int((time.time() - float(f["mtime"])) / 3600)
        lines.append(f"· `{f['rel']}` ({age_h} sa önce)")
    return "\n".join(lines)


def parse_at_refs(message: str) -> list[str]:
    """@dosya yolları ve @projects/... kısayolları."""
    paths: list[str] = []
    seen: set[str] = set()
    for m in _AT_REF_RE.finditer(message or ""):
        p = _norm_rel(m.group(1))
        if p and p not in seen:
            seen.add(p)
            paths.append(p)
    for m in _AT_PATH_RE.finditer(message or ""):
        p = _norm_rel(m.group(1).rstrip("/"))
        if p and p not in seen:
            seen.add(p)
            paths.append(p)
    return paths


def batch_read_at_refs(
    workspace_root: str | Path | None,
    paths: list[str],
    *,
    max_files: int = 6,
    max_chars_each: int = 4000,
) -> str:
    from ilim_assistant.motorlar.programlama_motoru import ProgramlamaAraclari

    tools = ProgramlamaAraclari(workspace_root)
    lines = ["[@DOSYA OKUMA — Faz 44]"]
    for rel in paths[:max_files]:
        rep = tools.read(rel, max_chars=max_chars_each)
        if rep.ok:
            lines.append(f"\n### `{rel}`\n```\n{rep.content[:max_chars_each]}\n```")
        else:
            lines.append(f"\n### `{rel}` — HATA: {rep.error}")
    return "\n".join(lines)


def select_relevant_files(
    workspace_root: str | Path | None,
    scope_rel: str,
    message: str,
    *,
    limit: int = 8,
) -> list[str]:
    """Anahtar kelime + giriş dosyaları skoru."""
    from ilim_assistant.motorlar.programlama_faz13 import scan_project_files

    scan = scan_project_files(workspace_root, scope_rel, max_files=120)
    if not scan.get("ok"):
        return []
    files = scan.get("files") or []
    low = _ascii_fold(message)
    tokens = [t for t in re.split(r"[^\w]+", low) if len(t) >= 3]
    entry_hints = (
        "main",
        "app",
        "index",
        "server",
        "health",
        "api",
        "test",
        "routes",
    )

    scored: list[tuple[float, str]] = []
    for f in files:
        rel = str(f.get("rel") or "")
        rlow = _ascii_fold(rel)
        score = 0.0
        for t in tokens:
            if t in rlow:
                score += 2.0
        for h in entry_hints:
            if h in rlow and h in low:
                score += 3.0
        if rel.endswith("main.py") or rel.endswith("app.py"):
            score += 1.0
        if score > 0:
            scored.append((score, rel))
    scored.sort(key=lambda x: -x[0])
    out: list[str] = []
    for _, rel in scored:
        if rel not in out:
            out.append(rel)
        if len(out) >= limit:
            break
    if out:
        return out
    entry_rank = (
        "main.py",
        "app/main.py",
        "app.py",
        "index.js",
        "App.js",
        "server.py",
    )
    fallback: list[tuple[int, str]] = []
    for f in files:
        rel = str(f.get("rel") or "")
        if not rel:
            continue
        rank = 99
        for i, hint in enumerate(entry_rank):
            if rel.endswith(hint) or f"/{hint}" in f"/{rel}":
                rank = i
                break
        fallback.append((rank, rel))
    fallback.sort(key=lambda x: (x[0], x[1]))
    for _, rel in fallback:
        if rel not in out:
            out.append(rel)
        if len(out) >= limit:
            break
    return out


def format_relevant_block(paths: list[str]) -> str:
    if not paths:
        return ""
    lines = ["[İLGİLİ DOSYALAR (otomatik)]"]
    for p in paths:
        lines.append(f"· `{p}`")
    return "\n".join(lines)


def build_context_v3_block(
    workspace_root: str | Path | None,
    *,
    scope_rel: str | None = None,
    message: str = "",
    active_file: str | None = None,
    include_at_reads: bool = True,
) -> str:
    """Görev bağlamına eklenecek Faz 44 bloğu."""
    if not _enabled():
        return ""
    scope = scope_rel
    if not scope:
        try:
            from ilim_assistant.motorlar.programlama_faz13 import resolve_scope_rel

            scope = resolve_scope_rel(
                workspace_root, active_file=active_file, message=message
            )
        except Exception:
            scope = None
    if not scope:
        return ""

    parts: list[str] = [f"[BAĞLAM v3 — Faz 44 — `{scope}`]"]
    tree = build_project_tree_map(workspace_root, scope)
    if tree:
        parts.append(tree[:4000])
    parts.append(format_recent_block(recent_changed_files(workspace_root, scope)))
    rel_paths = select_relevant_files(workspace_root, scope, message)
    rel_block = format_relevant_block(rel_paths)
    if rel_block:
        parts.append(rel_block)

    at_paths = parse_at_refs(message)
    if include_at_reads and at_paths:
        parts.append(batch_read_at_refs(workspace_root, at_paths))
    elif include_at_reads and rel_paths and len(at_paths) < 4:
        parts.append(
            batch_read_at_refs(workspace_root, rel_paths[:3], max_files=3)
        )

    try:
        from ilim_assistant.motorlar.programlama_faz53 import (
            symbol_lite_enabled,
            build_symbol_lite_block,
        )

        if symbol_lite_enabled():
            sym_lite = build_symbol_lite_block(
                workspace_root, scope, message
            ).strip()
            if sym_lite:
                parts.append(sym_lite[:5000])
    except Exception:
        pass

    parts.append(f"({FAZ44_VERSION})")
    return "\n\n".join(p for p in parts if p.strip())


def augment_light_context(
    existing: str,
    workspace_root: str | Path | None,
    *,
    message: str = "",
    active_file: str | None = None,
) -> str:
    block = build_context_v3_block(
        workspace_root,
        message=message,
        active_file=active_file,
    )
    if not block:
        return existing
    return existing.rstrip() + "\n\n" + block


def wants_context_map(message: str) -> bool:
    if not _enabled():
        return False
    return bool(_MAP_CMD_RE.search(message or ""))


def maybe_instant_faz44(
    message: str,
    workspace_root: str | Path | None,
    *,
    active_file: str | Path | None = None,
) -> str | None:
    if not _enabled():
        return None
    at_paths = parse_at_refs(message)
    if at_paths and not wants_context_map(message):
        block = batch_read_at_refs(workspace_root, at_paths)
        return f"Ümit abi, **@dosya okuma** (Faz 44):\n\n{block}\n"
    if wants_context_map(message):
        block = build_context_v3_block(
            workspace_root,
            message=message,
            active_file=active_file,
            include_at_reads=False,
        )
        return f"Ümit abi, **proje haritası**:\n\n{block}\n"
    return None


def detect_main_entry(scope_rel: str, workspace_root: str | Path | None) -> str | None:
    """Ana giriş dosyası tahmini."""
    rels = select_relevant_files(
        workspace_root,
        scope_rel,
        "main app server health api entry",
        limit=5,
    )
    for candidate in (
        "app/main.py",
        "main.py",
        "src/main.py",
        "index.js",
        "app.py",
    ):
        for r in rels:
            if r.endswith(candidate) or candidate in r:
                return r
    return rels[0] if rels else None


def faz44_directive() -> str:
    return (
        "[BAĞLAM v3 — Faz 44]\n"
        "Görevde repo ağacı + son değişenler + ilgili dosyalar otomatik eklenir.\n"
        "`@dosya projects/foo/main.py` · `@projects/foo/` · `repo harita`\n"
        "Kapat: RUZGAR_FAZ44=0\n"
    )
