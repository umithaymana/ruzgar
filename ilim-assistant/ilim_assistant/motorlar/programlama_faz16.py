# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 16: çok dosya patch + onay UI.

Bekleyen patch dosya bazlı kabul/red; toplu uygula; son .bak geri alma.
Varsayılan: otomatik diske yazma kapalı (RUZGAR_FAZ10_AUTO_PATCH boşken).
"""

from __future__ import annotations

import os
import re
import time
import unicodedata
from pathlib import Path
from typing import Any

from ilim_assistant.motorlar.programlama_motoru import ProgramlamaAraclari, repo_root

FAZ16_VERSION = "programlama-faz16-v1-2026-05-25"

STATUS_PENDING = "pending"
STATUS_ACCEPTED = "accepted"
STATUS_REJECTED = "rejected"
STATUS_APPLIED = "applied"

_LAST_APPLIED_KEY = "last_applied"
_ROLLBACK_FILE = "programlama_last_applied.json"


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ16", "1").strip().lower() not in ("0", "false", "no")


def _ascii_fold(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def effective_auto_patch_enabled() -> bool:
    """Faz 16 açıkken varsayılan False; env ile açıkça override edilebilir."""
    try:
        from ilim_assistant.motorlar.programlama_faz23 import effective_auto_patch_for_task

        if effective_auto_patch_for_task():
            return True
    except Exception:
        pass
    raw = os.environ.get("RUZGAR_FAZ10_AUTO_PATCH", "").strip().lower()
    if raw in ("1", "true", "yes", "on"):
        return True
    if raw in ("0", "false", "no", "off"):
        return False
    if _enabled():
        return False
    return True


def _norm_rel(rel: str) -> str:
    return (rel or "").strip().replace("\\", "/").lstrip("/")


def _load_save_clear():
    from ilim_assistant.motorlar.programlama_faz10 import (
        clear_pending,
        load_pending,
        save_pending,
    )

    return load_pending, save_pending, clear_pending


def _ruzgar_dir(workspace_root: str | Path | None) -> Path | None:
    root = repo_root(workspace_root)
    if root is None:
        return None
    d = root / ".ruzgar"
    try:
        d.mkdir(parents=True, exist_ok=True)
    except OSError:
        return None
    return d


def _save_last_applied(
    workspace_root: str | Path | None,
    paths: list[str],
    backup_paths: list[str],
) -> None:
    import json

    rd = _ruzgar_dir(workspace_root)
    if rd is None or not paths:
        return
    payload = {
        "paths": paths,
        "backup_paths": backup_paths,
        "at": time.time(),
        "version": FAZ16_VERSION,
    }
    try:
        (rd / _ROLLBACK_FILE).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError:
        pass


def _load_last_applied(workspace_root: str | Path | None) -> dict[str, Any]:
    import json

    rd = _ruzgar_dir(workspace_root)
    if rd is None:
        return {}
    fp = rd / _ROLLBACK_FILE
    if not fp.is_file():
        return {}
    try:
        return json.loads(fp.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _enrich_job(
    workspace_root: str | Path | None,
    row: dict[str, Any],
    tools: ProgramlamaAraclari,
) -> dict[str, Any]:
    from ilim_assistant.motorlar.programlama_faz10 import unified_diff_text

    rel = _norm_rel(str(row.get("path") or ""))
    body = str(row.get("content") or "")
    status = str(row.get("status") or STATUS_PENDING)
    if status not in (STATUS_PENDING, STATUS_ACCEPTED, STATUS_REJECTED, STATUS_APPLIED):
        status = STATUS_PENDING
    old = ""
    if tools.root is not None and rel:
        rep = tools.read(rel, max_chars=12000)
        old = rep.content if rep.ok else ""
    diff = str(row.get("diff") or "") or unified_diff_text(old, body, rel)
    return {
        "path": rel,
        "status": status,
        "diff": diff,
        "new_lines": len(body.splitlines()),
        "old_lines": len(old.splitlines()) if old else 0,
        "is_new_file": not (old or "").strip(),
        "has_content": bool(body),
    }


def normalize_pending_data(
    workspace_root: str | Path | None,
    pending: dict[str, Any] | None = None,
) -> dict[str, Any]:
    load_pending, _, _ = _load_save_clear()
    data = dict(pending if pending is not None else load_pending(workspace_root))
    tools = ProgramlamaAraclari(workspace_root)
    jobs_in = list(data.get("jobs") or [])
    jobs_out: list[dict[str, Any]] = []
    for row in jobs_in:
        if not isinstance(row, dict):
            continue
        rel = _norm_rel(str(row.get("path") or ""))
        if not rel:
            continue
        merged = dict(row)
        merged["path"] = rel
        jobs_out.append(_enrich_job(workspace_root, merged, tools))
    data["jobs"] = jobs_out
    data.setdefault("version", FAZ16_VERSION)
    return data


def build_pending_bundle(workspace_root: str | Path | None) -> dict[str, Any]:
    data = normalize_pending_data(workspace_root)
    jobs = list(data.get("jobs") or [])
    counts = {
        "total": len(jobs),
        "pending": sum(1 for j in jobs if j.get("status") == STATUS_PENDING),
        "accepted": sum(1 for j in jobs if j.get("status") == STATUS_ACCEPTED),
        "rejected": sum(1 for j in jobs if j.get("status") == STATUS_REJECTED),
        "applied": sum(1 for j in jobs if j.get("status") == STATUS_APPLIED),
    }
    return {
        "ok": bool(jobs),
        "action": "staged" if jobs else "empty",
        "count": counts["total"],
        "counts": counts,
        "items": jobs,
        "paths": [j.get("path") for j in jobs if j.get("path")],
        "pending": data,
        "version": FAZ16_VERSION,
    }


def stage_pending_enriched(
    text: str,
    workspace_root: str | Path | None,
    *,
    source: str = "assistant",
) -> dict[str, Any]:
    from ilim_assistant.motorlar.programlama_faz10 import extract_write_jobs

    load_pending, save_pending, _ = _load_save_clear()
    jobs = extract_write_jobs(text)
    if not jobs:
        return {"ok": False, "error": "@@write bloğu yok"}
    tools = ProgramlamaAraclari(workspace_root)
    payload_jobs: list[dict[str, Any]] = []
    for rel, body in jobs:
        nrel = _norm_rel(rel)
        row = {"path": nrel, "content": body, "status": STATUS_PENDING}
        enriched = _enrich_job(workspace_root, row, tools)
        payload_jobs.append(
            {
                "path": nrel,
                "content": body,
                "status": STATUS_PENDING,
                "diff": enriched.get("diff"),
            }
        )
    payload = {
        "jobs": payload_jobs,
        "source": source,
        "staged_at": time.time(),
        "faz": 16,
    }
    save_pending(workspace_root, payload)
    return {
        "ok": True,
        "count": len(payload["jobs"]),
        "paths": [r["path"] for r in payload["jobs"]],
        "items": [_enrich_job(workspace_root, r, tools) for r in payload["jobs"]],
    }


def _find_job_index(jobs: list[dict[str, Any]], path: str) -> int | None:
    target = _norm_rel(path)
    for i, row in enumerate(jobs):
        if _norm_rel(str(row.get("path") or "")) == target:
            return i
    return None


def set_job_status(
    workspace_root: str | Path | None,
    path: str,
    status: str,
) -> dict[str, Any]:
    load_pending, save_pending, _ = _load_save_clear()
    data = load_pending(workspace_root)
    jobs = list(data.get("jobs") or [])
    idx = _find_job_index(jobs, path)
    if idx is None:
        return {"ok": False, "error": f"Dosyada bekleyen patch yok: {path}"}
    st = status.strip().lower()
    if st not in (STATUS_ACCEPTED, STATUS_REJECTED, STATUS_PENDING):
        return {"ok": False, "error": f"Geçersiz durum: {status}"}
    jobs[idx]["status"] = st
    data["jobs"] = jobs
    save_pending(workspace_root, data)
    return {"ok": True, "path": _norm_rel(path), "status": st}


def accept_all_pending(workspace_root: str | Path | None) -> dict[str, Any]:
    load_pending, save_pending, _ = _load_save_clear()
    data = load_pending(workspace_root)
    jobs = list(data.get("jobs") or [])
    n = 0
    for row in jobs:
        if row.get("status") == STATUS_PENDING:
            row["status"] = STATUS_ACCEPTED
            n += 1
    data["jobs"] = jobs
    save_pending(workspace_root, data)
    return {"ok": True, "accepted": n}


def reject_all_pending(workspace_root: str | Path | None) -> dict[str, Any]:
    load_pending, save_pending, _ = _load_save_clear()
    data = load_pending(workspace_root)
    jobs = list(data.get("jobs") or [])
    n = 0
    for row in jobs:
        if row.get("status") in (STATUS_PENDING, STATUS_ACCEPTED):
            row["status"] = STATUS_REJECTED
            n += 1
    data["jobs"] = jobs
    save_pending(workspace_root, data)
    return {"ok": True, "rejected": n}


def apply_pending_selective(
    workspace_root: str | Path | None,
    *,
    mode: str = "accepted",
    run_verify: bool = True,
    scope_rel: str | None = None,
) -> dict[str, Any]:
    """
    mode=accepted — yalnızca kabul edilenler
    mode=all — reddedilmeyenler (pending + accepted)
    mode=force — tüm bekleyenler (red hariç değil, red hariç: pending+accepted only)
    """
    from ilim_assistant.motorlar.programlama_faz10 import (
        clear_pending,
        run_project_verify,
    )

    load_pending, save_pending, _ = _load_save_clear()
    data = load_pending(workspace_root)
    jobs = list(data.get("jobs") or [])
    if not jobs:
        return {"ok": False, "error": "Bekleyen patch yok."}

    mode_n = (mode or "accepted").strip().lower()
    to_apply: list[dict[str, Any]] = []
    for row in jobs:
        st = str(row.get("status") or STATUS_PENDING)
        if st == STATUS_REJECTED or st == STATUS_APPLIED:
            continue
        if mode_n == "accepted":
            if st == STATUS_ACCEPTED:
                to_apply.append(row)
        elif mode_n in ("all", "force"):
            if st in (STATUS_PENDING, STATUS_ACCEPTED):
                to_apply.append(row)
        else:
            if st == STATUS_ACCEPTED:
                to_apply.append(row)

    if not to_apply:
        return {
            "ok": False,
            "error": "Uygulanacak dosya yok — önce dosyaları kabul edin veya «patch hepsini uygula».",
        }

    tools = ProgramlamaAraclari(workspace_root)
    applied: list[str] = []
    errors: list[str] = []
    diff_items: list[dict[str, Any]] = []
    backup_paths: list[str] = []

    for row in to_apply:
        rel = _norm_rel(str(row.get("path") or ""))
        body = str(row.get("content") or "")
        if not rel:
            continue
        old = ""
        if tools.root is not None:
            rep = tools.read(rel, max_chars=12000)
            old = rep.content if rep.ok else ""
        w = tools.write(rel, body)
        if w.ok:
            applied.append(rel)
            row["status"] = STATUS_APPLIED
            diff_items.append(
                {
                    "path": rel,
                    "diff": str(row.get("diff") or ""),
                    "status": STATUS_APPLIED,
                }
            )
            if tools.root is not None:
                bp = tools.root / rel.replace("/", os.sep)
                bak = bp.with_name(bp.name + ".bak")
                if bak.is_file():
                    backup_paths.append(rel)
        else:
            errors.append(f"{rel}: {w.detail}")

    _save_last_applied(workspace_root, applied, backup_paths)
    remaining = [
        r
        for r in jobs
        if r.get("status") not in (STATUS_APPLIED,) and _norm_rel(str(r.get("path") or ""))
        not in applied
    ]
    if remaining:
        data["jobs"] = remaining
        save_pending(workspace_root, data)
    else:
        clear_pending(workspace_root)

    verify: dict[str, Any] = {}
    if run_verify and applied:
        scope = scope_rel or applied[0]
        verify = run_project_verify(workspace_root, scope)
    try:
        from ilim_assistant.motorlar.programlama_faz5 import record_tool_summary

        record_tool_summary(workspace_root, writes=applied)
    except Exception:
        pass

    return {
        "ok": not errors,
        "action": "applied",
        "applied": applied,
        "errors": errors,
        "items": diff_items,
        "verify": verify,
        "mode": mode_n,
        "version": FAZ16_VERSION,
    }


def rollback_last_applied(workspace_root: str | Path | None) -> dict[str, Any]:
    """Son uygulama turundaki dosyaları .bak yedeğinden geri yükle."""
    last = _load_last_applied(workspace_root)
    paths = list(last.get("paths") or last.get("backup_paths") or [])

    root = repo_root(workspace_root)
    if root is None:
        return {"ok": False, "error": "workspace kökü yok"}

    restored: list[str] = []
    errors: list[str] = []
    for rel in paths:
        nrel = _norm_rel(str(rel))
        if not nrel:
            continue
        fp = root / nrel.replace("/", os.sep)
        bak = fp.with_name(fp.name + ".bak")
        if not bak.is_file():
            errors.append(f"{nrel}: .bak yok")
            continue
        try:
            content = bak.read_text(encoding="utf-8", errors="replace")
            fp.write_text(content, encoding="utf-8")
            restored.append(nrel)
        except OSError as exc:
            errors.append(f"{nrel}: {exc}")

    rd = _ruzgar_dir(workspace_root)
    if rd is not None:
        try:
            (rd / _ROLLBACK_FILE).unlink(missing_ok=True)
        except OSError:
            pass
    return {
        "ok": bool(restored) and not errors,
        "restored": restored,
        "errors": errors,
        "version": FAZ16_VERSION,
    }


def process_reply_patches_v16(
    reply_body: str,
    workspace_root: str | Path | None,
    *,
    scope_rel: str | None = None,
    skip_if_debug_loop: bool = False,
) -> dict[str, Any]:
    from ilim_assistant.motorlar.programlama_faz10 import (
        _faz10_enabled,
        extract_write_jobs,
        process_assistant_reply_patches,
    )

    if not _faz10_enabled() or skip_if_debug_loop:
        return {"action": "skip"}
    if not extract_write_jobs(reply_body):
        return {"action": "none"}
    if effective_auto_patch_enabled():
        return process_assistant_reply_patches(
            reply_body,
            workspace_root,
            scope_rel=scope_rel,
            skip_if_debug_loop=skip_if_debug_loop,
        )
    staged = stage_pending_enriched(reply_body, workspace_root)
    bundle = build_pending_bundle(workspace_root)
    return {
        "action": "staged",
        "count": staged.get("count", 0),
        "items": bundle.get("items") or staged.get("items") or [],
        "counts": bundle.get("counts") or {},
        "footer": (
            "\n\n---\n**Faz 16:** Patch atölyede bekliyor — dosya bazlı **Kabul/Red**, "
            "sonra «Kabul edilenleri uygula» veya `patch onayla`.\n"
        ),
    }


def format_pending_strip_report(bundle: dict[str, Any]) -> str:
    items = bundle.get("items") or []
    if not items:
        return "Bekleyen patch yok."
    c = bundle.get("counts") or {}
    lines = [
        f"Ümit abi, **{len(items)} dosya** bekliyor (Faz 16):",
        f"— kabul: {c.get('accepted', 0)} · bekleyen: {c.get('pending', 0)} · red: {c.get('rejected', 0)}",
        "",
    ]
    for it in items:
        st = it.get("status") or STATUS_PENDING
        lines.append(f"• `{it.get('path')}` — **{st}**")
    lines.extend(
        [
            "",
            "Atölyede Kabul/Red veya: `patch kabul <yol>` · `patch onayla`",
            f"({FAZ16_VERSION})",
        ]
    )
    return "\n".join(lines)


def _patch_commit_hint() -> str:
    try:
        from ilim_assistant.motorlar.programlama_faz17 import post_patch_commit_hint

        return post_patch_commit_hint()
    except Exception:
        return ""


def format_apply_report_v16(result: dict[str, Any]) -> str:
    if result.get("error") and not result.get("applied"):
        return f"Patch: {result.get('error')}"
    lines = ["Ümit abi, patch uygulandı (Faz 16):", ""]
    for p in result.get("applied") or []:
        lines.append(f"✓ `{p}`")
    for e in result.get("errors") or []:
        lines.append(f"✗ {e}")
    ver = result.get("verify") or {}
    if ver.get("report"):
        lines.extend(["", str(ver["report"])[:2500]])
    if result.get("applied"):
        lines.append(_patch_commit_hint().strip())
    lines.append(f"\n({FAZ16_VERSION})")
    return "\n".join(lines)


def wants_patch_accept(message: str) -> bool:
    low = _ascii_fold(message)
    return any(
        k in low
        for k in (
            "patch kabul",
            "yama kabul",
            "patch accept",
            "hepsini kabul",
            "tumunu kabul",
            "tümünü kabul",
        )
    )


def wants_patch_reject(message: str) -> bool:
    low = _ascii_fold(message)
    return any(k in low for k in ("patch red", "patch reddet", "yama red", "hepsini red"))


def wants_patch_rollback(message: str) -> bool:
    low = _ascii_fold(message)
    return any(
        k in low
        for k in ("patch geri al", "geri al patch", "son yedeği geri", "rollback patch")
    )


def wants_patch_list(message: str) -> bool:
    low = _ascii_fold(message)
    return any(k in low for k in ("patch liste", "bekleyen patch", "patch durum"))


def _extract_path_from_message(message: str) -> str | None:
    m = re.search(r"(?:projects/[\w./-]+|[\w./-]+\.(?:py|js|ts|tsx|jsx|html|css|json|md))", message or "")
    return _norm_rel(m.group(0)) if m else None


def maybe_instant_faz16(
    message: str,
    workspace_root: str | Path | None,
    *,
    active_file: str | None = None,
) -> str | None:
    if not _enabled():
        return None
    from ilim_assistant.motorlar.programlama_faz10 import (
        clear_pending,
        format_patch_preview_report,
        preview_writes,
        resolve_scope_rel,
        wants_patch_apply,
        wants_patch_cancel,
        wants_patch_preview,
    )

    scope = resolve_scope_rel(workspace_root, active_file=active_file)

    if wants_patch_cancel(message):
        clear_pending(workspace_root)
        return "Ümit abi, bekleyen patch iptal edildi (Faz 16)."

    if wants_patch_list(message):
        return format_pending_strip_report(build_pending_bundle(workspace_root))

    if wants_patch_rollback(message):
        res = rollback_last_applied(workspace_root)
        if res.get("restored"):
            return "Ümit abi, geri alındı: " + ", ".join(f"`{p}`" for p in res["restored"])
        return f"Geri alınamadı: {res.get('error') or res.get('errors')}"

    low = _ascii_fold(message)
    if wants_patch_reject(message):
        if "hepsini" in low or "tumunu" in low or "tümünü" in low:
            reject_all_pending(workspace_root)
            return "Ümit abi, bekleyen patch'lerin tamamı reddedildi."
        path = _extract_path_from_message(message)
        if path:
            set_job_status(workspace_root, path, STATUS_REJECTED)
            return f"Ümit abi, `{path}` reddedildi."
        return "Hangi dosya? Örnek: `patch red projects/foo/app.py`"

    if wants_patch_accept(message):
        if "hepsini" in low or "tumunu" in low or "tümünü" in low:
            accept_all_pending(workspace_root)
            return "Ümit abi, bekleyen dosyaların tamamı kabul edildi — `patch onayla` ile uygula."
        path = _extract_path_from_message(message)
        if path:
            set_job_status(workspace_root, path, STATUS_ACCEPTED)
            return f"Ümit abi, `{path}` kabul edildi."
        return "Hangi dosya? Örnek: `patch kabul projects/foo/app.py`"

    if wants_patch_preview(message):
        prev = preview_writes(message, workspace_root)
        stage_pending_enriched(message, workspace_root, source="preview_cmd")
        return format_patch_preview_report(prev)

    if wants_patch_apply(message):
        mode = "all" if "hepsini" in low or "tumunu" in low else "accepted"
        res = apply_pending_selective(
            workspace_root,
            mode=mode,
            scope_rel=scope,
        )
        return format_apply_report_v16(res)

    return None


def enrich_code_patch_meta(meta: dict[str, Any], workspace_root: str | Path | None) -> dict[str, Any]:
    if not _enabled() or not meta:
        return meta
    action = meta.get("action")
    if action == "staged":
        bundle = build_pending_bundle(workspace_root)
        meta["items"] = bundle.get("items") or meta.get("items") or []
        meta["counts"] = bundle.get("counts") or {}
        meta["count"] = bundle.get("count") or meta.get("count")
    return meta


def faz16_directive() -> str:
    return (
        "[PATCH ONAY — Faz 16]\n"
        "Çok dosya @@write → atölyede diff + Kabul/Red; varsayılan otomatik yazım kapalı.\n"
        "Komutlar: `patch liste` · `patch kabul <yol>` · `patch red <yol>` · "
        "`patch onayla` · `patch geri al`\n"
    )
