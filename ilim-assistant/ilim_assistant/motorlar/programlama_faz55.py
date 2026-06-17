# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 55: Canlı görev başarı KPI + Ana Motor handoff paketi.

Offline parity 8/8 ile canlı görev sonucu arasındaki boşluğu ölçer ve kapatmaya yardım eder.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

FAZ55_VERSION = "programlama-faz55-v2-2026-05-26-55b"
_OUTCOMES_FILE = "task_outcomes.json"
_TARGET_SUCCESS_RATE = 0.70
_MAX_HISTORY = 200


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ55", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz55_enabled() -> bool:
    return _enabled()


def faz55b_enabled() -> bool:
    """Başarısız görev sonrası +1 otomatik bonus tur (Faz 55b / Faz 61)."""
    if not _enabled():
        return False
    return os.environ.get("RUZGAR_FAZ55B", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz55b_bonus_turn_count() -> int:
    return 1 if faz55b_enabled() else 0


def is_faz55b_bonus_turn(turn: int, base_max_turns: int) -> bool:
    return faz55b_enabled() and int(turn) > int(base_max_turns)


def target_success_rate() -> float:
    try:
        return max(0.4, min(0.95, float(os.environ.get("RUZGAR_TASK_SUCCESS_TARGET", "0.70"))))
    except ValueError:
        return _TARGET_SUCCESS_RATE


def _outcomes_path(workspace_root: str | Path | None) -> Path | None:
    try:
        from ilim_assistant.motorlar.programlama_motoru import repo_root

        root = repo_root(workspace_root)
        if root is None:
            return None
        cache = root / ".ruzgar"
        cache.mkdir(parents=True, exist_ok=True)
        return cache / _OUTCOMES_FILE
    except Exception:
        return None


def _load_store(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {"outcomes": [], "version": FAZ55_VERSION}


def _save_store(path: Path, store: dict[str, Any]) -> None:
    store["version"] = FAZ55_VERSION
    store["saved_at"] = time.time()
    path.write_text(json.dumps(store, ensure_ascii=False, indent=2), encoding="utf-8")


def record_task_outcome(
    workspace_root: str | Path | None,
    *,
    scope_rel: str,
    goal: str = "",
    success: bool,
    turns_used: int = 0,
    verify_ok: bool = False,
    writes_ok: int = 0,
    elapsed_sec: float = 0.0,
    source: str = "code_agent",
    detail: str = "",
    bonus_retry: bool = False,
) -> dict[str, Any]:
    """Görev sonunu kaydet."""
    if not _enabled():
        return {"ok": False, "skipped": True}
    path = _outcomes_path(workspace_root)
    if path is None:
        return {"ok": False, "error": "path"}
    store = _load_store(path) if path.is_file() else {"outcomes": []}
    outcomes = list(store.get("outcomes") or [])
    root_cause = ""
    try:
        from ilim_assistant.motorlar.programlama_faz102_e1_live import (
            classify_root_cause,
            record_root_cause_hint,
        )

        root_cause = classify_root_cause(
            success=bool(success),
            verify_ok=bool(verify_ok),
            writes_ok=int(writes_ok),
            detail=detail or "",
            bonus_retry=bool(bonus_retry),
        )
    except Exception:
        root_cause = "unknown_fail" if not success else "ok"
    entry = {
        "ts": time.time(),
        "scope_rel": (scope_rel or "").replace("\\", "/"),
        "goal": (goal or "")[:500],
        "success": bool(success),
        "turns_used": int(turns_used),
        "verify_ok": bool(verify_ok),
        "writes_ok": int(writes_ok),
        "elapsed_sec": round(float(elapsed_sec), 2),
        "source": source,
        "detail": (detail or "")[:300],
        "bonus_retry": bool(bonus_retry),
        "root_cause": root_cause,
    }
    outcomes.append(entry)
    store["outcomes"] = outcomes[-_MAX_HISTORY:]
    try:
        _save_store(path, store)
        try:
            from ilim_assistant.motorlar.programlama_faz63 import record_live_kpi_rollup

            record_live_kpi_rollup(workspace_root, task_entry=entry)
        except Exception:
            pass
        try:
            from ilim_assistant.motorlar.programlama_faz102_e1_live import record_root_cause_hint

            record_root_cause_hint(
                workspace_root,
                scope_rel=scope_rel,
                root_cause=root_cause,
            )
        except Exception:
            pass
        return {"ok": True, "entry": entry, "root_cause": root_cause}
    except OSError as exc:
        return {"ok": False, "error": str(exc)[:120]}


def compute_task_stats(
    workspace_root: str | Path | None,
    *,
    window_days: int = 30,
) -> dict[str, Any]:
    path = _outcomes_path(workspace_root)
    if path is None or not path.is_file():
        return {
            "ok": True,
            "total": 0,
            "success_count": 0,
            "success_rate": 0.0,
            "target_rate": target_success_rate(),
            "meets_target": False,
            "avg_turns": 0.0,
            "avg_elapsed_sec": 0.0,
            "recent": [],
        }
    store = _load_store(path)
    cutoff = time.time() - window_days * 86400
    rows = [
        o
        for o in (store.get("outcomes") or [])
        if isinstance(o, dict) and float(o.get("ts") or 0) >= cutoff
    ]
    filtered_out = 0
    try:
        from ilim_assistant.motorlar.programlama_faz91 import (
            faz91_enabled,
            is_kpi_eligible_outcome,
        )

        if faz91_enabled():
            eligible = [o for o in rows if is_kpi_eligible_outcome(o)]
            filtered_out = len(rows) - len(eligible)
            rows = eligible
    except Exception:
        pass
    if not rows:
        return {
            "ok": True,
            "total": 0,
            "success_count": 0,
            "success_rate": 0.0,
            "target_rate": target_success_rate(),
            "meets_target": False,
            "avg_turns": 0.0,
            "avg_elapsed_sec": 0.0,
            "recent": [],
            "filtered_out": filtered_out,
        }
    ok_n = sum(1 for r in rows if r.get("success"))
    total = len(rows)
    rate = ok_n / total if total else 0.0
    target = target_success_rate()
    base = {
        "ok": True,
        "total": total,
        "success_count": ok_n,
        "success_rate": round(rate, 3),
        "target_rate": target,
        "meets_target": rate >= target,
        "avg_turns": round(
            sum(int(r.get("turns_used") or 0) for r in rows) / total, 1
        ),
        "avg_elapsed_sec": round(
            sum(float(r.get("elapsed_sec") or 0) for r in rows) / total, 1
        ),
        "recent": rows[-8:],
        "window_days": window_days,
        "filtered_out": filtered_out,
    }
    try:
        from ilim_assistant.motorlar.programlama_faz102_e1_live import enrich_task_stats

        return enrich_task_stats(base, workspace_root, all_rows=rows)
    except Exception:
        return base


def build_retry_nudge(
    workspace_root: str | Path | None,
    *,
    scope_rel: str,
    goal: str,
    last_detail: str = "",
    for_bonus_turn: bool = False,
) -> str | None:
    """Başarısız görev sonrası bir tur daha deneme mesajı."""
    if not _enabled():
        return None
    if not for_bonus_turn:
        stats = compute_task_stats(workspace_root, window_days=7)
        recent_fail = [
            r
            for r in (stats.get("recent") or [])
            if not r.get("success") and r.get("scope_rel") == scope_rel
        ]
        if len(recent_fail) > 2:
            return None
    label = "FAZ 55b — OTOMATİK TEKRAR" if for_bonus_turn else "FAZ 55 — TEKRAR DENE"
    return (
        f"[{label}]\n"
        f"Proje: `{scope_rel}`\n"
        f"Önceki tur başarısız: {(last_detail or 'verify/yazım eksik')[:200]}\n"
        "Bu turda mutlaka: read → write (en az 1 dosya) → verify (pytest).\n"
        f"Hedef: {(goal or '').strip()}\n"
    )


def inject_faz55b_turn_prefix(
    workspace_root: str | Path | None,
    *,
    scope_rel: str,
    goal: str,
    turn_user: str,
    last_fail_snippet: str = "",
) -> str:
    """Bonus tur kullanıcı mesajına Faz 55b nudge ekler."""
    if not is_faz55b_bonus_turn_enabled():
        return turn_user
    nudge = build_retry_nudge(
        workspace_root,
        scope_rel=scope_rel,
        goal=goal,
        last_detail=last_fail_snippet,
        for_bonus_turn=True,
    )
    if not nudge:
        nudge = ""
    try:
        from ilim_assistant.motorlar.programlama_root_cause_learn import (
            augment_turn_with_root_cause_learn,
        )

        turn_user = augment_turn_with_root_cause_learn(
            turn_user,
            workspace_root,
            scope_rel=scope_rel,
            failure_snippet=last_fail_snippet,
        )
    except Exception:
        pass
    if not nudge:
        return turn_user
    return nudge.rstrip() + "\n\n" + (turn_user or "").lstrip()


def is_faz55b_bonus_turn_enabled() -> bool:
    return faz55b_enabled()


def faz55b_directive() -> str:
    return (
        "[FAZ 55b — Otomatik retry]\n"
        "Normal turlar bittikten sonra verify/yazım başarısızsa +1 bonus tur (read→write→verify).\n"
        "Kapat: RUZGAR_FAZ55B=0\n"
    )


def build_handoff_packet(
    message: str,
    workspace_root: str | Path | None,
    *,
    active_file: str | None = None,
) -> dict[str, Any]:
    """
    Ana Motor → Programlama delege bağlamı.
    desktop_server / faz10 delege öncesi zenginleştirme.
    """
    if not _enabled():
        return {"ok": False}
    scope = None
    goal = (message or "").strip()[:2000]
    try:
        from ilim_assistant.motorlar.programlama_faz13 import resolve_scope_rel

        scope = resolve_scope_rel(
            workspace_root, active_file=active_file, message=message
        )
    except Exception:
        pass

    parts: list[str] = ["[HANDOFF — Faz 55 — Ana Motor → Programlama]"]
    if scope:
        parts.append(f"Kapsam: `{scope}`")
    stats = compute_task_stats(workspace_root, window_days=30)
    if stats.get("total", 0) > 0:
        pct = int(float(stats.get("success_rate", 0)) * 100)
        parts.append(
            f"Son {stats.get('window_days', 30)} gün görev başarısı: "
            f"**{pct}%** ({stats.get('success_count')}/{stats.get('total')})"
        )

    spec = None
    try:
        from ilim_assistant.motorlar.programlama_faz50 import parse_faz50_proje_uret

        spec = parse_faz50_proje_uret(message)
    except Exception:
        pass
    if spec is None:
        try:
            from ilim_assistant.motorlar.programlama_faz47 import parse_proje_uret_command

            spec = parse_proje_uret_command(message)
        except Exception:
            pass
    if spec is not None:
        parts.append(
            f"Önerilen şablon: **{spec.template_id}** · proje: `{spec.project_name}`"
        )
        if spec.features:
            parts.append(f"Özellikler: {', '.join(spec.features[:8])}")

    if scope:
        try:
            from ilim_assistant.motorlar.programlama_faz53 import build_symbol_lite_block

            sym = build_symbol_lite_block(workspace_root, scope, message)
            if sym:
                parts.append(sym[:2500])
        except Exception:
            pass

    packet_text = "\n\n".join(parts)
    try:
        from ilim_assistant.ana_motor_faz59 import enrich_handoff_with_intent

        packet_text = enrich_handoff_with_intent(packet_text, message)
    except Exception:
        pass
    return {
        "ok": True,
        "scope_rel": scope,
        "goal": goal,
        "packet_text": packet_text,
        "parsed_template": getattr(spec, "template_id", None) if spec else None,
        "stats": stats,
        "version": FAZ55_VERSION,
    }


def format_task_stats_report(stats: dict[str, Any]) -> str:
    if not stats.get("ok"):
        return "Görev istatistiği alınamadı."
    total = int(stats.get("total") or 0)
    if total == 0:
        return "Ümit abi, henüz kayıtlı görev sonucu yok — bir görev çalıştırınca burada görünür."
    pct = int(float(stats.get("success_rate", 0)) * 100)
    tgt = int(float(stats.get("target_rate", 0.7)) * 100)
    mark = "✓" if stats.get("meets_target") else "↓"
    lines = [
        f"Ümit abi, **görev başarı KPI** (Faz 55) {mark}",
        "",
        f"Son {stats.get('window_days', 30)} gün: **{pct}%** başarı "
        f"({stats.get('success_count')}/{total}) · hedef ≥{tgt}%",
        f"Ortalama: {stats.get('avg_turns')} tur · {stats.get('avg_elapsed_sec')} sn",
        "",
        "Son kayıtlar:",
    ]
    for r in stats.get("recent") or []:
        ok = "✓" if r.get("success") else "✗"
        rc = r.get("root_cause")
        rc_bit = f", {rc}" if rc and not r.get("success") else ""
        lines.append(
            f"  {ok} `{r.get('scope_rel', '?')}` — "
            f"{r.get('turns_used')} tur, verify={r.get('verify_ok')}{rc_bit}"
        )
    e1 = stats.get("e1") if isinstance(stats.get("e1"), dict) else {}
    if e1.get("total"):
        ep = int(float(e1.get("success_rate", 0)) * 100)
        et = int(float(stats.get("e1_target_rate", 0.9)) * 100)
        lines.append(f"\nE1 (7g, filtreli): **{ep}%** ({e1.get('success_count')}/{e1.get('total')}) · hedef ≥{et}%")
    roll = stats.get("rolling_20") if isinstance(stats.get("rolling_20"), dict) else {}
    if roll.get("total"):
        rp = int(float(roll.get("success_rate", 0)) * 100)
        lines.append(
            f"Son {roll.get('window', 20)} görev: **{rp}%** ({roll.get('success_count')}/{roll.get('total')})"
        )
    lines.append(f"\n({FAZ55_VERSION})")
    return "\n".join(lines)


def faz55_directive() -> str:
    parts = [
        "[GÖREV KPI — Faz 55]\n"
        f"Canlı görev sonuçları kaydedilir; hedef başarı ≥{int(target_success_rate()*100)}%.\n"
        "Ana Motor delege: handoff paketi (şablon + sembol özeti).\n"
        "Kapat: RUZGAR_FAZ55=0\n",
    ]
    if faz55b_enabled():
        parts.append(faz55b_directive())
    return "\n".join(parts)
