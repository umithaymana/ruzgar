# Created by Ümit & Gökçenur
"""Çırak sözleşme kapısı — doğru API / hedef pytest / bitti kararı.

Yalan yeşil kesici:
- Hedefte adı geçen def/imza diskte yoksa görev bitmez.
- Pytest mümkünse yalnız hedef test dosyalarında çalışır.
"""

from __future__ import annotations

import ast
import os
import re
from pathlib import Path
from typing import Any

SOZLESME_VERSION = "ruzgar-cirak-sozlesme-v1-2026-11-18"

_KNOWN_API = (
    "filtre_satirlar",
    "normalize",
    "kelime_say",
    "json_ozet",
    "carp",
    "fark",
    "bol",
    "topla",
    "isle",
    "ozetle",
    "mod",
    "mutlak",
    "ters",
    "ortalama",
    "selam",
    "ozet",
    "birlestir",
)

_DEF_RE = re.compile(r"\bdef\s+([a-z_][a-z0-9_]*)\s*\(", re.I)
_ARROW_RE = re.compile(r"\b([a-z_][a-z0-9_]*)\s*\([^)]*\)\s*->", re.I)
_BARE_API_RE = re.compile(
    r"\b(" + "|".join(re.escape(x) for x in _KNOWN_API) + r")\b",
    re.I,
)


def cirak_required_symbols(goal: str) -> list[str]:
    """Görev metninden beklenen fonksiyon adları."""
    text = goal or ""
    found: list[str] = []
    for rx in (_DEF_RE, _ARROW_RE, _BARE_API_RE):
        for m in rx.finditer(text):
            name = m.group(1)
            low = name.lower()
            if low.startswith("test_") or low in {"print", "main", "int", "str", "float", "list", "dict"}:
                continue
            if name not in found:
                found.append(name)
    return found


def _collect_defs(py_path: Path) -> set[str]:
    try:
        src = py_path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(src)
    except Exception:
        return set()
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names.add(node.name)
    return names


def cirak_symbols_on_disk(
    workspace_root: str | Path | None,
    scope_rel: str,
) -> set[str]:
    try:
        from ilim_assistant.motorlar.programlama_motoru import repo_root

        root = repo_root(workspace_root)
    except Exception:
        root = Path(workspace_root) if workspace_root else None
    if root is None:
        return set()
    scope = (scope_rel or "").replace("\\", "/").strip("/")
    base = root / scope.replace("/", os.sep)
    if not base.is_dir():
        return set()
    found: set[str] = set()
    for py in base.rglob("*.py"):
        if "__pycache__" in py.parts:
            continue
        found |= _collect_defs(py)
    return found


def cirak_missing_symbols(
    workspace_root: str | Path | None,
    goal: str,
    scope_rel: str = "",
) -> list[str]:
    need = cirak_required_symbols(goal)
    if not need:
        return []
    have = cirak_symbols_on_disk(workspace_root, scope_rel)
    return [n for n in need if n not in have]


def cirak_pytest_targets(goal: str, scope_rel: str = "") -> list[str]:
    """pytest'e verilecek göreli test yolları (proje köküne göre)."""
    from ilim_assistant.motorlar.programlama_faz34 import cirak_goal_required_paths

    paths = cirak_goal_required_paths(goal, scope_rel)
    scope = (scope_rel or "projects/cirak-atolyesi").replace("\\", "/").rstrip("/")
    out: list[str] = []
    for rel in paths:
        r = rel.replace("\\", "/")
        if "/tests/" in r and r.endswith(".py"):
            # projects/cirak-atolyesi/tests/x.py → tests/x.py
            if r.startswith(scope + "/"):
                out.append(r[len(scope) + 1 :])
            elif r.startswith("tests/"):
                out.append(r)
    # çıplak test_*.py
    if not out:
        for m in re.finditer(r"\b(test_[\w\-]+\.py)\b", goal or "", flags=re.I):
            out.append(f"tests/{m.group(1)}")
    # tekilleştir
    uniq: list[str] = []
    for x in out:
        if x not in uniq:
            uniq.append(x)
    return uniq


def cirak_sozlesme_nudge(
    *,
    missing_files: list[str] | None = None,
    missing_symbols: list[str] | None = None,
    turn: int = 1,
) -> str:
    lines = [f"[ÇIRAK SÖZLEŞME KAPISI — tur {turn}]"]
    if missing_files:
        lines.append("Eksik dosya — görev bitmedi:")
        for p in missing_files[:6]:
            lines.append(f"- @@write {p}")
    if missing_symbols:
        lines.append("Eksik fonksiyon/imza — kendi uydurduğun API yetmez:")
        for s in missing_symbols[:8]:
            lines.append(f"- `def {s}(...):` zorunlu")
        if "filtre_satirlar" in (missing_symbols or []):
            lines.append(
                "Örnek imza:\n"
                "```python\ndef filtre_satirlar(satirlar, anahtar: str):\n"
                "    ...\n    yield satir\n```"
            )
    lines.append("Salt grep YASAK. Doğru dosya + doğru def yaz, sonra verify.")
    return "\n".join(lines)


def cirak_contract_status(
    workspace_root: str | Path | None,
    goal: str,
    scope_rel: str = "",
) -> dict[str, Any]:
    from ilim_assistant.motorlar.programlama_faz34 import (
        cirak_missing_required_files,
        is_cirak_yazim_gorev,
    )

    if not is_cirak_yazim_gorev(goal, scope_rel):
        return {"active": False, "ok": True, "version": SOZLESME_VERSION}
    missing_files = cirak_missing_required_files(workspace_root, goal, scope_rel)
    missing_syms = cirak_missing_symbols(workspace_root, goal, scope_rel)
    ok = not missing_files and not missing_syms
    return {
        "active": True,
        "ok": ok,
        "missing_files": missing_files,
        "missing_symbols": missing_syms,
        "pytest_targets": cirak_pytest_targets(goal, scope_rel),
        "version": SOZLESME_VERSION,
    }
