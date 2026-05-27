from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ilim_assistant.motorlar.programlama_motoru import repo_root

FAZ94_VERSION = "programlama-faz94-v1-2026-05-27"

_TEST_DIR_NAMES = ("tests", "test", "__tests__")
_SKIP_PARTS = frozenset(
    {
        ".git",
        ".venv",
        "venv",
        "node_modules",
        "__pycache__",
        ".pytest_cache",
        "dist",
        "build",
    }
)


def _norm_rel(rel: str) -> str:
    return (rel or "").strip().replace("\\", "/").lstrip("/")


def _stem_name(path: str) -> str:
    p = Path(_norm_rel(path))
    name = p.stem
    if name.startswith("test_"):
        name = name[5:]
    elif name.endswith("_test"):
        name = name[:-5]
    return name.lower()


def suggest_test_path_for_module(module_rel: str, *, scope_rel: str = "") -> str:
    rel = _norm_rel(module_rel)
    scope = _norm_rel(scope_rel)
    if scope and rel.startswith(scope + "/"):
        rel = rel[len(scope) + 1 :]
    p = Path(rel)
    if p.suffix.lower() in (".py", ".pyi"):
        stem = p.stem
        if scope:
            return f"{scope}/tests/test_{stem}.py"
        return f"tests/test_{stem}.py"
    if p.suffix.lower() in (".ts", ".tsx", ".js", ".jsx"):
        base = p.stem
        if scope:
            return f"{scope}/__tests__/{base}.test{p.suffix.lower()}"
        return f"__tests__/{base}.test{p.suffix.lower()}"
    if scope:
        return f"{scope}/tests/test_{p.stem}.py"
    return f"tests/test_{p.stem}.py"


def _is_test_file(rel: str) -> bool:
    low = _norm_rel(rel).lower()
    parts = low.split("/")
    if any(p.startswith("test_") or p.endswith("_test.py") for p in parts):
        return True
    return any(p in _TEST_DIR_NAMES for p in parts)


def _is_source_file(rel: str) -> bool:
    low = _norm_rel(rel).lower()
    if _is_test_file(low):
        return False
    return low.endswith((".py", ".ts", ".tsx", ".js", ".jsx"))


def _file_exists(workspace_root: str | Path | None, rel: str) -> bool:
    root = repo_root(workspace_root)
    if root is None:
        return False
    p = root / _norm_rel(rel)
    return p.is_file()


def _find_existing_tests_for_module(
    module_rel: str,
    workspace_root: str | Path | None,
    *,
    scope_rel: str = "",
) -> list[str]:
    mod = _norm_rel(module_rel)
    stem = _stem_name(mod)
    scope = _norm_rel(scope_rel)
    root = repo_root(workspace_root)
    if root is None or not stem:
        return []

    hits: list[str] = []
    search_roots: list[Path] = []
    if scope:
        search_roots.append(root / scope)
    search_roots.append(root)

    patterns = (
        f"test_{stem}.py",
        f"{stem}_test.py",
        f"{stem}.test.ts",
        f"{stem}.test.tsx",
        f"{stem}.test.js",
    )
    for base in search_roots:
        if not base.is_dir():
            continue
        for pat in patterns:
            for p in base.rglob(pat):
                if any(part in _SKIP_PARTS for part in p.parts):
                    continue
                try:
                    rel = p.relative_to(root).as_posix()
                except ValueError:
                    continue
                if rel not in hits:
                    hits.append(rel)
                if len(hits) >= 6:
                    return hits
    return hits


def wants_targeted_tests(message: str) -> bool:
    low = (message or "").lower()
    return any(
        x in low
        for x in (
            "test",
            "pytest",
            "unit test",
            "regresyon",
            "regression",
            "dogrula",
            "doğrula",
            "fix",
            "düzelt",
            "duzelt",
            "refactor",
            "implement",
            "ekle",
            "yaz",
        )
    )


def build_regression_shield(
    applied_files: list[str] | None,
    workspace_root: str | Path | None,
    scope_rel: str,
) -> dict[str, Any]:
    applied = [_norm_rel(x) for x in (applied_files or []) if str(x).strip()]
    scope = _norm_rel(scope_rel)
    source_files = [f for f in applied if _is_source_file(f)]
    test_files = [f for f in applied if _is_test_file(f)]

    existing_tests: list[str] = []
    missing_tests: list[dict[str, str]] = []
    for src in source_files[:12]:
        found = _find_existing_tests_for_module(src, workspace_root, scope_rel=scope)
        for t in found:
            if t not in existing_tests:
                existing_tests.append(t)
        if not found:
            suggested = suggest_test_path_for_module(src, scope_rel=scope)
            missing_tests.append({"module": src, "suggested_test": suggested})

    verify_cmds: list[str] = []
    if existing_tests:
        sample = existing_tests[:4]
        verify_cmds.append(f"pytest {' '.join(sample)}")
    elif scope:
        verify_cmds.append(f"pytest {scope}/tests")
    else:
        verify_cmds.append("pytest")

    return {
        "version": FAZ94_VERSION,
        "scope_rel": scope,
        "changed_count": len(applied),
        "source_files": source_files[:12],
        "test_files_written": test_files[:8],
        "existing_tests": existing_tests[:12],
        "missing_tests": missing_tests[:8],
        "verify_commands": verify_cmds[:3],
        "needs_new_tests": bool(missing_tests),
    }


def build_pre_turn_test_directive(
    message: str,
    workspace_root: str | Path | None,
    scope_rel: str,
) -> str:
    if not wants_targeted_tests(message):
        return ""
    scope = _norm_rel(scope_rel)
    shield = build_regression_shield([], workspace_root, scope)
    lines = ["[PROGRAMLAMA REGRESYON KALKANI — P7]"]
    lines.append(
        "Degisiklikten sonra hedefli test yaz/ calistir; 'calisiyor gibi' ile yetinme."
    )
    if scope:
        lines.append(f"Kapsam: `{scope}`")
    lines.append("Adimlar:")
    lines.append("- Degisen modul icin unit test ekle veya guncelle.")
    lines.append("- Once ilgili test dosyasini calistir, sonra genel pytest.")
    if shield.get("verify_commands"):
        lines.append(f"- Ornek: `{shield['verify_commands'][0]}`")
    lines.append("[/PROGRAMLAMA REGRESYON KALKANI]")
    return "\n".join(lines)


def render_test_directive(shield: dict[str, Any]) -> str:
    if not shield.get("changed_count") and not shield.get("needs_new_tests"):
        return ""
    lines = ["[PROGRAMLAMA HEDEFLI TEST — P7]"]
    src = list(shield.get("source_files") or [])
    if src:
        lines.append("Degisen kaynak dosyalar:")
        lines.extend(f"- `{s}`" for s in src[:8])
    existing = list(shield.get("existing_tests") or [])
    if existing:
        lines.append("Mevcut ilgili testler (once bunlari calistir):")
        lines.extend(f"- `{t}`" for t in existing[:8])
    missing = list(shield.get("missing_tests") or [])
    if missing:
        lines.append("Eksik test onerileri:")
        for row in missing[:6]:
            mod = str(row.get("module") or "")
            sug = str(row.get("suggested_test") or "")
            if mod and sug:
                lines.append(f"- `{mod}` -> `{sug}`")
    cmds = list(shield.get("verify_commands") or [])
    if cmds:
        lines.append("Verify komutlari:")
        lines.extend(f"- `{c}`" for c in cmds[:3])
    lines.append(
        "Talimat: Eksik test varsa @@write ile ekle; pytest yesil olmadan 'bitti' deme."
    )
    lines.append("[/PROGRAMLAMA HEDEFLI TEST]")
    return "\n".join(lines)


def run_regression_shield_check(
    workspace_root: str | Path | None,
    scope_rel: str,
    applied_files: list[str] | None,
) -> dict[str, Any]:
    shield = build_regression_shield(applied_files, workspace_root, scope_rel)
    verify_ok = False
    verify_detail = ""
    if not list(shield.get("source_files") or []):
        return {**shield, "verify_ok": False, "verify_skipped": True, "verify_detail": ""}

    try:
        from ilim_assistant.motorlar.programlama_faz14 import run_project_verify

        rep = run_project_verify(
            workspace_root,
            scope_rel,
            goal="pytest targeted regression",
        )
        verify_ok = bool(rep and rep.ok)
        verify_detail = (rep.output if rep else "")[:600]
    except Exception as exc:
        verify_detail = str(exc)[:200]

    return {
        **shield,
        "verify_ok": verify_ok,
        "verify_skipped": False,
        "verify_detail": verify_detail,
    }


def regression_status_text(shield: dict[str, Any]) -> str:
    changed = int(shield.get("changed_count") or 0)
    existing = len(shield.get("existing_tests") or [])
    missing = len(shield.get("missing_tests") or [])
    parts = [f"P7 regresyon: {changed} dosya degisti"]
    if existing:
        parts.append(f"{existing} ilgili test bulundu")
    if missing:
        parts.append(f"{missing} modul icin yeni test onerildi")
    if shield.get("verify_skipped"):
        return " · ".join(parts)
    if shield.get("verify_ok"):
        parts.append("pytest yesil")
    else:
        parts.append("pytest kontrol et")
    return " · ".join(parts)
