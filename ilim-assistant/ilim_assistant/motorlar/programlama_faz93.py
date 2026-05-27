from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from ilim_assistant.motorlar.programlama_motoru import repo_root

FAZ93_VERSION = "programlama-faz93-v2-2026-05-27"
_REL_PATH = ".ruzgar/programlama_karar_defteri.json"
_CHECKPOINT_PATH = ".ruzgar/programlama_refactor_checkpoints.json"


def _file(workspace_root: str | Path | None) -> Path | None:
    root = repo_root(workspace_root)
    if root is None:
        return None
    return root / _REL_PATH


def _load(workspace_root: str | Path | None) -> dict[str, Any]:
    p = _file(workspace_root)
    if p is None or not p.is_file():
        return {"version": FAZ93_VERSION, "updated_at": time.time(), "decisions": []}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {"version": FAZ93_VERSION, "updated_at": time.time(), "decisions": []}
        if not isinstance(data.get("decisions"), list):
            data["decisions"] = []
        return data
    except Exception:
        return {"version": FAZ93_VERSION, "updated_at": time.time(), "decisions": []}


def _save(workspace_root: str | Path | None, data: dict[str, Any]) -> None:
    p = _file(workspace_root)
    if p is None:
        return
    out = dict(data)
    out["version"] = FAZ93_VERSION
    out["updated_at"] = time.time()
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        return


def recent_decisions(workspace_root: str | Path | None, limit: int = 5) -> list[dict[str, Any]]:
    data = _load(workspace_root)
    rows = [r for r in (data.get("decisions") or []) if isinstance(r, dict)]
    lim = max(1, min(int(limit), 12))
    return rows[-lim:]


def record_decision(
    workspace_root: str | Path | None,
    *,
    user_message: str,
    assistant_reply: str,
    patch_meta: dict[str, Any] | None = None,
) -> None:
    msg = " ".join((user_message or "").split()).strip()
    rep = " ".join((assistant_reply or "").split()).strip()
    if not msg:
        return
    data = _load(workspace_root)
    rows = [r for r in (data.get("decisions") or []) if isinstance(r, dict)]
    item = {
        "ts": time.time(),
        "goal": msg[:220],
        "decision": rep[:260],
        "applied_files": list((patch_meta or {}).get("applied") or [])[:8],
        "patch_action": str((patch_meta or {}).get("action") or ""),
    }
    rows.append(item)
    if len(rows) > 60:
        rows = rows[-60:]
    data["decisions"] = rows
    _save(workspace_root, data)


def build_decision_context(workspace_root: str | Path | None) -> str:
    rows = recent_decisions(workspace_root, limit=4)
    if not rows:
        return ""
    lines = ["[PROGRAMLAMA KARAR DEFTERI]"]
    for r in rows:
        g = str(r.get("goal") or "").strip()
        d = str(r.get("decision") or "").strip()
        f = list(r.get("applied_files") or [])
        if g:
            lines.append(f"- Hedef: {g}")
        if d:
            lines.append(f"  Karar: {d}")
        if f:
            lines.append(f"  Dosyalar: {', '.join(f[:4])}")
    lines.append(
        "Talimat: Benzer bir istek varsa bu kararları tutarlılık için kullan; kör tekrar yapma."
    )
    lines.append("[/PROGRAMLAMA KARAR DEFTERI]")
    return "\n".join(lines)


def summarize_large_change(patch_meta: dict[str, Any] | None) -> dict[str, Any]:
    pm = patch_meta or {}
    applied = list(pm.get("applied") or [])
    count = len(applied)
    large = count >= 10
    return {
        "version": FAZ93_VERSION,
        "is_large": large,
        "applied_count": count,
        "sample_files": applied[:8],
    }


def large_change_status_text(summary: dict[str, Any]) -> str:
    cnt = int(summary.get("applied_count") or 0)
    return (
        f"Çok dosyalı değişiklik tespit edildi ({cnt} dosya). "
        "Sonraki adımda küçük bir doğrulama/checkpoint yapman iyi olur."
    )


def _checkpoint_file(workspace_root: str | Path | None) -> Path | None:
    root = repo_root(workspace_root)
    if root is None:
        return None
    return root / _CHECKPOINT_PATH


def _load_checkpoints(workspace_root: str | Path | None) -> dict[str, Any]:
    p = _checkpoint_file(workspace_root)
    if p is None or not p.is_file():
        return {"version": FAZ93_VERSION, "updated_at": time.time(), "checkpoints": []}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {"version": FAZ93_VERSION, "updated_at": time.time(), "checkpoints": []}
        if not isinstance(data.get("checkpoints"), list):
            data["checkpoints"] = []
        return data
    except Exception:
        return {"version": FAZ93_VERSION, "updated_at": time.time(), "checkpoints": []}


def _save_checkpoints(workspace_root: str | Path | None, data: dict[str, Any]) -> None:
    p = _checkpoint_file(workspace_root)
    if p is None:
        return
    out = dict(data)
    out["version"] = FAZ93_VERSION
    out["updated_at"] = time.time()
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        return


def looks_like_refactor_pilot(message: str, *, goal: str = "") -> bool:
    raw = f"{message or ''} {goal or ''}".strip().lower()
    if not raw:
        return False
    cues = (
        "refactor",
        "refaktör",
        "refaktor",
        "çok dosya",
        "cok dosya",
        "multi file",
        "mega refactor",
        "büyük refactor",
        "buyuk refactor",
        "tüm proje",
        "tum proje",
        "whole codebase",
    )
    return any(c in raw for c in cues)


def build_refactor_pilot_plan(
    message: str,
    workspace_root: str | Path | None,
    scope_rel: str,
    *,
    goal: str = "",
) -> dict[str, Any]:
    msg = (message or "").strip()
    scope = (scope_rel or "").strip().replace("\\", "/").strip("/")
    targets: list[str] = []
    try:
        from ilim_assistant.motorlar.programlama_faz56 import infer_target_files

        targets = infer_target_files(workspace_root, scope, f"{msg} {goal}", limit=12)
    except Exception:
        targets = []

    phases = [
        "Keşif: read/grep ile hedef dosyaları doğrula.",
        "1. parti: en fazla 8 dosyada küçük güvenli değişiklik.",
        "Checkpoint: pytest/lint ile ara doğrulama.",
        "2. parti: kalan dosyalar (gerekirse).",
        "Final: verify + kısa özet.",
    ]
    checkpoints = [
        "Her 8 dosyadan sonra verify çalıştır.",
        "10+ dosya değişince durup onay/checkpoint al.",
    ]
    return {
        "version": FAZ93_VERSION,
        "scope_rel": scope,
        "goal": (goal or msg)[:220],
        "target_files": targets[:12],
        "phases": phases,
        "checkpoints": checkpoints,
        "rollback_hint": (
            "Sorun olursa git checkout -- <dosya> veya son checkpoint'e dön."
        ),
    }


def render_refactor_pilot_directive(plan: dict[str, Any]) -> str:
    scope = str(plan.get("scope_rel") or "").strip()
    goal = str(plan.get("goal") or "").strip()
    targets = [str(x).strip() for x in (plan.get("target_files") or []) if str(x).strip()]
    phases = [str(x).strip() for x in (plan.get("phases") or []) if str(x).strip()]
    checkpoints = [
        str(x).strip() for x in (plan.get("checkpoints") or []) if str(x).strip()
    ]
    lines = ["[PROGRAMLAMA REFACTOR PILOTU — P6]"]
    if scope:
        lines.append(f"Kapsam: `{scope}`")
    if goal:
        lines.append(f"Hedef: {goal}")
    if targets:
        lines.append("Oncelikli dosyalar:")
        lines.extend(f"- `{t}`" for t in targets[:10])
    if phases:
        lines.append("Fazlar:")
        lines.extend(f"{i + 1}. {p}" for i, p in enumerate(phases[:5]))
    if checkpoints:
        lines.append("Kontrol noktalari:")
        lines.extend(f"- {c}" for c in checkpoints[:4])
    lines.append(
        "Talimat: Buyuk degisiklikte once plan, sonra kucuk partiler; her partiden sonra verify."
    )
    lines.append("[/PROGRAMLAMA REFACTOR PILOTU]")
    return "\n".join(lines)


def build_rollback_plan(applied_files: list[str] | None) -> dict[str, Any]:
    files = [str(x).strip().replace("\\", "/") for x in (applied_files or []) if str(x).strip()]
    files = files[:24]
    if not files:
        return {"version": FAZ93_VERSION, "has_plan": False, "files": []}
    sample = files[:6]
    git_cmds = [f"git checkout -- {p}" for p in sample]
    if len(files) > len(sample):
        git_cmds.append("# ... diger dosyalar icin ayni komutu tekrarla")
    return {
        "version": FAZ93_VERSION,
        "has_plan": True,
        "files": files,
        "sample_files": sample,
        "git_commands": git_cmds,
        "manual_hint": "Patch oncesi commit yoksa dosyalari yedekten geri yukle.",
    }


def render_rollback_directive(rollback: dict[str, Any]) -> str:
    if not rollback.get("has_plan"):
        return ""
    cmds = [str(x) for x in (rollback.get("git_commands") or []) if str(x).strip()]
    lines = ["[PROGRAMLAMA GERI DONUS PLANI — P6]"]
    lines.append("Sorun cikarsa asagidaki adimlarla geri al:")
    lines.extend(f"- `{c}`" for c in cmds[:8])
    lines.append(str(rollback.get("manual_hint") or ""))
    lines.append("[/PROGRAMLAMA GERI DONUS PLANI]")
    return "\n".join(lines)


def rollback_status_text(rollback: dict[str, Any]) -> str:
    cnt = len(rollback.get("files") or [])
    if not cnt:
        return ""
    sample = list(rollback.get("sample_files") or [])
    first = sample[0] if sample else "dosya"
    return (
        f"Geri dönüş planı hazır ({cnt} dosya). Örnek: `git checkout -- {first}`"
    )


def record_refactor_checkpoint(
    workspace_root: str | Path | None,
    *,
    user_message: str,
    patch_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    applied = list((patch_meta or {}).get("applied") or [])
    count = len(applied)
    if count < 3:
        return {"version": FAZ93_VERSION, "recorded": False, "applied_count": count}
    data = _load_checkpoints(workspace_root)
    rows = [r for r in (data.get("checkpoints") or []) if isinstance(r, dict)]
    item = {
        "ts": time.time(),
        "goal": " ".join((user_message or "").split()).strip()[:220],
        "applied_files": applied[:24],
        "applied_count": count,
        "patch_action": str((patch_meta or {}).get("action") or ""),
        "rollback": build_rollback_plan(applied),
    }
    rows.append(item)
    if len(rows) > 40:
        rows = rows[-40:]
    data["checkpoints"] = rows
    _save_checkpoints(workspace_root, data)
    return {
        "version": FAZ93_VERSION,
        "recorded": True,
        "applied_count": count,
        "checkpoint_id": len(rows),
        "rollback": item["rollback"],
    }

