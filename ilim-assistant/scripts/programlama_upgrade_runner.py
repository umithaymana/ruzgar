#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

WORKSPACE = _ROOT.parent
OUT_REL = "scripts/ruzgar_programlama_upgrade_report.json"
RUNNER_VERSION = "programlama-upgrade-runner-v2-2026-05-29"


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _prepare_natural_fixtures(ws: Path) -> None:
    from ilim_assistant.motorlar.programlama_faz98 import prepare_command_golden_fixtures

    prepare_command_golden_fixtures(ws)


def _pass_ratio(by_tag: dict[str, dict[str, int]], tag: str) -> float:
    row = by_tag.get(tag) or {}
    total = max(1, int(row.get("total") or 0))
    return float((int(row.get("passed") or 0) / total) * 100.0)


def _root_cause_from_check(chk: dict[str, Any]) -> str:
    if not chk.get("gate_ok"):
        return "gate_detection_mismatch"
    if not chk.get("kind_ok"):
        return "kind_parse_mismatch"
    return "unknown"


def main() -> int:
    ap = argparse.ArgumentParser(description="Programlama motoru yükseltme gate runner")
    ap.add_argument("--strict", action="store_true", help="Süre ve tüm kontrol eşiğini sert uygula")
    ap.add_argument("--dataset", default="scripts/programlama_command_goldens.json")
    ap.add_argument("--ladder", default="scripts/programlama_task_ladder.json")
    args = ap.parse_args()

    ws = Path((os.environ.get("RUZGAR_WORKSPACE_ROOT") or "").strip() or str(WORKSPACE))
    dataset_fp = _ROOT / args.dataset
    ladder_fp = _ROOT / args.ladder
    t0 = time.perf_counter()

    from ilim_assistant.motorlar.programlama_faz54 import run_parity_smoke_suite
    from ilim_assistant.motorlar.programlama_faz98 import evaluate_command_dataset
    from ilim_assistant.motorlar.programlama_faz99 import (
        faz99_check_named,
        run_autonomy_benchmark,
    )
    from ilim_assistant.motorlar.programlama_router import run_monorepo_router_smoke
    from ilim_assistant.motorlar.programlama_monorepo_live import run_monorepo_live_gate
    from ilim_assistant.motorlar.programlama_monorepo_refactor import run_monorepo_refactor_gate
    from ilim_assistant.motorlar.programlama_review_loop import run_review_loop_gate

    dataset = _load_json(dataset_fp)
    ladder = _load_json(ladder_fp)
    _prepare_natural_fixtures(ws)
    c98 = evaluate_command_dataset(dataset, ws)

    b1 = run_autonomy_benchmark(ws)
    b2 = run_autonomy_benchmark(ws)
    faz99_dual_ok = bool(b1.get("ok")) and bool(b2.get("ok"))
    consistency_ok = faz99_dual_ok and abs(int(b1.get("score") or 0) - int(b2.get("score") or 0)) <= 5
    git_commit_ok = faz99_check_named(b1.get("checks"), "git_branch_commit") and faz99_check_named(
        b2.get("checks"), "git_branch_commit"
    )

    parity_rep = run_parity_smoke_suite(ws, mode="quick")
    parity_total = max(1, int(getattr(parity_rep, "total", 0) or 8))
    parity_passed = int(getattr(parity_rep, "passed", 0) or 0)
    parity_score = int(round((parity_passed / parity_total) * 100))
    parity_ok = bool(getattr(parity_rep, "ok", False))

    monorepo_smoke = run_monorepo_router_smoke(ws)
    monorepo_score = 100 if bool(monorepo_smoke.get("ok")) else 0
    monorepo_live = run_monorepo_live_gate(ws)
    monorepo_live_score = 100 if bool(monorepo_live.get("ok")) else 0
    monorepo_refactor = run_monorepo_refactor_gate(ws)
    monorepo_refactor_score = 100 if bool(monorepo_refactor.get("ok")) else 0
    review_loop = run_review_loop_gate(ws)
    review_loop_score = 100 if bool(review_loop.get("ok")) else 0

    cmd_score = int(c98.get("score") or 0)
    auto_score = min(int(b1.get("score") or 0), int(b2.get("score") or 0))
    independence_score = min(cmd_score, auto_score, parity_score)
    elapsed = round(time.perf_counter() - t0, 2)

    approval_score = int(round((_pass_ratio(c98.get("by_tag") or {}, "approval") + _pass_ratio(c98.get("by_tag") or {}, "rejection")) / 2.0))
    natural_score = int(round((_pass_ratio(c98.get("by_tag") or {}, "natural") + _pass_ratio(c98.get("by_tag") or {}, "shell")) / 2.0))
    reliability_score = int(
        round(
            (
                (100.0 if consistency_ok else 0.0)
                + (100.0 if b1.get("ok") else 0.0)
                + (100.0 if b2.get("ok") else 0.0)
            )
            / 3.0
        )
    )

    gate_ok = cmd_score >= 95 and auto_score >= 95 and independence_score >= 95 and consistency_ok
    gate_ok = gate_ok and faz99_dual_ok and parity_ok and git_commit_ok
    if args.strict:
        gate_ok = gate_ok and elapsed <= 180

    ladder_out: list[dict[str, Any]] = []
    for row in ladder:
        level = str(row.get("level") or "").lower()
        min_score = int(row.get("min_score") or 0)
        require_ok = bool(row.get("require_ok"))
        if level == "small":
            lv_score = cmd_score
            lv_ok = c98.get("ok")
        elif level == "medium":
            lv_score = int(b1.get("score") or 0)
            lv_ok = b1.get("ok")
        elif level == "large":
            lv_score = parity_score
            lv_ok = parity_ok
        elif level == "full":
            lv_score = independence_score
            lv_ok = (
                bool(c98.get("ok"))
                and faz99_dual_ok
                and parity_ok
                and git_commit_ok
                and consistency_ok
            )
        elif level == "monorepo":
            lv_score = monorepo_score
            lv_ok = bool(monorepo_smoke.get("ok"))
        elif level == "monorepo_live":
            lv_score = monorepo_live_score
            lv_ok = bool(monorepo_live.get("ok"))
        elif level == "monorepo_refactor":
            lv_score = monorepo_refactor_score
            lv_ok = bool(monorepo_refactor.get("ok"))
        elif level == "review_loop":
            lv_score = review_loop_score
            lv_ok = bool(review_loop.get("ok"))
        else:
            lv_score = auto_score
            lv_ok = consistency_ok
        pass_cond = lv_score >= min_score and ((not require_ok) or bool(lv_ok))
        ladder_out.append(
            {
                "id": row.get("id"),
                "level": level,
                "description": row.get("description"),
                "score": lv_score,
                "min_score": min_score,
                "pass": bool(pass_cond),
            }
        )

    failed_examples = [c for c in (c98.get("checks") or []) if not c.get("ok")]
    report: dict[str, Any] = {
        "ok": gate_ok and all(bool(x.get("pass")) for x in ladder_out),
        "version": RUNNER_VERSION,
        "elapsed_sec": elapsed,
        "scores": {
            "command_level": cmd_score,
            "autonomy_level": auto_score,
            "independence_level": independence_score,
            "parity_level": parity_score,
            "approval_safety": approval_score,
            "natural_language": natural_score,
            "reliability": reliability_score,
        },
        "checks": {
            "consistency_two_runs": consistency_ok,
            "faz99_run1_ok": bool(b1.get("ok")),
            "faz99_run2_ok": bool(b2.get("ok")),
            "faz99_dual_run_required": faz99_dual_ok,
            "parity_8_8_ok": parity_ok,
            "git_commit_proof": git_commit_ok,
            "independence_min_95": independence_score >= 95,
        },
        "ladder": ladder_out,
        "command_eval": {
            "passed": c98.get("passed"),
            "total": c98.get("total"),
            "by_tag": c98.get("by_tag"),
            "failed_examples": failed_examples[:10],
            "root_causes": {
                "gate_detection_mismatch": sum(1 for c in failed_examples if _root_cause_from_check(c) == "gate_detection_mismatch"),
                "kind_parse_mismatch": sum(1 for c in failed_examples if _root_cause_from_check(c) == "kind_parse_mismatch"),
            },
        },
        "artifacts": {
            "dataset": str(dataset_fp),
            "ladder": str(ladder_fp),
            "faz99_scope_1": b1.get("scope_rel"),
            "faz99_scope_2": b2.get("scope_rel"),
            "parity_mode": "quick",
            "parity_passed": parity_passed,
            "parity_total": parity_total,
            "monorepo_smoke": monorepo_smoke,
            "monorepo_live": monorepo_live,
            "monorepo_refactor": monorepo_refactor,
            "review_loop": review_loop,
        },
    }
    out_fp = ws / OUT_REL
    _save_json(out_fp, report)

    print(f"upgrade-gate ok={report['ok']} elapsed={elapsed}s")
    print(
        "scores:",
        f"command={report['scores']['command_level']}",
        f"autonomy={report['scores']['autonomy_level']}",
        f"independence={report['scores']['independence_level']}",
        f"parity={report['scores']['parity_level']}",
        f"reliability={report['scores']['reliability']}",
    )
    ladder_pass = sum(1 for x in ladder_out if x.get("pass"))
    print(f"ladder: {ladder_pass}/{len(ladder_out)}")
    print(f"saved: {out_fp}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
