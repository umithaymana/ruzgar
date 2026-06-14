# Created by Ümit & Gökçenur
"""Ana Motor — Faz AH2: SLO aksiyon planından kopyalanabilir .env rehberi."""

from __future__ import annotations

import os
import re
from typing import Any

FAZ_AH_SLO_ENV_REHBER_VERSION = "slo-env-rehber-faz-ah-v1-2026-06-13"

_ENV_TOKEN = re.compile(r"(RUZGAR_[A-Z0-9_]+(?:=[^\s—,;]+)?|ENABLE_[A-Z0-9_]+(?:=[^\s—,;]+)?)")


def slo_env_rehber_enabled() -> bool:
    return os.environ.get("RUZGAR_SLO_ENV_REHBER", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _extract_env_lines(text: str, seen: set[str], out: list[str]) -> None:
    for match in _ENV_TOKEN.findall(text or ""):
        key = match.split("=", 1)[0].strip()
        if key in seen:
            continue
        seen.add(key)
        if "=" in match:
            out.append(match.strip())
        else:
            out.append(f"{key}=1")


def build_slo_env_rehber(*, limit: int = 8) -> dict[str, Any]:
    """AF aksiyon planından güvenli (salt okunur) .env öneri listesi."""
    if not slo_env_rehber_enabled():
        return {
            "ok": False,
            "enabled": False,
            "version": FAZ_AH_SLO_ENV_REHBER_VERSION,
            "summary_tr": "SLO env rehberi kapalı",
            "env_lines": [],
            "checklist_tr": "",
        }

    try:
        from ilim_assistant.ana_motor_faz_af_slo_aksiyon import build_slo_action_plan
    except Exception as exc:
        return {
            "ok": False,
            "enabled": True,
            "error": str(exc)[:160],
            "version": FAZ_AH_SLO_ENV_REHBER_VERSION,
            "env_lines": [],
        }

    plan = build_slo_action_plan(limit=limit)
    env_lines: list[str] = []
    seen: set[str] = set()
    notes: list[str] = []

    for action in plan.get("actions") or []:
        label = str(action.get("label") or action.get("id") or "")
        pri = str(action.get("priority") or "normal")
        for item in action.get("items") or []:
            text = str(item or "")
            before = len(env_lines)
            _extract_env_lines(text, seen, env_lines)
            if len(env_lines) == before and text.strip():
                prefix = "!" if pri == "high" else "·"
                notes.append(f"{prefix} [{label}] {text.strip()[:120]}")

    header = "# Rüzgar SLO önerileri — elle .env veya RUZGAR_BRAIN.env dosyasına ekleyin\n"
    body = "\n".join(env_lines) if env_lines else "# Henüz env satırı çıkarılamadı — SLO koşusu sonrası tekrar deneyin"
    checklist = header + body
    if notes:
        checklist += "\n\n# Notlar\n" + "\n".join(notes[:12])

    summary = f"{len(env_lines)} env satırı"
    if plan.get("summary_tr"):
        summary += f" · {plan.get('summary_tr')}"

    return {
        "ok": True,
        "enabled": True,
        "version": FAZ_AH_SLO_ENV_REHBER_VERSION,
        "summary_tr": summary[:240],
        "env_lines": env_lines,
        "checklist_tr": checklist[:4000],
        "action_count": len(plan.get("actions") or []),
        "weak_count": plan.get("weak_count"),
    }


def slo_env_rehber_status() -> dict[str, Any]:
    panel = build_slo_env_rehber(limit=6)
    return {
        "enabled": slo_env_rehber_enabled(),
        "version": FAZ_AH_SLO_ENV_REHBER_VERSION,
        "summary_tr": panel.get("summary_tr"),
        "env_line_count": len(panel.get("env_lines") or []),
    }
