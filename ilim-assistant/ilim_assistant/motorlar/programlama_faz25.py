# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 25: Cursor parity smoke.

Offline: fastapi scaffold → health+version patch → pytest (API/LLM yok).
Canlı: --parity-live ile sunucu + isteğe bağlı Groq görev turu.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ilim_assistant.motorlar.programlama_faz18 import SloCheck

FAZ25_VERSION = "programlama-faz25-v1-2026-05-25"
DEFAULT_PARITY_SLO_SEC = 300.0


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ25", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def parity_slo_sec() -> float:
    try:
        return float(os.environ.get("RUZGAR_PARITY_SLO_SEC", str(DEFAULT_PARITY_SLO_SEC)))
    except ValueError:
        return DEFAULT_PARITY_SLO_SEC


def _slug_unique(prefix: str = "smoke-parity") -> str:
    return f"{prefix}-{int(time.time()) % 100000}"


@dataclass
class ParityRunReport:
    ok: bool
    checks: list[SloCheck] = field(default_factory=list)
    project_name: str = ""
    scope_rel: str = ""
    scorecard: dict[str, bool] = field(default_factory=dict)
    version: str = FAZ25_VERSION
    live_skipped: bool = True
    live_note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "checks": [c.to_dict() for c in self.checks],
            "project_name": self.project_name,
            "scope_rel": self.scope_rel,
            "scorecard": self.scorecard,
            "parity_slo_sec": parity_slo_sec(),
            "version": self.version,
            "live_skipped": self.live_skipped,
            "live_note": self.live_note,
        }


def build_parity_scorecard() -> dict[str, bool]:
    """Faz 20–24 kabiliyet bayrakları (offline doğrulama)."""
    card: dict[str, bool] = {}

    def _flag(key: str, fn: Any) -> None:
        try:
            card[key] = bool(fn())
        except Exception:
            card[key] = False

    _flag(
        "unified_agent",
        lambda: __import__(
            "ilim_assistant.motorlar.programlama_faz20", fromlist=["unified_agent_enabled"]
        ).unified_agent_enabled(),
    )
    _flag(
        "light_context",
        lambda: __import__(
            "ilim_assistant.motorlar.programlama_faz21", fromlist=["light_context_enabled"]
        ).light_context_enabled(),
    )
    _flag(
        "symbol_index",
        lambda: __import__(
            "ilim_assistant.motorlar.programlama_faz22", fromlist=["_enabled"]
        )._enabled(),
    )
    _flag(
        "task_5min",
        lambda: __import__(
            "ilim_assistant.motorlar.programlama_faz23", fromlist=["resolve_code_agent_budget_sec"]
        ).resolve_code_agent_budget_sec()
        >= 300.0,
    )
    _flag(
        "agent_steps_sse",
        lambda: __import__(
            "ilim_assistant.motorlar.programlama_faz24", fromlist=["sse_steps_enabled"]
        ).sse_steps_enabled(),
    )
    _flag(
        "implementation_intent",
        lambda: __import__(
            "ilim_assistant.motorlar.programlama_faz20", fromlist=["wants_implementation_agent"]
        ).wants_implementation_agent(
            "benim-api health version ekle ve pytest gecir", "programlama"
        ),
    )
    return card


def _health_patch_for_scope(scope_rel: str, slug: str) -> str:
    mod = slug.replace("-", "_")
    rel = f"{scope_rel}/app/main.py"
    body = f'''"""FastAPI — parity smoke"""
from __future__ import annotations

from fastapi import FastAPI

app = FastAPI(title="{slug}")


@app.get("/health")
def health() -> dict[str, str]:
    return {{"ok": "true", "service": "{mod}", "version": "1.0.0-parity"}}


@app.get("/items")
def list_items() -> list[dict[str, str]]:
    return [{{"id": "1", "name": "ornek"}}]
'''
    return f"@@write {rel}\n```python\n{body}\n```\n"


def run_offline_parity_scenario(
    workspace_root: str | Path | None,
    *,
    project_name: str | None = None,
) -> ParityRunReport:
    """
    Cursor-benzeri zincir (offline):
    scaffold fastapi → otomatik patch (version) → pytest geçer.
    """
    from ilim_assistant.motorlar.programlama_motoru import (
        apply_assistant_reply_tools,
        repo_root,
    )

    checks: list[SloCheck] = []
    scorecard = build_parity_scorecard()
    name = project_name or _slug_unique()
    scope_rel = f"projects/{name}"
    budget = parity_slo_sec()
    t0_all = time.monotonic()

    # 1 — Scaffold
    t0 = time.monotonic()
    try:
        from ilim_assistant.motorlar.programlama_faz6 import run_scaffold

        res = run_scaffold("fastapi_api", name, workspace_root, force=True)
        elapsed = time.monotonic() - t0
        ok = bool(res.get("ok")) and elapsed <= min(budget, 60.0)
        checks.append(
            SloCheck(
                "parity_scaffold",
                "FastAPI scaffold",
                ok,
                elapsed,
                min(budget, 60.0),
                str(res.get("base_dir") or res.get("error") or "")[:100],
            )
        )
    except Exception as exc:
        checks.append(
            SloCheck(
                "parity_scaffold",
                "FastAPI scaffold",
                False,
                time.monotonic() - t0,
                budget,
                str(exc)[:120],
            )
        )
        return ParityRunReport(
            ok=False,
            checks=checks,
            project_name=name,
            scope_rel=scope_rel,
            scorecard=scorecard,
        )

    # 2 — Görev modu + otomatik patch (Faz 23)
    t0 = time.monotonic()
    patch_text = _health_patch_for_scope(scope_rel, name)
    writes_ok = 0
    verify_ok = False
    verify_detail = ""
    try:
        from ilim_assistant.motorlar.programlama_faz23 import (
            enter_task_mode,
            exit_task_mode,
            task_mode_active,
        )

        enter_task_mode()
        assert task_mode_active()
        summ, _ = apply_assistant_reply_tools(
            patch_text,
            workspace_root,
            run_pytest=False,
        )
        writes_ok = len([w for w in summ.writes if w.ok])
        from ilim_assistant.motorlar.programlama_faz14 import run_project_verify

        verify = run_project_verify(
            workspace_root,
            scope_rel,
            goal="pytest gecir health version",
        )
        verify_ok = bool(verify and verify.ok)
        verify_detail = (verify.output if verify else "")[:200]
        exit_task_mode()
        elapsed = time.monotonic() - t0
        ok = writes_ok >= 1 and verify_ok and elapsed <= budget
        checks.append(
            SloCheck(
                "parity_agent_chain",
                "Patch + pytest (görev modu)",
                ok,
                elapsed,
                budget,
                f"writes={writes_ok} verify={verify_ok}",
            )
        )
    except Exception as exc:
        try:
            from ilim_assistant.motorlar.programlama_faz23 import exit_task_mode

            exit_task_mode()
        except Exception:
            pass
        checks.append(
            SloCheck(
                "parity_agent_chain",
                "Patch + pytest",
                False,
                time.monotonic() - t0,
                budget,
                str(exc)[:120],
            )
        )

    # 3 — Dosya içeriği
    t0 = time.monotonic()
    root = repo_root(workspace_root)
    has_version = False
    if root is not None:
        main_fp = root / scope_rel.replace("/", os.sep) / "app" / "main.py"
        try:
            txt = main_fp.read_text(encoding="utf-8", errors="replace")
            has_version = "version" in txt and "health" in txt
        except OSError:
            pass
    checks.append(
        SloCheck(
            "parity_health_version",
            "health endpoint version alanı",
            has_version,
            time.monotonic() - t0,
            0.0,
            scope_rel,
        )
    )

    # 4 — Scorecard
    score_ok = all(scorecard.values()) if scorecard else False
    failed = [k for k, v in scorecard.items() if not v]
    checks.append(
        SloCheck(
            "parity_scorecard",
            "Faz 20–24 scorecard",
            score_ok,
            0.0,
            0.0,
            "" if score_ok else ", ".join(failed[:6]),
        )
    )

    elapsed_all = time.monotonic() - t0_all
    core_ok = all(c.ok for c in checks)
    checks.append(
        SloCheck(
            "parity_total",
            "Parity paketi toplam",
            core_ok and elapsed_all <= budget,
            elapsed_all,
            budget,
            f"{name}",
        )
    )

    ok_all = all(c.ok for c in checks)
    return ParityRunReport(
        ok=ok_all,
        checks=checks,
        project_name=name,
        scope_rel=scope_rel,
        scorecard=scorecard,
    )


def format_parity_report(report: ParityRunReport) -> str:
    lines = [
        f"Ümit abi, **Cursor parity** (Faz 25) — {'GEÇTİ' if report.ok else 'KIRMIZI'}",
        "",
        f"Proje: `{report.scope_rel}` · bütçe {int(parity_slo_sec())} sn",
        "",
        "**Scorecard (Faz 20–24):**",
    ]
    for k, v in sorted((report.scorecard or {}).items()):
        lines.append(f"  {'✓' if v else '✗'} {k}")
    lines.extend(["", "**Senaryolar:**"])
    for c in report.checks:
        mark = "✓" if c.ok else "✗"
        lines.append(
            f"  {mark} {c.label}"
            + (f" ({c.elapsed_sec:.2f}s)" if c.elapsed_sec > 0 else "")
            + (f" — {c.detail}" if c.detail else "")
        )
    if report.live_note:
        lines.extend(["", report.live_note])
    lines.append(f"\n({FAZ25_VERSION})")
    technical = "\n".join(lines)
    try:
        from ilim_assistant.motorlar.programlama_faz97 import (
            choose_report,
            format_sade_parity_run,
            sade_rapor_enabled,
        )

        if sade_rapor_enabled():
            return choose_report(technical, format_sade_parity_run(report))
    except Exception:
        pass
    return technical


def save_parity_report_json(
    report: ParityRunReport,
    path: str | Path | None = None,
) -> str | None:
    if path is None:
        path = Path(__file__).resolve().parents[2] / "scripts" / "ruzgar_parity_smoke_sonuc.json"
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


def run_live_parity_preflight(base_url: str, workspace_root: str | Path | None) -> ParityRunReport:
    """Sunucu ayaktaysa: build rev + parity offline tekrar (API üzerinden kalite)."""
    import urllib.parse
    import urllib.request

    checks: list[SloCheck] = []
    base = base_url.rstrip("/")
    enc = urllib.parse.quote(str(workspace_root or ""), safe="")
    live_note = ""
    try:
        with urllib.request.urlopen(f"{base}/api/health", timeout=15) as r:
            h = json.loads(r.read())
        rev = str((h.get("build") or {}).get("rev") or "")
        ok_rev = "faz2" in rev and "programlama" in rev
        checks.append(
            SloCheck(
                "live_build",
                "Build rev programlama",
                ok_rev,
                0.0,
                0.0,
                rev[:80],
            )
        )
    except Exception as exc:
        checks.append(
            SloCheck("live_build", "Health API", False, 0.0, 0.0, str(exc)[:80])
        )
        return ParityRunReport(
            ok=False,
            checks=checks,
            scorecard=build_parity_scorecard(),
            live_skipped=False,
            live_note="Canlı preflight başarısız.",
        )

    groq = bool(os.environ.get("GROQ_API_KEY", "").strip())
    if groq:
        live_note = (
            "GROQ_API_KEY tanımlı — tam LLM görev turu için masaüstünde "
            "«benim-api health version ekle pytest geçir» deneyin."
        )
    else:
        live_note = (
            "GROQ_API_KEY yok — canlı LLM görev turu atlandı; offline parity yeterli."
        )

    offline = run_offline_parity_scenario(workspace_root)
    checks.extend(offline.checks)
    ok = all(c.ok for c in checks)
    rep = ParityRunReport(
        ok=ok,
        checks=checks,
        project_name=offline.project_name,
        scope_rel=offline.scope_rel,
        scorecard=offline.scorecard,
        live_skipped=not groq,
        live_note=live_note,
    )
    return rep


def faz25_directive() -> str:
    return (
        "[CURSOR PARITY — Faz 25]\n"
        "Smoke: `python scripts/programlama_smoke.py --parity` veya `--ci` (dahil).\n"
        f"SLO: sıfırdan API + pytest < {int(DEFAULT_PARITY_SLO_SEC)} sn (offline).\n"
    )
