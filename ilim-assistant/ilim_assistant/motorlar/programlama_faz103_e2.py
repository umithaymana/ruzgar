# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 103 / E2 dilim 2: çok dosya pili + mega ölçüm.

Offline (LLM yok):
  1) niyet → agent_multi / agent_mega / faz85
  2) monorepo 3 dosya refactor gate
  3) cursor parity üç dosya refactor
  4) mega limit + workbench KPI

Canlı (--live): çok dosyalı ajan senaryosu (Ollama/Groq/Gemini).

Komut: «e2 pil» · «çok dosya pil»
API: GET /api/programlama/combined-e2-battery
"""

from __future__ import annotations

import os
import re
import time
import unicodedata
from pathlib import Path
from typing import Any

FAZ103_VERSION = "programlama-faz103-e2-v1-2026-10-20"
_E2_BATTERY_TARGET = 0.90
_INTENT_CASES: list[tuple[str, str]] = [
    ("health endpointine version 2.0.0 ekle pytest gecir", "faz85_fast"),
    ("app/main.py ve app/api.py refactor et", "agent_multi"),
    ("iki dosyada auth ekle", "agent_multi"),
    ("mega refactor 10+ dosya", "agent_mega"),
    ("cok dosyali monorepo duzenle", "agent_multi"),
]
_E2_GOAL_RE = re.compile(
    r"(?:multi\s*file|çok\s*dosya|cok\s*dosya|iki\s*dosya|üç\s*dosya|uc\s*dosya|"
    r"mega\s*refactor|10\+\s*dosya|ve\s+[\w./\\-]+\.py|"
    r"dosyada|monorepo|triple|üç\s*cerrahi)",
    re.I,
)
_BATTERY_RE = re.compile(
    r"(?:e2\s*pil|çok\s*dosya\s*pil|cok\s*dosya\s*pil|"
    r"e2\s*battery|multi.?file\s*battery|combined.?e2)",
    re.I,
)


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ103", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz103_enabled() -> bool:
    return _enabled()


def e2_battery_target() -> float:
    try:
        from ilim_assistant.motorlar.programlama_mega_workbench import e2_target_rate

        return float(e2_target_rate())
    except Exception:
        return _E2_BATTERY_TARGET


def _ascii_fold(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def wants_e2_battery(message: str) -> bool:
    if not _enabled():
        return False
    return bool(_BATTERY_RE.search(_ascii_fold(message)))


def live_llm_requested() -> bool:
    return os.environ.get("RUZGAR_E2_BATTERY_LIVE", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def is_e2_outcome(row: dict[str, Any]) -> bool:
    """Çok dosya / mega KPI satırı mı? (Faz85 tek-dosya gürültüsü sayılmaz.)"""
    if not isinstance(row, dict):
        return False
    src = str(row.get("source") or "").lower()
    if src.startswith("e2_") or "e2_battery" in src:
        return True
    if "monorepo" in src or "multi_file" in src or "mega_refactor" in src:
        return True
    goal = str(row.get("goal") or "")
    if _E2_GOAL_RE.search(goal):
        return True
    return False


def compute_e2_stats(
    workspace_root: str | Path | None,
    *,
    window_days: int = 30,
) -> dict[str, Any]:
    target = e2_battery_target()
    empty = {
        "ok": True,
        "total": 0,
        "success_count": 0,
        "success_rate": 0.0,
        "target_rate": target,
        "meets_target": False,
        "window_days": window_days,
        "recent": [],
    }
    try:
        from ilim_assistant.motorlar.programlama_faz55 import _load_store, _outcomes_path
    except Exception:
        return {**empty, "ok": False, "error": "faz55"}
    path = _outcomes_path(workspace_root)
    if path is None or not path.is_file():
        return empty
    store = _load_store(path)
    cutoff = time.time() - window_days * 86400
    raw = [
        o
        for o in (store.get("outcomes") or [])
        if isinstance(o, dict) and float(o.get("ts") or 0) >= cutoff
    ]
    rows = [o for o in raw if is_e2_outcome(o)]
    if not rows:
        return {**empty, "filtered_from": len(raw)}
    ok_n = sum(1 for r in rows if r.get("success"))
    total = len(rows)
    rate = ok_n / total if total else 0.0
    return {
        "ok": True,
        "total": total,
        "success_count": ok_n,
        "success_rate": round(rate, 3),
        "target_rate": target,
        "meets_target": total >= 3 and rate >= target,
        "window_days": window_days,
        "filtered_from": len(raw),
        "recent": rows[-8:],
    }


def _check_intent_routing() -> dict[str, Any]:
    from ilim_assistant.motorlar.programlama_faz85 import goal_wants_agent_path
    from ilim_assistant.motorlar.programlama_yuzey_bridge import (
        build_surface_handoff_payload,
    )

    rows: list[dict[str, Any]] = []
    for goal, hint in _INTENT_CASES:
        payload = build_surface_handoff_payload(f"gorev: {goal}")
        got = payload.get("path_hint")
        agent = goal_wants_agent_path(goal)
        if hint == "faz85_fast":
            ok = (not agent) and got == "faz85_fast"
        else:
            ok = bool(agent) and got == hint
        rows.append(
            {
                "goal": goal,
                "expected": hint,
                "got": got,
                "agent": agent,
                "ok": ok,
            }
        )
    ok_n = sum(1 for r in rows if r["ok"])
    return {
        "name": "intent_routing",
        "ok": ok_n == len(rows),
        "success_count": ok_n,
        "total": len(rows),
        "detail": f"{ok_n}/{len(rows)} niyet yolu",
        "rows": rows,
    }


def _check_monorepo_gate(workspace_root: str | Path | None) -> dict[str, Any]:
    from ilim_assistant.motorlar.programlama_monorepo_refactor import (
        run_monorepo_refactor_gate,
    )

    rep = run_monorepo_refactor_gate(workspace_root)
    return {
        "name": "monorepo_triple_gate",
        "ok": bool(rep.get("ok")),
        "detail": str(rep.get("detail") or "")[:200],
        "checks": rep.get("checks") or {},
        "scope_rel": rep.get("scope_rel"),
    }


def _check_three_file_parity(workspace_root: str | Path | None) -> dict[str, Any]:
    from ilim_assistant.motorlar.programlama_cursor_parity import (
        scenario_three_file_refactor,
    )

    check, name = scenario_three_file_refactor(workspace_root)
    return {
        "name": "three_file_parity",
        "ok": bool(check.ok),
        "detail": str(check.detail or "")[:200],
        "elapsed_sec": round(float(check.elapsed_sec or 0), 2),
        "project": name,
    }


def _check_mega_workbench(workspace_root: str | Path | None) -> dict[str, Any]:
    from ilim_assistant.motorlar.programlama_faz80 import (
        effective_agent_limits,
        wants_mega_refactor,
    )
    from ilim_assistant.motorlar.programlama_mega_workbench import (
        build_mega_workbench_payload,
    )

    msg = "mega refactor 10+ dosya tum repoyu duzenle"
    wants = wants_mega_refactor(msg)
    lim = effective_agent_limits(msg)
    wb = build_mega_workbench_payload(workspace_root)
    e2 = compute_e2_stats(workspace_root, window_days=30)
    mega_ok = (
        wants
        and bool(lim.get("mega"))
        and int(lim.get("max_files_per_turn") or 0) >= 16
        and int(lim.get("max_turns") or 0) >= 20
        and bool(wb.get("ok"))
    )
    return {
        "name": "mega_workbench",
        "ok": mega_ok,
        "detail": (
            f"mega={lim.get('mega')} turns={lim.get('max_turns')} "
            f"files/tur={lim.get('max_files_per_turn')} "
            f"e2_rate={e2.get('success_rate')} ({e2.get('success_count')}/{e2.get('total')})"
        ),
        "limits": lim,
        "workbench_ok": bool(wb.get("ok")),
        "e2_stats": e2,
    }


def _setup_multi_file_broken(
    workspace_root: str | Path | None,
    scope_rel: str,
) -> tuple[bool, str]:
    """Üç dosyalı bozuk iskelet: util + service + main (version eksik / wrong)."""
    try:
        from ilim_assistant.motorlar.programlama_faz6 import run_scaffold
        from ilim_assistant.motorlar.programlama_motoru import ProgramlamaAraclari

        slug = scope_rel.split("/")[-1]
        service_name = slug.replace("-", "_")
        sc = run_scaffold("fastapi_api", slug, workspace_root, force=True)
        if not sc.get("ok"):
            return False, str(sc.get("error") or "scaffold")
        tools = ProgramlamaAraclari(workspace_root)
        util = '''"""util — e2 multi."""
VERSION = "1.0.0-broken"


def greet(name: str) -> str:
    return f"hi {name}"
'''
        service = f'''"""service — e2 multi."""
from app.util import VERSION, greet


def health_payload() -> dict[str, str]:
    return {{"ok": "true", "service": "{service_name}", "msg": greet("ruzgar")}}
'''
        main = '''"""main — e2 multi."""
from fastapi import FastAPI
from app.service import health_payload

app = FastAPI()


@app.get("/health")
def health():
    return health_payload()
'''
        test = f'''"""tests — e2 multi (scaffold test_health yerine)."""
from fastapi.testclient import TestClient
from app.main import app
from app.util import VERSION, greet
from app.service import health_payload

client = TestClient(app)


def test_version():
    assert VERSION == "2.0.0"


def test_greet():
    assert "ruzgar" in greet("ruzgar")


def test_health_payload():
    p = health_payload()
    assert p["ok"] == "true"
    assert p["service"] == "{service_name}"
    assert p.get("version") == "2.0.0"


def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") == "true"
    assert data.get("service") == "{service_name}"
    assert data.get("version") == "2.0.0"
'''
        for rel, body in (
            (f"{scope_rel}/app/util.py", util),
            (f"{scope_rel}/app/service.py", service),
            (f"{scope_rel}/app/main.py", main),
            (f"{scope_rel}/tests/test_e2_multi.py", test),
            (f"{scope_rel}/tests/test_health.py", "# superseded by test_e2_multi\n"),
        ):
            w = tools.write(rel, body)
            if not w.ok:
                return False, w.detail
        return True, "3-file broken util/service/main"
    except Exception as exc:
        return False, str(exc)[:120]


def _run_offline_multi_heal(
    workspace_root: str | Path | None,
    scope_rel: str,
) -> dict[str, Any]:
    """Deterministik 3 dosya patch + pytest (canlı LLM yok)."""
    t0 = time.perf_counter()
    # service satırı setup’taki service_name ile uyumlu aranır
    service_name = scope_rel.split("/")[-1].replace("-", "_")
    patch = f"""@@patch {scope_rel}/app/util.py
```search-replace
<<<SEARCH
VERSION = "1.0.0-broken"
===
VERSION = "2.0.0"
>>>REPLACE
```
@@patch {scope_rel}/app/service.py
```search-replace
<<<SEARCH
    return {{"ok": "true", "service": "{service_name}", "msg": greet("ruzgar")}}
===
    return {{
        "ok": "true",
        "service": "{service_name}",
        "version": VERSION,
        "msg": greet("ruzgar"),
    }}
>>>REPLACE
```
"""
    try:
        from ilim_assistant.motorlar.programlama_motoru import repo_root
        from ilim_assistant.motorlar.programlama_patch import apply_patch_jobs
        from ilim_assistant.motorlar.programlama_faz14 import run_project_verify

        root = repo_root(workspace_root)
        if root is None:
            return {
                "ok": False,
                "detail": "workspace yok",
                "elapsed_sec": 0.0,
                "writes_ok": 0,
                "verify_ok": False,
                "source": "e2_offline_multi",
            }
        reps = apply_patch_jobs(patch, root)
        writes = sum(1 for r in reps if r.ok)
        v = run_project_verify(
            workspace_root,
            scope_rel,
            goal="util service main version 2.0.0 pytest gecir",
        )
        ok = writes >= 2 and bool(v and v.ok)
        return {
            "ok": ok,
            "detail": f"writes={writes} verify={bool(v and v.ok)}",
            "elapsed_sec": round(time.perf_counter() - t0, 2),
            "writes_ok": writes,
            "verify_ok": bool(v and v.ok),
            "turns": 1,
            "source": "e2_offline_multi",
        }
    except Exception as exc:
        return {
            "ok": False,
            "detail": str(exc)[:200],
            "elapsed_sec": round(time.perf_counter() - t0, 2),
            "writes_ok": 0,
            "verify_ok": False,
            "source": "e2_offline_multi",
        }


def _record_e2_outcome(
    workspace_root: str | Path | None,
    *,
    name: str,
    scope_rel: str,
    goal: str,
    row: dict[str, Any],
) -> None:
    try:
        from ilim_assistant.motorlar.programlama_faz55 import record_task_outcome

        record_task_outcome(
            workspace_root,
            scope_rel=scope_rel,
            goal=goal[:200],
            success=bool(row.get("ok")),
            turns_used=int(row.get("turns") or 0),
            verify_ok=bool(row.get("verify_ok")),
            writes_ok=int(row.get("writes_ok") or 0),
            elapsed_sec=float(row.get("elapsed_sec") or 0),
            source=f"e2_battery_{row.get('source', 'faz103')}",
            detail=f"[{name}] {str(row.get('detail') or '')[:180]}",
        )
    except Exception:
        pass


def _run_live_multi_agent(
    workspace_root: str | Path | None,
    scope_rel: str,
    goal: str,
) -> dict[str, Any]:
    from ilim_assistant.motorlar.programlama_faz88 import (
        brain_available,
        run_live_code_agent,
    )

    if not brain_available():
        return {
            "ok": False,
            "skipped": True,
            "detail": "canlı ajan atlandı (beyin yok)",
            "elapsed_sec": 0.0,
            "writes_ok": 0,
            "verify_ok": False,
            "source": "skipped",
        }
    row = run_live_code_agent(workspace_root, scope_rel, goal, max_turns=5)
    row["source"] = "e2_live_multi"
    return row


def run_e2_offline_battery(workspace_root: str | Path | None) -> dict[str, Any]:
    """Deterministik E2 pili (LLM yok)."""
    if not _enabled():
        return {"ok": False, "error": "faz103 kapalı"}
    stamp = int(time.time())
    checks = [
        _check_intent_routing(),
        _check_monorepo_gate(workspace_root),
        _check_three_file_parity(workspace_root),
        _check_mega_workbench(workspace_root),
    ]
    # Offline 3-dosya heal senaryosu
    scope = f"projects/e2-bat-{stamp}-m1"
    setup_ok, setup_msg = _setup_multi_file_broken(workspace_root, scope)
    if setup_ok:
        heal = _run_offline_multi_heal(workspace_root, scope)
        heal_row = {
            "name": "offline_multi_heal",
            "ok": bool(heal.get("ok")),
            "detail": f"{setup_msg}; {heal.get('detail')}",
            "elapsed_sec": heal.get("elapsed_sec"),
            "writes_ok": heal.get("writes_ok"),
            "verify_ok": heal.get("verify_ok"),
            "turns": heal.get("turns", 1),
            "source": heal.get("source"),
            "scope_rel": scope,
        }
        _record_e2_outcome(
            workspace_root,
            name="offline_multi_heal",
            scope_rel=scope,
            goal="app/util.py ve app/service.py version 2.0.0 pytest gecir",
            row=heal_row,
        )
        checks.append(heal_row)
    else:
        checks.append(
            {
                "name": "offline_multi_heal",
                "ok": False,
                "detail": f"setup: {setup_msg}",
            }
        )

    scored = [c for c in checks if "ok" in c]
    ok_n = sum(1 for c in scored if c.get("ok"))
    total = len(scored)
    rate = ok_n / total if total else 0.0
    e2 = compute_e2_stats(workspace_root, window_days=30)
    return {
        "ok": True,
        "version": FAZ103_VERSION,
        "generated_at": time.time(),
        "total": total,
        "success_count": ok_n,
        "success_rate": rate,
        "meets_target_90": rate >= e2_battery_target() if total else False,
        "target_rate": e2_battery_target(),
        "scenarios": checks,
        "e2_stats": e2,
    }


def run_combined_e2_battery(
    workspace_root: str | Path | None,
    *,
    live_llm: bool | None = None,
) -> dict[str, Any]:
    """Offline E2 + isteğe canlı çok dosya ajan."""
    if live_llm is None:
        live_llm = live_llm_requested()
    offline = run_e2_offline_battery(workspace_root)
    live_row: dict[str, Any] | None = None
    if live_llm:
        stamp = int(time.time())
        scope = f"projects/e2-bat-{stamp}-live"
        setup_ok, setup_msg = _setup_multi_file_broken(workspace_root, scope)
        goal = (
            "app/util.py ve app/service.py duzelt: VERSION 2.0.0 olsun, "
            "health payload'a version ekle, pytest gecir"
        )
        if setup_ok:
            live_row = _run_live_multi_agent(workspace_root, scope, goal)
            live_row = {
                "name": "live_multi_agent",
                "mode": "live_agent",
                "ok": bool(live_row.get("ok")),
                "detail": f"{setup_msg}; {live_row.get('detail')}",
                "elapsed_sec": live_row.get("elapsed_sec"),
                "writes_ok": live_row.get("writes_ok"),
                "verify_ok": live_row.get("verify_ok"),
                "turns": live_row.get("turns"),
                "skipped": bool(live_row.get("skipped")),
                "source": live_row.get("source"),
                "scope_rel": scope,
            }
            if not live_row.get("skipped"):
                _record_e2_outcome(
                    workspace_root,
                    name="live_multi_agent",
                    scope_rel=scope,
                    goal=goal,
                    row=live_row,
                )
        else:
            live_row = {
                "name": "live_multi_agent",
                "ok": False,
                "detail": f"setup: {setup_msg}",
                "skipped": False,
            }

    o_rate = float(offline.get("success_rate") or 0)
    if live_row and not live_row.get("skipped"):
        combined = (o_rate + (1.0 if live_row.get("ok") else 0.0)) / 2.0
    else:
        combined = o_rate
    return {
        "ok": True,
        "version": FAZ103_VERSION,
        "live_llm": bool(live_llm),
        "offline_battery": offline,
        "live_scenario": live_row,
        "combined_success_rate": combined,
        "combined_meets_target_90": combined >= e2_battery_target(),
        "e2_stats": compute_e2_stats(workspace_root, window_days=30),
    }


def format_e2_battery_report(report: dict[str, Any]) -> str:
    if not report.get("ok"):
        return f"E2 pili çalışmadı: {report.get('error', '?')}"
    # combined veya offline tek paket
    offline = report.get("offline_battery") or report
    lines = [
        "**E2 çok dosya pili (Faz 103)**",
        "",
        f"Offline: **{offline.get('success_count')}/{offline.get('total')}** "
        f"({int(float(offline.get('success_rate') or 0) * 100)}%) · "
        f"hedef ≥{int(float(offline.get('target_rate') or 0.9) * 100)}% "
        f"{'✓' if offline.get('meets_target_90') else '↓'}",
        "",
    ]
    for s in offline.get("scenarios") or []:
        mark = "✓" if s.get("ok") else "✗"
        lines.append(f"- {mark} `{s.get('name')}` — {str(s.get('detail') or '')[:120]}")
    live = report.get("live_scenario")
    if live:
        if live.get("skipped"):
            lines.append(f"\n- ○ canlı ajan atlandı — {live.get('detail')}")
        else:
            mark = "✓" if live.get("ok") else "✗"
            lines.append(
                f"\n- {mark} canlı çok dosya — {live.get('detail')} "
                f"({live.get('elapsed_sec')} sn)"
            )
        lines.append(
            f"\nBirleşik: **{int(float(report.get('combined_success_rate') or 0) * 100)}%** "
            f"{'✓' if report.get('combined_meets_target_90') else '↓'}"
        )
    e2 = report.get("e2_stats") or offline.get("e2_stats") or {}
    if e2.get("total"):
        lines.append(
            f"\nE2 KPI (30g): **{int(float(e2.get('success_rate') or 0) * 100)}%** "
            f"({e2.get('success_count')}/{e2.get('total')})"
        )
    lines.append(f"\n({FAZ103_VERSION})")
    return "\n".join(lines)


def maybe_instant_faz103(
    message: str,
    workspace_root: str | Path | None = None,
) -> str | None:
    if not wants_e2_battery(message):
        return None
    low = _ascii_fold(message)
    live = "canli" in low or "live" in low or live_llm_requested()
    if live or "birlesik" in low or "combined" in low:
        bundle = run_combined_e2_battery(workspace_root, live_llm=live)
        return format_e2_battery_report(bundle)
    report = run_e2_offline_battery(workspace_root)
    return format_e2_battery_report(report)


def enrich_health_build(build: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(build or {})
    out["programlama_faz103"] = faz103_enabled()
    return out


def faz103_directive() -> str:
    return (
        "[Faz 103 — E2 çok dosya pili]\n"
        "Komut: `e2 pil` · birleşik/canlı: `e2 pil canlı`\n"
        "Canlı LLM: RUZGAR_E2_BATTERY_LIVE=1\n"
        f"Kapat: RUZGAR_FAZ103=0 · {FAZ103_VERSION}\n"
    )
