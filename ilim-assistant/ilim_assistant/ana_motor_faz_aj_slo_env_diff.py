# Created by Ümit & Gökçenur
"""Ana Motor — Faz AJ2: SLO env rehberi ile canlı ortam karşılaştırması."""

from __future__ import annotations

import os
from typing import Any

FAZ_AJ_SLO_ENV_DIFF_VERSION = "slo-env-diff-faz-aj-v1-2026-06-13"


def slo_env_diff_enabled() -> bool:
    return os.environ.get("RUZGAR_SLO_ENV_DIFF", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _parse_env_pair(line: str) -> tuple[str, str | None]:
    raw = (line or "").strip()
    if not raw or raw.startswith("#"):
        return "", None
    if "=" in raw:
        key, val = raw.split("=", 1)
        return key.strip(), val.strip()
    return raw, None


def _norm_val(val: str | None) -> str:
    return str(val or "").strip().lower()


def build_slo_env_diff(*, limit: int = 8) -> dict[str, Any]:
    """Önerilen env satırları vs os.environ — eksik / farklı / uyumlu."""
    if not slo_env_diff_enabled():
        return {
            "ok": False,
            "enabled": False,
            "version": FAZ_AJ_SLO_ENV_DIFF_VERSION,
            "summary_tr": "SLO env diff kapalı",
        }
    try:
        from ilim_assistant.ana_motor_faz_ah_slo_env_rehber import build_slo_env_rehber
    except Exception as exc:
        return {
            "ok": False,
            "enabled": True,
            "error": str(exc)[:160],
            "version": FAZ_AJ_SLO_ENV_DIFF_VERSION,
        }

    rehber = build_slo_env_rehber(limit=limit)
    env_lines = list(rehber.get("env_lines") or [])
    missing: list[dict[str, str]] = []
    different: list[dict[str, str]] = []
    matched: list[str] = []

    for line in env_lines:
        key, want = _parse_env_pair(line)
        if not key:
            continue
        cur = os.environ.get(key)
        if cur is None or str(cur).strip() == "":
            missing.append({"key": key, "suggested": want or "1", "line": line})
            continue
        if want is not None and _norm_val(cur) != _norm_val(want):
            different.append(
                {
                    "key": key,
                    "current": str(cur).strip()[:80],
                    "suggested": want,
                    "line": line,
                }
            )
        else:
            matched.append(key)

    parts: list[str] = []
    if missing:
        parts.append(f"{len(missing)} eksik")
    if different:
        parts.append(f"{len(different)} farklı")
    if matched:
        parts.append(f"{len(matched)} uyumlu")
    if not env_lines:
        summary = "Karşılaştırılacak env satırı yok — SLO aksiyon planını bekleyin"
    else:
        summary = " · ".join(parts) if parts else "Tüm öneriler uyumlu"

    diff_lines: list[str] = []
    for row in missing[:8]:
        diff_lines.append(f"- Eksik: {row['key']}={row['suggested']}")
    for row in different[:8]:
        diff_lines.append(
            f"- Farklı: {row['key']} şimdi={row['current']} öneri={row['suggested']}"
        )
    for key in matched[:6]:
        diff_lines.append(f"✓ {key}")

    return {
        "ok": True,
        "enabled": True,
        "version": FAZ_AJ_SLO_ENV_DIFF_VERSION,
        "summary_tr": summary[:280],
        "missing": missing,
        "different": different,
        "matched": matched,
        "diff_tr": "\n".join(diff_lines)[:2000],
        "env_line_count": len(env_lines),
    }


def slo_env_diff_status() -> dict[str, Any]:
    panel = build_slo_env_diff(limit=6)
    return {
        "enabled": slo_env_diff_enabled(),
        "version": FAZ_AJ_SLO_ENV_DIFF_VERSION,
        "summary_tr": panel.get("summary_tr"),
    }
