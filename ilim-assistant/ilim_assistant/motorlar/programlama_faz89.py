# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 89: Haftalık parity full (E6).

Faz 60 kilidini kullanır: haftada bir 8/8 parity full + KPI güncelleme.
Komut: «parity full» · «haftalık parity»
"""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any

FAZ89_VERSION = "programlama-faz89-v1-2026-05-27"
_BATTERY_RE = re.compile(
    r"(?:parity\s+full|haftalik\s+parity|haftalık\s+parity|"
    r"weekly\s+parity|e6\s+parity)",
    re.I,
)


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ89", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz89_enabled() -> bool:
    return _enabled()


def wants_weekly_parity_full(message: str) -> bool:
    return _enabled() and bool(_BATTERY_RE.search((message or "").strip()))


def load_last_full_parity_run(
    workspace_root: str | Path | None,
) -> dict[str, Any]:
    try:
        from ilim_assistant.motorlar.programlama_faz60 import _ruzgar_cache

        cache = _ruzgar_cache(workspace_root)
        if cache is None:
            return {}
        path = cache / "last_parity_full_run.json"
        if not path.is_file():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def parity_full_due(workspace_root: str | Path | None) -> bool:
    try:
        from ilim_assistant.motorlar.programlama_faz60 import (
            should_run_weekly_full_parity,
        )

        return bool(should_run_weekly_full_parity(workspace_root))
    except Exception:
        return True


def run_weekly_parity_battery(
    workspace_root: str | Path | None,
    *,
    force: bool = False,
) -> dict[str, Any]:
    """Haftalık parity full — due değilse atlar (force ile zorla)."""
    if not _enabled():
        return {"ok": False, "error": "faz89 kapalı"}
    due = parity_full_due(workspace_root)
    if not due and not force:
        last = load_last_full_parity_run(workspace_root)
        weakness: dict[str, Any] = {}
        try:
            from ilim_assistant.motorlar.programlama_faz82 import build_weakness_report

            weakness = build_weakness_report(workspace_root)
        except Exception:
            pass
        return {
            "ok": True,
            "skipped": True,
            "reason": "already_ran_this_week",
            "version": FAZ89_VERSION,
            "last_run": last,
            "due": False,
            "weakness": weakness,
        }
    t0 = time.perf_counter()
    try:
        from ilim_assistant.motorlar.programlama_faz60 import (
            generate_weekly_kpi_report,
            run_parity_full_if_due,
        )

        step = run_parity_full_if_due(workspace_root, force=force or not due)
    except Exception as exc:
        return {
            "ok": False,
            "error": str(exc)[:200],
            "version": FAZ89_VERSION,
            "due": due,
        }
    elapsed = time.perf_counter() - t0
    kpi: dict[str, Any] = {}
    weakness: dict[str, Any] = {}
    try:
        kpi = generate_weekly_kpi_report(workspace_root)
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz82 import build_weakness_report

        weakness = build_weakness_report(workspace_root)
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz54 import load_parity_smoke_json

        parity_json = load_parity_smoke_json()
    except Exception:
        parity_json = {}
    ok = bool(step.get("ok"))
    if step.get("skipped"):
        return {
            "ok": True,
            "skipped": True,
            "reason": step.get("reason", "already_ran_this_week"),
            "version": FAZ89_VERSION,
            "last_run": load_last_full_parity_run(workspace_root),
            "due": False,
            "weakness": weakness,
        }
    passed = int(step.get("passed") or parity_json.get("passed") or 0)
    total = int(step.get("total") or parity_json.get("total") or 8)
    parity_ok = ok and passed >= total
    return {
        "ok": ok,
        "skipped": False,
        "due": due,
        "force": force,
        "passed": passed,
        "total": total,
        "parity_ok": parity_ok,
        "meets_target_8_8": parity_ok,
        "elapsed_sec": round(elapsed, 2),
        "step": step,
        "parity_last": parity_json,
        "weekly_kpi": kpi,
        "weakness": weakness,
        "last_run": load_last_full_parity_run(workspace_root),
        "version": FAZ89_VERSION,
        "generated_at": time.time(),
    }


def _ascii_report(text: str) -> str:
    return (
        (text or "")
        .replace("\u2192", "->")
        .replace("\u2265", ">=")
        .replace("\u2713", "OK")
    )


def format_weekly_parity_report(report: dict[str, Any]) -> str:
    if report.get("error"):
        return f"Parity full çalışmadı: {report.get('error')}"
    if report.get("skipped"):
        last = report.get("last_run") or {}
        wk = last.get("week") or "?"
        pct = last.get("passed")
        tot = last.get("total") or 8
        lines = [
            "**Haftalık parity full (Faz 89)** — bu hafta zaten çalıştı",
            "",
            f"Son koşu: `{wk}` · **{pct}/{tot}**",
            "Zorla: `parity full zorla` veya `RUZGAR_FAZ60_FORCE_FULL_PARITY=1`",
        ]
        e6 = [
            it
            for it in (report.get("weakness") or {}).get("items") or []
            if it.get("id") == "E6"
        ]
        if not e6:
            lines.append("E6: **temiz** (haftalık parity kayıtlı)")
        lines.append(f"\n({FAZ89_VERSION})")
        return _ascii_report("\n".join(lines))

    passed = report.get("passed", 0)
    total = report.get("total", 8)
    lines = [
        "**Haftalık parity full (Faz 89)** — Cursor 8/8",
        "",
        f"Sonuç: **{passed}/{total}** "
        f"({'OK' if report.get('parity_ok') else 'KIRMIZI'})",
        f"Süre: {report.get('elapsed_sec', '?')}s",
    ]
    parity = report.get("parity_last") or {}
    for chk in parity.get("checks") or []:
        mark = "OK" if chk.get("ok") else "FAIL"
        det = _ascii_report(str(chk.get("detail") or "")[:60].replace("\n", " "))
        lines.append(f"- [{mark}] {chk.get('label', chk.get('id'))} — {det}")
    wr = report.get("weakness") or {}
    e6 = [it for it in wr.get("items") or [] if it.get("id") == "E6"]
    if not e6:
        lines.append("")
        lines.append("E6: **temiz** — haftalık parity kaydedildi.")
    else:
        lines.append("")
        lines.append("E6: hâlâ uyarı (kayıt kontrol edin)")
    score = wr.get("score")
    grade = wr.get("grade")
    if score is not None:
        lines.append(f"Zayıflık skoru: **{score}/100 ({grade})**")
    lines.append(f"\n({FAZ89_VERSION})")
    return _ascii_report("\n".join(lines))


def maybe_instant_faz89(
    message: str,
    workspace_root: str | Path | None = None,
) -> str | None:
    if not wants_weekly_parity_full(message):
        return None
    low = (message or "").lower()
    force = any(k in low for k in ("zorla", "force", "yeniden"))
    report = run_weekly_parity_battery(workspace_root, force=force)
    return format_weekly_parity_report(report)


def enrich_health_build(build: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(build or {})
    out["programlama_faz89"] = faz89_enabled()
    return out


def faz89_directive() -> str:
    return (
        "[Faz 89 — haftalık parity full E6]\n"
        "Komut: `parity full` · zorla: `parity full zorla`\n"
        f"Kapat: RUZGAR_FAZ89=0 · {FAZ89_VERSION}\n"
    )
