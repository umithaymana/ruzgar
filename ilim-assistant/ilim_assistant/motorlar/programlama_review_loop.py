# Created by Ümit & Gökçenur
"""
Programlama motoru — P6 / S9: review loop (diff özeti + geri al UX).

Deterministik kapı:
  1) P5 bench üzerinde patch uygula
  2) Dosya başına diff özeti üret
  3) Checkpoint + rollback planı yaz
  4) Rollback metni formatla
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from ilim_assistant.motorlar.programlama_motoru import repo_root
from ilim_assistant.motorlar.programlama_monorepo_refactor import (
    _BENCH_ROOT,
    _PATCH_BUNDLE,
    _PKG,
    _V1_FILES,
    _write_v1_bench,
)

REVIEW_LOOP_VERSION = "programlama-review-loop-v1-2026-06-15"
_BENCH_FILES = [f"{_PKG}/core.py", f"{_PKG}/service.py", f"{_PKG}/api.py"]


def review_loop_enabled() -> bool:
    return os.environ.get("RUZGAR_PROG_REVIEW_LOOP", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _diff_line_stats(diff: str) -> tuple[int, int]:
    add = rem = 0
    for line in (diff or "").splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            add += 1
        elif line.startswith("-") and not line.startswith("---"):
            rem += 1
    return add, rem


def build_file_diff_summaries(
    workspace_root: str | Path | None,
    rel_paths: list[str],
) -> list[dict[str, Any]]:
    from ilim_assistant.motorlar.programlama_faz10 import unified_diff_text
    from ilim_assistant.motorlar.programlama_faz27 import build_inline_diff_for_path

    root = repo_root(workspace_root)
    if root is None:
        return []
    rows: list[dict[str, Any]] = []
    for rel in rel_paths:
        rel_n = rel.strip().replace("\\", "/").lstrip("/")
        if not rel_n:
            continue
        old = _V1_FILES.get(rel_n, "")
        if not old:
            payload = build_inline_diff_for_path(workspace_root, rel_n)
            if payload.get("ok"):
                old = str(payload.get("old_text") or "")
        try:
            new = (root / rel_n.replace("/", os.sep)).read_text(encoding="utf-8", errors="replace")
        except OSError:
            new = ""
        diff = unified_diff_text(old, new, rel_n)
        add, rem = _diff_line_stats(diff)
        rows.append(
            {
                "path": rel_n,
                "add_lines": add,
                "remove_lines": rem,
                "diff_preview": diff[:600],
            }
        )
    return rows


def format_diff_summary_block(summaries: list[dict[str, Any]]) -> str:
    if not summaries:
        return ""
    lines = ["**Diff özeti (P6):**"]
    for row in summaries:
        path = str(row.get("path") or "?")
        add = int(row.get("add_lines") or 0)
        rem = int(row.get("remove_lines") or 0)
        lines.append(f"- `{path}` · +{add} / −{rem}")
    return "\n".join(lines)


def format_review_loop_instant_report(rep: dict[str, Any]) -> str:
    checks = rep.get("checks") or {}
    lines = [
        "Ümit abi, **P6 review loop gate** (S9):",
        "",
        f"Sonuç: **{'OK' if rep.get('ok') else 'KIRIK'}**",
    ]
    for key, ok in checks.items():
        lines.append(f"- {'✓' if ok else '✗'} {key}")
    diff_block = str(rep.get("diff_summary_text") or "").strip()
    if diff_block:
        lines.extend(["", diff_block])
    rb = str(rep.get("rollback_hint") or "").strip()
    if rb:
        lines.extend(["", rb])
    lines.append(f"\nKapsam: `{rep.get('scope_rel', '?')}` · dosya: {rep.get('files', 3)}")
    lines.append(f"({REVIEW_LOOP_VERSION})")
    return "\n".join(lines)


def wants_review_loop_gate(message: str) -> bool:
    low = (message or "").lower()
    return any(
        k in low
        for k in (
            "p6 review gate",
            "p6 gate",
            "p6 review",
            "review loop gate",
            "s9 gate",
        )
    )


def wants_review_summary(message: str) -> bool:
    low = (message or "").lower()
    if wants_review_loop_gate(message):
        return False
    return any(
        k in low
        for k in (
            "patch özeti",
            "patch ozeti",
            "diff özeti",
            "diff ozeti",
            "son checkpoint",
            "geri dönüş planı",
            "geri donus plani",
        )
    )


def format_last_checkpoint_review(workspace_root: str | Path | None) -> str:
    from ilim_assistant.motorlar.programlama_faz93 import (
        build_rollback_plan,
        render_rollback_directive,
        rollback_status_text,
    )

    try:
        data_path = repo_root(workspace_root)
        if data_path is None:
            return "Ümit abi, workspace kökü bulunamadı."
        cp_file = data_path / ".ruzgar" / "programlama_refactor_checkpoints.json"
        if not cp_file.is_file():
            return "Ümit abi, henüz kayıtlı refactor checkpoint yok — önce `p6 gate` çalıştır."
        import json

        data = json.loads(cp_file.read_text(encoding="utf-8"))
        rows = [r for r in (data.get("checkpoints") or []) if isinstance(r, dict)]
        if not rows:
            return "Ümit abi, checkpoint listesi boş — `p6 gate` ile oluştur."
        last = rows[-1]
        applied = [str(x) for x in (last.get("applied_files") or []) if str(x).strip()]
        summaries = build_file_diff_summaries(workspace_root, applied)
        diff_block = format_diff_summary_block(summaries)
        rb = last.get("rollback") or build_rollback_plan(applied)
        rb_txt = rollback_status_text(rb)
        rb_dir = render_rollback_directive(rb).strip()
        lines = [
            "Ümit abi, **son checkpoint review** (P6):",
            "",
            f"Hedef: {str(last.get('goal') or '')[:180]}",
            f"Dosya: {int(last.get('applied_count') or len(applied))}",
        ]
        if diff_block:
            lines.extend(["", diff_block])
        if rb_txt:
            lines.extend(["", rb_txt])
        if rb_dir:
            lines.extend(["", rb_dir])
        lines.append(f"\n({REVIEW_LOOP_VERSION})")
        return "\n".join(lines)
    except Exception as exc:
        return f"Ümit abi, checkpoint okunamadı: {exc}"


def maybe_instant_review_loop(
    message: str,
    workspace_root: str | Path | None,
) -> str | None:
    if wants_review_loop_gate(message):
        rep = run_review_loop_gate(workspace_root)
        return format_review_loop_instant_report(rep)
    if wants_review_summary(message):
        return format_last_checkpoint_review(workspace_root)
    return None


def run_review_loop_gate(workspace_root: str | Path | None) -> dict[str, Any]:
    checks: dict[str, bool] = {}
    detail_parts: list[str] = []
    if not review_loop_enabled():
        return {
            "ok": False,
            "detail": "RUZGAR_PROG_REVIEW_LOOP=0",
            "checks": checks,
            "version": REVIEW_LOOP_VERSION,
        }

    root = repo_root(workspace_root)
    if root is None:
        return {
            "ok": False,
            "detail": "workspace_root yok",
            "checks": checks,
            "version": REVIEW_LOOP_VERSION,
        }

    checks["bench_reset"] = _write_v1_bench(root)
    if not checks["bench_reset"]:
        return {
            "ok": False,
            "detail": "bench_reset_fail",
            "checks": checks,
            "version": REVIEW_LOOP_VERSION,
        }

    try:
        from ilim_assistant.motorlar.programlama_patch import apply_patch_jobs

        reps = apply_patch_jobs(_PATCH_BUNDLE, root)
        checks["patch_apply"] = len(reps) == 3 and all(r.ok for r in reps)
        if not checks["patch_apply"]:
            detail_parts.append(
                "; ".join(f"{r.path}:{r.detail}" for r in reps if not r.ok)[:160]
            )
    except Exception as exc:
        checks["patch_apply"] = False
        detail_parts.append(f"patch:{exc}")

    summaries = build_file_diff_summaries(root, _BENCH_FILES)
    checks["diff_summary"] = len(summaries) == 3 and all(
        int(s.get("add_lines") or 0) + int(s.get("remove_lines") or 0) > 0
        for s in summaries
    )
    diff_summary_text = format_diff_summary_block(summaries)

    cp: dict[str, Any] = {}
    try:
        from ilim_assistant.motorlar.programlama_faz93 import (
            record_refactor_checkpoint,
            rollback_status_text,
        )

        cp = record_refactor_checkpoint(
            root,
            user_message="P6 review loop gate",
            patch_meta={"applied": _BENCH_FILES, "action": "applied"},
        )
        checks["checkpoint"] = bool(cp.get("recorded"))
        rb = cp.get("rollback") or {}
        checks["rollback_plan"] = bool(rb.get("has_plan"))
        rollback_hint = rollback_status_text(rb)
    except Exception as exc:
        checks["checkpoint"] = False
        checks["rollback_plan"] = False
        rollback_hint = ""
        detail_parts.append(f"checkpoint:{exc}")

    ok = all(checks.values()) if checks else False
    return {
        "ok": ok,
        "detail": "; ".join(detail_parts) if detail_parts else "review loop gate",
        "checks": checks,
        "scope_rel": _BENCH_ROOT,
        "files": len(_BENCH_FILES),
        "diff_summary_text": diff_summary_text,
        "rollback_hint": rollback_hint,
        "checkpoint": cp,
        "version": REVIEW_LOOP_VERSION,
    }
