# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 102 / Blok C: Canlı E1 (kök neden, rolling, E1 %90).
"""

from __future__ import annotations

import json
import os
import time
from collections import Counter
from pathlib import Path
from typing import Any

FAZ102_VERSION = "programlama-faz102-v1-2026-05-29"
_RULE_HINTS_FILE = "root_cause_rule_hints.jsonl"
_ROLLING_WINDOW = 20
_REPEAT_THRESHOLD = 2


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ102", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def e1_target_rate() -> float:
    """E1 hedef çizgisi — faz55 ile aynı (varsayılan %70; Blok C için RUZGAR_E1_TARGET_RATE=0.90)."""
    env = os.environ.get("RUZGAR_E1_TARGET_RATE", "").strip()
    if env:
        try:
            return max(0.5, min(0.99, float(env)))
        except ValueError:
            pass
    try:
        from ilim_assistant.motorlar.programlama_faz55 import target_success_rate

        return target_success_rate()
    except Exception:
        return 0.70


def task_duration_warn_sec() -> float:
    try:
        return max(300.0, float(os.environ.get("RUZGAR_TASK_DURATION_WARN_SEC", "1200")))
    except ValueError:
        return 1200.0


def classify_root_cause(
    *,
    success: bool,
    verify_ok: bool = False,
    writes_ok: int = 0,
    detail: str = "",
    bonus_retry: bool = False,
) -> str:
    if success:
        return "ok"
    low = (detail or "").lower()
    if bonus_retry:
        return "bonus_retry_still_fail"
    # pytest_scope doğrulama etiketi — kök neden «scope_rejected» sayılmaz
    low_scope = low.replace("pytest_scope", "")
    if any(x in low_scope for x in ("scope", "kapsam", "çekirdek", "cekirdek", "faz 78")):
        return "scope_rejected"
    if any(x in low for x in ("timeout", "timed out", "süre sınırı", "sure siniri")):
        return "timeout"
    if not verify_ok:
        if any(x in low for x in ("pytest", "test", "verify")):
            return "pytest_failed"
        return "verify_failed"
    if int(writes_ok or 0) <= 0:
        return "no_write"
    return "unknown_fail"


def _hints_path(workspace_root: str | Path | None) -> Path | None:
    try:
        from ilim_assistant.motorlar.programlama_faz55 import _outcomes_path

        op = _outcomes_path(workspace_root)
        if op is None:
            return None
        return op.parent / _RULE_HINTS_FILE
    except Exception:
        return None


def record_root_cause_hint(
    workspace_root: str | Path | None,
    *,
    scope_rel: str,
    root_cause: str,
) -> dict[str, Any]:
    """Tekrarlayan kök neden → kural önerisi (.ruzgar/ jsonl)."""
    if not _enabled() or root_cause in ("ok", ""):
        return {"ok": True, "skipped": True}
    path = _hints_path(workspace_root)
    if path is None:
        return {"ok": False, "error": "path"}
    try:
        from ilim_assistant.motorlar.programlama_faz55 import _load_store, _outcomes_path

        op = _outcomes_path(workspace_root)
        if op is None or not op.is_file():
            return {"ok": True, "repeat_count": 0}
        store = _load_store(op)
        cutoff = time.time() - 7 * 86400
        same = [
            o
            for o in (store.get("outcomes") or [])
            if isinstance(o, dict)
            and float(o.get("ts") or 0) >= cutoff
            and str(o.get("root_cause") or "") == root_cause
        ]
        count = len(same)
        if count < _REPEAT_THRESHOLD:
            return {"ok": True, "repeat_count": count}
        rule = {
            "ts": time.time(),
            "root_cause": root_cause,
            "scope_rel": (scope_rel or "").replace("\\", "/"),
            "repeat_count": count,
            "suggestion": _rule_suggestion_for(root_cause),
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rule, ensure_ascii=False) + "\n")
        return {"ok": True, "repeat_count": count, "rule": rule}
    except OSError as exc:
        return {"ok": False, "error": str(exc)[:120]}


def _rule_suggestion_for(root_cause: str) -> str:
    mapping = {
        "pytest_failed": "Görev öncesi `verify` veya pytest çıktısını oku; bonus turda read→write→verify.",
        "verify_failed": "Tur sonunda mutlaka `verify` çağır; kırmızıysa hatayı düzeltmeden bitirme.",
        "no_write": "En az bir `@@write` veya write aracı kullan; salt okuma ile görev sayılmaz.",
        "scope_rejected": "Çekirdek dosya için «çekirdek:» ekle veya yolu ilim-assistant/ruzgar-desktop ile başlat.",
        "timeout": "Kapsamı küçült; tek dosya/tek test ile ilerle.",
        "bonus_retry_still_fail": "Faz 55b turunda önceki pytest hatasını düzelt; aynı patch tekrar etme.",
    }
    return mapping.get(
        root_cause,
        "Son başarısız görevleri `görev istatistik` ile incele; kök nedeni tekrar etme.",
    )


def compute_rolling_window(
    rows: list[dict[str, Any]],
    *,
    n: int = _ROLLING_WINDOW,
) -> dict[str, Any]:
    tail = [r for r in rows if isinstance(r, dict)][-n:]
    if not tail:
        return {"window": n, "total": 0, "success_rate": 0.0, "success_count": 0}
    ok_n = sum(1 for r in tail if r.get("success"))
    total = len(tail)
    return {
        "window": n,
        "total": total,
        "success_count": ok_n,
        "success_rate": round(ok_n / total, 3) if total else 0.0,
    }


def weekly_outcome_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Son 7 gün günlük özet (basit)."""
    now = time.time()
    days: list[dict[str, Any]] = []
    for i in range(6, -1, -1):
        start = now - (i + 1) * 86400
        end = now - i * 86400
        subset = [r for r in rows if start <= float(r.get("ts") or 0) < end]
        ok_n = sum(1 for r in subset if r.get("success"))
        total = len(subset)
        days.append(
            {
                "day_offset": i,
                "total": total,
                "success_count": ok_n,
                "success_rate": round(ok_n / total, 3) if total else 0.0,
            }
        )
    return {"days": days, "version": FAZ102_VERSION}


def enrich_task_stats(
    stats: dict[str, Any],
    workspace_root: str | Path | None,
    *,
    all_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if not _enabled():
        return stats
    out = dict(stats)
    e1_tgt = e1_target_rate()
    out["e1_target_rate"] = e1_tgt
    try:
        from ilim_assistant.motorlar.programlama_faz91 import compute_e1_stats

        e1 = compute_e1_stats(workspace_root, window_days=7)
        out["e1"] = e1
        out["e1_success_rate"] = e1.get("success_rate")
        out["e1_meets_target"] = float(e1.get("success_rate") or 0) >= e1_tgt
    except Exception:
        out["e1"] = {"ok": False}
    rows = all_rows if all_rows is not None else []
    if not rows:
        try:
            from ilim_assistant.motorlar.programlama_faz55 import _load_store, _outcomes_path

            path = _outcomes_path(workspace_root)
            if path and path.is_file():
                store = _load_store(path)
                wd = int(stats.get("window_days") or 30)
                cutoff = time.time() - wd * 86400
                rows = [
                    o
                    for o in (store.get("outcomes") or [])
                    if isinstance(o, dict) and float(o.get("ts") or 0) >= cutoff
                ]
        except Exception:
            rows = []
    out["rolling_20"] = compute_rolling_window(rows, n=_ROLLING_WINDOW)
    causes = Counter(str(r.get("root_cause") or "unknown") for r in rows if not r.get("success"))
    out["root_cause_top"] = [
        {"cause": k, "count": v} for k, v in causes.most_common(5)
    ]
    out["weekly_summary"] = weekly_outcome_summary(rows)
    return out


def format_retry_footer(
    *,
    used_bonus: bool,
    success: bool,
    root_cause: str = "",
) -> str:
    if not used_bonus:
        return ""
    if success:
        return (
            "\n\n— **Faz 55b:** Otomatik tekrar turu sonrası görev **başarılı**."
        )
    cause = root_cause or "verify_failed"
    return (
        "\n\n— **Faz 55b:** Otomatik tekrar turu bitti — hâlâ kırmızı.\n"
        f"Kök neden: `{cause}`. Sohbette `görev istatistik` ile son kayıtlara bak."
    )


def format_verify_failure_line(
    *,
    verify_ok: bool,
    last_verify_snippet: str = "",
) -> str:
    if verify_ok:
        return ""
    snip = (last_verify_snippet or "pytest/verify kırmızı")[:400]
    return (
        "\n\n**Doğrulama kırmızı (Faz 102)** — görev tam sayılmadı.\n"
        f"Özet: {snip}\n"
        "İpucu: hatayı düzelt → tekrar `verify` veya Faz 55b bonus turunu bekle."
    )


def format_duration_warning(elapsed_sec: float) -> str:
    limit = task_duration_warn_sec()
    if float(elapsed_sec or 0) < limit:
        return ""
    return (
        f"\n\n**Süre uyarısı:** Görev **{elapsed_sec:.0f} sn** sürdü "
        f"(eşik {limit:.0f} sn). Kapsamı küçültmeyi düşün."
    )


def format_scope_early_rejection(reason: str) -> str:
    r = (reason or "").strip()
    return (
        "Ümit abi, bu yol programlama atölyesi kapsamı dışında.\n"
        f"{r}\n"
        "Çözüm: `projects/...` altında çalış veya mesaja **çekirdek:** ekle.\n"
        f"({FAZ102_VERSION})"
    )
