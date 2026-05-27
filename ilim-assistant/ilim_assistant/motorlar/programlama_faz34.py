# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 34: Araç-öncelikli protokol (tool-first).

Sıra: read/grep/symbol → write → verify/run.
Model atlamışsa tur içinde otomatik ön okuma ve doğrulama.
"""

from __future__ import annotations

import os
import re
import unicodedata
from pathlib import Path
from typing import Any

FAZ34_VERSION = "programlama-faz34-v1-2026-05-25"

_DISCOVERY_TOOLS = frozenset({"read", "grep", "symbol"})
_WRITE_TOOLS = frozenset({"write"})
_VERIFY_TOOLS = frozenset({"verify", "run"})

_ENTRY_CANDIDATES = (
    "app/main.py",
    "main.py",
    "src/main.py",
    "src/index.ts",
    "src/App.jsx",
    "index.js",
    "app.py",
)


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ34", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def tool_first_enabled() -> bool:
    return _enabled()


def _ascii_fold(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def goal_wants_verify(goal: str) -> bool:
    low = _ascii_fold(goal or "")
    return any(
        k in low
        for k in (
            "test",
            "pytest",
            "gecir",
            "geçir",
            "dogrula",
            "doğrula",
            "verify",
            "build",
            "npm",
        )
    )


def tool_ids_from_results(results: list[dict[str, Any]]) -> set[str]:
    return {str(r.get("tool") or "").lower() for r in results if r.get("tool")}


def executed_write_in_results(results: list[dict[str, Any]]) -> bool:
    """Yalnızca başarılı diske yazım — LLM metnindeki planlanmış write sayılmaz."""
    return any(
        str(r.get("tool") or "").lower() == "write" and r.get("ok") for r in results
    )


def compliance_violations(
    results: list[dict[str, Any]],
    *,
    turn: int,
    goal: str = "",
) -> list[str]:
    """İhlal kodları — bir sonraki tur uyarısı için."""
    if not tool_first_enabled():
        return []
    ids = tool_ids_from_results(results)
    violations: list[str] = []
    wrote = executed_write_in_results(results)
    discovered = bool(ids & _DISCOVERY_TOOLS)
    verified = bool(ids & _VERIFY_TOOLS)

    if turn <= 2 and wrote and not discovered:
        violations.append("write_without_discovery")
    if wrote and goal_wants_verify(goal) and not verified:
        violations.append("write_without_verify")
    return violations


def _grep_pattern_from_goal(goal: str) -> str | None:
    low = _ascii_fold(goal)
    for token in ("health", "version", "endpoint", "pytest", "main", "api"):
        if token in low:
            return token
    m = re.search(r"[\w.\-]{3,32}", goal or "")
    return m.group(0) if m else None


def discovery_tool_specs(
    workspace_root: str | Path | None,
    scope_rel: str,
    *,
    goal: str = "",
    max_reads: int = 2,
) -> list[dict[str, Any]]:
    """Yazımdan önce otomatik keşif araçları."""
    if not tool_first_enabled():
        return []
    specs: list[dict[str, Any]] = []
    scope = (scope_rel or "").strip().replace("\\", "/").rstrip("/")
    if not scope:
        return specs

    try:
        from ilim_assistant.motorlar.programlama_motoru import repo_root

        root = repo_root(workspace_root)
        if root is None:
            return specs
        proj = root / scope.replace("/", os.sep)
        if not proj.is_dir():
            return specs
    except Exception:
        return specs

    reads = 0
    for rel_suffix in _ENTRY_CANDIDATES:
        if reads >= max_reads:
            break
        rel = f"{scope}/{rel_suffix}"
        p = proj / rel_suffix.replace("/", os.sep)
        if p.is_file():
            specs.append({"tool": "read", "path": rel, "_faz34": "preflight"})
            reads += 1

    pat = _grep_pattern_from_goal(goal)
    if pat:
        specs.append(
            {
                "tool": "grep",
                "scope": scope,
                "pattern": pat,
                "_faz34": "preflight",
            }
        )
    return specs


def verify_tool_spec(scope_rel: str, *, goal: str = "") -> dict[str, Any]:
    scope = (scope_rel or "").strip().replace("\\", "/").rstrip("/")
    preset = "npm_test"
    low = _ascii_fold(goal)
    if "build" in low and "test" not in low:
        preset = "npm_build"
    return {
        "tool": "verify",
        "scope": scope,
        "goal": goal,
        "_faz34": "post_write",
    }


def run_tool_specs(
    specs: list[dict[str, Any]],
    workspace_root: str | Path | None,
    *,
    scope_rel: str | None = None,
) -> tuple[list[dict[str, Any]], str]:
    """Araç listesini çalıştır; özet blok döner."""
    if not specs:
        return [], ""
    try:
        from ilim_assistant.motorlar.programlama_faz20 import execute_tool
    except Exception:
        return [], ""

    results: list[dict[str, Any]] = []
    blocks: list[str] = ["[Faz 34 — araç-öncelik otomatik]"]
    for i, spec in enumerate(specs, 1):
        clean = {k: v for k, v in spec.items() if not str(k).startswith("_")}
        res = execute_tool(clean, workspace_root, scope_rel=scope_rel)
        tag = str(spec.get("_faz34") or "auto")
        res["faz34"] = tag
        results.append(res)
        mark = "OK" if res.get("ok") else "HATA"
        blocks.append(
            f"{i}. {res.get('tool')} [{mark}] ({tag})\n"
            f"```text\n{str(res.get('output') or '')[:3500]}\n```"
        )
    return results, "\n\n".join(blocks)


def apply_turn_tool_first(
    tool_results: list[dict[str, Any]],
    llm_body: str,
    workspace_root: str | Path | None,
    scope_rel: str,
    goal: str,
    turn: int,
) -> tuple[list[dict[str, Any]], str, list[str]]:
    """
    Tur sonu: eksik keşif/doğrulama araçlarını çalıştır.
    Dönüş: (birleşik sonuçlar, ek metin, ihlaller)
    """
    if not tool_first_enabled():
        return tool_results, "", []

    combined = list(tool_results)
    extra_blocks: list[str] = []
    auto_specs: list[dict[str, Any]] = []

    ids = tool_ids_from_results(combined)
    executed_write = executed_write_in_results(combined)
    llm_planned_write = False
    try:
        from ilim_assistant.motorlar.programlama_faz20 import extract_tool_calls

        if extract_tool_calls(llm_body or ""):
            for spec in extract_tool_calls(llm_body):
                if str(spec.get("tool") or "").lower() == "write":
                    llm_planned_write = True
                    break
    except Exception:
        pass

    if turn <= 2 and (executed_write or llm_planned_write) and not (ids & _DISCOVERY_TOOLS):
        auto_specs.extend(
            discovery_tool_specs(workspace_root, scope_rel, goal=goal)
        )

    if executed_write and goal_wants_verify(goal) and not (ids & _VERIFY_TOOLS):
        auto_specs.append(verify_tool_spec(scope_rel, goal=goal))

    if auto_specs:
        auto_res, auto_block = run_tool_specs(
            auto_specs, workspace_root, scope_rel=scope_rel
        )
        combined.extend(auto_res)
        if auto_block:
            extra_blocks.append(auto_block)

    violations = compliance_violations(combined, turn=turn, goal=goal)
    return combined, "\n\n".join(extra_blocks), violations


def build_tool_first_nudge(violations: list[str], turn: int) -> str:
    if not violations:
        return ""
    lines = [f"[Faz 34 — araç sırası — tur {turn}]"]
    if "write_without_discovery" in violations:
        lines.append(
            "Önce `read` / `grep` / `symbol` ile keşif yap, sonra `write`."
        )
    if "write_without_verify" in violations:
        lines.append(
            "Yazımdan sonra `verify` veya `run` (pytest/npm) ile doğrula."
        )
    lines.append(
        'Örnek:\n```ruzgar-tool\n{"tool":"read","path":"projects/foo/app/main.py"}\n```'
    )
    return "\n".join(lines)


def augment_turn_user_message(base: str, *, turn: int, goal: str = "") -> str:
    if not tool_first_enabled():
        return base
    rules = (
        "\n\n[Faz 34 — araç-öncelik]\n"
        "Sıra: 1) read/grep/symbol  2) write  3) verify/run.\n"
        "Her turda en az bir `ruzgar-tool` bloğu kullan.\n"
    )
    if turn <= 1:
        rules += "İlk turda yazmadan önce keşif araçları zorunlu.\n"
    if goal_wants_verify(goal):
        rules += "Hedefte test var — yazımdan sonra verify çalıştır.\n"
    return base.rstrip() + rules


def augment_agent_system(system: str) -> str:
    if not tool_first_enabled():
        return system
    return (system or "").rstrip() + "\n\n" + faz34_directive()


def faz34_directive() -> str:
    return (
        "[ARAÇ-ÖNCELİK — Faz 34]\n"
        "Cursor sırası: keşif (read/grep/symbol) → write → verify/run.\n"
        "Yazmadan önce ilgili dosyayı oku; test isteniyorsa verify ile bitir.\n"
        "Atlanırsa motor tur içinde otomatik okur/doğrular.\n"
    )


def format_protocol_status(
    workspace_root: str | Path | None,
    scope_rel: str | None = None,
) -> str:
    scope = scope_rel or "(proje seçili değil)"
    return (
        "Ümit abi, **araç-öncelik protokolü** (Faz 34):\n\n"
        f"- Durum: {'açık' if tool_first_enabled() else 'kapalı'} (`RUZGAR_FAZ34`)\n"
        f"- Proje: `{scope}`\n"
        "- Sıra: read/grep/symbol → write → verify/run\n"
        "- Otomatik: yazım öncesi keşif, yazım sonrası doğrulama\n\n"
        f"({FAZ34_VERSION})"
    )


def wants_tool_protocol_status(message: str) -> bool:
    low = _ascii_fold(message or "")
    return bool(
        re.search(
            r"(?:arac|araç)\s+(?:sira|sıra|protokol|durum)|tool\s+protocol|tool\s+first",
            low,
        )
    )


def maybe_instant_faz34(
    message: str,
    workspace_root: str | Path | None,
    *,
    active_file: str | None = None,
) -> str | None:
    if not _enabled() or not wants_tool_protocol_status(message):
        return None
    scope = None
    try:
        from ilim_assistant.motorlar.programlama_faz13 import resolve_scope_rel

        scope = resolve_scope_rel(
            workspace_root, active_file=active_file, message=message
        )
    except Exception:
        pass
    return format_protocol_status(workspace_root, scope)
