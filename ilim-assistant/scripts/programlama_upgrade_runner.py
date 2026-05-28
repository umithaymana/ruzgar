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


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _prepare_natural_fixtures() -> None:
    try:
        desk = Path.home() / "Desktop"
        docs = Path.home() / "Documents"
        desk.mkdir(parents=True, exist_ok=True)
        docs.mkdir(parents=True, exist_ok=True)
        (desk / "log.txt").write_text("log", encoding="utf-8")
        (docs / "notlar.txt").write_text("not", encoding="utf-8")
    except OSError:
        return


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

    from ilim_assistant.motorlar.programlama_faz98 import evaluate_command_dataset
    from ilim_assistant.motorlar.programlama_faz99 import run_autonomy_benchmark

    dataset = _load_json(dataset_fp)
    ladder = _load_json(ladder_fp)
    _prepare_natural_fixtures()
    c98 = evaluate_command_dataset(dataset, ws)

    b1 = run_autonomy_benchmark(ws)
    b2 = run_autonomy_benchmark(ws)
    consistency_ok = bool(b1.get("ok")) and bool(b2.get("ok")) and abs(int(b1.get("score") or 0) - int(b2.get("score") or 0)) <= 5

    cmd_score = int(c98.get("score") or 0)
    auto_score = min(int(b1.get("score") or 0), int(b2.get("score") or 0))
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

    gate_ok = cmd_score >= 95 and auto_score >= 95 and consistency_ok
    if args.strict:
        gate_ok = gate_ok and elapsed <= 120

    ladder_out: list[dict[str, Any]] = []
    for row in ladder:
        level = str(row.get("level") or "")
        min_score = int(row.get("min_score") or 0)
        require_ok = bool(row.get("require_ok"))
        if level == "small":
            lv_score = cmd_score
            lv_ok = c98.get("ok")
        elif level == "medium":
            lv_score = int(b1.get("score") or 0)
            lv_ok = b1.get("ok")
        else:
            lv_score = auto_score
            lv_ok = consistency_ok and b1.get("ok") and b2.get("ok")
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
        "version": "programlama-upgrade-runner-v1-2026-05-28",
        "elapsed_sec": elapsed,
        "scores": {
            "command_level": cmd_score,
            "autonomy_level": auto_score,
            "approval_safety": approval_score,
            "natural_language": natural_score,
            "reliability": reliability_score,
        },
        "checks": {
            "consistency_two_runs": consistency_ok,
            "faz99_run1_ok": bool(b1.get("ok")),
            "faz99_run2_ok": bool(b2.get("ok")),
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
        },
    }
    out_fp = ws / OUT_REL
    _save_json(out_fp, report)

    print(f"upgrade-gate ok={report['ok']} elapsed={elapsed}s")
    print(
        "scores:",
        f"command={report['scores']['command_level']}",
        f"autonomy={report['scores']['autonomy_level']}",
        f"reliability={report['scores']['reliability']}",
    )
    print(f"saved: {out_fp}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
