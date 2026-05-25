# Created by Ümit & Gökçenur
"""
Cursor seviye kilidi — 3 offline senaryo + 0–100 puan (hedef ≥85).

Senaryolar:
1. API ekle (scaffold + health/version + pytest)
2. Bugfix + test (kırmızı test → düzelt → yeşil)
3. Üç dosya refactor (util + service + main)
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ilim_assistant.motorlar.programlama_faz18 import SloCheck

CURSOR_PARITY_VERSION = "programlama-cursor-parity-v1-2026-05-25"
FAZ46_VERSION = CURSOR_PARITY_VERSION
TARGET_CURSOR_SCORE = 85
_MAX_SCENARIO_SEC = 120.0


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ46", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def cursor_parity_enabled() -> bool:
    return _enabled()


def _slug(prefix: str) -> str:
    return f"{prefix}-{int(time.time()) % 100000}"


def _norm_rel(rel: str) -> str:
    return (rel or "").strip().replace("\\", "/").lstrip("/")


@dataclass
class CursorSeviyeReport:
    ok: bool
    score: int
    target_score: int = TARGET_CURSOR_SCORE
    scenarios: list[SloCheck] = field(default_factory=list)
    capabilities: dict[str, bool] = field(default_factory=dict)
    capability_points: int = 0
    scenario_points: int = 0
    project_names: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    version: str = CURSOR_PARITY_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "score": self.score,
            "target_score": self.target_score,
            "meets_target": self.score >= self.target_score,
            "scenarios": [c.to_dict() for c in self.scenarios],
            "capabilities": self.capabilities,
            "capability_points": self.capability_points,
            "scenario_points": self.scenario_points,
            "project_names": self.project_names,
            "warnings": self.warnings,
            "version": self.version,
        }


def build_extended_capability_scorecard() -> dict[str, bool]:
    """Faz 20–45 kabiliyet bayrakları."""
    card: dict[str, bool] = {}

    def _try(key: str, mod: str, attr: str, *args: Any) -> None:
        try:
            m = __import__(f"ilim_assistant.motorlar.{mod}", fromlist=[attr])
            fn = getattr(m, attr)
            card[key] = bool(fn(*args)) if args else bool(fn())
        except Exception:
            card[key] = False

    _try("unified_agent", "programlama_faz20", "unified_agent_enabled")
    _try("light_context", "programlama_faz21", "light_context_enabled")
    _try("symbol_index", "programlama_faz22", "_enabled")
    _try(
        "task_budget_5m",
        "programlama_faz23",
        "resolve_code_agent_budget_sec",
    )
    card["task_budget_5m"] = card.get("task_budget_5m") and (
        __import__(
            "ilim_assistant.motorlar.programlama_faz23",
            fromlist=["resolve_code_agent_budget_sec"],
        ).resolve_code_agent_budget_sec()
        >= 300.0
    )
    _try("agent_steps_sse", "programlama_faz24", "sse_steps_enabled")
    _try("nested_tool_loop", "programlama_faz38", "nested_tool_loop_enabled")
    _try("task_completion_gate", "programlama_faz39", "completion_gate_enabled")
    _try("structured_tools", "programlama_faz40", "structured_tools_enabled")
    _try("long_task_budget", "programlama_faz41", "long_task_enabled")
    _try("lsp_v2", "programlama_faz42", "lsp_v2_enabled")
    _try("terminal_v3", "programlama_faz43", "terminal_v3_enabled")
    _try("context_v3", "programlama_faz44", "context_v3_enabled")
    _try("editor_v2", "programlama_faz45", "editor_v2_enabled")
    return card


def _capability_points(cap: dict[str, bool]) -> int:
    """Maks 35 puan — kabiliyet oranı."""
    if not cap:
        return 0
    on = sum(1 for v in cap.values() if v)
    return int(round(35 * on / len(cap)))


def _apply_patch(workspace_root: str | Path | None, text: str) -> tuple[int, bool]:
    from ilim_assistant.motorlar.programlama_motoru import apply_assistant_reply_tools
    from ilim_assistant.motorlar.programlama_faz23 import enter_task_mode, exit_task_mode

    enter_task_mode()
    try:
        summ, _ = apply_assistant_reply_tools(
            text, workspace_root, run_pytest=False
        )
        writes = len([w for w in summ.writes if w.ok])
        return writes, writes > 0
    finally:
        try:
            exit_task_mode()
        except Exception:
            pass


def _verify_pytest(
    workspace_root: str | Path | None, scope_rel: str, goal: str = "pytest"
) -> bool:
    from ilim_assistant.motorlar.programlama_faz14 import run_project_verify

    v = run_project_verify(workspace_root, scope_rel, goal=goal)
    return bool(v and v.ok)


def scenario_api_add(
    workspace_root: str | Path | None,
    *,
    project_name: str | None = None,
) -> tuple[SloCheck, str]:
    """Senaryo 1: sıfırdan API + version + pytest."""
    from ilim_assistant.motorlar.programlama_faz25 import run_offline_parity_scenario

    t0 = time.monotonic()
    name = project_name or _slug("smoke-cursor-api")
    rep = run_offline_parity_scenario(workspace_root, project_name=name)
    core = [c for c in rep.checks if c.id in ("parity_agent_chain", "parity_health_version")]
    ok = rep.ok and all(c.ok for c in core)
    return (
        SloCheck(
            "cursor_api_add",
            "API ekle + pytest",
            ok,
            time.monotonic() - t0,
            _MAX_SCENARIO_SEC,
            rep.scope_rel,
        ),
        name,
    )


def scenario_bugfix_test(
    workspace_root: str | Path | None,
    *,
    project_name: str | None = None,
) -> tuple[SloCheck, str]:
    """Senaryo 2: bilerek kırık test → düzelt → pytest yeşil."""
    from ilim_assistant.motorlar.programlama_motoru import repo_root

    t0 = time.monotonic()
    name = project_name or _slug("smoke-cursor-bug")
    scope = f"projects/{name}"
    ok = False
    detail = scope
    try:
        from ilim_assistant.motorlar.programlama_faz6 import run_scaffold

        sc = run_scaffold("fastapi_api", name, workspace_root, force=True)
        if not sc.get("ok"):
            detail = str(sc.get("error") or "scaffold")[:100]
        else:
            broken = f"""@@write {scope}/app/main.py
```python
from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health():
    return {{"ok": "false"}}
```
@@write {scope}/tests/test_health.py
```python
from app.main import health


def test_health_ok():
    assert health()["ok"] == "true"
```
"""
            _apply_patch(workspace_root, broken)
            fail_before = not _verify_pytest(workspace_root, scope)
            fix = f"""@@write {scope}/app/main.py
```python
from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health():
    return {{"ok": "true", "version": "1.0.1-fix"}}
```
"""
            writes, _ = _apply_patch(workspace_root, fix)
            pass_after = _verify_pytest(workspace_root, scope)
            root = repo_root(workspace_root)
            has_fix = False
            if root:
                fp = root / scope.replace("/", os.sep) / "app" / "main.py"
                try:
                    has_fix = "1.0.1-fix" in fp.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    pass
            ok = fail_before and pass_after and writes >= 1 and has_fix
            detail = f"fail_before={fail_before} pass_after={pass_after} fix={has_fix}"
    except Exception as exc:
        detail = str(exc)[:120]
    return (
        SloCheck(
            "cursor_bugfix_test",
            "Bugfix + test",
            ok,
            time.monotonic() - t0,
            _MAX_SCENARIO_SEC,
            detail,
        ),
        name,
    )


def scenario_three_file_refactor(
    workspace_root: str | Path | None,
    *,
    project_name: str | None = None,
) -> tuple[SloCheck, str]:
    """Senaryo 3: üç dosyalı refactor + doğrulama."""
    from ilim_assistant.motorlar.programlama_motoru import repo_root

    t0 = time.monotonic()
    name = project_name or _slug("smoke-cursor-ref")
    scope = f"projects/{name}"
    ok = False
    detail = scope
    try:
        from ilim_assistant.motorlar.programlama_faz6 import run_scaffold

        sc = run_scaffold("fastapi_api", name, workspace_root, force=True)
        if not sc.get("ok"):
            detail = str(sc.get("error") or "scaffold")[:100]
        else:
            mod = name.replace("-", "_")
            patch = f"""@@write {scope}/app/util.py
```python
def greet(name: str) -> str:
    return f"merhaba {{name}}"
```
@@write {scope}/app/service.py
```python
from app.util import greet


def health_payload() -> dict[str, str]:
    return {{
        "ok": "true",
        "service": "{mod}",
        "version": "1.0.0-ref",
        "msg": greet("ruzgar"),
    }}
```
@@write {scope}/app/main.py
```python
from fastapi import FastAPI
from app.service import health_payload

app = FastAPI()


@app.get("/health")
def health():
    return health_payload()
```
@@write {scope}/tests/test_refactor.py
```python
from app.util import greet
from app.service import health_payload


def test_greet():
    assert "ruzgar" in greet("ruzgar")


def test_health_payload():
    assert health_payload()["ok"] == "true"
```
"""
            writes, wok = _apply_patch(workspace_root, patch)
            root = repo_root(workspace_root)
            paths_ok = False
            if root:
                base = root / scope.replace("/", os.sep)
                paths_ok = all(
                    (base / p).is_file()
                    for p in ("app/util.py", "app/service.py", "app/main.py")
                )
            pytest_ok = _verify_pytest(workspace_root, scope)
            ok = wok and writes >= 3 and paths_ok and pytest_ok
            detail = f"writes={writes} files={paths_ok} pytest={pytest_ok}"
    except Exception as exc:
        detail = str(exc)[:120]
    return (
        SloCheck(
            "cursor_three_file_refactor",
            "3 dosya refactor",
            ok,
            time.monotonic() - t0,
            _MAX_SCENARIO_SEC * 1.5,
            detail,
        ),
        name,
    )


def compute_cursor_score(
    scenarios: list[SloCheck],
    capabilities: dict[str, bool],
) -> tuple[int, int, int]:
    """(toplam, kabiliyet_puan, senaryo_puan)."""
    cap_pts = _capability_points(capabilities)
    weights = {
        "cursor_api_add": 22,
        "cursor_bugfix_test": 22,
        "cursor_three_file_refactor": 21,
    }
    scen_pts = 0
    for s in scenarios:
        if s.ok:
            scen_pts += weights.get(s.id, 15)
    total = min(100, cap_pts + scen_pts)
    return total, cap_pts, scen_pts


def run_cursor_seviye_assessment(
    workspace_root: str | Path | None,
) -> CursorSeviyeReport:
    """Üç senaryo + kabiliyet kartı → Cursor seviye raporu."""
    if not _enabled():
        return CursorSeviyeReport(
            ok=False,
            score=0,
            warnings=["Faz 46 kapalı (RUZGAR_FAZ46=0)"],
        )

    capabilities = build_extended_capability_scorecard()
    scenarios: list[SloCheck] = []
    projects: dict[str, str] = {}

    s1, n1 = scenario_api_add(workspace_root)
    scenarios.append(s1)
    projects["api_add"] = n1

    s2, n2 = scenario_bugfix_test(workspace_root)
    scenarios.append(s2)
    projects["bugfix_test"] = n2

    s3, n3 = scenario_three_file_refactor(workspace_root)
    scenarios.append(s3)
    projects["three_file_refactor"] = n3

    score, cap_pts, scen_pts = compute_cursor_score(scenarios, capabilities)
    warnings: list[str] = []
    if score < TARGET_CURSOR_SCORE:
        failed = [s.label for s in scenarios if not s.ok]
        cap_fail = [k for k, v in capabilities.items() if not v]
        warnings.append(
            f"Cursor seviye {score}/{TARGET_CURSOR_SCORE} — hedef altında (CI bloklamaz)."
        )
        if failed:
            warnings.append(f"Kırmızı senaryo: {', '.join(failed)}")
        if cap_fail:
            warnings.append(f"Kapalı kabiliyet: {', '.join(cap_fail[:8])}")

    ok = score >= TARGET_CURSOR_SCORE and all(s.ok for s in scenarios)
    return CursorSeviyeReport(
        ok=ok,
        score=score,
        scenarios=scenarios,
        capabilities=capabilities,
        capability_points=cap_pts,
        scenario_points=scen_pts,
        project_names=projects,
        warnings=warnings,
    )


def format_cursor_seviye_report(report: CursorSeviyeReport) -> str:
    mark = "HEDEF" if report.score >= report.target_score else "UYARI"
    lines = [
        f"Ümit abi, **Cursor seviye kilidi** (Faz 46) — **{report.score}/100** [{mark}]",
        f"Hedef: ≥{report.target_score}/100",
        "",
        f"Kabiliyet puanı: {report.capability_points}/35 · "
        f"Senaryo puanı: {report.scenario_points}/65",
        "",
        "**Kabiliyetler (Faz 20–45):**",
    ]
    for k, v in sorted((report.capabilities or {}).items()):
        lines.append(f"  {'✓' if v else '✗'} {k}")
    lines.extend(["", "**3 senaryo:**"])
    for s in report.scenarios:
        lines.append(
            f"  {'✓' if s.ok else '✗'} {s.label}"
            + (f" ({s.elapsed_sec:.2f}s)" if s.elapsed_sec > 0 else "")
            + (f" — {s.detail}" if s.detail else "")
        )
    for w in report.warnings:
        lines.extend(["", f"⚠ {w}"])
    lines.append(f"\n({CURSOR_PARITY_VERSION})")
    return "\n".join(lines)


def save_cursor_seviye_json(
    report: CursorSeviyeReport,
    path: str | Path | None = None,
) -> str | None:
    if path is None:
        path = (
            Path(__file__).resolve().parents[2]
            / "scripts"
            / "ruzgar_cursor_seviye_sonuc.json"
        )
    fp = Path(path)
    try:
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(
            json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return str(fp)
    except OSError:
        return None


def ci_score_warning(report: CursorSeviyeReport) -> str | None:
    """Skor <85 ise uyarı metni (CI bloklamaz)."""
    if report.score >= TARGET_CURSOR_SCORE:
        return None
    return (
        f"UYARI: Cursor seviye {report.score}/100 < {TARGET_CURSOR_SCORE} "
        "(kilidi geçmedi — CI bloklamaz)"
    )
