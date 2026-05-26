# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 63: Canlı görev KPI ölçümü.

Offline parity ile canlı görev sonuçlarını ayırır; trend + yeterli örneklem.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

FAZ63_VERSION = "programlama-faz63-v1-2026-05-26"
_LIVE_KPI_FILE = "live_kpi_rollups.json"
_MIN_SAMPLE = 5


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ63", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz63_enabled() -> bool:
    return _enabled()


def min_sample_size() -> int:
    try:
        return max(3, min(30, int(os.environ.get("RUZGAR_LIVE_KPI_MIN_SAMPLE", str(_MIN_SAMPLE)))))
    except ValueError:
        return _MIN_SAMPLE


def _rollup_path(workspace_root: str | Path | None) -> Path | None:
    try:
        from ilim_assistant.motorlar.programlama_faz55 import _outcomes_path

        op = _outcomes_path(workspace_root)
        if op is None:
            return None
        return op.parent / _LIVE_KPI_FILE
    except Exception:
        return None


def _load_outcomes(workspace_root: str | Path | None) -> list[dict[str, Any]]:
    try:
        from ilim_assistant.motorlar.programlama_faz55 import _load_store, _outcomes_path

        path = _outcomes_path(workspace_root)
        if path is None or not path.is_file():
            return []
        store = _load_store(path)
        rows = store.get("outcomes") or []
        return [r for r in rows if isinstance(r, dict)]
    except Exception:
        return []


def _rate_in_window(
    rows: list[dict[str, Any]],
    *,
    start_ts: float,
    end_ts: float,
) -> dict[str, Any]:
    subset = [
        r
        for r in rows
        if start_ts <= float(r.get("ts") or 0) < end_ts
    ]
    if not subset:
        return {"total": 0, "success_count": 0, "success_rate": 0.0}
    ok_n = sum(1 for r in subset if r.get("success"))
    total = len(subset)
    return {
        "total": total,
        "success_count": ok_n,
        "success_rate": round(ok_n / total, 3) if total else 0.0,
    }


def compute_live_kpi(
    workspace_root: str | Path | None,
) -> dict[str, Any]:
    """7/30 gün + önceki hafta trend + hedef karşılaştırma."""
    if not _enabled():
        return {"ok": False, "skipped": True}
    try:
        from ilim_assistant.motorlar.programlama_faz55 import (
            compute_task_stats,
            target_success_rate,
        )

        now = time.time()
        rows = _load_outcomes(workspace_root)
        w7 = _rate_in_window(rows, start_ts=now - 7 * 86400, end_ts=now)
        w_prev = _rate_in_window(
            rows,
            start_ts=now - 14 * 86400,
            end_ts=now - 7 * 86400,
        )
        stats_7 = compute_task_stats(workspace_root, window_days=7)
        stats_30 = compute_task_stats(workspace_root, window_days=30)
        tgt = target_success_rate()
        min_n = min_sample_size()
        sample_ok = int(w7.get("total") or 0) >= min_n
        rate_7 = float(w7.get("success_rate") or 0)
        rate_prev = float(w_prev.get("success_rate") or 0)
        delta = rate_7 - rate_prev if w_prev.get("total") else 0.0
        if w_prev.get("total"):
            if delta > 0.05:
                trend = "up"
            elif delta < -0.05:
                trend = "down"
            else:
                trend = "flat"
        else:
            trend = "unknown"
        meets = rate_7 >= tgt if sample_ok else None
        bonus_retries = sum(1 for r in rows[-30:] if r.get("bonus_retry"))
        return {
            "ok": True,
            "version": FAZ63_VERSION,
            "target_rate": tgt,
            "min_sample": min_n,
            "sample_sufficient": sample_ok,
            "meets_target_live": meets,
            "window_7d": {**stats_7, **w7},
            "window_30d": stats_30,
            "previous_7d": w_prev,
            "trend": trend,
            "trend_delta": round(delta, 3),
            "recent": (stats_7.get("recent") or [])[:8],
            "bonus_retry_count_30": bonus_retries,
            "headline": _headline(sample_ok, rate_7, tgt, trend, int(w7.get("total") or 0)),
            "recorded_at": now,
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:120]}


def _headline(
    sample_ok: bool,
    rate_7: float,
    tgt: float,
    trend: str,
    total_7: int,
) -> str:
    pct = int(rate_7 * 100)
    tg = int(tgt * 100)
    if not sample_ok:
        return f"Canlı KPI: son 7 günde {total_7} görev (≥{min_sample_size()} gerekli)"
    mark = "hedefte" if rate_7 >= tgt else "hedef altı"
    arrow = {"up": "↑", "down": "↓", "flat": "→", "unknown": ""}.get(trend, "")
    return f"Canlı KPI: {pct}% başarı (7 gün, {mark} ≥{tg}%) {arrow}".strip()


def record_live_kpi_rollup(
    workspace_root: str | Path | None,
    *,
    task_entry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Her görev sonunda rollup dosyasına anlık özet yaz."""
    if not _enabled():
        return {"ok": False, "skipped": True}
    path = _rollup_path(workspace_root)
    if path is None:
        return {"ok": False, "error": "path"}
    snap = compute_live_kpi(workspace_root)
    store: dict[str, Any] = {"rollups": [], "version": FAZ63_VERSION}
    if path.is_file():
        try:
            store = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(store, dict):
                store = {"rollups": []}
        except (OSError, json.JSONDecodeError):
            pass
    rollups = list(store.get("rollups") or [])
    rollups.append(
        {
            "ts": time.time(),
            "task": task_entry,
            "snapshot": {
                "rate_7d": (snap.get("window_7d") or {}).get("success_rate"),
                "total_7d": (snap.get("window_7d") or {}).get("total"),
                "meets": snap.get("meets_target_live"),
                "trend": snap.get("trend"),
            },
        }
    )
    store["rollups"] = rollups[-120:]
    store["last"] = snap
    store["saved_at"] = time.time()
    try:
        path.write_text(json.dumps(store, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"ok": True, "live_kpi": snap}
    except OSError as exc:
        return {"ok": False, "error": str(exc)[:80]}


def enrich_kpi_dashboard(
    payload: dict[str, Any],
    workspace_root: str | Path | None,
) -> dict[str, Any]:
    out = dict(payload)
    live = compute_live_kpi(workspace_root)
    out["live_kpi"] = live
    out["faz63"] = _enabled()
    if live.get("ok"):
        out["live_kpi_headline"] = live.get("headline")
        ts = live.get("window_7d") or {}
        out["task_stats_live"] = ts
        out["overall_live_ok"] = bool(
            live.get("sample_sufficient") and live.get("meets_target_live")
        )
    return out


def format_live_kpi_report(live: dict[str, Any]) -> str:
    if not live.get("ok"):
        return "Ümit abi, canlı KPI alınamadı."
    lines = [
        f"Ümit abi, **canlı görev KPI** (Faz 63)",
        "",
        str(live.get("headline") or ""),
        "",
    ]
    w7 = live.get("window_7d") or {}
    w30 = live.get("window_30d") or {}
    if w7.get("total"):
        lines.append(
            f"Son 7 gün: **{int(float(w7.get('success_rate', 0)) * 100)}%** "
            f"({w7.get('success_count')}/{w7.get('total')})"
        )
    if w30.get("total"):
        lines.append(
            f"Son 30 gün: **{int(float(w30.get('success_rate', 0)) * 100)}%** "
            f"({w30.get('success_count')}/{w30.get('total')})"
        )
    prev = live.get("previous_7d") or {}
    if prev.get("total"):
        lines.append(
            f"Önceki 7 gün: {int(float(prev.get('success_rate', 0)) * 100)}% "
            f"({prev.get('success_count')}/{prev.get('total')}) · trend: {live.get('trend')}"
        )
    if not live.get("sample_sufficient"):
        lines.append(
            f"\nNot: güvenilir ölçüm için en az **{live.get('min_sample')}** görev gerekir."
        )
    lines.append("\nSon kayıtlar:")
    for r in live.get("recent") or []:
        ok = "✓" if r.get("success") else "✗"
        br = " [55b]" if r.get("bonus_retry") else ""
        lines.append(
            f"  {ok} `{r.get('scope_rel', '?')}` — {r.get('turns_used')} tur{br}"
        )
    lines.append(f"\n({FAZ63_VERSION})")
    return "\n".join(lines)


def wants_live_kpi(message: str) -> bool:
    low = (message or "").lower()
    return any(
        k in low
        for k in (
            "canli kpi",
            "canlı kpi",
            "gorev kpi",
            "görev kpi",
            "gorev basari",
            "görev başarı",
            "canli gorev",
            "canlı görev",
            "task kpi",
            "gorev istatistik",
            "görev istatistik",
        )
    )


def maybe_instant_faz63(message: str, workspace_root: str | Path | None) -> str | None:
    if not _enabled() or not wants_live_kpi(message):
        return None
    return format_live_kpi_report(compute_live_kpi(workspace_root))


def enrich_health_build(build: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(build or {})
    out["faz63"] = faz63_enabled()
    out["live_kpi_enabled"] = faz63_enabled()
    return out


def faz63_directive() -> str:
    return (
        "[CANLI KPI — Faz 63]\n"
        "Görev sonuçları 7/30 gün trend; atölye kartı + `canlı kpi` komutu.\n"
        "Kapat: RUZGAR_FAZ63=0\n"
    )
