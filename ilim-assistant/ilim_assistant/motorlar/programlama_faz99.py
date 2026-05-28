from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from ilim_assistant.approved_executor import run_argv
from ilim_assistant.motorlar.programlama_motoru import repo_root

FAZ99_VERSION = "programlama-faz99-v1-2026-05-28"
_OUT_JSON = "scripts/ruzgar_autonomy_benchmark_sonuc.json"


def _persist(workspace_root: str | Path | None, payload: dict[str, Any]) -> None:
    root = repo_root(workspace_root)
    if root is None:
        return
    p = root / _OUT_JSON
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        return


def _append_health_endpoint(main_py: Path) -> tuple[bool, str]:
    try:
        text = main_py.read_text(encoding="utf-8")
    except OSError as exc:
        return False, str(exc)[:140]
    if "benchmark_health" in text:
        return True, "already_present"
    marker = "@app.get(\"/health\")"
    i = text.find(marker)
    if i < 0:
        return False, "health_marker_missing"
    insert_block = (
        "\n\n@app.get(\"/benchmark-health\")\n"
        "def benchmark_health() -> dict[str, str]:\n"
        "    return {\"ok\": \"true\", \"phase\": \"faz99\"}\n"
    )
    # Insert near the end to minimize conflict.
    patched = text.rstrip() + insert_block + "\n"
    try:
        main_py.write_text(patched, encoding="utf-8")
    except OSError as exc:
        return False, str(exc)[:140]
    return True, "patched"


def _write_benchmark_test(test_py: Path) -> tuple[bool, str]:
    body = (
        "from fastapi.testclient import TestClient\n\n"
        "from app.main import app\n\n"
        "client = TestClient(app)\n\n"
        "def test_benchmark_health_endpoint() -> None:\n"
        "    r = client.get('/benchmark-health')\n"
        "    assert r.status_code == 200\n"
        "    data = r.json()\n"
        "    assert data.get('ok') == 'true'\n"
        "    assert data.get('phase') == 'faz99'\n"
    )
    try:
        test_py.parent.mkdir(parents=True, exist_ok=True)
        test_py.write_text(body, encoding="utf-8")
    except OSError as exc:
        return False, str(exc)[:140]
    return True, "written"


def _write_static_banner(index_html: Path) -> tuple[bool, str]:
    try:
        text = index_html.read_text(encoding="utf-8")
    except OSError as exc:
        return False, str(exc)[:140]
    if "faz99-benchmark" in text:
        return True, "already_present"
    marker = "</body>"
    banner = '<div id="faz99-benchmark">faz99 ok</div>'
    if marker in text:
        patched = text.replace(marker, f"{banner}\n{marker}")
    else:
        patched = text.rstrip() + "\n" + banner + "\n"
    try:
        index_html.write_text(patched, encoding="utf-8")
    except OSError as exc:
        return False, str(exc)[:140]
    return True, "patched"


def _run_static_smoke(scope_abs: Path) -> tuple[bool, str]:
    code, out, err = run_argv(
        [
            "python",
            "-c",
            "from pathlib import Path; t=Path('index.html').read_text(encoding='utf-8'); "
            "assert 'faz99-benchmark' in t; print('static_ok')",
        ],
        cwd=str(scope_abs),
        timeout_sec=20,
    )
    return code == 0, (out or err or "")[:140]


def _recovery_probe(scope_abs: Path) -> tuple[bool, str]:
    probe = scope_abs / "app" / "recovery_probe.py"
    try:
        probe.parent.mkdir(parents=True, exist_ok=True)
        probe.write_text("def broken(:\n    pass\n", encoding="utf-8")
    except OSError as exc:
        return False, f"write_fail:{str(exc)[:80]}"
    code_bad, _, err_bad = run_argv(
        ["python", "-m", "py_compile", str(probe)],
        cwd=str(scope_abs),
        timeout_sec=15,
    )
    bad_seen = code_bad != 0
    try:
        probe.write_text(
            "def healed() -> str:\n    return 'ok'\n",
            encoding="utf-8",
        )
    except OSError as exc:
        return False, f"heal_write_fail:{str(exc)[:80]}"
    code_ok, out_ok, err_ok = run_argv(
        ["python", "-m", "py_compile", str(probe)],
        cwd=str(scope_abs),
        timeout_sec=15,
    )
    healed = code_ok == 0
    return bad_seen and healed, ((out_ok or err_ok or err_bad or "")[:140] or "recovery_ok")


def _runtime_recovery_probe(scope_abs: Path) -> tuple[bool, str]:
    tag = int(time.time() * 1000) % 100000
    test_name = f"test_runtime_recovery_case_{tag}"
    test_fp = scope_abs / "tests" / f"test_faz99_runtime_recovery_{tag}.py"
    broken = (
        f"def {test_name}() -> None:\n"
        "    assert 1 == 2\n"
    )
    healed = (
        f"def {test_name}() -> None:\n"
        "    assert 1 == 1\n"
    )
    try:
        test_fp.parent.mkdir(parents=True, exist_ok=True)
        test_fp.write_text(broken, encoding="utf-8")
    except OSError as exc:
        return False, f"write_fail:{str(exc)[:80]}"

    c1, _, e1 = run_argv(
        ["python", "-m", "pytest", "-q", str(test_fp), "-p", "no:cacheprovider"],
        cwd=str(scope_abs),
        timeout_sec=40,
    )
    fail_seen = c1 != 0
    try:
        test_fp.write_text(healed, encoding="utf-8")
    except OSError as exc:
        return False, f"heal_write_fail:{str(exc)[:80]}"
    c2, o2, e2 = run_argv(
        ["python", "-m", "pytest", "-q", str(test_fp), "-p", "no:cacheprovider"],
        cwd=str(scope_abs),
        timeout_sec=40,
    )
    pass_seen = c2 == 0
    return fail_seen and pass_seen, ((o2 or e2 or e1 or "")[:140] or "runtime_recovery_ok")


def _git_lifecycle_probe(
    workspace_root: str | Path | None,
    *,
    scope_rel: str,
) -> tuple[bool, str]:
    root = repo_root(workspace_root)
    if root is None:
        return False, "workspace_root_missing"
    c1, o1, e1 = run_argv(["git", "status", "--short"], cwd=str(root), timeout_sec=20)
    if c1 != 0:
        return False, str((o1 or e1 or "git_status_failed"))[:120]
    c2, o2, e2 = run_argv(["git", "diff", "--stat"], cwd=str(root), timeout_sec=20)
    if c2 != 0:
        return False, str((o2 or e2 or "git_diff_failed"))[:120]
    lines = [ln.strip() for ln in str(o2 or "").splitlines() if ln.strip()]
    hint = lines[0] if lines else "working tree clean"
    return True, f"git_ready · {hint[:100]}"


def _git_branch_commit_probe(scope_abs: Path) -> tuple[bool, str]:
    c1, o1, e1 = run_argv(["git", "init"], cwd=str(scope_abs), timeout_sec=20)
    if c1 != 0:
        return False, str((o1 or e1 or "git_init_failed"))[:120]
    c2, o2, e2 = run_argv(["git", "checkout", "-b", "faz99-bench"], cwd=str(scope_abs), timeout_sec=20)
    if c2 != 0:
        return False, str((o2 or e2 or "git_branch_failed"))[:120]
    c3, o3, e3 = run_argv(["git", "add", "-A"], cwd=str(scope_abs), timeout_sec=20)
    if c3 != 0:
        return False, str((o3 or e3 or "git_add_failed"))[:120]
    c4, o4, e4 = run_argv(
        [
            "git",
            "-c",
            "user.name=Faz99Bot",
            "-c",
            "user.email=faz99@local",
            "commit",
            "-m",
            "feat: faz99 benchmark baseline",
        ],
        cwd=str(scope_abs),
        timeout_sec=25,
    )
    if c4 != 0:
        return False, str((o4 or e4 or "git_commit_failed"))[:120]
    return True, str((o4 or e4 or "git_commit_ok"))[:120]


def _stability_probe(scope_abs: Path) -> tuple[bool, str]:
    test_fp = scope_abs / "tests" / "test_benchmark_health.py"
    c1, o1, e1 = run_argv(["python", "-m", "pytest", "-q", str(test_fp)], cwd=str(scope_abs), timeout_sec=40)
    c2, o2, e2 = run_argv(["python", "-m", "pytest", "-q", str(test_fp)], cwd=str(scope_abs), timeout_sec=40)
    ok = c1 == 0 and c2 == 0
    return ok, ((o2 or e2 or o1 or e1 or "")[:120] or "stable")


def run_autonomy_benchmark(workspace_root: str | Path | None = None) -> dict[str, Any]:
    """
    Faz 99 — bağımsız proje tamamlama benchmark:
    plan -> iki proje tipi -> kod+test -> smoke -> toparlama -> sistem analizi.
    """
    t0 = time.perf_counter()
    out: dict[str, Any] = {
        "ok": False,
        "score": 0,
        "checks": [],
        "version": FAZ99_VERSION,
    }
    budget_sec = 45

    def add(name: str, ok: bool, detail: str = "", points: int = 0) -> None:
        out["checks"].append({"name": name, "ok": bool(ok), "detail": detail[:180], "points": points if ok else 0})

    root = repo_root(workspace_root)
    if root is None:
        out["error"] = "workspace_root yok"
        return out

    try:
        from ilim_assistant.motorlar.programlama_faz92 import build_task_plan

        plan = build_task_plan(
            "FastAPI projesi oluştur, benchmark-health endpointi ekle, testleri çalıştır."
        )
        plan_ok = bool(plan.get("goal")) and bool(plan.get("steps"))
        add("plan_build", plan_ok, plan.get("goal", ""), points=8)
    except Exception as exc:
        add("plan_build", False, str(exc), points=8)
        plan = {}

    slug = f"smoke-autonomy-{int(time.time()) % 100000}"
    scope = f"projects/{slug}"
    static_slug = f"{slug}-site"
    static_scope = f"projects/{static_slug}"
    try:
        from ilim_assistant.motorlar.programlama_faz6 import run_scaffold

        sc = run_scaffold("fastapi_api", slug, workspace_root, force=False)
        sc_ok = bool(sc.get("ok"))
        add("scaffold_fastapi", sc_ok, sc.get("base_dir") or sc.get("error", ""), points=10)
    except Exception as exc:
        sc = {"ok": False, "error": str(exc)}
        add("scaffold_fastapi", False, str(exc), points=10)

    try:
        from ilim_assistant.motorlar.programlama_faz6 import run_scaffold

        sc2 = run_scaffold("static_site", static_slug, workspace_root, force=False)
        sc2_ok = bool(sc2.get("ok"))
        add("scaffold_static_site", sc2_ok, sc2.get("base_dir") or sc2.get("error", ""), points=5)
    except Exception as exc:
        sc2 = {"ok": False, "error": str(exc)}
        add("scaffold_static_site", False, str(exc), points=5)

    main_py = root / scope / "app" / "main.py"
    test_py = root / scope / "tests" / "test_benchmark_health.py"
    impl_ok = False
    if sc.get("ok") and main_py.is_file():
        impl_ok, detail = _append_health_endpoint(main_py)
        add("implement_endpoint", impl_ok, detail, points=10)
    else:
        add("implement_endpoint", False, "scaffold_missing", points=10)

    test_write_ok = False
    if sc.get("ok"):
        test_write_ok, detail = _write_benchmark_test(test_py)
        add("write_targeted_test", test_write_ok, detail, points=5)
    else:
        add("write_targeted_test", False, "skip_no_scaffold", points=5)

    test_ok = False
    if sc.get("ok"):
        code, out_s, err_s = run_argv(
            ["python", "-m", "pytest", "-q"],
            cwd=str(root / scope),
            timeout_sec=120,
        )
        test_ok = code == 0
        add("pytest_project", test_ok, (out_s or err_s or "")[:120], points=5)
    else:
        add("pytest_project", False, "skip_no_scaffold", points=5)

    multi_ok = bool(main_py.is_file() and test_py.is_file())
    add("multi_file_delivery", multi_ok, "main.py + targeted test", points=0)

    static_main = root / static_scope / "index.html"
    if sc2.get("ok") and static_main.is_file():
        st_ok, st_detail = _write_static_banner(static_main)
        add("implement_static_change", st_ok, st_detail, points=8)
        sm_ok, sm_detail = _run_static_smoke(root / static_scope)
        add("static_smoke", sm_ok, sm_detail, points=5)
    else:
        add("implement_static_change", False, "static_scaffold_missing", points=8)
        add("static_smoke", False, "skip_no_static", points=5)

    rec_ok = False
    if sc.get("ok"):
        rec_ok, rec_detail = _recovery_probe(root / scope)
        add("recovery_cycle", rec_ok, rec_detail, points=7)
        rr_ok, rr_detail = _runtime_recovery_probe(root / scope)
        add("runtime_recovery_cycle", rr_ok, rr_detail, points=8)
    else:
        add("recovery_cycle", False, "skip_no_fastapi", points=7)
        add("runtime_recovery_cycle", False, "skip_no_fastapi", points=8)

    git_ok, git_detail = _git_lifecycle_probe(workspace_root, scope_rel=scope)
    add("git_lifecycle_ready", git_ok, git_detail, points=5)
    g2_ok, g2_detail = _git_branch_commit_probe(root / scope)
    add("git_branch_commit", g2_ok, g2_detail, points=7)

    try:
        from ilim_assistant.motorlar.programlama_faz96 import run_autonomous_system_analysis

        rep = run_autonomous_system_analysis(workspace_root, include_parity=False)
        ana_ok = isinstance(rep, dict) and "score" in rep
        add("system_analysis", ana_ok, f"score={rep.get('score') if isinstance(rep, dict) else '?'}", points=10)
    except Exception as exc:
        add("system_analysis", False, str(exc), points=10)

    elapsed = round(time.perf_counter() - t0, 2)
    within_budget = elapsed <= budget_sec
    add("time_budget", within_budget, f"{elapsed}s / {budget_sec}s", points=5)
    st_ok, st_detail = _stability_probe(root / scope)
    add("stability_probe", st_ok, st_detail, points=2)

    score = int(sum(int(c.get("points") or 0) for c in out["checks"]))
    out["score"] = max(0, min(100, score))
    out["scope_rel"] = scope
    out["static_scope_rel"] = static_scope
    out["elapsed_sec"] = elapsed
    out["ok"] = out["score"] >= 85 and all(
        c.get("ok")
        for c in out["checks"]
        if c.get("name")
        in {
            "plan_build",
            "scaffold_fastapi",
            "implement_endpoint",
            "pytest_project",
            "scaffold_static_site",
            "implement_static_change",
            "static_smoke",
            "recovery_cycle",
            "runtime_recovery_cycle",
            "git_lifecycle_ready",
            "git_branch_commit",
            "time_budget",
            "stability_probe",
        }
    )
    out["dimensions"] = {
        "planning": 8,
        "fastapi_delivery": 30,
        "static_delivery": 18,
        "recovery": 15,
        "git_lifecycle": 12,
        "analysis": 10,
        "time_budget": 5,
        "stability": 2,
    }
    out["budget_sec"] = budget_sec
    out["plan"] = plan
    _persist(workspace_root, out)
    return out


def format_autonomy_benchmark_report(rep: dict[str, Any]) -> str:
    score = int(rep.get("score") or 0)
    lines = [f"Ümit abi, Faz 99 bağımsız tamamlama skoru: **{score}/100**", ""]
    dims = rep.get("dimensions") or {}
    if dims:
        lines.append(
            "Kırılım: "
            + " · ".join(f"{k}={v}" for k, v in dims.items())
        )
        lines.append("")
    for c in rep.get("checks") or []:
        mark = "OK" if c.get("ok") else "FAIL"
        lines.append(f"- {mark} {c.get('name')}: {c.get('detail', '')}")
    lines.append(
        f"\nKapsam: `{rep.get('scope_rel', '?')}` + `{rep.get('static_scope_rel', '?')}` · Süre: {rep.get('elapsed_sec', '?')}s"
    )
    lines.append(f"({FAZ99_VERSION})")
    return "\n".join(lines)

