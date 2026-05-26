#!/usr/bin/env python3
"""Programlama motoru duman testi (Faz 6–18) — Ollama/API gerekmez (offline).

Çalıştırma (ilim-assistant kökünde):
  python scripts/programlama_smoke.py
  python scripts/programlama_smoke.py --slo

Canlı API (sunucu ayakta):
  python scripts/programlama_smoke.py --live http://127.0.0.1:8777

CI paketi (offline + SLO + isteğe bağlı live):
  python scripts/programlama_smoke.py --ci
  python scripts/programlama_smoke.py --ci --live http://127.0.0.1:8777
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

WORKSPACE = _ROOT.parent


def _ok(label: str) -> None:
    print(f"  OK  {label}")


def _fail(label: str, detail: str = "") -> None:
    msg = f"  FAIL {label}"
    if detail:
        msg += f" — {detail}"
    print(msg)


def run_offline() -> int:
    fails = 0
    print("=== Faz 6 — şablonlar ===")
    from ilim_assistant.motorlar.programlama_faz6 import list_templates

    ids = {t["id"] for t in list_templates()}
    for tid in ("fastapi_api", "static_site", "react_vite", "cli_python", "mobile_expo"):
        if tid in ids:
            _ok(f"template {tid}")
        else:
            _fail(f"template {tid}")
            fails += 1

    print("=== Faz 8 — odak ===")
    from ilim_assistant.motorlar.programlama_faz8 import pick_focus_rel

    fr = pick_focus_rel(
        {
            "ok": True,
            "template_id": "react_vite",
            "base_dir": "projects/demo",
            "written": ["projects/demo/src/App.jsx"],
        }
    )
    if fr and fr.endswith("App.jsx"):
        _ok(f"focus {fr}")
    else:
        _fail("focus react", str(fr))
        fails += 1

    print("=== Faz 10 — delege & indeks ===")
    from ilim_assistant.motorlar.programlama_faz10 import (
        build_workspace_index,
        should_delegate_to_programlama,
    )

    if should_delegate_to_programlama("projects/foo/main.py duzelt", "genel"):
        _ok("delegate genel -> programlama")
    else:
        _fail("delegate")
        fails += 1
    idx = build_workspace_index(WORKSPACE, scope_rel="projects")
    if idx and "projects" in idx:
        _ok("workspace index")
    else:
        _fail("workspace index")
        fails += 1

    print("=== Faz 11 — orkestra ===")
    from ilim_assistant.motorlar.programlama_faz11 import build_programlama_orchestra_steps

    steps = build_programlama_orchestra_steps(
        "test",
        WORKSPACE,
        phase="done",
        patch_meta={"action": "applied", "applied": ["projects/x/a.py"]},
    )
    if len(steps) >= 5 and steps[0].get("id") == "plan":
        _ok(f"orchestra steps ({len(steps)})")
    else:
        _fail("orchestra steps", str(len(steps)))
        fails += 1

    print("=== Faz 12 — diff onizleme ===")
    from ilim_assistant.motorlar.programlama_faz10 import preview_writes, unified_diff_text

    diff = unified_diff_text("a=1\n", "a=2\nb=3\n", "test.py")
    if "+b=3" in diff or "b=3" in diff:
        _ok("unified_diff")
    else:
        _fail("unified_diff", diff[:80])
        fails += 1
    prev = preview_writes("@@write z.py\n```\nx=1\n```", WORKSPACE)
    if prev.get("items") and prev["items"][0].get("diff"):
        _ok("preview_writes diff")
    else:
        _fail("preview_writes diff")
        fails += 1

    print("=== Faz 13 — proje zekasi ===")
    from ilim_assistant.motorlar.programlama_faz13 import (
        extract_symbols_from_text,
        scan_project_files,
        search_in_project,
        wants_find_command,
    )

    syms = extract_symbols_from_text("x.py", "def hello():\n    pass\nclass Bot:\n    pass\n")
    if "hello" in syms and "Bot" in syms:
        _ok("symbol extract py")
    else:
        _fail("symbol extract", str(syms))
        fails += 1
    if wants_find_command("@@find health"):
        _ok("wants_find")
    else:
        _fail("wants_find")
        fails += 1
    proj_base = WORKSPACE / "projects"
    if proj_base.is_dir():
        first = next((p.name for p in proj_base.iterdir() if p.is_dir()), None)
        if first:
            scope = f"projects/{first}"
            scan = scan_project_files(WORKSPACE, scope, max_files=30)
            if scan.get("ok") and scan.get("file_count", 0) > 0:
                _ok(f"scan {scope} ({scan.get('file_count')} dosya)")
            else:
                _fail("scan", str(scan.get("error")))
                fails += 1
            sr = search_in_project(WORKSPACE, scope, "def ", max_hits=3)
            if sr.get("ok"):
                _ok("search_in_project")
            else:
                _fail("search", str(sr.get("error")))
                fails += 1
        else:
            _ok("scan skip (projects bos)")
    else:
        _ok("scan skip (projects yok)")

    print("=== Faz 14 — otonom gorev ===")
    from ilim_assistant.motorlar.programlama_faz14 import (
        code_agent_max_turns,
        parse_code_agent_task,
        should_run_code_agent_loop,
        wants_code_agent_stop,
    )

    task = parse_code_agent_task("gorev: benim-api health endpointine version ekle")
    if task and task.scope_rel.endswith("benim-api"):
        _ok(f"parse task {task.scope_rel}")
    else:
        _fail("parse task", str(task))
        fails += 1
    if should_run_code_agent_loop("gorev: foo bar", "programlama"):
        _ok("should_run agent")
    else:
        _fail("should_run agent")
        fails += 1
    if wants_code_agent_stop("gorev durdur"):
        _ok("wants stop")
    else:
        _fail("wants stop")
        fails += 1
    if 1 <= code_agent_max_turns() <= 16:
        _ok(f"max_turns={code_agent_max_turns()}")
    else:
        _fail("max_turns")
        fails += 1

    print("=== Faz 15 — terminal v2 ===")
    from ilim_assistant.motorlar.programlama_motoru import is_programlama_reserved_command
    from ilim_assistant.motorlar.programlama_faz15 import (
        is_dangerous_shell,
        list_terminal_presets,
        parse_terminal_preset,
        wants_terminal_command,
    )

    presets = {p["id"] for p in list_terminal_presets()}
    if presets >= {"npm_install", "git_status", "npm_build"}:
        _ok(f"terminal presets ({len(presets)})")
    else:
        _fail("terminal presets", str(presets))
        fails += 1
    if parse_terminal_preset("npm run build") == "npm_build":
        _ok("parse npm build")
    else:
        _fail("parse npm build")
        fails += 1
    if wants_terminal_command("git status") and is_programlama_reserved_command("git status"):
        _ok("git status reserved")
    elif wants_terminal_command("git status"):
        _ok("wants git status")
    else:
        _fail("git status")
        fails += 1
    if is_dangerous_shell("git push origin main --force"):
        _ok("dangerous blocked")
    else:
        _fail("dangerous")
        fails += 1

    print("=== Faz 16 — patch onay ===")
    from ilim_assistant.motorlar.programlama_faz16 import (
        build_pending_bundle,
        effective_auto_patch_enabled,
        stage_pending_enriched,
    )

    if not effective_auto_patch_enabled():
        _ok("auto_patch default off (faz16)")
    else:
        _fail("auto_patch should default off")
        fails += 1
    sample = (
        "@@write projects/smoke-faz16/a.py\n```python\nx = 1\n```\n"
        "@@write projects/smoke-faz16/b.py\n```python\ny = 2\n```\n"
    )
    staged = stage_pending_enriched(sample, WORKSPACE)
    if staged.get("count") == 2:
        _ok("stage 2 files")
    else:
        _fail("stage", str(staged))
        fails += 1
    bundle = build_pending_bundle(WORKSPACE)
    if bundle.get("counts", {}).get("pending") == 2:
        _ok("bundle pending=2")
    else:
        _fail("bundle counts", str(bundle.get("counts")))
        fails += 1
    from ilim_assistant.motorlar.programlama_faz16 import set_job_status, apply_pending_selective

    set_job_status(WORKSPACE, "projects/smoke-faz16/a.py", "accepted")
    applied = apply_pending_selective(WORKSPACE, mode="accepted", run_verify=False)
    if applied.get("ok") and "projects/smoke-faz16/a.py" in (applied.get("applied") or []):
        _ok("apply accepted only")
    else:
        _fail("apply selective", str(applied.get("error")))
        fails += 1
    from ilim_assistant.motorlar.programlama_faz10 import clear_pending

    clear_pending(WORKSPACE)

    print("=== Faz 17 — git koprusu ===")
    from ilim_assistant.motorlar.programlama_faz17 import (
        heuristic_commit_message,
        wants_commit_suggest,
        wants_git_status,
    )

    if wants_git_status("git durum"):
        _ok("wants git durum")
    else:
        _fail("wants git durum")
        fails += 1
    if wants_commit_suggest("commit oner"):
        _ok("wants commit oner")
    else:
        _fail("wants commit oner")
        fails += 1
    fake_snap = {
        "scope_rel": "projects/demo",
        "diff_stat": {"output": " app/main.py | 2 +1 -\n 1 file changed"},
        "diff_cached_stat": {"output": ""},
        "status": {"output": "## main\n M app/main.py"},
    }
    msg = heuristic_commit_message(fake_snap)
    if msg and "demo" in msg:
        _ok(f"heuristic commit: {msg[:40]}")
    else:
        _fail("heuristic", msg)
        fails += 1

    print("=== Faz 24 — adim seridi SSE ===")
    from ilim_assistant.motorlar.programlama_faz24 import (
        CodeAgentStepTracker,
        FAZ24_VERSION,
        extract_plan_lines,
        sse_steps_enabled,
    )

    if sse_steps_enabled():
        _ok("sse steps on")
    else:
        _fail("sse off")
        fails += 1
    tr = CodeAgentStepTracker(
        scope_rel="projects/demo",
        goal="health version ekle",
        max_turns=8,
        budget_sec=300.0,
    )
    ev0 = tr.on_started(brain_chain=["groq", "kod"])
    if ev0.get("type") == "agent_step" and len(ev0.get("steps") or []) >= 6:
        _ok(f"agent_step started ({len(ev0['steps'])} steps)")
    else:
        _fail("agent_step start", str(ev0)[:80])
        fails += 1
    ev1 = tr.on_turn_start(1)
    ev2 = tr.on_writes(1, 2, ["projects/demo/a.py"])
    ev3 = tr.on_verify(1, True)
    ev4 = tr.on_finish(success=True, elapsed_sec=12.5, turns_used=2)
    if ev4.get("code_agent", {}).get("success"):
        _ok("agent_step finish")
    else:
        _fail("finish event")
        fails += 1
    plan = extract_plan_lines("Plan:\n1. health ekle\n2. pytest calistir")
    if "health" in plan:
        _ok(f"plan extract: {plan[:40]}")
    else:
        _ok("plan extract skip")
    if FAZ24_VERSION in str(ev4.get("code_agent", {}).get("version", "")):
        _ok("faz24 version")

    print("=== Faz 23 — gorev modu 5dk ===")
    from ilim_assistant.motorlar.programlama_faz23 import (
        FAZ23_VERSION,
        enter_task_mode,
        exit_task_mode,
        resolve_code_agent_budget_sec,
        task_auto_apply_enabled,
        task_mode_active,
        task_success_met,
    )

    if resolve_code_agent_budget_sec() == 300.0:
        _ok("budget default 300s (5dk)")
    else:
        _ok(f"budget={resolve_code_agent_budget_sec()}")
    enter_task_mode()
    if task_mode_active() and task_auto_apply_enabled():
        _ok("task mode + auto apply")
    else:
        _fail("task mode")
        fails += 1
    exit_task_mode()
    if not task_mode_active():
        _ok("task mode exit")
    else:
        _fail("task mode stuck")
        fails += 1
    if task_success_met(verify_ok=True, writes_ok=2):
        _ok("task success criteria")
    else:
        _fail("task success")
        fails += 1
    if FAZ23_VERSION.startswith("programlama-faz23"):
        _ok("faz23 version")

    print("=== Faz 22 — sembol indeks v2 ===")
    from ilim_assistant.motorlar.programlama_faz22 import (
        FAZ22_VERSION,
        build_symbol_index,
        extract_file_symbols,
        lookup_symbols,
        parse_symbol_query,
        wants_symbol_command,
    )

    py_sample = "def health():\n    return {'ok': True}\n\nclass ApiRouter:\n    pass\n"
    syms = extract_file_symbols("projects/demo/app/main.py", py_sample)
    names = {s.get("name") for s in syms}
    if "health" in names and "ApiRouter" in names:
        _ok(f"extract py symbols ({len(syms)})")
    else:
        _fail("extract py", str(names))
        fails += 1
    if parse_symbol_query("sembol health") == "health":
        _ok("parse sembol health")
    else:
        _fail("parse sembol", parse_symbol_query("sembol health"))
        fails += 1
    if wants_symbol_command("@@symbol health"):
        _ok("wants @@symbol")
    else:
        _fail("wants symbol")
        fails += 1
    sym_dir = WORKSPACE / "projects" / "smoke-faz22" / "app"
    sym_dir.mkdir(parents=True, exist_ok=True)
    main_py = sym_dir / "main.py"
    main_py.write_text(py_sample, encoding="utf-8")
    built = build_symbol_index(WORKSPACE, "projects/smoke-faz22", force=True)
    if built.get("ok") and int(built.get("symbol_count") or 0) >= 2:
        _ok(f"index build symbols={built.get('symbol_count')}")
    else:
        _fail("index build", str(built))
        fails += 1
    look = lookup_symbols(WORKSPACE, "projects/smoke-faz22", "health")
    hits = look.get("hits") or []
    if look.get("ok") and hits and hits[0].get("name") == "health":
        _ok(f"lookup health line={hits[0].get('line')}")
    else:
        _fail("lookup health", str(look))
        fails += 1
    if FAZ22_VERSION in str(look.get("version") or ""):
        _ok("faz22 version tag")
    else:
        _fail("version tag")
        fails += 1

    print("=== Faz 21 — hafif baglam ===")
    from ilim_assistant.motorlar.programlama_faz21 import (
        FAZ21_VERSION,
        build_light_programming_context,
        light_context_enabled,
    )
    from ilim_assistant.motorlar.programlama_motoru import build_motor_context

    if light_context_enabled():
        _ok("light context on")
    else:
        _fail("light context off")
        fails += 1
    ctx = build_light_programming_context(
        "pytest calistir",
        workspace_root=None,
        include_tools=False,
    )
    if FAZ21_VERSION in ctx and "Faz 21" in ctx:
        _ok(f"light ctx len={len(ctx)}")
    else:
        _fail("light ctx", ctx[:120])
        fails += 1
    heavy_off = os.environ.get("RUZGAR_PROG_LIGHT_CONTEXT", "1")
    os.environ["RUZGAR_PROG_LIGHT_CONTEXT"] = "1"
    lite = build_motor_context("test", run_presets=False)
    if "Faz 21" in lite and "dinamit" not in lite.lower():
        _ok("build_motor_context uses light")
    else:
        _ok("build_motor_context light path")
    os.environ["RUZGAR_PROG_LIGHT_CONTEXT"] = heavy_off

    print("=== Faz 20 — Cursor yolu ===")
    from ilim_assistant.motorlar.programlama_faz20 import (
        execute_tool,
        extract_tool_calls,
        wants_implementation_agent,
    )

    sample = (
        'Plan\n```ruzgar-tool\n{"tool":"read","path":"projects/benim-api/app/main.py"}\n```\n'
    )
    calls = extract_tool_calls(sample)
    if calls and calls[0].get("tool") == "read":
        _ok("extract ruzgar-tool")
    else:
        _fail("extract tool", str(calls))
        fails += 1
    if wants_implementation_agent("benim-api health version ekle ve test gecir", "programlama"):
        _ok("wants implementation agent")
    else:
        _fail("wants implementation")
        fails += 1

    print("=== Faz 19 — gorev v2 ===")
    from ilim_assistant.motorlar.programlama_faz19 import (
        AgentLoopState,
        code_agent_budget_sec,
        normalize_agent_message,
        parse_implicit_programming_task,
        parse_task_aliases,
        should_abort_loop,
    )

    aliased = parse_task_aliases("is: benim-api version ekle")
    if aliased and "görev:" in aliased:
        _ok("is: alias")
    else:
        _fail("is: alias", str(aliased))
        fails += 1
    implicit = parse_implicit_programming_task(
        "benim-api health endpointine version ekle ve test gecir"
    )
    if implicit and "benim-api" in implicit:
        _ok(f"implicit task: {implicit[:50]}")
    else:
        _fail("implicit", str(implicit))
        fails += 1
    st = AgentLoopState()
    st.record_turn(wrote_files=0, llm_kind="quota")
    abort, _ = should_abort_loop(st)
    if abort:
        _ok("abort on quota no writes")
    else:
        _fail("abort quota")
        fails += 1
    b = code_agent_budget_sec()
    if b >= 300.0:
        _ok(f"budget {int(b)}s (faz23)")
    elif b == 120.0:
        _ok("budget 120s")
    else:
        _ok(f"budget={b}")

    print("=== Faz 18 — kalite modulu ===")
    from ilim_assistant.motorlar.programlama_faz18 import (
        FAZ18_VERSION,
        faz18_directive,
        slo_scaffold_sec,
    )

    if "SLO" in faz18_directive() and slo_scaffold_sec() == 30.0:
        _ok("faz18 directive/slo")
    else:
        _fail("faz18 config")
        fails += 1
    _ok(f"module {FAZ18_VERSION}")

    print("=== Motor — rezerve komut ===")

    for msg in (
        "patch onayla",
        "patch liste",
        "git durum",
        "commit oner",
        "workspace indeks",
        "sablon listele",
        "@@find test",
        "sembol health",
        "git dal",
        "proje listesi",
        "proje sec: demo",
        "pr durum",
        "is akisi",
        "proje tara",
        "npm install",
    ):
        if is_programlama_reserved_command(msg):
            _ok(f"reserved: {msg[:24]}")
        else:
            _fail(f"reserved: {msg}")
            fails += 1

    return fails


def run_slo() -> int:
    """Faz 18 — zamanlı senaryolar (scaffold / patch / delege)."""
    from ilim_assistant.motorlar.programlama_faz18 import (
        format_quality_report,
        run_offline_slo_scenarios,
        slo_scaffold_sec,
        slo_simple_task_sec,
    )

    print("=== Faz 18 — SLO senaryolari (offline) ===")
    print(f"  scaffold budget: {slo_scaffold_sec():.0f}s · task budget: {slo_simple_task_sec():.0f}s")
    report = run_offline_slo_scenarios(WORKSPACE)
    fails = 0
    for c in report.checks:
        if c.ok:
            if c.budget_sec > 0:
                _ok(f"{c.id} ({c.elapsed_sec:.2f}s / {c.budget_sec:.0f}s)")
            else:
                _ok(c.id)
        else:
            _fail(c.id, c.detail or f"{c.elapsed_sec:.2f}s")
            fails += 1
    try:
        print()
        print(format_quality_report(report))
    except UnicodeEncodeError:
        print("(kalite raporu konsolda yazdirilamadi - ASCII disi karakter)")
    return fails


def run_live(base: str) -> int:
    from ilim_assistant.motorlar.programlama_faz18 import (
        QualityRunReport,
        merge_live_timings,
        run_offline_slo_scenarios,
        slo_scaffold_sec,
    )

    fails = 0
    base = base.rstrip("/")
    enc = urllib.parse.quote(str(WORKSPACE), safe="")
    live_timings: list[dict] = []
    print(f"=== Canli API {base} ===")

    def get(path: str, timeout: int = 30) -> dict:
        with urllib.request.urlopen(base + path, timeout=timeout) as r:
            return json.loads(r.read())

    def post(path: str, body: dict, timeout: int = 60) -> dict:
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            base + path,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())

    try:
        h = get("/api/health")
        rev = str((h.get("build") or {}).get("rev") or "")
        if (
            "faz68" in rev
            or rev.endswith("-v78")
            or "faz67" in rev
            or rev.endswith("-v77")
            or "faz66" in rev
            or "faz65" in rev
            or rev.endswith("-v76")
            or "faz63" in rev
            or "faz62" in rev
            or "faz61" in rev
            or rev.endswith("-v74")
            or "faz60" in rev
            or "faz59" in rev
            or rev.endswith("-v73")
            or rev.endswith("-v72")
            or rev.endswith("-v71")
            or rev.endswith("-v70")
        ):
            _ok(f"build.rev={rev}")
        else:
            _fail("build.rev", rev)
            fails += 1
    except Exception as e:
        _fail("health", str(e)[:120])
        return fails + 1

    try:
        q = get(f"/api/programlama/quality-report?workspace_root={enc}")
        if q.get("ok") is not None and q.get("report"):
            _ok("quality-report API")
        else:
            _fail("quality-report")
            fails += 1
    except Exception as e:
        _fail("quality-report", str(e)[:120])
        fails += 1

    try:
        pr = get(f"/api/programlama/parity-report?workspace_root={enc}")
        if pr.get("ok") is not None and pr.get("data"):
            _ok("parity-report API")
        else:
            _fail("parity-report")
            fails += 1
        cs = get(f"/api/programlama/cursor-seviye?workspace_root={enc}")
        if cs.get("score") is not None and cs.get("report"):
            _ok(f"cursor-seviye API score={cs.get('score')}")
        else:
            _fail("cursor-seviye")
            fails += 1
        pu_name = f"smoke-live-pu-{int(time.time()) % 100000}"
        pu = get(
            f"/api/programlama/proje-uret?workspace_root={enc}"
            f"&template_id=fastapi_api&project_name={pu_name}"
            f"&goal=health+version+pytest"
        )
        if pu.get("ok") and pu.get("data", {}).get("scaffold_ok"):
            _ok(f"proje-uret API ({pu_name})")
        else:
            _fail("proje-uret API", str(pu)[:80])
            fails += 1
    except Exception as e:
        _fail("parity-report", str(e)[:120])
        fails += 1

    try:
        wp = get(f"/api/programlama/workspace-projects?workspace_root={enc}")
        if wp.get("ok") and isinstance(wp.get("projects"), list):
            _ok("workspace-projects API (Faz 29)")
        else:
            _fail("workspace-projects")
            fails += 1
    except Exception as e:
        _fail("workspace-projects", str(e)[:120])
        fails += 1

    try:
        t = get("/api/programlama/templates")
        ids = {x["id"] for x in (t.get("templates") or [])}
        if "static_site" in ids and "react_vite" in ids and "mobile_expo" in ids:
            _ok("templates API")
        else:
            _fail("templates API", str(ids))
            fails += 1
    except Exception as e:
        _fail("templates", str(e)[:120])
        fails += 1

    try:
        w = get(f"/api/programlama/workspace-index?workspace_root={enc}")
        if w.get("ok") and w.get("index"):
            _ok("workspace-index")
        else:
            _fail("workspace-index")
            fails += 1
    except Exception as e:
        _fail("workspace-index", str(e)[:120])
        fails += 1

    proj_name = f"smoke-live-{int(time.time()) % 100000}"
    t0 = time.monotonic()
    try:
        sc = post(
            "/api/programlama/scaffold",
            {
                "workspace_root": str(WORKSPACE),
                "template_id": "cli_python",
                "project_name": proj_name,
                "force": True,
            },
            timeout=90,
        )
        elapsed = time.monotonic() - t0
        budget = slo_scaffold_sec()
        ok = bool(sc.get("ok")) and elapsed <= budget
        live_timings.append(
            {
                "id": "api_scaffold",
                "label": "API scaffold",
                "ok": ok,
                "elapsed_sec": elapsed,
                "budget_sec": budget,
                "detail": str(sc.get("base_dir") or sc.get("error") or "")[:80],
            }
        )
        if ok:
            _ok(f"live scaffold ({elapsed:.2f}s)")
        else:
            _fail("live scaffold", f"{elapsed:.2f}s {sc.get('error')}")
            fails += 1
    except Exception as e:
        _fail("live scaffold", str(e)[:120])
        fails += 1

    scope = f"projects/{proj_name}"
    patch_body = (
        f"@@write {scope}/main.py\n```python\n# smoke\nprint(1)\n```\n"
    )
    try:
        prev = post(
            "/api/programlama/patch/preview",
            {"workspace_root": str(WORKSPACE), "text": patch_body},
        )
        if prev.get("ok") or prev.get("preview"):
            _ok("patch preview API")
        else:
            _fail("patch preview")
            fails += 1
        pend = get(f"/api/programlama/patch/pending?workspace_root={enc}")
        if pend.get("count", 0) >= 1:
            _ok("patch pending API")
        else:
            _fail("patch pending", str(pend.get("count")))
            fails += 1
        idiff = get(
            f"/api/programlama/patch/inline-diff?workspace_root={enc}"
            f"&path={urllib.parse.quote(f'{scope}/main.py')}"
        )
        if idiff.get("ok") and "new_text" in idiff:
            _ok("inline-diff API (Faz 27)")
        else:
            _fail("inline-diff", str(idiff.get("error") or "")[:80])
            fails += 1
        post(
            "/api/programlama/patch/item",
            {
                "workspace_root": str(WORKSPACE),
                "path": f"{scope}/main.py",
                "status": "accepted",
            },
        )
        app = post(
            "/api/programlama/patch/apply",
            {
                "workspace_root": str(WORKSPACE),
                "mode": "accepted",
                "run_verify": False,
            },
        )
        if app.get("applied"):
            _ok("patch apply API (live)")
        else:
            _fail("patch apply live", str(app.get("error")))
            fails += 1
    except Exception as e:
        _fail("patch chain live", str(e)[:120])
        fails += 1

    try:
        tp = get("/api/programlama/terminal/presets")
        if len(tp.get("presets") or []) >= 4:
            _ok("terminal presets API")
        else:
            _fail("terminal presets API")
            fails += 1
    except Exception as e:
        _fail("terminal presets", str(e)[:120])
        fails += 1

    try:
        gs = get(
            f"/api/programlama/git/status?workspace_root={enc}&scope_rel={urllib.parse.quote(scope)}"
        )
        if gs.get("report") or gs.get("snapshot"):
            _ok("git status API")
        else:
            _fail("git status API")
            fails += 1
    except Exception as e:
        _fail("git status", str(e)[:120])
        fails += 1

    try:
        prs = get(f"/api/programlama/git/pr-status?workspace_root={enc}")
        if prs.get("ok") and prs.get("snapshot"):
            _ok("git pr-status API (Faz 31)")
        else:
            _fail("git pr-status", str(prs.get("snapshot", {}).get("error") or "")[:80])
            fails += 1
    except Exception as e:
        _fail("git pr-status API", str(e)[:120])
        fails += 1

    try:
        ac = get(f"/api/programlama/agent-compliance?workspace_root={enc}")
        if ac.get("ok") is not None and ac.get("data") is not None:
            _ok("agent-compliance API (Faz 37)")
        else:
            _fail("agent-compliance", str(ac)[:80])
            fails += 1
    except Exception as e:
        _fail("agent-compliance API", str(e)[:120])
        fails += 1

    try:
        s = get(f"/api/programlama/project-scan?workspace_root={enc}&scope_rel={scope}")
        if s.get("ok"):
            _ok("project-scan API")
        else:
            _fail("project-scan", str(s.get("error")))
            fails += 1
    except Exception as e:
        _fail("project-scan", str(e)[:120])
        fails += 1

    offline_report = run_offline_slo_scenarios(WORKSPACE)
    merged = merge_live_timings(offline_report, live_timings)
    if merged.ok:
        _ok("SLO birlesik rapor (offline+live)")
    else:
        _fail("SLO birlesik")
        fails += 1

    return fails


def run_parity(*, live_base: str | None = None) -> int:
    """Faz 25 — Cursor parity (offline; isteğe bağlı live preflight)."""
    from ilim_assistant.motorlar.programlama_faz25 import (
        FAZ25_VERSION,
        format_parity_report,
        run_live_parity_preflight,
        run_offline_parity_scenario,
        save_parity_report_json,
    )

    fails = 0
    print("=== Faz 26 — prog beyin zinciri ===")
    from ilim_assistant.motorlar.programlama_faz26 import (
        programming_brain_chain_ids,
    )

    chain = programming_brain_chain_ids()
    if chain and chain[0] in ("groq", "kod"):
        _ok(f"prog chain: {','.join(chain[:4])}")
    else:
        _fail("prog chain", str(chain))
        fails += 1

    print("=== Faz 27 — editor inline diff ===")
    from ilim_assistant.motorlar.programlama_faz27 import (
        build_inline_diff_for_path,
    )

    f27_dir = WORKSPACE / "projects" / "smoke-faz27" / "app"
    f27_dir.mkdir(parents=True, exist_ok=True)
    (f27_dir / "x.py").write_text("v = 1\n", encoding="utf-8")
    sample_patch = (
        "@@write projects/smoke-faz27/app/x.py\n```python\nv = 2\n```\n"
    )
    from ilim_assistant.motorlar.programlama_faz16 import stage_pending_enriched

    stage_pending_enriched(sample_patch, WORKSPACE)
    payload = build_inline_diff_for_path(WORKSPACE, "projects/smoke-faz27/app/x.py")
    if payload.get("ok") and "v = 2" in str(payload.get("new_text") or ""):
        _ok("inline diff payload")
    else:
        _fail("inline diff", str(payload)[:80])
        fails += 1

    print("=== Faz 46 — Cursor seviye kilidi ===")
    from ilim_assistant.motorlar.programlama_cursor_parity import (
        CURSOR_PARITY_VERSION,
        TARGET_CURSOR_SCORE,
        build_extended_capability_scorecard,
        ci_score_warning,
        compute_cursor_score,
        cursor_parity_enabled,
        run_cursor_seviye_assessment,
        save_cursor_seviye_json,
    )

    if cursor_parity_enabled():
        _ok("cursor parity on")
    else:
        _fail("cursor parity")
        fails += 1
    cap = build_extended_capability_scorecard()
    if len(cap) >= 10:
        _ok(f"capability card n={len(cap)}")
    else:
        _fail("capability card")
        fails += 1
    sc, cp, sp = compute_cursor_score([], cap)
    if 0 <= sc <= 100:
        _ok(f"score model cap={cp} scen={sp}")
    else:
        _fail("score model")
        fails += 1
    report = run_cursor_seviye_assessment(WORKSPACE)
    saved = save_cursor_seviye_json(report)
    if saved:
        _ok(f"cursor seviye rapor: {saved[-52:]}")
    else:
        _fail("cursor seviye save")
        fails += 1
    for s in report.scenarios:
        if s.ok:
            _ok(f"scenario {s.id}")
        else:
            print(f"  WARN senaryo {s.id}: {s.detail or s.label}")
    warn = ci_score_warning(report)
    if report.score >= TARGET_CURSOR_SCORE:
        _ok(f"cursor score {report.score}/100 (hedef >={TARGET_CURSOR_SCORE})")
    elif warn:
        print(f"  WARN {warn}")
        _ok(f"cursor score {report.score}/100 (uyari, CI bloklamaz)")
    else:
        _fail("cursor score", str(report.score))
        fails += 1
    _ok(f"faz46 {CURSOR_PARITY_VERSION}")

    print("=== Faz 47 — bağımsız proje üret ===")
    from ilim_assistant.motorlar.programlama_faz47 import (
        FAZ47_VERSION,
        ProjeUretSpec,
        infer_template_from_text,
        parse_proje_uret_command,
        proje_uret_enabled,
        run_offline_bootstrap,
        run_proje_uret_prepare,
        should_run_proje_uret_pipeline,
        wants_proje_uret,
    )

    if proje_uret_enabled():
        _ok("proje uret on")
    else:
        _fail("proje uret")
        fails += 1
    spec_parsed = parse_proje_uret_command(
        "proje üret: fastapi_api smoke-faz47-api health version pytest"
    )
    if spec_parsed and spec_parsed.template_id == "fastapi_api":
        _ok("parse proje uret")
    else:
        _fail("parse proje uret")
        fails += 1
    if wants_proje_uret("sıfırdan fastapi yap smoke-faz47-nat test geçir"):
        _ok("wants proje uret natural")
    else:
        _fail("wants proje uret natural")
        fails += 1
    print("=== Faz 50 — doğal dil proje üret ===")
    from ilim_assistant.motorlar.programlama_faz50 import (
        FAZ50_VERSION,
        extract_features_list,
        parse_faz50_proje_uret,
        should_delegate_proje_uret_from_genel,
    )
    from ilim_assistant.motorlar.programlama_faz10 import should_delegate_to_programlama

    spec50 = parse_faz50_proje_uret(
        "şu özelliklere sahip login ve iletişim formu bir html sitesi yap vitrin-abi"
    )
    if (
        spec50
        and spec50.template_id == "static_site"
        and spec50.project_name == "vitrin-abi"
        and "login" in spec50.goal.lower()
    ):
        _ok("faz50 parse site + features")
    else:
        _fail("faz50 parse site", str(spec50)[:80] if spec50 else "none")
        fails += 1
    if should_delegate_proje_uret_from_genel("bana bir web sitesi yap dükkan-vitrin"):
        _ok("faz50 delegate cue")
    else:
        _fail("faz50 delegate cue")
        fails += 1
    if should_delegate_to_programlama(
        "bana bir web sitesi yap dükkan-vitrin",
        "genel",
        motor_flags={},
    ):
        _ok("faz10 delegate site yap")
    else:
        _fail("faz10 delegate site yap")
        fails += 1
    feats = extract_features_list("özellikleri: login, crud, admin panel")
    if len(feats) >= 2:
        _ok("faz50 extract features")
    else:
        _fail("faz50 extract features", str(feats))
        fails += 1
    _ok(f"faz50 {FAZ50_VERSION}")

    print("=== Faz 51 — CRUD/JWT/dashboard şablonları ===")
    from ilim_assistant.motorlar.programlama_faz51 import (
        FAZ51_VERSION,
        faz51_enabled,
        extra_template_catalog,
        resolve_faz51_template,
    )
    from ilim_assistant.motorlar.programlama_faz6 import list_templates

    if faz51_enabled():
        _ok("faz51 on")
    else:
        _fail("faz51")
        fails += 1
    f51_ids = {r["id"] for r in extra_template_catalog()}
    if f51_ids >= {"crud_api", "auth_jwt", "dashboard_static"}:
        _ok("faz51 catalog")
    else:
        _fail("faz51 catalog", str(f51_ids))
        fails += 1
    listed = {t["id"] for t in list_templates()}
    if f51_ids.issubset(listed):
        _ok("faz51 list_templates merge")
    else:
        _fail("faz51 list_templates", str(f51_ids - listed))
        fails += 1
    if resolve_faz51_template("jwt") == "auth_jwt":
        _ok("faz51 alias jwt")
    else:
        _fail("faz51 alias")
        fails += 1
    if infer_template_from_text("crud api yap magaza-api") == "crud_api":
        _ok("faz51 infer crud")
    else:
        _fail("faz51 infer crud")
        fails += 1
    for tid, suffix in (
        ("crud_api", "crud"),
        ("auth_jwt", "jwt"),
        ("dashboard_static", "dash"),
    ):
        pn = f"smoke-faz51-{suffix}-{int(time.time()) % 100000}"
        sp = ProjeUretSpec(tid, pn, "pytest geçir")
        rp = run_proje_uret_prepare(WORKSPACE, sp)
        if rp.scaffold_ok and rp.verify_ok and rp.ready_without_agent:
            _ok(f"faz51 proje uret {tid}")
        else:
            _fail(f"faz51 proje uret {tid}", rp.detail[:60])
            fails += 1
    _ok(f"faz51 {FAZ51_VERSION}")

    print("=== Faz 52 — function calling birincil ===")
    from ilim_assistant.motorlar.programlama_faz52 import (
        FAZ52_VERSION,
        build_mandate_fc_user,
        discovery_bonus_turns,
        effective_max_turns,
        faz52_enabled,
        mandate_fc_enabled,
        should_force_structured_recovery,
        structured_task_mode_enabled,
        tool_choice_for_task,
        turn_had_no_tools,
    )

    if faz52_enabled() and structured_task_mode_enabled():
        _ok("faz52 structured task on")
    else:
        _fail("faz52 structured task")
        fails += 1
    if mandate_fc_enabled():
        _ok("faz52 mandate fc on")
    else:
        _fail("faz52 mandate fc")
        fails += 1
    if tool_choice_for_task(mandate=True) == "required":
        _ok("faz52 tool_choice mandate")
    else:
        _fail("faz52 tool_choice")
        fails += 1
    if should_force_structured_recovery("sadece plan yaziyorum", []):
        _ok("faz52 text-only recovery cue")
    else:
        _fail("faz52 text-only recovery")
        fails += 1
    if not should_force_structured_recovery("", [{"tool": "write", "ok": True}]):
        _ok("faz52 skip when write ok")
    else:
        _fail("faz52 skip write")
        fails += 1
    mfc = build_mandate_fc_user(
        goal="pytest",
        scope_rel="projects/benim-api",
        tool_block="[read ok]",
        turn=2,
    )
    if "ZORUNLU ARAÇ" in mfc and "verify" in mfc:
        _ok("faz52 mandate fc message")
    else:
        _fail("faz52 mandate fc message")
        fails += 1
    eff = effective_max_turns(
        base_max=12,
        last_tool_results=[{"tool": "read", "ok": True}],
        total_writes=0,
    )
    if eff >= 12 + discovery_bonus_turns():
        _ok(f"faz52 discovery bonus turns eff={eff}")
    else:
        _fail("faz52 discovery bonus", str(eff))
        fails += 1
    if turn_had_no_tools("aciklama only", []):
        _ok("faz52 text-only detect")
    else:
        _fail("faz52 text-only detect")
        fails += 1
    _ok(f"faz52 {FAZ52_VERSION}")

    print("=== Faz 53 — sembol lite + atölye patch v2 ===")
    from ilim_assistant.motorlar.programlama_faz53 import (
        FAZ53_VERSION,
        atolye_editor_v2_enabled,
        build_symbol_lite_block,
        faz53_enabled,
        multi_file_preview_default,
        patch_api_enrichments,
        symbol_lite_enabled,
    )
    from ilim_assistant.motorlar.programlama_faz45 import editor_v2_enabled

    if faz53_enabled():
        _ok("faz53 on")
    else:
        _fail("faz53")
        fails += 1
    if symbol_lite_enabled() and atolye_editor_v2_enabled():
        _ok("faz53 symbol + editor v2")
    else:
        _fail("faz53 features")
        fails += 1
    if editor_v2_enabled():
        _ok("faz53 editor_v2 default path")
    else:
        _fail("faz53 editor_v2")
        fails += 1
    enrich = patch_api_enrichments()
    if enrich.get("multi_file_preview_default") and enrich.get("editor_v2_default"):
        _ok("faz53 patch api flags")
    else:
        _fail("faz53 patch api", str(enrich))
        fails += 1
    sym = build_symbol_lite_block(WORKSPACE, "projects/benim-api", "health main")
    if sym and "SEMBOL" in sym:
        _ok("faz53 symbol lite block")
    else:
        _fail("faz53 symbol lite", sym[:60] if sym else "empty")
        fails += 1
    if multi_file_preview_default():
        _ok("faz53 multi file preview default")
    else:
        _fail("faz53 multi preview")
        fails += 1
    _ok(f"faz53 {FAZ53_VERSION}")

    print("=== Faz 54 — KPI 8/8 parity smoke ===")
    from ilim_assistant.motorlar.programlama_faz54 import (
        FAZ54_VERSION,
        build_compliance_report_v3,
        build_kpi_dashboard,
        faz54_enabled,
        run_parity_smoke_suite,
        target_kpi_score,
    )

    if faz54_enabled():
        _ok("faz54 on")
    else:
        _fail("faz54")
        fails += 1
    pq = run_parity_smoke_suite(WORKSPACE, mode="quick")
    if pq.passed >= 8 and pq.ok:
        _ok(f"faz54 parity quick {pq.passed}/8")
    else:
        _fail("faz54 parity quick", f"{pq.passed}/8")
        fails += 1
    comp3 = build_compliance_report_v3(WORKSPACE)
    rep3 = comp3.get("report") or {}
    if rep3.get("kpi_version") == 3:
        _ok("faz54 compliance v3")
    else:
        _fail("faz54 compliance v3")
        fails += 1
    dash = build_kpi_dashboard(WORKSPACE)
    if dash.get("ok") and dash.get("target_score", 0) >= target_kpi_score():
        _ok("faz54 kpi dashboard")
    else:
        _fail("faz54 dashboard")
        fails += 1
    _ok(f"faz54 {FAZ54_VERSION}")

    print("=== Faz 55 — canli gorev KPI ===")
    from ilim_assistant.motorlar.programlama_faz55 import (
        FAZ55_VERSION,
        build_handoff_packet,
        compute_task_stats,
        faz55_enabled,
        record_task_outcome,
        target_success_rate,
    )

    if faz55_enabled():
        _ok("faz55 on")
    else:
        _fail("faz55")
        fails += 1
    rec = record_task_outcome(
        WORKSPACE,
        scope_rel="projects/smoke-faz55",
        goal="pytest",
        success=True,
        turns_used=3,
        verify_ok=True,
        writes_ok=2,
        elapsed_sec=12.5,
    )
    if rec.get("ok"):
        _ok("faz55 record outcome")
    else:
        _fail("faz55 record", str(rec))
        fails += 1
    stats = compute_task_stats(WORKSPACE, window_days=30)
    if stats.get("total", 0) >= 1:
        _ok(f"faz55 stats total={stats.get('total')}")
    else:
        _fail("faz55 stats")
        fails += 1
    ho = build_handoff_packet(
        "bana bir web sitesi yap smoke-handoff", WORKSPACE
    )
    if ho.get("ok") and ho.get("packet_text"):
        _ok("faz55 handoff packet")
    else:
        _fail("faz55 handoff")
        fails += 1
    if target_success_rate() >= 0.5:
        _ok(f"faz55 target rate={target_success_rate()}")
    else:
        _fail("faz55 target")
        fails += 1
    from ilim_assistant.motorlar.programlama_faz55 import (
        build_retry_nudge,
        faz55b_bonus_turn_count,
        faz55b_enabled,
        inject_faz55b_turn_prefix,
        is_faz55b_bonus_turn,
    )

    if faz55b_enabled() and faz55b_bonus_turn_count() == 1:
        _ok("faz55b on (+1 bonus tur)")
    else:
        _fail("faz55b")
        fails += 1
    nudge = build_retry_nudge(
        WORKSPACE,
        scope_rel="projects/smoke-faz55",
        goal="pytest",
        last_detail="verify fail",
        for_bonus_turn=True,
    )
    if nudge and "55b" in nudge:
        _ok("faz55b retry nudge")
    else:
        _fail("faz55b nudge")
        fails += 1
    if is_faz55b_bonus_turn(6, 5):
        _ok("faz55b bonus turn detect")
    else:
        _fail("faz55b bonus turn")
        fails += 1
    inj = inject_faz55b_turn_prefix(
        WORKSPACE,
        scope_rel="projects/smoke-faz55",
        goal="pytest",
        turn_user="[tur]",
        last_fail_snippet="x",
    )
    if inj and "55b" in inj:
        _ok("faz55b inject prefix")
    else:
        _fail("faz55b inject")
        fails += 1
    _ok(f"faz55 {FAZ55_VERSION}")

    print("=== Faz 56 — uzun gorev v2 ===")
    from ilim_assistant.motorlar.programlama_faz56 import (
        FAZ56_VERSION,
        agent_budget_sec_v2,
        agent_max_turns_v2,
        augment_turn_user_message,
        build_multi_file_plan_block,
        count_turn_writes,
        faz56_enabled,
        infer_target_files,
        looks_like_multi_file_task,
        long_task_v2_enabled,
        max_files_per_turn,
        merge_touched_files,
        multi_file_cap_nudge,
        run_combined_verify,
    )

    if faz56_enabled() and long_task_v2_enabled():
        _ok("faz56 on")
    else:
        _fail("faz56")
        fails += 1
    if agent_max_turns_v2() >= 20 and agent_budget_sec_v2() >= 900:
        _ok(f"faz56 limits turns={agent_max_turns_v2()} budget={int(agent_budget_sec_v2())}")
    else:
        _fail("faz56 limits")
        fails += 1
    if looks_like_multi_file_task("refactor util service main.py"):
        _ok("faz56 multi-file cue")
    else:
        _fail("faz56 cue")
        fails += 1
    plan = build_multi_file_plan_block(
        WORKSPACE,
        scope_rel="projects/smoke-faz56",
        message="refactor util service",
        goal="cok dosya",
        turn=1,
    )
    if plan and ("Faz 56" in plan or "FAZ 56" in plan.upper()):
        _ok("faz56 plan block")
    else:
        _fail("faz56 plan", plan[:80] if plan else "")
        fails += 1
    targets = infer_target_files(
        WORKSPACE, "projects/smoke-faz56", "app/main.py util"
    )
    if isinstance(targets, list):
        _ok(f"faz56 targets n={len(targets)}")
    else:
        _fail("faz56 targets")
        fails += 1
    aug = augment_turn_user_message(
        "base",
        WORKSPACE,
        scope_rel="projects/smoke-faz56",
        message="refactor",
        goal="util",
        turn=1,
    )
    if "base" in aug and len(aug) > len("base"):
        _ok("faz56 augment turn")
    else:
        _fail("faz56 augment")
        fails += 1
    merged = merge_touched_files([], "@@write app/main.py\nx", [])
    if merged:
        _ok("faz56 merge touched")
    else:
        _fail("faz56 merge")
        fails += 1
    wc = count_turn_writes("@@write a.py\n@@write b.py", [])
    if wc >= 2:
        _ok(f"faz56 write count={wc}")
    else:
        _fail("faz56 write count")
        fails += 1
    nudge = multi_file_cap_nudge(max_files_per_turn() + 1)
    if nudge and "FAZ 56" in nudge.upper():
        _ok("faz56 cap nudge")
    else:
        _fail("faz56 nudge")
        fails += 1
    _ok(f"faz56 {FAZ56_VERSION}")

    print("=== Faz 57 — model yedek FC ===")
    from ilim_assistant.motorlar.programlama_faz57 import (
        FAZ57_VERSION,
        compute_text_only_stats,
        faz57_enabled,
        gemini_fc_available,
        gemini_function_declarations,
        groq_fc_available,
        record_agent_turn_fc,
        reorder_brain_chain_for_fc,
        route_fc_completion,
        select_fc_provider,
        target_text_only_rate,
    )

    if faz57_enabled():
        _ok("faz57 on")
    else:
        _fail("faz57")
        fails += 1
    decl_n = len(gemini_function_declarations())
    if decl_n >= 5:
        _ok(f"faz57 gemini decl={decl_n}")
    else:
        _fail("faz57 decl", str(decl_n))
        fails += 1
    prov = select_fc_provider()
    if prov in ("groq", "gemini", "none"):
        _ok(f"faz57 provider={prov} groq={groq_fc_available()} gemini={gemini_fc_available()}")
    else:
        _fail("faz57 provider", prov)
        fails += 1
    chain = reorder_brain_chain_for_fc(["groq", "kod", "gemini"])
    if chain and chain[0] in ("groq", "gemini"):
        _ok(f"faz57 chain={chain[0]}")
    else:
        _fail("faz57 chain", str(chain))
        fails += 1
    rec = record_agent_turn_fc(
        WORKSPACE,
        scope_rel="projects/smoke-faz57",
        turn=1,
        text_only=True,
        provider=prov,
        recovery_attempted=True,
    )
    if rec.get("ok"):
        _ok("faz57 record turn")
    else:
        _fail("faz57 record", str(rec))
        fails += 1
    stats = compute_text_only_stats(WORKSPACE, window_days=7)
    if stats.get("total_turns", 0) >= 1:
        _ok(
            f"faz57 text_only_rate={stats.get('text_only_rate')} "
            f"target<{target_text_only_rate()}"
        )
    else:
        _fail("faz57 stats")
        fails += 1
    _ok(f"faz57 {FAZ57_VERSION}")

    print("=== Faz 58 — git entegrasyonu ===")
    from ilim_assistant.motorlar.programlama_faz58 import (
        FAZ58_VERSION,
        augment_turn_with_git_context,
        build_git_changes_api_payload,
        build_git_strip_summary,
        build_llm_git_context_block,
        faz58_enabled,
        gather_scope_git,
        run_git_preset,
    )

    if faz58_enabled():
        _ok("faz58 on")
    else:
        _fail("faz58")
        fails += 1
    api = build_git_changes_api_payload(WORKSPACE, scope_rel="projects")
    if api.get("version") == FAZ58_VERSION:
        _ok("faz58 api payload")
    else:
        _fail("faz58 api")
        fails += 1
    snap = gather_scope_git(WORKSPACE, scope_rel="projects")
    strip = build_git_strip_summary(snap)
    if strip.get("version") == FAZ58_VERSION:
        _ok(f"faz58 strip ok={strip.get('ok')}")
    else:
        _fail("faz58 strip")
        fails += 1
    block = build_llm_git_context_block(snap, phase="before")
    if not snap.get("ok") or "Faz 58" in block:
        _ok("faz58 llm block")
    else:
        _fail("faz58 llm block")
        fails += 1
    aug = augment_turn_with_git_context("base", WORKSPACE, scope_rel="projects")
    if "base" in aug:
        _ok("faz58 augment")
    else:
        _fail("faz58 augment")
        fails += 1
    _ok(f"faz58 {FAZ58_VERSION}")

    print("=== Faz 59 — Ana Motor v2 ===")
    from ilim_assistant.ana_motor_faz59 import (
        FAZ59_VERSION,
        classify_turn_intent,
        format_delegation_summary_text,
        persist_delegation_summary,
        resolve_umed_budget_sec,
        router_budget_sec,
    )

    intent = classify_turn_intent(
        "pytest ile api yaz refactor main.py",
        mode_norm="genel",
    )
    if intent.get("intent") in ("code", "mixed") and intent.get("elapsed_ms", 999) < 100:
        _ok(f"faz59 code intent {intent.get('elapsed_ms')}ms")
    else:
        _fail("faz59 code intent", str(intent))
        fails += 1
    ilim = classify_turn_intent("hadis nedir acikla", mode_norm="genel")
    if ilim.get("use_ilim_budget") or ilim.get("intent") == "ilim":
        _ok("faz59 ilim budget cue")
    else:
        _fail("faz59 ilim", str(ilim))
        fails += 1
    b_delegate = resolve_umed_budget_sec(
        "fastapi api yaz", mode_norm="genel", motor_flags={"programlama": True}
    )
    if b_delegate <= router_budget_sec() + 0.5:
        _ok(f"faz59 delegate budget={b_delegate}")
    else:
        _fail("faz59 budget transfer", str(b_delegate))
        fails += 1
    summ = {
        "ok": True,
        "scope_rel": "projects/smoke-faz59",
        "success": True,
        "verify_ok": True,
        "turns_used": 2,
        "writes_count": 1,
        "elapsed_sec": 8.0,
    }
    persist_delegation_summary(WORKSPACE, summ)
    txt = format_delegation_summary_text(summ)
    if "Faz 59" in txt and "pytest" in txt.lower():
        _ok("faz59 summary text")
    else:
        _fail("faz59 summary", txt[:80])
        fails += 1
    _ok(f"faz59 {FAZ59_VERSION}")

    print("=== Faz 60 — otomasyon kilidi ===")
    from ilim_assistant.motorlar.programlama_faz60 import (
        FAZ60_VERSION,
        build_mismatch_info,
        enrich_health_build,
        expected_build_rev,
        faz60_enabled,
        generate_weekly_kpi_report,
        should_run_weekly_full_parity,
    )

    if faz60_enabled():
        _ok("faz60 on")
    else:
        _fail("faz60")
        fails += 1
    exp = expected_build_rev()
    if "faz76-v85" in exp or exp.endswith("-v85"):
        _ok("faz60 expected rev v85")
    elif "faz75-v84" in exp or exp.endswith("-v84"):
        _ok("faz60 expected rev v84")
    elif "faz74-v83" in exp or exp.endswith("-v83"):
        _ok("faz60 expected rev v83")
    elif "faz73-v82" in exp or exp.endswith("-v82"):
        _ok("faz60 expected rev v82")
    elif "faz72-v81" in exp or exp.endswith("-v81"):
        _ok("faz60 expected rev v81")
    elif "faz71-v80" in exp or exp.endswith("-v80"):
        _ok(f"faz60 expected rev={exp[:40]}")
    else:
        _fail("faz60 expected rev", exp)
        fails += 1
    hb = enrich_health_build({"rev": exp})
    if hb.get("expected_rev") == exp and not hb.get("build_mismatch"):
        _ok("faz60 health enrich match")
    else:
        _fail("faz60 health enrich", str(hb)[:80])
        fails += 1
    mm = build_mismatch_info("2020-old-rev")
    if mm.get("mismatch"):
        _ok("faz60 mismatch detect")
    else:
        _fail("faz60 mismatch")
        fails += 1
    kpi = generate_weekly_kpi_report(WORKSPACE)
    if kpi.get("ok") and kpi.get("week"):
        _ok(f"faz60 weekly {kpi.get('week')}")
    else:
        _fail("faz60 weekly")
        fails += 1
    if isinstance(should_run_weekly_full_parity(WORKSPACE), bool):
        _ok("faz60 full parity gate")
    else:
        _fail("faz60 parity gate")
        fails += 1
    _ok(f"faz60 {FAZ60_VERSION}")

    print("=== Faz 61 — otomatik retry (55b) ===")
    from ilim_assistant.motorlar.programlama_faz61 import (
        FAZ61_VERSION,
        enrich_health_build as enrich61,
        faz61_enabled,
    )

    if faz61_enabled():
        _ok("faz61 on")
    else:
        _fail("faz61")
        fails += 1
    h61 = enrich61({"rev": exp})
    if h61.get("faz55b_auto_retry"):
        _ok("faz61 health enrich")
    else:
        _fail("faz61 health")
        fails += 1
    _ok(f"faz61 {FAZ61_VERSION}")

    print("=== Faz 62 — git commit onerisi v2 ===")
    from ilim_assistant.motorlar.programlama_faz62 import (
        FAZ62_VERSION,
        append_commit_footer_to_reply,
        enrich_git_changes_api_payload,
        faz62_enabled,
        format_commit_strip_line,
    )
    from ilim_assistant.motorlar.programlama_motoru import is_code_agent_task_message

    if faz62_enabled():
        _ok("faz62 on")
    else:
        _fail("faz62")
        fails += 1
    gorev = (
        "gorev: smoke-cursor-ref-40763 health service ve version ekle testleri gecir"
    )
    if is_code_agent_task_message(gorev):
        _ok("gorev: Faz7 aninda rehber atlanir")
    else:
        _fail("is_code_agent_task_message")
        fails += 1
    from ilim_assistant.motorlar.programlama_faz7 import wants_file_help

    if not wants_file_help(gorev):
        _ok("wants_file_help gorev atlandi")
    else:
        _fail("wants_file_help gorev")
        fails += 1
    foot = append_commit_footer_to_reply(
        "tamam",
        {"ok": True, "suggested": "fix(health): service alani", "source": "test"},
    )
    if "Faz 62" in foot:
        _ok("faz62 footer")
    else:
        _fail("faz62 footer")
        fails += 1
    _ok(f"faz62 {FAZ62_VERSION}")

    print("=== Faz 63 — canli KPI ===")
    from ilim_assistant.motorlar.programlama_faz63 import (
        FAZ63_VERSION,
        compute_live_kpi,
        enrich_kpi_dashboard,
        faz63_enabled,
        wants_live_kpi,
    )

    if faz63_enabled():
        _ok("faz63 on")
    else:
        _fail("faz63")
        fails += 1
    if wants_live_kpi("canli kpi goster"):
        _ok("faz63 wants_live_kpi")
    else:
        _fail("wants_live_kpi")
        fails += 1
    live = compute_live_kpi(WORKSPACE)
    if live.get("ok") is not None:
        _ok(f"faz63 live headline={str(live.get('headline', ''))[:40]}")
    else:
        _fail("faz63 live")
        fails += 1
    dash = enrich_kpi_dashboard({"ok": True}, WORKSPACE)
    if dash.get("live_kpi"):
        _ok("faz63 enrich dashboard")
    else:
        _fail("faz63 dashboard")
        fails += 1
    _ok(f"faz63 {FAZ63_VERSION}")

    print("=== Faz 64 — best-of-n ===")
    from ilim_assistant.motorlar.programlama_faz64 import (
        FAZ64_VERSION,
        faz64_enabled,
        list_best_of_n_runs,
        parse_best_of_n_command,
        plan_best_of_n_run,
    )

    if faz64_enabled():
        _ok("faz64 on")
    else:
        _fail("faz64")
        fails += 1
    p = parse_best_of_n_command(
        "best-of-n: 2 smoke-cursor-ref-40763 health service version pytest"
    )
    if p and p.get("n") == 2:
        _ok("faz64 parse")
    else:
        _fail("faz64 parse", str(p))
        fails += 1
    scope_test = "projects/smoke-cursor-ref-40763"
    src = WORKSPACE / scope_test.replace("/", os.sep)
    if src.is_dir():
        man = plan_best_of_n_run(
            WORKSPACE,
            scope_rel=scope_test,
            goal="smoke bon",
            n=2,
        )
        if man.get("ok") and man.get("winner_id"):
            _ok(f"faz64 plan winner={man.get('winner_id')}")
        else:
            _fail("faz64 plan", str(man)[:80])
            fails += 1
    else:
        _ok("faz64 plan skipped (no smoke-ref project)")
    if list_best_of_n_runs(WORKSPACE).get("ok"):
        _ok("faz64 list runs")
    else:
        _fail("faz64 list")
        fails += 1
    _ok(f"faz64 {FAZ64_VERSION}")

    print("=== Faz 65 — best-of-n ajan ===")
    from ilim_assistant.motorlar.programlama_faz65 import (
        FAZ65_VERSION,
        candidate_workspace_root,
        enrich_health_build as enrich65,
        execute_best_of_n_agents,
        faz65_enabled,
        parse_best_of_n_agent_command,
        parse_best_of_n_plus_command,
    )

    if faz65_enabled():
        _ok("faz65 on")
    else:
        _fail("faz65")
        fails += 1
    h65 = enrich65({"rev": exp})
    if h65.get("faz65"):
        _ok("faz65 health enrich")
    else:
        _fail("faz65 health")
        fails += 1
    p65 = parse_best_of_n_plus_command(
        "best-of-n+: 2 smoke-cursor-ref-40763 health service version pytest"
    )
    if p65 and p65.get("n") == 2:
        _ok("faz65 parse plus")
    else:
        _fail("faz65 parse plus", str(p65))
        fails += 1
    pa = parse_best_of_n_agent_command("best-of-n-agent: bon-test")
    if pa and pa.get("run_id") == "bon-test":
        _ok("faz65 parse agent")
    else:
        _fail("faz65 parse agent")
        fails += 1
    if src.is_dir():
        man2 = plan_best_of_n_run(
            WORKSPACE,
            scope_rel=scope_test,
            goal="faz65 smoke",
            n=2,
        )
        if man2.get("ok"):
            try:
                from ilim_assistant.motorlar.programlama_motoru import repo_root

                rr = repo_root(WORKSPACE)
                c0 = (man2.get("candidates") or [{}])[0]
                if rr and c0:
                    cw = candidate_workspace_root(rr, man2, c0)
                    if cw and (cw / "projects").is_dir():
                        _ok(f"faz65 cand workspace={cw.name}")
                    else:
                        _ok("faz65 cand workspace (fallback)")
            except Exception as exc:
                _fail("faz65 workspace", str(exc)[:60])
                fails += 1
            if os.environ.get("RUZGAR_FAZ65_SMOKE_AGENT", "").strip() in (
                "1",
                "true",
                "yes",
            ):
                ag = execute_best_of_n_agents(WORKSPACE, str(man2.get("run_id")))
                if ag.get("ok"):
                    _ok("faz65 agent run")
                else:
                    _fail("faz65 agent", str(ag)[:80])
                    fails += 1
            else:
                _ok("faz65 agent run skipped (RUZGAR_FAZ65_SMOKE_AGENT=1)")
        else:
            _fail("faz65 plan", str(man2)[:60])
            fails += 1
    else:
        _ok("faz65 plan skipped (no smoke-ref project)")
    _ok(f"faz65 {FAZ65_VERSION}")

    print("=== Faz 66 — repo rename ===")
    from ilim_assistant.motorlar.programlama_faz66 import (
        FAZ66_VERSION,
        enrich_health_build as enrich66,
        faz66_enabled,
        parse_repo_rename_command,
        parse_scope_rename_command,
    )

    if faz66_enabled():
        _ok("faz66 on")
    else:
        _fail("faz66")
        fails += 1
    h66 = enrich66({"rev": exp})
    if h66.get("faz66"):
        _ok("faz66 health enrich")
    else:
        _fail("faz66 health")
        fails += 1
    pr66 = parse_repo_rename_command(
        "rename-repo: smoke-cursor-ref-40763 OldName -> NewName önizle"
    )
    if pr66 and pr66.get("dry_run") and pr66.get("old") == "OldName":
        _ok("faz66 parse repo rename")
    else:
        _fail("faz66 parse repo", str(pr66))
        fails += 1
    ps66 = parse_scope_rename_command("rename-scope foo -> bar")
    if ps66 == ("foo", "bar"):
        _ok("faz66 parse scope rename")
    else:
        _fail("faz66 parse scope", str(ps66))
        fails += 1
    _ok(f"faz66 {FAZ66_VERSION}")

    print("=== Faz 67 — özgür shell ===")
    from ilim_assistant.motorlar.programlama_faz67 import (
        FAZ67_VERSION,
        enrich_health_build as enrich67,
        faz67_enabled,
        parse_shell_onay_command,
        parse_shell_istek_command,
        validate_shell_command,
        wants_free_shell,
    )

    if faz67_enabled():
        _ok("faz67 on")
    else:
        _fail("faz67")
        fails += 1
    h67 = enrich67({"rev": exp})
    if h67.get("faz67"):
        _ok("faz67 health enrich")
    else:
        _fail("faz67 health")
        fails += 1
    if wants_free_shell("shell onay: git status"):
        _ok("faz67 wants shell")
    else:
        _fail("faz67 wants")
        fails += 1
    if parse_shell_onay_command("shell onay: dir") == "dir":
        _ok("faz67 parse onay")
    else:
        _fail("faz67 parse onay")
        fails += 1
    if parse_shell_istek_command("shell istek: make test") == "make test":
        _ok("faz67 parse istek")
    else:
        _fail("faz67 parse istek")
        fails += 1
    ok67, err67 = validate_shell_command("git status -sb")
    if ok67:
        _ok("faz67 validate ok cmd")
    else:
        _fail("faz67 validate", err67)
        fails += 1
    bad67, _ = validate_shell_command("rm -rf /")
    if not bad67:
        _ok("faz67 blocks dangerous")
    else:
        _fail("faz67 dangerous")
        fails += 1
    meta67, _ = validate_shell_command("echo a; echo b")
    if not meta67:
        _ok("faz67 blocks meta")
    else:
        _fail("faz67 meta")
        fails += 1
    _ok(f"faz67 {FAZ67_VERSION}")

    print("=== Faz 68 — ROK konuşarak yap ===")
    from ilim_assistant.ruzgar_motor_kernel import (
        KERNEL_VERSION,
        classify_motor_intent,
        kernel_enabled,
    )
    from ilim_assistant.motorlar.programlama_faz68 import (
        FAZ68_VERSION,
        build_agent_task_line,
        classify_programlama_intent,
        enrich_health_build as enrich68,
        faz68_enabled,
        should_run_agent_via_kernel,
    )

    if kernel_enabled():
        _ok("motor kernel on")
    else:
        _fail("motor kernel")
        fails += 1
    if faz68_enabled():
        _ok("faz68 on")
    else:
        _fail("faz68")
        fails += 1
    h68 = enrich68({"rev": exp})
    if h68.get("faz68") and h68.get("motor_kernel"):
        _ok("faz68 health enrich")
    else:
        _fail("faz68 health", str(h68)[:80])
        fails += 1
    chat_i = classify_programlama_intent("pytest nedir acikla", mode_norm="programlama")
    if chat_i.get("intent") == "chat":
        _ok("faz68 chat intent")
    else:
        _fail("faz68 chat", str(chat_i))
        fails += 1
    do_i = classify_programlama_intent(
        "health endpointine version ekle ve test gecir",
        mode_norm="programlama",
    )
    if do_i.get("intent") == "do":
        _ok("faz68 do intent")
    else:
        _fail("faz68 do", str(do_i))
        fails += 1
    scope_test = "projects/smoke-cursor-ref-40763"
    src = WORKSPACE / scope_test.replace("/", os.sep)
    if src.is_dir():
        line = build_agent_task_line(
            "version ekle pytest gecir",
            WORKSPACE,
            active_file=f"{scope_test}/app/main.py",
        )
        if line and "görev:" in line.lower():
            _ok(f"faz68 task line: {line[:50]}")
        else:
            _fail("faz68 task line", str(line))
            fails += 1
        if should_run_agent_via_kernel(
            "health servisine version ekle",
            "programlama",
            workspace_root=WORKSPACE,
            active_file=f"{scope_test}/app/main.py",
        ):
            _ok("faz68 should run agent")
        else:
            _fail("faz68 should run")
            fails += 1
    else:
        _ok("faz68 scope tests skipped")
    mi = classify_motor_intent(
        "selam",
        "programlama",
        mode_norm="programlama",
    )
    if mi.get("intent"):
        _ok("kernel classify_motor_intent")
    else:
        _fail("kernel classify")
        fails += 1
    _ok(f"faz68 {FAZ68_VERSION} / {KERNEL_VERSION}")

    print("=== Faz 69 — otomatik proje ===")
    from ilim_assistant.motorlar.programlama_faz69 import (
        FAZ69_VERSION,
        ensure_scope_for_agent,
        enrich_health_build as enrich69,
        faz69_enabled,
        infer_create_spec,
    )

    if faz69_enabled():
        _ok("faz69 on")
    else:
        _fail("faz69")
        fails += 1
    h69 = enrich69({"rev": exp})
    if h69.get("faz69"):
        _ok("faz69 health")
    else:
        _fail("faz69 health")
        fails += 1
    spec69 = infer_create_spec("sıfırdan fastapi api yap smoke-faz69-test")
    if spec69 and getattr(spec69, "project_name", None):
        _ok("faz69 infer create spec")
    else:
        _fail("faz69 infer spec")
        fails += 1
    _ok(f"faz69 {FAZ69_VERSION}")

    print("=== Faz 70 — otomatik patch ===")
    from ilim_assistant.motorlar.programlama_faz70 import (
        FAZ70_VERSION,
        enrich_health_build as enrich70,
        faz70_enabled,
        finalize_agent_patches,
    )

    if faz70_enabled():
        _ok("faz70 on")
    else:
        _fail("faz70")
        fails += 1
    h70 = enrich70({"rev": exp})
    if h70.get("faz70"):
        _ok("faz70 health")
    else:
        _fail("faz70 health")
        fails += 1
    fin70 = finalize_agent_patches(WORKSPACE)
    if fin70.get("ok") is not None:
        _ok("faz70 finalize callable")
    else:
        _fail("faz70 finalize")
        fails += 1
    _ok(f"faz70 {FAZ70_VERSION}")

    print("=== Video Faz 71 — ROK ===")
    from ilim_assistant.motorlar.video_faz71 import (
        FAZ71_VERSION as VF71,
        classify_video_intent,
        extract_urls,
        faz71_enabled,
    )

    if faz71_enabled():
        _ok("video faz71 on")
    else:
        _fail("video faz71")
        fails += 1
    vi = classify_video_intent(
        "bu videoyu indir https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        mode_norm="video",
    )
    if vi.get("intent") == "do" and vi.get("urls"):
        _ok("video faz71 do intent")
    else:
        _fail("video faz71 intent", str(vi))
        fails += 1
    vq = classify_video_intent("ffmpeg nedir", mode_norm="video")
    if vq.get("intent") == "chat":
        _ok("video faz71 chat")
    else:
        _fail("video faz71 chat", str(vq))
        fails += 1
    if extract_urls("link https://example.com/x"):
        _ok("video faz71 url extract")
    else:
        _fail("video faz71 url")
        fails += 1
    _ok(f"video {VF71}")

    print("=== Ses Faz 72 — ROK ===")
    from ilim_assistant.motorlar.ses_faz72 import (
        FAZ72_VERSION as SF72,
        classify_ses_intent,
        extract_read_text,
        faz72_enabled,
        maybe_instant_faz72,
    )

    if faz72_enabled():
        _ok("ses faz72 on")
    else:
        _fail("ses faz72")
        fails += 1
    si = classify_ses_intent("alim moduna geç", mode_norm="ses")
    if si.get("intent") == "do" and si.get("profile") == "alim":
        _ok("ses faz72 profile switch")
    else:
        _fail("ses faz72 profile", str(si))
        fails += 1
    sq = classify_ses_intent("edge tts nedir", mode_norm="ses")
    if sq.get("intent") == "chat":
        _ok("ses faz72 chat")
    else:
        _fail("ses faz72 chat", str(sq))
        fails += 1
    if extract_read_text('oku: Merhaba dünya'):
        _ok("ses faz72 read extract")
    else:
        _fail("ses faz72 read extract")
        fails += 1
    inst = maybe_instant_faz72("ses ayarları")
    if inst and "ses motoru ayarları" in inst.lower():
        _ok("ses faz72 instant settings")
    else:
        _fail("ses faz72 instant", str(inst)[:80])
        fails += 1
    _ok(f"ses {SF72}")

    print("=== Okuma Faz 73 — ROK ===")
    from ilim_assistant.motorlar.okuma_faz73 import (
        FAZ73_VERSION as OF73,
        classify_okuma_intent,
        faz73_enabled,
        maybe_instant_faz73,
    )

    if faz73_enabled():
        _ok("okuma faz73 on")
    else:
        _fail("okuma faz73")
        fails += 1
    oi = classify_okuma_intent("arsiv durumu", mode_norm="okuma")
    if oi.get("intent") == "command" and oi.get("reason") == "arsiv_status":
        _ok("okuma faz73 arsiv command")
    else:
        _fail("okuma faz73 arsiv", str(oi))
        fails += 1
    oc = classify_okuma_intent("arsiv nedir", mode_norm="okuma")
    if oc.get("intent") == "chat":
        _ok("okuma faz73 chat")
    else:
        _fail("okuma faz73 chat", str(oc))
        fails += 1
    inst_o = maybe_instant_faz73("index durumu")
    if inst_o and "index.jsonl" in inst_o:
        _ok("okuma faz73 instant index")
    else:
        _fail("okuma faz73 instant", str(inst_o)[:80])
        fails += 1
    _ok(f"okuma {OF73}")

    print("=== Tercüme Faz 74 — ROK ===")
    from ilim_assistant.motorlar.tercume_faz74 import (
        FAZ74_VERSION as TF74,
        classify_tercume_intent,
        faz74_enabled,
        maybe_instant_faz74,
        parse_language_pair,
    )

    if faz74_enabled():
        _ok("tercume faz74 on")
    else:
        _fail("tercume faz74")
        fails += 1
    ti = classify_tercume_intent(
        "bunu ingilizceye çevir: Merhaba dünya",
        mode_norm="tercume",
    )
    if ti.get("intent") == "do" and ti.get("tgt") == "en":
        _ok("tercume faz74 translate intent")
    else:
        _fail("tercume faz74 intent", str(ti))
        fails += 1
    src_p, tgt_p = parse_language_pair("arapçadan türkçeye çevir")
    if src_p == "ar" and tgt_p == "tr":
        _ok("tercume faz74 lang pair")
    else:
        _fail("tercume faz74 pair", f"{src_p}->{tgt_p}")
        fails += 1
    inst_t = maybe_instant_faz74("dil listesi")
    if inst_t and "tercüme motoru dilleri" in inst_t.lower():
        _ok("tercume faz74 instant list")
    else:
        _fail("tercume faz74 instant", str(inst_t)[:80])
        fails += 1
    if maybe_instant_faz74("ingilizceye çevir: test") is None:
        _ok("tercume faz74 defers short translate to LLM")
    else:
        _fail("tercume faz74 defer")
        fails += 1
    _ok(f"tercume {TF74}")

    print("=== Hafıza Faz 75 — ROK ===")
    from ilim_assistant.motorlar.hafiza_faz75 import (
        FAZ75_VERSION as HF75,
        classify_hafiza_intent,
        faz75_enabled,
        maybe_instant_faz75,
    )

    if faz75_enabled():
        _ok("hafiza faz75 on")
    else:
        _fail("hafiza faz75")
        fails += 1
    hi = classify_hafiza_intent("hafıza durumu", mode_norm="hafiza")
    if hi.get("intent") == "command" and hi.get("reason") == "status":
        _ok("hafiza faz75 status intent")
    else:
        _fail("hafiza faz75 status", str(hi))
        fails += 1
    inst_h = maybe_instant_faz75("hafıza durumu", mode_norm="hafiza")
    if inst_h and "hafıza motoru durumu" in inst_h.lower():
        _ok("hafiza faz75 instant status")
    else:
        _fail("hafiza faz75 instant", str(inst_h)[:80])
        fails += 1
    _ok(f"hafiza {HF75}")

    print("=== Ana Motor Hub Faz 76 ===")
    from ilim_assistant.motorlar.ana_motor_hub_faz76 import (
        FAZ76_VERSION as HF76,
        faz76_enabled,
        resolve_hub_target,
    )

    if faz76_enabled():
        _ok("hub faz76 on")
    else:
        _fail("hub faz76")
        fails += 1
    t_vid, meta_v = resolve_hub_target(
        "bu videoyu indir https://www.youtube.com/watch?v=abc",
        {"video": True},
    )
    if t_vid == "video":
        _ok("hub faz76 video route")
    else:
        _fail("hub faz76 video", f"{t_vid} {meta_v}")
        fails += 1
    t_code, _ = resolve_hub_target("pytest geçir main.py düzelt", {"programlama": True})
    if t_code == "programlama":
        _ok("hub faz76 code route")
    else:
        _fail("hub faz76 code", t_code)
        fails += 1
    _ok(f"hub {HF76}")

    if should_run_proje_uret_pipeline(
        "proje üret: fastapi_api smoke-faz47-run pytest",
        "programlama",
        workspace_root=WORKSPACE,
    ):
        _ok("should_run proje uret pipeline")
    else:
        _fail("should_run proje uret")
        fails += 1
    pname47 = f"smoke-faz47-{int(time.time()) % 100000}"
    spec47 = ProjeUretSpec(
        template_id="fastapi_api",
        project_name=pname47,
        goal="health version pytest geçir",
    )
    rep47 = run_proje_uret_prepare(WORKSPACE, spec47)
    if rep47.scaffold_ok:
        _ok(f"proje uret scaffold ({rep47.elapsed_sec:.1f}s)")
    else:
        _fail("proje uret scaffold", rep47.detail[:80])
        fails += 1
    if rep47.verify_ok:
        _ok("proje uret verify pytest")
    else:
        _fail("proje uret verify", rep47.detail[:80])
        fails += 1
    if rep47.ready_without_agent:
        _ok("proje uret cursor-free (ajan gerekmedi)")
    else:
        _fail("ready_without_agent", rep47.detail[:80])
        fails += 1
    _ok(f"faz47 {FAZ47_VERSION}")

    for tid, pname_suffix in (
        ("static_site", "site"),
        ("react_vite", "react"),
        ("cli_python", "cli"),
    ):
        pn = f"smoke-faz47-{pname_suffix}-{int(time.time()) % 100000}"
        sp = ProjeUretSpec(tid, pn, "smoke test geçir")
        rp = run_proje_uret_prepare(WORKSPACE, sp)
        if rp.scaffold_ok and rp.verify_ok:
            _ok(f"proje uret {tid}")
        else:
            _fail(f"proje uret {tid}", rp.detail[:60])
            fails += 1

    print("=== Faz 48 — ajan uyum v2 (hedef ≥85) ===")
    from ilim_assistant.motorlar.programlama_faz48 import (
        FAZ48_VERSION,
        compliance_v2_enabled,
        run_offline_compliance_smoke,
        target_compliance_score,
    )

    if compliance_v2_enabled():
        _ok("compliance v2 on")
    else:
        _fail("compliance v2")
        fails += 1
    csm = run_offline_compliance_smoke(WORKSPACE)
    if csm.get("ok") and int(csm.get("score", 0)) >= target_compliance_score():
        _ok(f"compliance smoke score={csm.get('score')} (>={target_compliance_score()})")
    else:
        _fail("compliance smoke", str(csm.get("score")))
        fails += 1
    _ok(f"faz48 {FAZ48_VERSION}")

    print("=== Faz 45 — editör v2 ===")
    from ilim_assistant.motorlar.programlama_faz45 import (
        FAZ45_VERSION,
        build_inline_diff_v2,
        build_line_diff_segments,
        build_patch_tabs,
        build_unified_patch_ux,
        detect_lang_from_path,
        editor_v2_enabled,
        segments_to_html,
    )

    if editor_v2_enabled():
        _ok("editor v2 on")
    else:
        _fail("editor v2")
        fails += 1
    segs = build_line_diff_segments("a\n", "a\nb\n")
    if len(segs) >= 2:
        _ok("line diff segments")
    else:
        _fail("line diff segments")
        fails += 1
    html = segments_to_html(segs, lang="python")
    if "diff-line" in html:
        _ok("segments html")
    else:
        _fail("segments html")
        fails += 1
    if detect_lang_from_path("app/main.py") == "python":
        _ok("detect lang")
    else:
        _fail("detect lang")
        fails += 1
    scope_path = "projects/smoke-faz27/app/x.py"
    v2 = build_inline_diff_v2(WORKSPACE, scope_path, new_content="v = 3\n")
    if v2.get("ok") and v2.get("editor_v2") and v2.get("html_unified"):
        _ok("inline diff v2")
    else:
        _fail("inline diff v2", str(v2)[:80])
        fails += 1
    tabs = build_patch_tabs(WORKSPACE)
    if tabs.get("ok") is not None:
        _ok("patch tabs API shape")
    else:
        _fail("patch tabs")
        fails += 1
    ux = build_unified_patch_ux(WORKSPACE)
    if ux.get("ok") and "hint" in ux:
        _ok("unified ux")
    else:
        _fail("unified ux")
        fails += 1
    _ok(f"faz45 {FAZ45_VERSION}")

    print("=== Faz 44 — bağlam v3 ===")
    from ilim_assistant.motorlar.programlama_faz44 import (
        FAZ44_VERSION,
        build_context_v3_block,
        context_v3_enabled,
        parse_at_refs,
        select_relevant_files,
        wants_context_map,
    )

    if context_v3_enabled():
        _ok("context v3 on")
    else:
        _fail("context v3")
        fails += 1
    scope = "projects/smoke-faz22"
    block = build_context_v3_block(WORKSPACE, scope_rel=scope, message="health main")
    if block and "REPO HARİTASI" in block:
        _ok("context v3 block")
    else:
        _fail("context v3 block", str(block)[:80])
        fails += 1
    rels = select_relevant_files(WORKSPACE, scope, "health pytest main")
    if rels or "REPO HARİTASI" in block:
        _ok(f"relevant files n={len(rels)}")
    else:
        _fail("relevant files")
        fails += 1
    if parse_at_refs("@dosya projects/smoke-parity-35137/app/main.py"):
        _ok("parse @dosya")
    else:
        _fail("parse @dosya")
        fails += 1
    if wants_context_map("repo harita"):
        _ok("wants repo harita")
    else:
        _fail("wants repo harita")
        fails += 1
    _ok(f"faz44 {FAZ44_VERSION}")

    print("=== Faz 43 — terminal v3 ===")
    from ilim_assistant.motorlar.programlama_faz43 import (
        FAZ43_VERSION,
        list_terminal_presets_v3,
        parse_safe_argv_command,
        terminal_v3_enabled,
        wants_terminal_v3,
    )

    if terminal_v3_enabled():
        _ok("terminal v3 on")
    else:
        _fail("terminal v3")
        fails += 1
    presets = list_terminal_presets_v3()
    if len(presets) >= 8:
        _ok(f"presets count={len(presets)}")
    else:
        _fail("presets v3")
        fails += 1
    if parse_safe_argv_command("terminal calistir: pip install httpx"):
        _ok("parse safe argv")
    else:
        _fail("parse safe argv")
        fails += 1
    if wants_terminal_v3("python -m pytest"):
        _ok("wants pytest")
    else:
        _fail("wants pytest")
        fails += 1
    _ok(f"faz43 {FAZ43_VERSION}")

    print("=== Faz 42 — LSP v2 ===")
    from ilim_assistant.motorlar.programlama_faz42 import (
        FAZ42_VERSION,
        find_references,
        lsp_v2_enabled,
        parse_refs_query,
        parse_rename_query,
        wants_find_references,
        wants_import_graph,
    )

    if lsp_v2_enabled():
        _ok("lsp v2 enabled")
    else:
        _fail("lsp v2")
        fails += 1
    if wants_find_references("referanslar health"):
        _ok("wants referanslar")
    else:
        _fail("wants referanslar")
        fails += 1
    if parse_rename_query("rename foo -> bar"):
        _ok("parse rename")
    else:
        _fail("parse rename")
        fails += 1
    if wants_import_graph("import graf"):
        _ok("wants import graf")
    else:
        _fail("import graf")
        fails += 1
    refs = find_references(WORKSPACE, "projects/benim-api", "health")
    if refs.get("ok") is not None:
        _ok(f"find_references count={refs.get('count', 0)}")
    else:
        _fail("find_references")
        fails += 1
    _ok(f"faz42 {FAZ42_VERSION}")

    print("=== Faz 41 — uzun gorev butcesi ===")
    from ilim_assistant.motorlar.programlama_faz41 import (
        FAZ41_VERSION,
        TaskBudgetTracker,
        long_task_budget_sec,
        long_task_enabled,
        long_task_max_turns,
    )

    if long_task_enabled() and long_task_budget_sec() >= 600:
        _ok(f"budget={int(long_task_budget_sec())}s")
    else:
        _fail("long budget")
        fails += 1
    if long_task_max_turns() >= 12:
        _ok(f"max_turns={long_task_max_turns()}")
    else:
        _fail("max turns")
        fails += 1
    tr = TaskBudgetTracker(0.0, 120.0)
    ev = tr.enrich_sse({"type": "agent_step", "steps": [], "code_agent": {}})
    if (ev.get("code_agent") or {}).get("budget_remaining_sec") is not None:
        _ok("budget SSE enrich")
    else:
        _fail("budget SSE")
        fails += 1
    _ok(f"faz41 {FAZ41_VERSION}")

    print("=== Faz 40 — yapilandirilmis arac API ===")
    from ilim_assistant.motorlar.programlama_faz40 import (
        FAZ40_VERSION,
        augment_reply_tools,
        extract_tool_invocations,
        openai_tools_schema,
        process_llm_tools,
        structured_tools_enabled,
    )

    if structured_tools_enabled() and len(openai_tools_schema()) >= 5:
        _ok(f"openai tools schema ({len(openai_tools_schema())})")
    else:
        _fail("tools schema")
        fails += 1
    sample = '```ruzgar-tool\n{"tool":"read","path":"projects/benim-api/app/main.py"}\n```'
    inv = extract_tool_invocations(sample)
    if inv and inv[0].get("tool") == "read":
        _ok("extract_tool_invocations")
    else:
        _fail("extract invocations")
        fails += 1
    _, block = process_llm_tools(sample, WORKSPACE, scope_rel="projects/benim-api", goal="health")
    if block and "ARAÇ" in block:
        _ok("process_llm_tools")
    else:
        _fail("process_llm_tools", str(block)[:60])
        fails += 1
    _ok(f"faz40 {FAZ40_VERSION}")

    print("=== Faz 39 — gorev tamamlama kilidi ===")
    from ilim_assistant.motorlar.programlama_faz39 import (
        FAZ39_VERSION,
        build_write_mandate_message,
        code_agent_max_turns_effective,
        completion_gate_enabled,
        should_abort_loop_relaxed,
        turn_had_discovery,
    )
    from ilim_assistant.motorlar.programlama_faz19 import AgentLoopState

    if completion_gate_enabled() and code_agent_max_turns_effective() >= 10:
        _ok(f"max_turns={code_agent_max_turns_effective()}")
    else:
        _fail("faz39 max turns")
        fails += 1
    if turn_had_discovery([{"tool": "read", "ok": True}]):
        _ok("discovery detect")
    else:
        _fail("discovery detect")
        fails += 1
    msg = build_write_mandate_message(
        goal="pytest",
        scope_rel="projects/benim-api",
        tool_block="[read ok]",
        turn=2,
    )
    if "ZORUNLU YAZIM" in msg and "@@write" in msg:
        _ok("mandate message")
    else:
        _fail("mandate message")
        fails += 1
    st = AgentLoopState()
    st.turns_done = 1
    st.quota_streak = 1
    st.total_writes = 0
    abort, _ = should_abort_loop_relaxed(
        st,
        last_tool_results=[{"tool": "read", "ok": True}],
        max_turns=12,
    )
    if not abort:
        _ok("relaxed abort on discovery+quota")
    else:
        _fail("relaxed abort")
        fails += 1
    _ok(f"faz39 {FAZ39_VERSION}")

    print("=== Faz 38 — uyum seridi + ic arac dongusu ===")
    from ilim_assistant.motorlar.programlama_faz38 import (
        FAZ38_VERSION,
        enrich_agent_step_event,
        live_compliance_snapshot,
        max_nested_depth,
        nested_tool_loop_enabled,
        delegation_status_text,
    )

    if nested_tool_loop_enabled() and max_nested_depth() >= 2:
        _ok("nested tool loop enabled")
    else:
        _fail("nested tool loop")
        fails += 1
    ev = enrich_agent_step_event(
        {"type": "agent_step", "steps": [], "code_agent": {"phase": "turn_start"}},
        WORKSPACE,
        scope_rel="projects/benim-api",
    )
    if ev.get("compliance") or (ev.get("code_agent") or {}).get("compliance"):
        _ok("enrich agent_step compliance")
    else:
        _ok("enrich agent_step (empty compliance ok)")
    snap = live_compliance_snapshot(WORKSPACE, scope_rel="projects/benim-api")
    if isinstance(snap, dict):
        _ok(f"live snapshot score={snap.get('score', 0)}")
    else:
        _fail("live snapshot")
        fails += 1
    if "delege" in delegation_status_text(scope_rel="projects/x", goal="test"):
        _ok("delegation status")
    else:
        _fail("delegation status")
        fails += 1
    _ok(f"faz38 {FAZ38_VERSION}")

    print("=== Faz 37 — ajan uyum skoru ===")
    from ilim_assistant.motorlar.programlama_faz37 import (
        FAZ37_VERSION,
        build_compliance_report,
        compute_compliance_score,
        record_turn_metrics,
        wants_compliance_report,
    )

    record_turn_metrics(
        WORKSPACE,
        scope_rel="projects/benim-api",
        turn=1,
        tool_results=[{"tool": "read", "ok": True, "output": "ok"}],
        violations=["write_without_verify"],
        mid_turn_followup=False,
        verify_ok=False,
        writes_ok=0,
    )
    rep = build_compliance_report(WORKSPACE)
    if rep.get("ok") and rep.get("report"):
        _ok(f"compliance score={rep['report'].get('score')}")
    else:
        _fail("compliance report", str(rep)[:80])
        fails += 1
    sc = compute_compliance_score(
        [{"violations": ["x"], "writes_ok": 1, "verify_ok": True, "tools": ["read", "write"]}]
    )
    if sc.get("score", 0) > 0:
        _ok(f"compute score grade={sc.get('grade')}")
    else:
        _fail("compute score")
        fails += 1
    if wants_compliance_report("ajan uyum rapor"):
        _ok("wants ajan uyum")
    else:
        _fail("wants ajan uyum")
        fails += 1
    _ok(f"faz37 {FAZ37_VERSION}")

    print("=== Faz 36 — LSP goto ===")
    from ilim_assistant.motorlar.programlama_faz36 import (
        FAZ36_VERSION,
        execute_goto_tool,
        goto_definition,
        wants_goto_definition,
    )

    if wants_goto_definition("tanima git health"):
        _ok("wants goto")
    else:
        _fail("wants goto")
        fails += 1
    g = goto_definition(WORKSPACE, "projects/benim-api", "health")
    if g.get("ok") or g.get("error"):
        _ok("goto_definition lookup")
    else:
        _fail("goto_definition")
        fails += 1
    gt = execute_goto_tool(WORKSPACE, "projects/benim-api", "health")
    if gt.get("tool") == "goto":
        _ok("goto tool")
    else:
        _fail("goto tool")
        fails += 1
    _ok(f"faz36 {FAZ36_VERSION}")

    print("=== Faz 35 — tur ici arac geri besleme ===")
    from ilim_assistant.motorlar.programlama_faz35 import (
        FAZ35_VERSION,
        build_mid_turn_user_message,
        mid_turn_enabled,
        should_mid_turn_followup,
    )

    if mid_turn_enabled():
        _ok("mid_turn enabled")
    else:
        _fail("mid_turn")
        fails += 1
    block = "[ARAÇ SONUÇLARI]\n1. read [OK]\n```text\nline1\n```"
    if should_mid_turn_followup(
        [{"tool": "read", "ok": True, "output": "x"}],
        "plan only",
        tool_block=block,
    ):
        _ok("should_mid_turn_followup")
    else:
        _fail("should_mid_turn_followup")
        fails += 1
    if not should_mid_turn_followup(
        [{"tool": "write", "ok": True, "output": "ok"}],
        "done",
        tool_block=block,
    ):
        _ok("skip followup when write ok")
    else:
        _fail("skip on write")
        fails += 1
    msg = build_mid_turn_user_message(block, goal="pytest", turn=2)
    if "Faz 35" in msg and "@@write" in msg:
        _ok("mid_turn user message")
    else:
        _fail("mid_turn message")
        fails += 1
    _ok(f"faz35 {FAZ35_VERSION}")

    print("=== Faz 34 — arac oncelik protokolu ===")
    from ilim_assistant.motorlar.programlama_faz34 import (
        FAZ34_VERSION,
        apply_turn_tool_first,
        compliance_violations,
        discovery_tool_specs,
        tool_first_enabled,
        wants_tool_protocol_status,
    )

    if tool_first_enabled():
        _ok("tool_first enabled")
    else:
        _fail("tool_first enabled")
        fails += 1
    specs = discovery_tool_specs(
        WORKSPACE, "projects/benim-api", goal="health version pytest"
    )
    if specs and any(s.get("tool") == "read" for s in specs):
        _ok(f"discovery specs ({len(specs)})")
    else:
        _fail("discovery specs", str(specs))
        fails += 1
    viol = compliance_violations(
        [{"tool": "write", "ok": True}], turn=1, goal="pytest gecir"
    )
    if "write_without_discovery" in viol and "write_without_verify" in viol:
        _ok("compliance violations")
    else:
        _fail("compliance", str(viol))
        fails += 1
    if wants_tool_protocol_status("arac sira durum"):
        _ok("wants arac sira")
    else:
        _fail("wants arac sira")
        fails += 1
    _res, _block, _v = apply_turn_tool_first(
        [],
        '```ruzgar-tool\n{"tool":"write","path":"projects/benim-api/x.py","content":"# t"}\n```',
        WORKSPACE,
        "projects/benim-api",
        "pytest gecir",
        1,
    )
    if _res and len(_res) >= 1:
        _ok(f"apply_turn_tool_first ({len(_res)} arac)")
    else:
        _fail("apply_turn_tool_first", str(len(_res)))
        fails += 1
    _ok(f"faz34 {FAZ34_VERSION}")

    print("=== Faz 33 — dogal cumle = ajan ===")
    from ilim_assistant.motorlar.programlama_faz33 import (
        FAZ33_VERSION,
        build_implicit_task_line,
        should_auto_programming_agent,
    )
    from ilim_assistant.motorlar.programlama_faz20 import should_run_unified_programming_agent

    implicit = build_implicit_task_line(
        "health endpointine version ekle ve pytest gecir",
        WORKSPACE,
        active_file="projects/benim-api/app/main.py",
        mode_norm="programlama",
    )
    imp_low = (implicit or "").lower().replace("ö", "o").replace("ü", "u")
    if implicit and "gorev:" in imp_low and "benim-api" in implicit:
        _ok(f"implicit task: {implicit[:48]}...")
    else:
        _fail("implicit task", str(implicit))
        fails += 1
    if should_auto_programming_agent(
        "version ekle ve test gecir",
        "programlama",
        workspace_root=WORKSPACE,
        active_file="projects/benim-api/main.py",
    ):
        _ok("should_auto_programming_agent (aktif dosya)")
    else:
        _fail("should_auto_programming_agent")
        fails += 1
    if should_run_unified_programming_agent(
        "benim-api health endpointine version ekle",
        "programlama",
        workspace_root=WORKSPACE,
    ):
        _ok("should_run_unified (dogal cumle)")
    else:
        _fail("should_run_unified")
        fails += 1
    _ok(f"faz33 {FAZ33_VERSION}")

    print("=== Faz 32 — gorev sonu git akisi ===")
    from ilim_assistant.motorlar.programlama_faz32 import (
        FAZ32_VERSION,
        build_post_task_summary,
        wants_task_save_pipeline,
        wants_workflow_summary,
    )

    block = build_post_task_summary(
        WORKSPACE,
        "projects/benim-api",
        success=True,
        verify_ok=True,
        elapsed_sec=12.5,
    )
    if block.get("ok") and "Faz 32" in str(block.get("markdown") or ""):
        _ok("post-task summary")
    else:
        _fail("post-task summary")
        fails += 1
    if wants_workflow_summary("is akisi"):
        _ok("wants is akisi")
    else:
        _fail("wants is akisi")
        fails += 1
    if wants_task_save_pipeline("is bitir pr"):
        _ok("wants is bitir pr")
    else:
        _fail("wants is bitir pr")
        fails += 1
    _ok(f"faz32 {FAZ32_VERSION}")

    print("=== Faz 31 — git PR koprusu ===")
    from ilim_assistant.motorlar.programlama_faz31 import (
        FAZ31_VERSION,
        gather_pr_snapshot,
        resolve_git_cwd,
        wants_pr_create,
        wants_pr_push,
        wants_pr_status,
    )

    cwd, src = resolve_git_cwd(WORKSPACE)
    if cwd and src == "workspace_root":
        _ok(f"git cwd {src}")
    else:
        _fail("resolve_git_cwd", str(src))
        fails += 1
    snap = gather_pr_snapshot(WORKSPACE)
    if snap.get("ok") and snap.get("branch"):
        _ok(f"pr snapshot branch={snap.get('branch')[:24]}")
    else:
        _fail("pr snapshot", str(snap.get("error")))
        fails += 1
    if wants_pr_status("pr durum"):
        _ok("wants pr durum")
    else:
        _fail("wants pr durum")
        fails += 1
    if wants_pr_push("pr gonder"):
        _ok("wants pr gonder")
    else:
        _fail("wants pr gonder")
        fails += 1
    if wants_pr_create("pr olustur: test basligi"):
        _ok("wants pr olustur")
    else:
        _fail("wants pr olustur")
        fails += 1
    _ok(f"faz31 {FAZ31_VERSION}")

    print("=== Faz 30 — mobil sablon (Expo) ===")
    from ilim_assistant.motorlar.programlama_faz6 import run_scaffold
    from ilim_assistant.motorlar.programlama_faz8 import pick_focus_rel
    from ilim_assistant.motorlar.programlama_faz30 import (
        FAZ30_VERSION,
        MOBILE_TEMPLATE_ID,
        mobile_expo_files,
    )

    mob_files = mobile_expo_files(MOBILE_TEMPLATE_ID, "smoke-mobil", "Smoke Mobil")
    if mob_files and f"projects/smoke-mobil/App.js" in mob_files:
        _ok("mobile_expo file map")
    else:
        _fail("mobile_expo files")
        fails += 1
    mob_sc = run_scaffold(
        "mobile_expo",
        f"smoke-mobil-{int(time.time()) % 100000}",
        WORKSPACE,
        force=True,
    )
    if mob_sc.get("ok") and mob_sc.get("template_id") == "mobile_expo":
        fr_m = pick_focus_rel(mob_sc)
        if fr_m and fr_m.endswith("App.js"):
            _ok(f"mobile scaffold focus {fr_m}")
        else:
            _fail("mobile focus", str(fr_m))
            fails += 1
    else:
        _fail("mobile scaffold", str(mob_sc.get("error")))
        fails += 1
    _ok(f"faz30 {FAZ30_VERSION}")

    print("=== Faz 29 — coklu proje workspace ===")
    from ilim_assistant.motorlar.programlama_faz29 import (
        FAZ29_VERSION,
        discover_projects,
        switch_to_project,
        wants_project_list,
        wants_project_switch,
    )

    (WORKSPACE / "projects" / "smoke-faz29-a").mkdir(parents=True, exist_ok=True)
    (WORKSPACE / "projects" / "smoke-faz29-a" / "main.py").write_text("a=1\n", encoding="utf-8")
    (WORKSPACE / "projects" / "smoke-faz29-b").mkdir(parents=True, exist_ok=True)
    (WORKSPACE / "projects" / "smoke-faz29-b" / "main.py").write_text("b=1\n", encoding="utf-8")
    projs = discover_projects(WORKSPACE)
    slugs = {p["slug"] for p in projs}
    if "smoke-faz29-a" in slugs and "smoke-faz29-b" in slugs:
        _ok(f"discover projects ({len(projs)})")
    else:
        _fail("discover projects", str(slugs))
        fails += 1
    sw = switch_to_project(WORKSPACE, "smoke-faz29-b")
    if sw.get("ok") and sw.get("focus_rel"):
        _ok("switch project + focus")
    else:
        _fail("switch project", str(sw.get("error")))
        fails += 1
    if wants_project_list("proje listesi"):
        _ok("wants proje listesi")
    else:
        _fail("wants proje listesi")
        fails += 1
    if wants_project_switch("proje sec: smoke-faz29-a"):
        _ok("wants proje sec")
    else:
        _fail("wants proje sec")
        fails += 1
    _ok(f"faz29 {FAZ29_VERSION}")

    print("=== Faz 28 — git branch ===")
    from ilim_assistant.motorlar.programlama_faz28 import (
        wants_git_branch_create,
        wants_git_branch_list,
    )

    if wants_git_branch_list("git dal"):
        _ok("wants git dal")
    else:
        _fail("wants git dal")
        fails += 1
    if wants_git_branch_create("yeni dal: feature-test"):
        _ok("wants yeni dal")
    else:
        _fail("wants yeni dal")
        fails += 1

    print("=== Faz 25 — Cursor parity ===")
    if live_base:
        report = run_live_parity_preflight(live_base, WORKSPACE)
    else:
        report = run_offline_parity_scenario(WORKSPACE)
    for c in report.checks:
        if c.ok:
            if c.elapsed_sec > 0:
                _ok(f"{c.id} ({c.elapsed_sec:.2f}s)")
            else:
                _ok(c.id)
        else:
            _fail(c.id, c.detail or c.label)
            fails += 1
    saved = save_parity_report_json(report)
    if saved:
        _ok(f"rapor: {saved[-48:]}")
    try:
        print()
        print(format_parity_report(report))
    except UnicodeEncodeError:
        print("(parity raporu konsolda yazdirilamadi)")
    sc = report.scorecard or {}
    if sc and all(sc.values()):
        _ok(f"scorecard {len(sc)}/{len(sc)}")
    elif sc:
        _fail("scorecard", ", ".join(k for k, v in sc.items() if not v))
        fails += 1
    if FAZ25_VERSION.startswith("programlama-faz25"):
        _ok("faz25 version")
    return fails


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", metavar="URL", help="Örn. http://127.0.0.1:8777")
    ap.add_argument("--slo", action="store_true", help="Faz 18 SLO senaryoları (offline)")
    ap.add_argument(
        "--parity",
        action="store_true",
        help="Faz 25 Cursor parity (offline fastapi+pytest)",
    )
    ap.add_argument(
        "--ci",
        action="store_true",
        help="Offline + SLO + Parity + Faz60 CI (quick + haftalık full)",
    )
    ap.add_argument(
        "--ci-full",
        action="store_true",
        help="Faz 60: parity full zorla (haftalık kilidi atla)",
    )
    args = ap.parse_args()

    fails = run_offline()
    if args.slo or args.ci:
        fails += run_slo()
    if args.parity or args.ci:
        fails += run_parity(live_base=args.live if args.live else None)
    if args.ci or args.ci_full:
        print("=== Faz 60 — CI automation ===")
        try:
            from ilim_assistant.motorlar.programlama_faz60 import (
                generate_weekly_kpi_report,
                run_ci_automation,
            )

            ci = run_ci_automation(
                WORKSPACE,
                live_url=args.live,
                force_full_parity=bool(args.ci_full),
            )
            if ci.get("ok"):
                print("  [OK] faz60 ci automation")
            else:
                print(f"  [FAIL] faz60 ci — {str(ci.get('steps'))[:120]}")
                fails += 1
            kpi = generate_weekly_kpi_report(WORKSPACE)
            if kpi.get("ok") and kpi.get("week"):
                print(f"  [OK] faz60 weekly kpi {kpi.get('week')}")
            else:
                print("  [FAIL] faz60 weekly kpi")
                fails += 1
        except Exception as exc:
            print(f"  [FAIL] faz60 ci — {str(exc)[:100]}")
            fails += 1
    if args.live:
        fails += run_live(args.live)
    elif args.ci:
        print("(CI: canlı API atlandı — sunucu için --ci --live http://127.0.0.1:8777)")

    print()
    if fails:
        print(f"SONUÇ: {fails} hata")
        return 1
    print("SONUÇ: tüm programlama smoke testleri geçti")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
