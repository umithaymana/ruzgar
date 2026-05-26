# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 54: KPI kilidi (parity 8/8 + compliance v3 + dashboard).

- scripts/ruzgar_parity_smoke.py → 8 kontrol
- agent_compliance v3: hedef ≥85 + parity özeti
- Atölye KPI kartı API
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

FAZ54_VERSION = "programlama-faz54-v1-2026-05-26"
PARITY_SMOKE_TOTAL = 8
_KPI_JSON = "ruzgar_parity_smoke_sonuc.json"
_COMPLIANCE_FILE = "agent_compliance.json"


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ54", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz54_enabled() -> bool:
    return _enabled()


def target_kpi_score() -> int:
    try:
        return max(50, min(100, int(os.environ.get("RUZGAR_KPI_TARGET", "85"))))
    except ValueError:
        return 85


@dataclass
class ParitySmokeCheck:
    id: str
    label: str
    ok: bool
    elapsed_sec: float = 0.0
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "ok": self.ok,
            "elapsed_sec": round(self.elapsed_sec, 3),
            "detail": self.detail,
        }


@dataclass
class ParitySmokeReport:
    ok: bool
    passed: int
    total: int
    checks: list[ParitySmokeCheck] = field(default_factory=list)
    groq_e2e_ran: bool = False
    mode: str = "full"
    elapsed_sec: float = 0.0
    version: str = FAZ54_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "passed": self.passed,
            "total": self.total,
            "checks": [c.to_dict() for c in self.checks],
            "groq_e2e_ran": self.groq_e2e_ran,
            "mode": self.mode,
            "elapsed_sec": round(self.elapsed_sec, 3),
            "version": self.version,
        }


def build_kpi_capability_scorecard() -> dict[str, bool]:
    """Faz 20–54 kabiliyet matrisi."""
    try:
        from ilim_assistant.motorlar.programlama_cursor_parity import (
            build_extended_capability_scorecard,
        )

        card = build_extended_capability_scorecard()
    except Exception:
        card = {}

    def _flag(key: str, mod: str, attr: str) -> None:
        try:
            m = __import__(f"ilim_assistant.motorlar.{mod}", fromlist=[attr])
            card[key] = bool(getattr(m, attr)())
        except Exception:
            card[key] = False

    _flag("proje_uret", "programlama_faz47", "proje_uret_enabled")
    _flag("compliance_v2", "programlama_faz48", "compliance_v2_enabled")
    _flag("natural_proje", "programlama_faz50", "faz50_enabled")
    _flag("templates_faz51", "programlama_faz51", "faz51_enabled")
    _flag("fc_primary", "programlama_faz52", "structured_task_mode_enabled")
    _flag("symbol_lite", "programlama_faz53", "symbol_lite_enabled")
    _flag("kpi_faz54", "programlama_faz54", "faz54_enabled")
    return card


def _check_capabilities() -> ParitySmokeCheck:
    t0 = time.monotonic()
    card = build_kpi_capability_scorecard()
    on = sum(1 for v in card.values() if v)
    need = min(12, max(8, len(card) - 4))
    ok = on >= need
    return ParitySmokeCheck(
        "kpi_capabilities",
        "Kabiliyet matrisi (Faz 20–54)",
        ok,
        time.monotonic() - t0,
        f"{on}/{len(card)} acik (hedef >={need})",
    )


def _check_tools_schema() -> ParitySmokeCheck:
    t0 = time.monotonic()
    ok = False
    detail = ""
    try:
        from ilim_assistant.motorlar.programlama_faz40 import (
            openai_tools_schema,
            structured_tools_enabled,
        )

        schema = openai_tools_schema()
        ok = structured_tools_enabled() and len(schema) >= 5
        detail = f"tools={len(schema)}"
    except Exception as exc:
        detail = str(exc)[:80]
    return ParitySmokeCheck(
        "structured_tools",
        "Function calling şeması",
        ok,
        time.monotonic() - t0,
        detail,
    )


def _check_compliance_offline(
    workspace_root: str | Path | None = None,
) -> ParitySmokeCheck:
    t0 = time.monotonic()
    try:
        from ilim_assistant.motorlar.programlama_motoru import repo_root

        root = repo_root(workspace_root)
        from ilim_assistant.motorlar.programlama_faz48 import run_offline_compliance_smoke

        res = run_offline_compliance_smoke(root)
        ok = bool(res.get("ok")) and int(res.get("score", 0)) >= target_kpi_score()
        detail = f"score={res.get('score')} target={res.get('target')}"
    except Exception as exc:
        ok = False
        detail = str(exc)[:80]
    return ParitySmokeCheck(
        "compliance_v3_offline",
        f"Uyum smoke ≥{target_kpi_score()}",
        ok,
        time.monotonic() - t0,
        detail,
    )


def _check_faz51_templates() -> ParitySmokeCheck:
    t0 = time.monotonic()
    ok = False
    try:
        from ilim_assistant.motorlar.programlama_faz6 import list_templates

        ids = {t["id"] for t in list_templates()}
        need = {"crud_api", "auth_jwt", "dashboard_static"}
        ok = need.issubset(ids)
        detail = f"missing={need - ids}" if not ok else "faz51 ok"
    except Exception as exc:
        detail = str(exc)[:80]
    return ParitySmokeCheck(
        "templates_faz51",
        "Faz 51 şablonları",
        ok,
        time.monotonic() - t0,
        detail,
    )


def _check_faz52_53() -> ParitySmokeCheck:
    t0 = time.monotonic()
    try:
        from ilim_assistant.motorlar.programlama_faz52 import (
            faz52_enabled,
            tool_choice_for_task,
        )
        from ilim_assistant.motorlar.programlama_faz53 import patch_api_enrichments

        flags = patch_api_enrichments()
        ok = (
            faz52_enabled()
            and tool_choice_for_task(mandate=True) == "required"
            and flags.get("multi_file_preview_default")
        )
        detail = str(flags)[:80]
    except Exception as exc:
        ok = False
        detail = str(exc)[:80]
    return ParitySmokeCheck(
        "faz52_53_wiring",
        "FC birincil + Atölye v2",
        ok,
        time.monotonic() - t0,
        detail,
    )


def _check_faz50_parse() -> ParitySmokeCheck:
    t0 = time.monotonic()
    ok = False
    try:
        from ilim_assistant.motorlar.programlama_faz50 import parse_faz50_proje_uret

        spec = parse_faz50_proje_uret("bana bir web sitesi yap vitrin-test")
        ok = bool(spec and spec.template_id == "static_site")
        detail = str(spec.template_id if spec else "none")
    except Exception as exc:
        detail = str(exc)[:80]
    return ParitySmokeCheck(
        "faz50_natural",
        "Doğal dil proje üret",
        ok,
        time.monotonic() - t0,
        detail,
    )


def _check_cursor_scenario(
    fn_name: str,
    check_id: str,
    label: str,
) -> ParitySmokeCheck:
    t0 = time.monotonic()
    try:
        from ilim_assistant.motorlar.programlama_motoru import repo_root
        from ilim_assistant.motorlar import programlama_cursor_parity as cp

        root = repo_root(None)
        fn = getattr(cp, fn_name)
        slo, _name = fn(root)
        ok = bool(slo.ok)
        detail = str(slo.detail or "")[:100]
    except Exception as exc:
        ok = False
        detail = str(exc)[:100]
    return ParitySmokeCheck(check_id, label, ok, time.monotonic() - t0, detail)


def _check_proje_uret_fastapi(
    workspace_root: str | Path | None,
    *,
    scaffold_only: bool = False,
) -> ParitySmokeCheck:
    t0 = time.monotonic()
    try:
        from ilim_assistant.motorlar.programlama_faz47 import (
            ProjeUretSpec,
            run_proje_uret_prepare,
        )

        pn = f"smoke-parity-api-{int(time.time()) % 100000}"
        rep = run_proje_uret_prepare(
            workspace_root,
            ProjeUretSpec("fastapi_api", pn, "pytest"),
        )
        ok = rep.scaffold_ok and (
            scaffold_only or (rep.verify_ok and rep.ready_without_agent)
        )
        detail = f"scaffold={rep.scaffold_ok} verify={rep.verify_ok}"
    except Exception as exc:
        ok = False
        detail = str(exc)[:80]
    return ParitySmokeCheck(
        "proje_uret_fastapi",
        "Proje üret FastAPI",
        ok,
        time.monotonic() - t0,
        detail,
    )


def _check_proje_uret_crud(
    workspace_root: str | Path | None,
    *,
    scaffold_only: bool = False,
) -> ParitySmokeCheck:
    t0 = time.monotonic()
    try:
        from ilim_assistant.motorlar.programlama_faz47 import (
            ProjeUretSpec,
            run_proje_uret_prepare,
        )

        pn = f"smoke-parity-crud-{int(time.time()) % 100000}"
        rep = run_proje_uret_prepare(
            workspace_root,
            ProjeUretSpec("crud_api", pn, "pytest"),
        )
        ok = rep.scaffold_ok and (
            scaffold_only or (rep.verify_ok and rep.ready_without_agent)
        )
        detail = f"scaffold={rep.scaffold_ok} verify={rep.verify_ok}"
    except Exception as exc:
        ok = False
        detail = str(exc)[:80]
    return ParitySmokeCheck(
        "proje_uret_crud",
        "Proje üret CRUD (Faz 51)",
        ok,
        time.monotonic() - t0,
        detail,
    )


def _check_groq_e2e() -> ParitySmokeCheck:
    t0 = time.monotonic()
    if not os.environ.get("GROQ_API_KEY", "").strip():
        return ParitySmokeCheck(
            "groq_e2e_optional",
            "Groq E2E (opsiyonel)",
            True,
            time.monotonic() - t0,
            "GROQ_API_KEY yok — atlandı (OK)",
        )
    try:
        from ilim_assistant.motorlar.programlama_faz40 import chat_completion_with_tools

        text, batch = chat_completion_with_tools(
            "Test.",
            "Ping: respond with OK only.",
            tool_choice="auto",
        )
        ok = bool(text) or bool(batch)
        detail = f"text={len(text)} tools={len(batch)}"
    except Exception as exc:
        ok = False
        detail = str(exc)[:80]
    return ParitySmokeCheck(
        "groq_e2e_optional",
        "Groq E2E (opsiyonel)",
        ok,
        time.monotonic() - t0,
        detail,
    )


def run_parity_smoke_suite(
    workspace_root: str | Path | None,
    *,
    mode: str = "full",
    groq_e2e: bool = False,
) -> ParitySmokeReport:
    """
    8 kontrol — full: 3 cursor senaryo + 5 hızlı; quick: 8 hızlı (senaryosuz).
    """
    if not _enabled():
        return ParitySmokeReport(
            ok=False,
            passed=0,
            total=PARITY_SMOKE_TOTAL,
            mode=mode,
        )

    t0 = time.monotonic()
    quick = mode.strip().lower() in ("quick", "fast")

    if quick:
        checks = [
            _check_capabilities(),
            _check_tools_schema(),
            _check_compliance_offline(workspace_root),
            _check_faz51_templates(),
            _check_faz52_53(),
            _check_faz50_parse(),
            _check_proje_uret_fastapi(workspace_root, scaffold_only=True),
            _check_proje_uret_crud(workspace_root, scaffold_only=True),
        ]
    else:
        checks = [
            _check_cursor_scenario(
                "scenario_api_add", "parity_api", "Cursor API + pytest"
            ),
            _check_cursor_scenario(
                "scenario_bugfix_test", "parity_bugfix", "Cursor bugfix"
            ),
            _check_cursor_scenario(
                "scenario_three_file_refactor",
                "parity_refactor",
                "Cursor 3 dosya",
            ),
            _check_compliance_offline(workspace_root),
            _check_capabilities(),
            _check_tools_schema(),
            _check_faz51_templates(),
            _check_faz52_53() if not groq_e2e else _check_groq_e2e(),
        ]

    passed = sum(1 for c in checks if c.ok)
    all_ok = passed == PARITY_SMOKE_TOTAL and all(c.ok for c in checks)
    return ParitySmokeReport(
        ok=all_ok,
        passed=passed,
        total=PARITY_SMOKE_TOTAL,
        checks=checks,
        groq_e2e_ran=groq_e2e,
        mode=mode,
        elapsed_sec=time.monotonic() - t0,
    )


def save_parity_smoke_json(
    report: ParitySmokeReport,
    path: str | Path | None = None,
) -> str | None:
    if path is None:
        path = (
            Path(__file__).resolve().parents[2]
            / "scripts"
            / _KPI_JSON
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


def load_parity_smoke_json(path: str | Path | None = None) -> dict[str, Any]:
    if path is None:
        path = Path(__file__).resolve().parents[2] / "scripts" / _KPI_JSON
    fp = Path(path)
    if not fp.is_file():
        return {}
    try:
        return json.loads(fp.read_text(encoding="utf-8"))
    except Exception:
        return {}


def compliance_v3_enabled() -> bool:
    return _enabled()


def build_compliance_report_v3(
    workspace_root: str | Path | None,
) -> dict[str, Any]:
    """Faz 48 + parity KPI özeti."""
    try:
        from ilim_assistant.motorlar.programlama_faz48 import (
            FAZ48_VERSION,
            build_compliance_report_v2,
            target_compliance_score,
        )

        base = build_compliance_report_v2(workspace_root)
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:200]}

    parity = load_parity_smoke_json()
    rep = dict(base.get("report") or {})
    target = target_compliance_score()
    passed = int(parity.get("passed") or 0)
    total = int(parity.get("total") or PARITY_SMOKE_TOTAL)
    parity_ok = bool(parity.get("ok"))
    meets = bool(rep.get("meets_target"))
    overall = meets and (parity_ok or passed >= total)

    rep.update(
        {
            "kpi_version": 3,
            "target_score": target,
            "parity_passed": passed,
            "parity_total": total,
            "parity_ok": parity_ok,
            "overall_kpi_ok": overall,
            "parity_mode": parity.get("mode"),
            "parity_at": parity.get("elapsed_sec"),
        }
    )
    return {
        "ok": bool(base.get("ok")),
        "report": rep,
        "version": FAZ54_VERSION,
        "base_version": FAZ48_VERSION,
    }


def persist_compliance_v3_snapshot(
    workspace_root: str | Path | None,
    report: dict[str, Any],
) -> None:
    try:
        from ilim_assistant.motorlar.programlama_faz48 import _score_path

        path = _score_path(workspace_root)
        if path is None:
            return
        data: dict[str, Any] = {}
        if path.is_file():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                pass
        data["kpi_v3"] = {
            "saved_at": time.time(),
            "report": report.get("report") or {},
            "version": FAZ54_VERSION,
        }
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        pass


def format_compliance_report_v3(workspace_root: str | Path | None) -> str:
    data = build_compliance_report_v3(workspace_root)
    if not data.get("ok"):
        return f"KPI raporu alınamadı: {data.get('error')}"
    r = data.get("report") or {}
    target = r.get("target_score", target_kpi_score())
    lines = [
        "Ümit abi, **KPI dashboard v3** (Faz 54):",
        "",
        f"Uyum: **{r.get('score', 0)}/100** · not **{r.get('grade', '—')}**",
        f"Parity smoke: **{r.get('parity_passed', 0)}/{r.get('parity_total', 8)}**",
        f"Hedef ≥{target} — "
        f"{'✓ genel KPI OK' if r.get('overall_kpi_ok') else 'henüz tam değil'}",
    ]
    for note in r.get("notes") or []:
        lines.append(f"· {note}")
    lines.append(f"\n({FAZ54_VERSION})")
    return "\n".join(lines)


def build_kpi_dashboard(workspace_root: str | Path | None) -> dict[str, Any]:
    """Atölye KPI kartı — compliance v3 + son parity."""
    comp = build_compliance_report_v3(workspace_root)
    parity = load_parity_smoke_json()
    cap = build_kpi_capability_scorecard()
    on = sum(1 for v in cap.values() if v)
    rep = comp.get("report") or {}
    return {
        "ok": True,
        "compliance": rep,
        "parity": parity,
        "capabilities": cap,
        "capabilities_on": on,
        "capabilities_total": len(cap),
        "target_score": rep.get("target_score", target_kpi_score()),
        "meets_target": bool(rep.get("meets_target")),
        "overall_kpi_ok": bool(rep.get("overall_kpi_ok")),
        "version": FAZ54_VERSION,
    }


def run_parity_smoke_and_persist(
    workspace_root: str | Path | None,
    *,
    mode: str = "full",
    groq_e2e: bool = False,
) -> ParitySmokeReport:
    report = run_parity_smoke_suite(
        workspace_root, mode=mode, groq_e2e=groq_e2e
    )
    save_parity_smoke_json(report)
    comp = build_compliance_report_v3(workspace_root)
    persist_compliance_v3_snapshot(workspace_root, comp)
    return report


def faz54_directive() -> str:
    return (
        "[KPI KİLİDİ — Faz 54]\n"
        f"Parity smoke 8/8 · uyum ≥{target_kpi_score()} · `python scripts/ruzgar_parity_smoke.py`\n"
        "Kapat: RUZGAR_FAZ54=0\n"
    )
