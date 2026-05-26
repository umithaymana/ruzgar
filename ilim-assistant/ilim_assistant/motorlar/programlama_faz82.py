# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 82: Zayıflık raporu + canlı/parity köprüsü (E1, E6).
"""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any

FAZ82_VERSION = "programlama-faz82-v1-2026-05-26"
_REPORT_FILE = "weakness_report.json"

_WEAKNESS_RE = re.compile(
    r"(?:zayiflik\s+rapor|zayıflık\s+rapor|weakness\s+report|motor\s+durum\s+rapor)",
    re.I,
)


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ82", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz82_enabled() -> bool:
    return _enabled()


def _report_path(workspace_root: str | Path | None) -> Path | None:
    try:
        from ilim_assistant.motorlar.programlama_motoru import repo_root

        root = repo_root(workspace_root)
        if root is None:
            return None
        d = root / ".ruzgar"
        d.mkdir(parents=True, exist_ok=True)
        return d / _REPORT_FILE
    except Exception:
        return None


def build_weakness_report(workspace_root: str | Path | None) -> dict[str, Any]:
    """E1–E7 sinyallerini tek raporda topla."""
    report: dict[str, Any] = {
        "ok": True,
        "version": FAZ82_VERSION,
        "generated_at": time.time(),
        "items": [],
        "score": 100,
    }

    try:
        from ilim_assistant.motorlar.programlama_faz55 import compute_task_stats

        stats = compute_task_stats(workspace_root, window_days=30)
        rate = float(stats.get("success_rate") or 0)
        target = float(stats.get("target_rate") or 0.7)
        if stats.get("total", 0) >= 3 and rate < target:
            report["items"].append(
                {
                    "id": "E1",
                    "severity": "high",
                    "msg": f"Canlı görev başarısı %{int(rate*100)} (hedef ≥%{int(target*100)})",
                }
            )
            report["score"] -= 25
    except Exception:
        pass

    try:
        from ilim_assistant.motorlar.programlama_faz57 import compute_text_only_stats

        to = compute_text_only_stats(workspace_root, window_days=7)
        if to.get("total_turns", 0) >= 5 and not to.get("meets_target"):
            report["items"].append(
                {
                    "id": "E3",
                    "severity": "medium",
                    "msg": f"Metin-only oranı %{float(to.get('text_only_rate',0))*100:.1f}",
                }
            )
            report["score"] -= 15
    except Exception:
        pass

    try:
        from ilim_assistant.motorlar.programlama_faz60 import build_mismatch_info

        from ilim_assistant.motorlar.programlama_faz60 import expected_build_rev

        mi = build_mismatch_info(expected_build_rev())
        if mi.get("mismatch"):
            report["items"].append(
                {
                    "id": "E7",
                    "severity": "high",
                    "msg": "Build uyumsuz — API yeniden başlat",
                }
            )
            report["score"] -= 20
    except Exception:
        pass

    try:
        from ilim_assistant.motorlar.programlama_faz60 import should_run_weekly_full_parity

        pr = should_run_weekly_full_parity(workspace_root)
        if pr is True:
            report["items"].append(
                {
                    "id": "E6",
                    "severity": "low",
                    "msg": "Haftalık parity full çalıştırılmalı",
                }
            )
            report["score"] -= 5
    except Exception:
        pass

    report["score"] = max(0, min(100, int(report["score"])))
    report["grade"] = (
        "A" if report["score"] >= 85 else "B" if report["score"] >= 70 else "C" if report["score"] >= 50 else "D"
    )

    path = _report_path(workspace_root)
    if path:
        try:
            path.write_text(
                json.dumps(report, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError:
            pass
    return report


def format_weakness_report(report: dict[str, Any]) -> str:
    score = int(report.get("score") or 0)
    grade = report.get("grade") or "?"
    lines = [
        f"Ümit abi, **programlama zayıflık raporu (Faz 82)** — skor **{score}/100 ({grade})**",
        "",
    ]
    items = report.get("items") or []
    if not items:
        lines.append("Kritik zayıflık sinyali yok — devam.")
    else:
        for it in items:
            lines.append(f"· **{it.get('id')}** [{it.get('severity')}]: {it.get('msg')}")
    lines.append("")
    lines.append("Öneri: `python scripts/programlama_smoke.py --ci` · parity full haftalık.")
    lines.append(f"\n({FAZ82_VERSION})")
    return "\n".join(lines)


def wants_weakness_report(message: str) -> bool:
    return _enabled() and bool(_WEAKNESS_RE.search((message or "").strip()))


def enrich_health_build(build: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(build or {})
    out["programlama_faz82"] = faz82_enabled()
    return out


def maybe_instant_faz82(message: str, workspace_root: str | None = None) -> str | None:
    if not wants_weakness_report(message):
        return None
    return format_weakness_report(build_weakness_report(workspace_root))
