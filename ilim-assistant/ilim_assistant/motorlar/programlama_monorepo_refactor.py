# Created by Ümit & Gökçenur
"""
Programlama motoru — P5 / S8: çok dosyalı monorepo refactor gate.

Deterministik (LLM yok):
  1) mini_app v1 sıfırla (core + service + api)
  2) üç cerrahi @@patch
  3) paralel keşif + bağlam bütçesi smoke
  4) pytest + havuz yazımı
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from ilim_assistant.approved_executor import run_argv
from ilim_assistant.motorlar.programlama_motoru import repo_root

MONOREPO_REFACTOR_VERSION = "programlama-monorepo-refactor-v1-2026-06-15"
_BENCH_ROOT = "ilim-assistant/tests/monorepo_refactor"
_PKG = f"{_BENCH_ROOT}/bench_pkg"

_V1_FILES: dict[str, str] = {
    f"{_PKG}/core.py": (
        'VERSION = "bench-v1"\n\n\n'
        "def compute() -> int:\n"
        "    return 1\n"
    ),
    f"{_PKG}/service.py": (
        "from bench_pkg.core import VERSION\n\n\n"
        "def handler() -> str:\n"
        "    return VERSION\n"
    ),
    f"{_PKG}/api.py": (
        "from bench_pkg.service import handler\n\n\n"
        "def endpoint() -> str:\n"
        "    return f\"{handler()}-raw\"\n"
    ),
}

_PATCH_BUNDLE = (
    f"@@patch {_PKG}/core.py\n"
    "```search-replace\n"
    "<<<SEARCH\n"
    'VERSION = "bench-v1"\n'
    "===\n"
    'VERSION = "bench-v2"\n'
    ">>>REPLACE\n"
    "```\n"
    f"@@patch {_PKG}/service.py\n"
    "```search-replace\n"
    "<<<SEARCH\n"
    "    return VERSION\n"
    "===\n"
    '    return f"{VERSION}-svc"\n'
    ">>>REPLACE\n"
    "```\n"
    f"@@patch {_PKG}/api.py\n"
    "```search-replace\n"
    "<<<SEARCH\n"
    '    return f"{handler()}-raw"\n'
    "===\n"
    '    return f"{handler()}-ok"\n'
    ">>>REPLACE\n"
    "```"
)


def monorepo_refactor_enabled() -> bool:
    return os.environ.get("RUZGAR_PROG_MONOREPO_REFACTOR", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def bench_scope_rel() -> str:
    return _BENCH_ROOT


def _write_v1_bench(root: Path) -> bool:
    try:
        (root / _BENCH_ROOT / "bench_pkg").mkdir(parents=True, exist_ok=True)
        init_fp = root / _PKG / "__init__.py"
        if not init_fp.is_file():
            init_fp.write_text('"""P5 monorepo refactor bench."""\n', encoding="utf-8")
        for rel, body in _V1_FILES.items():
            fp = root / rel.replace("/", os.sep)
            fp.parent.mkdir(parents=True, exist_ok=True)
            fp.write_text(body, encoding="utf-8")
        return True
    except OSError:
        return False


def _run_bench_pytest(scope_abs: Path) -> tuple[bool, str]:
    code, out, err = run_argv(
        ["python", "-m", "pytest", "-q", "test_bench_gate.py", "-p", "no:cacheprovider"],
        cwd=str(scope_abs),
        timeout_sec=60,
    )
    return code == 0, ((out or err or "")[:200] or "pytest_ok")


def format_monorepo_refactor_instant_report(rep: dict[str, Any]) -> str:
    checks = rep.get("checks") or {}
    lines = [
        "Ümit abi, **P5 monorepo refactor gate** (S8):",
        "",
        f"Sonuç: **{'OK' if rep.get('ok') else 'KIRIK'}**",
        "**Sonraki:** `p6 gate`",
        "",
    ]
    for key, ok in checks.items():
        lines.append(f"- {'✓' if ok else '✗'} {key}")
    lines.append(f"\nKapsam: `{rep.get('scope_rel', '?')}` · patch: {rep.get('patches', 3)}")
    lines.append(f"({MONOREPO_REFACTOR_VERSION})")
    return "\n".join(lines)


def wants_monorepo_refactor_gate(message: str) -> bool:
    low = (message or "").lower()
    return any(
        k in low
        for k in (
            "monorepo refactor gate",
            "p5 refactor gate",
            "p5 gate",
            "s8 gate",
            "refactor gate",
        )
    )


def maybe_instant_monorepo_refactor(
    message: str,
    workspace_root: str | Path | None,
) -> str | None:
    if not wants_monorepo_refactor_gate(message):
        return None
    rep = run_monorepo_refactor_gate(workspace_root)
    return format_monorepo_refactor_instant_report(rep)


def run_monorepo_refactor_gate(workspace_root: str | Path | None) -> dict[str, Any]:
    checks: dict[str, bool] = {}
    detail_parts: list[str] = []
    if not monorepo_refactor_enabled():
        return {
            "ok": False,
            "detail": "RUZGAR_PROG_MONOREPO_REFACTOR=0",
            "checks": checks,
            "version": MONOREPO_REFACTOR_VERSION,
        }

    root = repo_root(workspace_root)
    if root is None:
        return {
            "ok": False,
            "detail": "workspace_root yok",
            "checks": checks,
            "version": MONOREPO_REFACTOR_VERSION,
        }

    checks["bench_reset"] = _write_v1_bench(root)
    if not checks["bench_reset"]:
        return {
            "ok": False,
            "detail": "bench_reset_fail",
            "checks": checks,
            "version": MONOREPO_REFACTOR_VERSION,
        }

    try:
        from ilim_assistant.motorlar.programlama_patch import apply_patch_jobs

        reps = apply_patch_jobs(_PATCH_BUNDLE, root)
        checks["triple_patch"] = len(reps) == 3 and all(r.ok for r in reps)
        if not checks["triple_patch"]:
            detail_parts.append(
                "; ".join(f"{r.path}:{r.detail}" for r in reps if not r.ok)[:160]
            )
    except Exception as exc:
        checks["triple_patch"] = False
        detail_parts.append(f"patch:{exc}")

    scope_abs = (root / _BENCH_ROOT).resolve()
    py_ok, py_detail = _run_bench_pytest(scope_abs)
    checks["pytest_triple"] = py_ok
    if not py_ok:
        detail_parts.append(py_detail)

    try:
        from ilim_assistant.motorlar.programlama_parallel_explore import (
            build_parallel_explore_block,
            parallel_explore_enabled,
        )

        blk = build_parallel_explore_block(
            root,
            scope_rel=_BENCH_ROOT,
            goal="refactor core service api bench",
            message="monorepo refactor",
        )
        checks["parallel_explore"] = parallel_explore_enabled() and bool(blk.strip())
    except Exception:
        checks["parallel_explore"] = False

    try:
        from ilim_assistant.motorlar.programlama_context_budget import (
            assemble_context,
            ContextPart,
        )

        text, rep = assemble_context(
            [
                ContextPart(key="core", text="x" * 500, priority=80),
                ContextPart(key="svc", text="y" * 500, priority=70),
                ContextPart(key="api", text="z" * 500, priority=60),
            ]
        )
        checks["context_budget"] = len(text) > 100 and rep.budget_chars >= 2000
    except Exception:
        checks["context_budget"] = False

    try:
        from ilim_assistant.motorlar.programlama_havuz_bridge import record_tool_outcome

        record_tool_outcome(
            root,
            patches=[f"{_PKG}/core.py", f"{_PKG}/service.py", f"{_PKG}/api.py"],
            pytest_ok=py_ok,
            goal="P5 monorepo triple refactor gate",
            scope_rel=_BENCH_ROOT,
        )
        checks["havuz_write"] = True
    except Exception:
        checks["havuz_write"] = False

    ok = all(checks.values()) if checks else False
    return {
        "ok": ok,
        "detail": "; ".join(detail_parts) if detail_parts else "monorepo refactor gate",
        "checks": checks,
        "scope_rel": _BENCH_ROOT,
        "patches": 3,
        "version": MONOREPO_REFACTOR_VERSION,
    }
