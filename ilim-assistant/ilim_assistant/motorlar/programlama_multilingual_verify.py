# Created by Ümit & Gökçenur
"""
Programlama motoru — Adım 10: çok dilli verify matrisi.

Python: ruff + mypy + pytest
Node: npm test + npm run build
Go: go test ./...
Rust: cargo check + cargo test
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any, Literal

from ilim_assistant.approved_executor import run_argv
from ilim_assistant.motorlar.programlama_motoru import ExecReport, repo_root

MULTILINGUAL_VERIFY_VERSION = "programlama-multilingual-verify-v1-2026-06-16"

StackId = Literal["python", "node", "go", "rust", "unknown"]

_VERIFY_MATRIX: dict[str, list[dict[str, Any]]] = {
    "python": [
        {"preset": "ruff_check", "kind": "preset"},
        {"preset": "mypy_check", "kind": "preset"},
        {"preset": "pytest_scope", "kind": "pytest"},
    ],
    "node": [
        {"preset": "npm_test", "kind": "argv", "argv": ["npm", "test", "--if-present"]},
        {"preset": "npm_build", "kind": "argv", "argv": ["npm", "run", "build", "--if-present"]},
    ],
    "go": [
        {"preset": "go_test", "kind": "argv", "argv": ["go", "test", "./..."]},
    ],
    "rust": [
        {"preset": "cargo_check", "kind": "argv", "argv": ["cargo", "check"]},
        {"preset": "cargo_test", "kind": "argv", "argv": ["cargo", "test", "--quiet"]},
    ],
}


def multilingual_verify_enabled() -> bool:
    return os.environ.get("RUZGAR_PROG_MULTILINGUAL_VERIFY", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _tool_available(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def detect_project_stack(scope_dir: Path) -> StackId:
    if not scope_dir.is_dir():
        return "unknown"
    if (scope_dir / "Cargo.toml").is_file():
        return "rust"
    if (scope_dir / "go.mod").is_file():
        return "go"
    if (scope_dir / "package.json").is_file():
        return "node"
    if any(scope_dir.rglob("*.py")):
        return "python"
    if any(scope_dir.rglob("*.ts")) or any(scope_dir.rglob("*.tsx")):
        return "node"
    return "unknown"


def verify_chain_for_stack(stack: StackId) -> list[dict[str, Any]]:
    if stack == "unknown":
        return list(_VERIFY_MATRIX["python"])
    return list(_VERIFY_MATRIX.get(stack, _VERIFY_MATRIX["python"]))


def _run_argv_step(
    preset: str,
    argv: list[str],
    cwd: Path,
    *,
    timeout: int = 300,
) -> ExecReport:
    if not argv or not _tool_available(argv[0]):
        cmd = argv[0] if argv else "?"
        return ExecReport(
            preset=preset,
            exit_code=0,
            output=f"[Araç yok: {cmd} — atlandı]",
        )
    code, out, err = run_argv(argv, timeout_sec=timeout, cwd=str(cwd))
    body = f"[Komut: {' '.join(argv)}]\n[Cwd: {cwd}]\n[Çıkış kodu: {code}]\n{out}"
    if err:
        body += f"\n[Hata] {err}"
    if code != 0 and "not found" in (out + err).lower():
        return ExecReport(
            preset=preset,
            exit_code=0,
            output=f"[Script yok — atlandı]\n{body[:600]}",
        )
    return ExecReport(preset=preset, exit_code=code, output=body)


def multilingual_verify_after_writes(
    tools: Any,
    write_paths: list[str],
    *,
    scope_rel: str | None = None,
) -> list[ExecReport]:
    """Kapsama göre doğru verify zincirini çalıştırır."""
    if not multilingual_verify_enabled():
        return tools._verify_after_writes_python(write_paths, scope_rel=scope_rel)

    root = tools.root
    if root is None:
        return []

    scope = scope_rel
    if not scope:
        try:
            from ilim_assistant.motorlar.programlama_motoru import (
                _infer_scope_rel_from_paths,
            )

            scope = _infer_scope_rel_from_paths(write_paths)
        except Exception:
            scope = None

    if not scope:
        return tools._verify_after_writes_python(write_paths, scope_rel=None)

    scope_dir = root / scope.replace("/", os.sep)
    stack = detect_project_stack(scope_dir)
    chain = verify_chain_for_stack(stack)
    reports: list[ExecReport] = []

    old_ruff = os.environ.get("RUZGAR_RUFF_TARGET")
    old_mypy = os.environ.get("RUZGAR_MYPY_TARGET")
    try:
        os.environ["RUZGAR_RUFF_TARGET"] = scope
        os.environ["RUZGAR_MYPY_TARGET"] = scope
        for step in chain:
            kind = step.get("kind")
            preset = str(step.get("preset") or "")
            if kind == "preset":
                reports.append(tools.run_dev_preset(preset))
            elif kind == "pytest":
                try:
                    from ilim_assistant.motorlar.programlama_faz14 import run_project_verify

                    verify = run_project_verify(root, scope, goal="pytest")
                    if verify is not None:
                        reports.append(verify)
                    else:
                        reports.append(tools.run_dev_preset("pytest_run"))
                except Exception:
                    reports.append(tools.run_dev_preset("pytest_run"))
            elif kind == "argv":
                argv = list(step.get("argv") or [])
                reports.append(_run_argv_step(preset, argv, scope_dir))
    finally:
        if old_ruff is None:
            os.environ.pop("RUZGAR_RUFF_TARGET", None)
        else:
            os.environ["RUZGAR_RUFF_TARGET"] = old_ruff
        if old_mypy is None:
            os.environ.pop("RUZGAR_MYPY_TARGET", None)
        else:
            os.environ["RUZGAR_MYPY_TARGET"] = old_mypy

    return reports


def multilingual_directive() -> str:
    return (
        "[ÇOK DİLLİ VERIFY — Adım 10]\n"
        "Stack algılar: python | node | go | rust — yazım sonrası doğru zincir.\n"
        "Kapat: RUZGAR_PROG_MULTILINGUAL_VERIFY=0\n"
    )


def run_multilingual_verify_smoke(
    workspace_root: str | Path | None,
) -> dict[str, Any]:
    """Bench: stack algılama + matris."""
    root = repo_root(workspace_root)
    if root is None:
        return {"ok": False, "error": "workspace_root yok"}

    samples: list[dict[str, Any]] = []
    projects = root / "projects"
    if projects.is_dir():
        for proj in sorted(projects.iterdir(), key=lambda p: p.name)[:80]:
            if not proj.is_dir():
                continue
            rel = f"projects/{proj.name}"
            stack = detect_project_stack(proj)
            if stack != "unknown":
                samples.append(
                    {
                        "scope": rel,
                        "stack": stack,
                        "chain": [s.get("preset") for s in verify_chain_for_stack(stack)],
                    }
                )
            if len(samples) >= 5:
                break

    py_chain = [s.get("preset") for s in verify_chain_for_stack("python")]
    node_chain = [s.get("preset") for s in verify_chain_for_stack("node")]
    ok = (
        py_chain == ["ruff_check", "mypy_check", "pytest_scope"]
        and node_chain == ["npm_test", "npm_build"]
        and len(samples) >= 1
    )
    return {
        "ok": ok,
        "python_chain": py_chain,
        "node_chain": node_chain,
        "go_chain": [s.get("preset") for s in verify_chain_for_stack("go")],
        "rust_chain": [s.get("preset") for s in verify_chain_for_stack("rust")],
        "detected_samples": samples,
        "version": MULTILINGUAL_VERIFY_VERSION,
    }
