# Created by Ümit & Gökçenur
"""
Programlama motoru — P9 / S11: delivery gate (zayıflık raporu + PR hazırlık).

Faz 82 + Faz 83 entegrasyon doğrulaması:
  - weakness report üretimi
  - PR planı (branch, commit, gh komutu)
  - Anında komutlar
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from ilim_assistant.motorlar.programlama_motoru import repo_root

DELIVERY_GATE_VERSION = "programlama-delivery-gate-v1-2026-06-15"


def delivery_gate_enabled() -> bool:
    return os.environ.get("RUZGAR_PROG_DELIVERY_GATE", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def format_delivery_instant_report(rep: dict[str, Any]) -> str:
    checks = rep.get("checks") or {}
    lines = [
        "Ümit abi, **P9 delivery gate** (S11):",
        "",
        f"Sonuç: **{'OK' if rep.get('ok') else 'KIRIK'}**",
        "**Sonraki komutlar:** `zayıflık raporu` · `pr hazırla: başlık`",
        "",
    ]
    for key, ok in checks.items():
        lines.append(f"- {'✓' if ok else '✗'} {key}")
    wr_score = rep.get("weakness_score")
    if wr_score is not None:
        lines.append(f"\nZayıflık skoru: **{wr_score}/100** · madde: {rep.get('weakness_items', 0)}")
    branch = str(rep.get("pr_branch") or "").strip()
    if branch:
        lines.append(f"PR dalı: `{branch}` · gh: {'✓' if rep.get('gh_available') else '—'}")
    lines.append(f"({DELIVERY_GATE_VERSION})")
    return "\n".join(lines)


def wants_delivery_gate(message: str) -> bool:
    low = (message or "").lower()
    return any(
        k in low
        for k in (
            "p9 gate",
            "p9 delivery",
            "delivery gate",
            "s11 gate",
        )
    )


def wants_delivery_summary(message: str) -> bool:
    low = (message or "").lower()
    if wants_delivery_gate(message):
        return False
    return any(
        k in low
        for k in (
            "teslimat özeti",
            "teslimat ozeti",
            "delivery özeti",
            "delivery ozeti",
        )
    )


def format_delivery_summary(workspace_root: str | Path | None) -> str:
    from ilim_assistant.motorlar.programlama_faz82 import (
        build_weakness_report,
        format_weakness_report,
    )
    from ilim_assistant.motorlar.programlama_faz83 import build_pr_plan, format_pr_plan

    wr = build_weakness_report(workspace_root)
    pr = build_pr_plan(workspace_root, title_hint="programlama delivery")
    lines = [
        "Ümit abi, **teslimat özeti (P9):**",
        "",
        format_weakness_report(wr).split("\n")[0],
        f"Skor: {wr.get('score', '?')}/100 · {len(wr.get('items') or [])} madde",
        "",
        "---",
        "",
    ]
    pr_lines = format_pr_plan(pr).splitlines()[:12]
    lines.extend(pr_lines)
    lines.append(f"\n({DELIVERY_GATE_VERSION})")
    return "\n".join(lines)


def maybe_instant_delivery(
    message: str,
    workspace_root: str | Path | None,
) -> str | None:
    if wants_delivery_gate(message):
        rep = run_delivery_gate(workspace_root)
        return format_delivery_instant_report(rep)
    if wants_delivery_summary(message):
        return format_delivery_summary(workspace_root)
    return None


def run_delivery_gate(workspace_root: str | Path | None) -> dict[str, Any]:
    checks: dict[str, bool] = {}
    detail_parts: list[str] = []
    if not delivery_gate_enabled():
        return {
            "ok": False,
            "detail": "RUZGAR_PROG_DELIVERY_GATE=0",
            "checks": checks,
            "version": DELIVERY_GATE_VERSION,
        }

    root = repo_root(workspace_root)
    if root is None:
        return {
            "ok": False,
            "detail": "workspace_root yok",
            "checks": checks,
            "version": DELIVERY_GATE_VERSION,
        }

    wr: dict[str, Any] = {}
    try:
        from ilim_assistant.motorlar.programlama_faz82 import (
            build_weakness_report,
            faz82_enabled,
            format_weakness_report,
        )

        checks["faz82_enabled"] = faz82_enabled()
        wr = build_weakness_report(root)
        checks["weakness_report"] = bool(wr.get("ok")) and "score" in wr
        txt = format_weakness_report(wr)
        checks["weakness_format"] = bool(txt.strip()) and "zayıflık" in txt.lower()
    except Exception as exc:
        checks["weakness_report"] = False
        checks["weakness_format"] = False
        detail_parts.append(f"weakness:{exc}")

    pr: dict[str, Any] = {}
    try:
        from ilim_assistant.motorlar.programlama_faz83 import (
            build_pr_plan,
            faz83_enabled,
            wants_pr_prepare,
        )

        checks["faz83_enabled"] = faz83_enabled()
        pr = build_pr_plan(root, title_hint="P9 delivery gate smoke")
        checks["pr_plan"] = bool(pr.get("ok"))
        steps = list(pr.get("steps") or [])
        checks["pr_steps"] = len(steps) >= 4
        checks["pr_parse"] = wants_pr_prepare("pr hazırla: test başlık")
    except Exception as exc:
        checks["pr_plan"] = False
        checks["pr_steps"] = False
        checks["pr_parse"] = False
        detail_parts.append(f"pr:{exc}")

    try:
        from ilim_assistant.motorlar.programlama_agent_nonblock import (
            agent_nonblock_enabled,
        )

        checks["p8_module"] = agent_nonblock_enabled()
    except Exception:
        checks["p8_module"] = False

    try:
        from ilim_assistant.motorlar.programlama_ci_pr_loop import (
            ci_pr_loop_enabled,
            run_ci_pr_loop_smoke,
        )

        checks["ci_pr_loop_enabled"] = ci_pr_loop_enabled()
        smoke = run_ci_pr_loop_smoke(root)
        checks["ci_pr_loop_smoke"] = bool(smoke.get("ok"))
    except Exception as exc:
        checks["ci_pr_loop_enabled"] = False
        checks["ci_pr_loop_smoke"] = False
        detail_parts.append(f"ci_pr:{exc}")

    ok = all(checks.values()) if checks else False
    return {
        "ok": ok,
        "detail": "; ".join(detail_parts) if detail_parts else "delivery gate",
        "checks": checks,
        "weakness_score": wr.get("score"),
        "weakness_items": len(wr.get("items") or []),
        "pr_branch": pr.get("branch"),
        "gh_available": pr.get("gh_available"),
        "version": DELIVERY_GATE_VERSION,
    }
