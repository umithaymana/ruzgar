# Created by Ümit & Gökçenur
"""
Programlama motoru — Adım 9: CI/PR döngüsü.

gh pr checks oku -> kırmızı kontrol -> yerel düzeltme önerisi -> tekrar push/PR.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import unicodedata
from pathlib import Path
from typing import Any

CI_PR_LOOP_VERSION = "programlama-ci-pr-loop-v1-2026-06-16"


def ci_pr_loop_enabled() -> bool:
    return os.environ.get("RUZGAR_PROG_CI_PR_LOOP", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _ascii_fold(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def _gh_available() -> bool:
    return shutil.which("gh") is not None


def _run_gh(args: list[str], cwd: Path, *, timeout: int = 90) -> dict[str, Any]:
    if not _gh_available():
        return {"ok": False, "error": "gh CLI yok", "output": ""}
    try:
        from ilim_assistant.motorlar.programlama_faz31 import _run_cmd

        return _run_cmd(["gh"] + args, cwd, timeout=timeout)
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:120], "output": ""}


def suggest_fix_for_check(name: str, *, conclusion: str = "") -> str:
    """CI kontrol adına göre yerel düzeltme önerisi."""
    n = _ascii_fold(name)
    c = _ascii_fold(conclusion)
    if "smoke" in n or "parity" in n or "bench" in n or "upgrade" in n:
        return (
            "Yerelde: `cd ilim-assistant` -> "
            "`python scripts/programlama_upgrade_runner.py`"
        )
    if "pytest" in n or "test" in n or "pytest" in c:
        return "Yerelde: proje dizininde `python -m pytest -q`"
    if "ruff" in n or "lint" in n:
        return "Yerelde: `ruff check` (veya programlama verify üçlüsü)"
    if "mypy" in n or "type" in n:
        return "Yerelde: `mypy` hedef paket"
    if "build" in n or "compile" in n:
        return "Yerelde: derleme komutunu tekrarla; log satırına bak"
    if "security" in n or "bandit" in n:
        return "Güvenlik uyarısını oku; gerekirse kodu daralt"
    return (
        "Kontrol logunu aç (`gh run view` veya GitHub Actions), "
        "hatayı düzelt, commit + push"
    )


def parse_status_checks(raw: Any) -> dict[str, Any]:
    """gh JSON statusCheckRollup veya checks listesini normalize eder."""
    failed: list[dict[str, str]] = []
    passed: list[str] = []
    pending: list[str] = []

    rows: list[Any]
    if isinstance(raw, list):
        rows = raw
    elif isinstance(raw, dict):
        rows = list(raw.get("checks") or raw.get("statusCheckRollup") or [])
    else:
        rows = []

    for row in rows:
        if not isinstance(row, dict):
            continue
        name = str(row.get("name") or row.get("context") or row.get("title") or "?")
        state = str(
            row.get("conclusion")
            or row.get("state")
            or row.get("status")
            or ""
        ).upper()
        if state in ("FAILURE", "FAILED", "ERROR", "CANCELLED", "TIMED_OUT"):
            failed.append(
                {
                    "name": name,
                    "state": state,
                    "fix": suggest_fix_for_check(name, conclusion=state),
                }
            )
        elif state in ("SUCCESS", "COMPLETED", "NEUTRAL", "SKIPPED"):
            if state != "SKIPPED":
                passed.append(name)
        elif state in ("PENDING", "IN_PROGRESS", "QUEUED", "WAITING"):
            pending.append(name)
        else:
            pending.append(name)

    return {
        "failed": failed,
        "passed": passed,
        "pending": pending,
        "total": len(rows),
    }


def _resolve_pr_number(
    workspace_root: str | Path | None,
    *,
    pr_number: int | None = None,
) -> tuple[int | None, Path | None, str]:
    try:
        from ilim_assistant.motorlar.programlama_faz31 import (
            gather_pr_snapshot,
            resolve_git_cwd,
        )
    except Exception:
        return None, None, "faz31 import"

    cwd, _ = resolve_git_cwd(workspace_root)
    if cwd is None:
        return None, None, "git cwd yok"

    if pr_number is not None:
        return int(pr_number), cwd, ""

    snap = gather_pr_snapshot(workspace_root)
    prs = snap.get("open_prs") or []
    if prs:
        num = prs[0].get("number")
        if num is not None:
            return int(num), cwd, ""
    return None, cwd, "no_open_pr"


def fetch_pr_checks(
    workspace_root: str | Path | None,
    *,
    pr_number: int | None = None,
) -> dict[str, Any]:
    """Aktif PR için GitHub kontrollerini çeker."""
    if not ci_pr_loop_enabled():
        return {"ok": False, "error": "RUZGAR_PROG_CI_PR_LOOP=0"}
    if not _gh_available():
        return {"ok": False, "error": "gh CLI kurulu değil"}

    num, cwd, hint = _resolve_pr_number(workspace_root, pr_number=pr_number)
    if cwd is None:
        return {"ok": False, "error": hint or "cwd yok"}
    if num is None:
        return {"ok": False, "error": hint or "açık PR yok", "cwd": str(cwd)}

    view = _run_gh(
        [
            "pr",
            "view",
            str(num),
            "--json",
            "number,title,url,state,statusCheckRollup",
        ],
        cwd,
    )
    if not view.get("ok"):
        checks = _run_gh(["pr", "checks", str(num)], cwd)
        if not checks.get("ok"):
            return {
                "ok": False,
                "error": (checks.get("output") or view.get("output") or "")[:200],
                "pr_number": num,
            }
        text = checks.get("output") or ""
        failed_names = [
            ln.split()[0]
            for ln in text.splitlines()
            if re.search(r"\bfail", ln, re.I)
        ]
        parsed = {
            "failed": [
                {"name": n, "state": "FAILURE", "fix": suggest_fix_for_check(n)}
                for n in failed_names[:12]
            ],
            "passed": [],
            "pending": [],
            "total": len(failed_names),
        }
        pr_title = f"PR #{num}"
        pr_url = ""
    else:
        try:
            data = json.loads(view.get("output") or "{}")
        except json.JSONDecodeError:
            return {"ok": False, "error": "gh JSON parse", "pr_number": num}
        parsed = parse_status_checks(data.get("statusCheckRollup"))
        pr_title = str(data.get("title") or "")
        pr_url = str(data.get("url") or "")

    return {
        "ok": True,
        "pr_number": num,
        "pr_title": pr_title,
        "pr_url": pr_url,
        "checks": parsed,
        "all_green": not parsed.get("failed") and not parsed.get("pending"),
        "version": CI_PR_LOOP_VERSION,
    }


def build_ci_fix_plan(checks: dict[str, Any]) -> list[dict[str, str]]:
    failed = list(checks.get("failed") or [])
    plan: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in failed:
        name = str(row.get("name") or "")
        fix = str(row.get("fix") or suggest_fix_for_check(name))
        if fix in seen:
            continue
        seen.add(fix)
        plan.append({"check": name, "action": fix})
    if not plan and checks.get("pending"):
        plan.append(
            {
                "check": "bekleyen",
                "action": "Birkaç dakika sonra `ci durum` ile tekrar kontrol et",
            }
        )
    return plan[:8]


def run_ci_pr_loop(
    workspace_root: str | Path | None,
    *,
    pr_number: int | None = None,
) -> dict[str, Any]:
    """Tam döngü: PR checks + düzeltme planı + sonraki adımlar."""
    rep = fetch_pr_checks(workspace_root, pr_number=pr_number)
    if not rep.get("ok"):
        return rep
    checks = rep.get("checks") or {}
    plan = build_ci_fix_plan(checks)
    next_steps = [
        "1) Önerilen yerel komutu çalıştır",
        "2) Yeşil olunca commit + push",
        "3) `ci durum` ile GitHub kontrollerini tekrar oku",
    ]
    if rep.get("all_green"):
        next_steps = ["Tüm kontroller yeşil — merge veya review bekleyebilirsin."]
    return {
        **rep,
        "fix_plan": plan,
        "next_steps": next_steps,
        "version": CI_PR_LOOP_VERSION,
    }


def format_ci_pr_report(rep: dict[str, Any]) -> str:
    if not rep.get("ok"):
        err = rep.get("error") or "bilinmeyen hata"
        extra = ""
        if err == "no_open_pr":
            extra = "\nÖnce feature dalında push yapıp `pr oluştur:` ile PR aç."
        return f"Ümit abi, CI/PR okunamadı: {err}{extra}\n({CI_PR_LOOP_VERSION})"

    checks = rep.get("checks") or {}
    failed = checks.get("failed") or []
    pending = checks.get("pending") or []
    passed_n = len(checks.get("passed") or [])

    lines = [
        f"Ümit abi, **CI/PR döngüsü** — PR #{rep.get('pr_number')}",
        f"Başlık: {rep.get('pr_title') or '—'}",
    ]
    if rep.get("pr_url"):
        lines.append(f"URL: {rep.get('pr_url')}")
    lines.append("")

    if rep.get("all_green"):
        lines.append("Durum: **tüm kontroller yeşil**")
    else:
        lines.append(
            f"Durum: **{len(failed)} kırmızı** · {len(pending)} bekliyor · {passed_n} yeşil"
        )

    if failed:
        lines.append("")
        lines.append("**Kırmızı kontroller:**")
        for row in failed[:8]:
            lines.append(f"- `{row.get('name')}` ({row.get('state')})")
            lines.append(f"  -> {row.get('fix')}")

    plan = rep.get("fix_plan") or []
    if plan and not rep.get("all_green"):
        lines.append("")
        lines.append("**Önerilen aksiyonlar:**")
        for i, step in enumerate(plan, 1):
            lines.append(f"{i}. {step.get('action')}")

    lines.append("")
    lines.append(f"({CI_PR_LOOP_VERSION})")
    return "\n".join(lines)


def wants_ci_checks(message: str) -> bool:
    low = _ascii_fold(message)
    return any(
        k in low
        for k in (
            "ci durum",
            "ci kontrol",
            "pr checks",
            "pr check",
            "github actions",
            "ci kirmizi",
            "ci kırmızı",
            "ci loop",
            "ci dongusu",
            "ci döngüsü",
        )
    )


def maybe_instant_ci_pr_loop(
    message: str,
    workspace_root: str | Path | None,
) -> str | None:
    if not ci_pr_loop_enabled() or not wants_ci_checks(message):
        return None
    rep = run_ci_pr_loop(workspace_root)
    return format_ci_pr_report(rep)


def run_ci_pr_loop_smoke(workspace_root: str | Path | None) -> dict[str, Any]:
    """Bench: parse + fix önerisi; gh varsa canlı okuma dener."""
    sample = [
        {"name": "smoke-offline-slo", "conclusion": "FAILURE"},
        {"name": "pytest", "conclusion": "SUCCESS"},
    ]
    parsed = parse_status_checks(sample)
    fix_ok = (
        len(parsed.get("failed") or []) == 1
        and "upgrade_runner" in (parsed["failed"][0].get("fix") or "")
    )

    live: dict[str, Any] = {"skipped": True, "ok": True, "reason": "gh_yok"}
    if _gh_available():
        rep = run_ci_pr_loop(workspace_root)
        live = {
            "ok": bool(rep.get("ok")) or rep.get("error") == "no_open_pr",
            "error": rep.get("error"),
            "all_green": rep.get("all_green"),
        }

    ok = bool(fix_ok) and bool(live.get("ok"))
    return {
        "ok": ok,
        "parse_fix": fix_ok,
        "live": live,
        "version": CI_PR_LOOP_VERSION,
    }


def ci_pr_directive() -> str:
    return (
        "[CI/PR DÖNGÜSÜ — Adım 9]\n"
        "Komutlar: `ci durum` · `pr checks` — kırmızı kontrol -> yerel düzeltme önerisi.\n"
        "Kapat: RUZGAR_PROG_CI_PR_LOOP=0\n"
    )
