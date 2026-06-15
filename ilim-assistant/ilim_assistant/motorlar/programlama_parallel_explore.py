# Created by Ümit & Gökçenur
"""
Programlama motoru — paralel keşif (okuma + grep).

Otonom görev başlamadan önce ilgili dosyaları arka planda toplar.
"""

from __future__ import annotations

import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from ilim_assistant.motorlar.programlama_motoru import ProgramlamaAraclari, repo_root

PROG_PARALLEL_EXPLORE_VERSION = "programlama-parallel-explore-v1-2026-06-15"
_MAX_WORKERS = 4
_READ_CAP = 4000


def parallel_explore_enabled() -> bool:
    return os.environ.get("RUZGAR_PROG_PARALLEL_EXPLORE", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _guess_paths(scope_rel: str, goal: str) -> list[str]:
    paths: list[str] = []
    low = (goal or "").lower()
    if "health" in low or "endpoint" in low:
        paths.extend(
            [
                f"{scope_rel}/app/main.py",
                f"{scope_rel}/main.py",
                f"{scope_rel}/tests/test_health.py",
            ]
        )
    if "test" in low or "pytest" in low:
        paths.append(f"{scope_rel}/tests/test_health.py")
    if "readme" in low:
        paths.append(f"{scope_rel}/README.md")
    if "refactor" in low or "monorepo" in low or "bench_pkg" in low:
        for tail in ("bench_pkg/core.py", "bench_pkg/service.py", "bench_pkg/api.py"):
            rel = f"{scope_rel}/{tail}".replace("//", "/")
            if rel not in paths:
                paths.append(rel)
    m = re.search(r"([\w./\-]+\.(?:py|js|ts|tsx|jsx|md))", goal or "", re.I)
    if m:
        p = m.group(1).replace("\\", "/").lstrip("/")
        if not p.startswith(scope_rel):
            p = f"{scope_rel}/{p.split('/')[-1]}"
        paths.append(p)
    seen: set[str] = set()
    out: list[str] = []
    for p in paths:
        n = p.replace("\\", "/")
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out[:6]


def _read_one(tools: ProgramlamaAraclari, rel: str) -> tuple[str, str]:
    rep = tools.read(rel, max_chars=_READ_CAP)
    if rep.ok:
        return rel, rep.content
    return rel, f"[HATA] {rep.error or 'okunamadı'}"


def _grep_one(
    workspace_root: str | Path | None,
    scope_rel: str,
    pattern: str,
) -> tuple[str, str]:
    try:
        from ilim_assistant.motorlar.programlama_faz13 import search_in_project

        res = search_in_project(workspace_root, scope_rel, pattern, max_hits=8)
        lines = []
        for h in res.get("hits") or []:
            rel = h.get("rel") or h.get("path") or "?"
            lines.append(f"{rel}:{h.get('line')}: {str(h.get('text') or '')[:100]}")
        return pattern, "\n".join(lines) or "sonuç yok"
    except Exception as e:
        return pattern, f"[HATA] {e}"


def build_parallel_explore_block(
    workspace_root: str | Path | None,
    *,
    scope_rel: str,
    goal: str = "",
    message: str = "",
) -> str:
    if not parallel_explore_enabled():
        return ""
    root = repo_root(workspace_root)
    if root is None or not scope_rel:
        return ""

    tools = ProgramlamaAraclari(root)
    paths = _guess_paths(scope_rel.replace("\\", "/").strip("/"), goal or message)
    patterns: list[str] = []
    for token in re.findall(r"\b(?:health|version|endpoint|test_\w+)\b", goal or message, re.I):
        if token not in patterns:
            patterns.append(token)
    patterns = patterns[:3]

    blocks: list[str] = [f"[PARALEL KEŞİF — {PROG_PARALLEL_EXPLORE_VERSION}]"]
    workers = min(_MAX_WORKERS, max(1, len(paths) + len(patterns)))

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = [pool.submit(_read_one, tools, p) for p in paths]
        futs += [
            pool.submit(_grep_one, workspace_root, scope_rel, pat) for pat in patterns
        ]
        for fut in as_completed(futs):
            try:
                key, body = fut.result()
            except Exception as e:
                key, body = "?", str(e)
            if body.startswith("[HATA]") and "okunamadı" in body:
                continue
            if key in patterns or key in paths:
                label = "grep" if key in patterns else "read"
                blocks.append(f"=== {label}: {key} ===\n{body[:_READ_CAP]}")

    if len(blocks) <= 1:
        return ""
    return "\n\n".join(blocks)[:12000]
