# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 10: workspace indeks, çok dosya patch, terminal, delege.

10.1 — Proje kapsamlı indeks + @@read / @@glob genişletme
10.2 — Patch önizle / onayla / uygula (.ruzgar/programlama_pending.json)
10.3 — projects/ kapsamında pytest + npm test/build
10.5 — Ana Motor → programlama otomatik delege
10.6 — Tur sonu patch + isteğe bağlı doğrulama özeti
"""

from __future__ import annotations

import difflib
import json
import os
import re
import time
import unicodedata
from pathlib import Path
from typing import Any

from ilim_assistant.approved_executor import run_argv
from ilim_assistant.motorlar.programlama_motoru import (
    ProgramlamaAraclari,
    repo_root,
)

FAZ10_VERSION = "programlama-faz10-v1-2026-05-24"
_PENDING_FILE = "programlama_pending.json"
_PENDING_DIR = ".ruzgar"

_READ_RE = re.compile(r"@@read\s+(\S+)", re.IGNORECASE)
_GLOB_RE = re.compile(r"@@glob\s+(\S+)", re.IGNORECASE)
_WRITE_RE = re.compile(
    r"@@write\s+(\S+)\s*\r?\n```(?:[\w+-]+)?\s*\r?\n(.*?)```",
    re.DOTALL | re.IGNORECASE,
)

_SKIP_DIRS = frozenset(
    {
        ".git",
        ".cursor",
        ".ruzgar",
        ".venv",
        "venv",
        "__pycache__",
        "node_modules",
        "hafiza",
        "knowledge",
        "dist",
        "build",
        ".pytest_cache",
        "video_indirilen",
    }
)


def _ascii_fold(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def _projects_base() -> str:
    return (
        os.environ.get("RUZGAR_SCAFFOLD_BASE", "projects").strip().replace("\\", "/").strip("/")
        or "projects"
    )


def _norm_rel(rel: str) -> str:
    return (rel or "").strip().replace("\\", "/").lstrip("/")


def _faz10_enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ10", "1").strip().lower() not in ("0", "false", "no")


def _auto_patch_enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ10_AUTO_PATCH", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _delegate_enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ10_DELEGATE", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def resolve_scope_rel(
    workspace_root: str | Path | None,
    *,
    active_file: str | None = None,
) -> str | None:
    """Aktif dosyadan projects/<ad>/ kapsamı."""
    af = _norm_rel(active_file or "")
    base = _projects_base()
    if af.startswith(f"{base}/"):
        parts = af.split("/")
        if len(parts) >= 2:
            return f"{base}/{parts[1]}"
    try:
        from ilim_assistant.motorlar.programlama_faz5 import load_session

        sess = load_session(workspace_root)
        af2 = _norm_rel(str(sess.get("active_file") or ""))
        if af2.startswith(f"{base}/"):
            return f"{base}/{af2.split('/')[1]}"
    except Exception:
        pass
    return None


def build_workspace_index(
    workspace_root: str | Path | None = None,
    *,
    scope_rel: str | None = None,
    max_lines: int = 72,
) -> str:
    """Faz 10.1 — LLM için proje/workspace indeksi."""
    root = repo_root(workspace_root)
    if root is None:
        return ""
    scope = _norm_rel(scope_rel or "")
    lines: list[str] = [f"Kök: {root}"]
    if scope:
        lines.append(f"Kapsam (odak proje): `{scope}`")

    def walk_dir(base: Path, rel_prefix: str, depth: int) -> None:
        if len(lines) >= max_lines or depth > 4:
            return
        try:
            children = sorted(
                base.iterdir(),
                key=lambda p: (not p.is_dir(), p.name.lower()),
            )
        except OSError:
            return
        shown = 0
        for child in children:
            if len(lines) >= max_lines:
                lines.append("  …")
                return
            name = child.name
            if name in _SKIP_DIRS or (name.startswith(".") and name not in (".env.example",)):
                continue
            rel = f"{rel_prefix}/{name}".replace("\\", "/") if rel_prefix else name
            if child.is_dir():
                lines.append(f"  {rel}/")
                walk_dir(child, rel, depth + 1)
            else:
                lines.append(f"  {rel}")
            shown += 1
            if shown > 22:
                lines.append("  …")
                return

    if scope:
        sp = root / scope.replace("/", os.sep)
        if sp.is_dir():
            walk_dir(sp, scope, 0)
        else:
            lines.append(f"(kapsam dizini yok: {scope})")
    else:
        for top in ("projects", "ilim-assistant", "ruzgar-desktop", "scripts"):
            if len(lines) >= max_lines:
                break
            tp = root / top
            if not tp.is_dir():
                continue
            lines.append(f"- {top}/")
            walk_dir(tp, top, 1)

    lines.append(
        "Araçlar: `@@read yol` · `@@glob projects/foo/**/*.py` · `@@write yol` + kod bloğu"
    )
    return "\n".join(lines)


def expand_message_paths(
    message: str,
    workspace_root: str | Path | None,
    *,
    max_glob: int = 12,
) -> list[str]:
    """@@read ve @@glob ile okunacak göreli yollar."""
    root = repo_root(workspace_root)
    if root is None:
        return []
    out: list[str] = []
    seen: set[str] = set()
    for m in _READ_RE.finditer(message or ""):
        rel = _norm_rel(m.group(1))
        if rel and rel not in seen:
            seen.add(rel)
            out.append(rel)
    for m in _GLOB_RE.finditer(message or ""):
        pattern = _norm_rel(m.group(1))
        if not pattern or "**" not in pattern and "*" not in pattern:
            continue
        try:
            for p in root.glob(pattern):
                if len(out) >= max_glob:
                    break
                if not p.is_file():
                    continue
                rel = _norm_rel(str(p.relative_to(root)))
                if rel not in seen:
                    seen.add(rel)
                    out.append(rel)
        except (OSError, ValueError):
            continue
    return out


def extract_write_jobs(text: str) -> list[tuple[str, str]]:
    jobs: list[tuple[str, str]] = []
    for m in _WRITE_RE.finditer(text or ""):
        rel = _norm_rel(m.group(1))
        body = m.group(2)
        if rel:
            jobs.append((rel, body))
    return jobs


def _pending_path(workspace_root: str | Path | None) -> Path | None:
    root = repo_root(workspace_root)
    if root is None:
        return None
    return root / _PENDING_DIR / _PENDING_FILE


def load_pending(workspace_root: str | Path | None) -> dict[str, Any]:
    path = _pending_path(workspace_root)
    if path is None or not path.is_file():
        return {"version": FAZ10_VERSION, "jobs": [], "updated_at": 0.0}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            raw.setdefault("jobs", [])
            return raw
    except (OSError, json.JSONDecodeError):
        pass
    return {"version": FAZ10_VERSION, "jobs": [], "updated_at": 0.0}


def save_pending(workspace_root: str | Path | None, data: dict[str, Any]) -> None:
    path = _pending_path(workspace_root)
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = time.time()
    data["version"] = FAZ10_VERSION
    try:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass


def clear_pending(workspace_root: str | Path | None) -> None:
    path = _pending_path(workspace_root)
    if path and path.is_file():
        try:
            path.unlink()
        except OSError:
            pass


def unified_diff_text(
    old: str,
    new: str,
    rel: str,
    *,
    max_lines: int = 28,
) -> str:
    """Kısa unified diff (Faz 12 önizleme)."""
    path = _norm_rel(rel) or "file"
    if not (old or "").strip():
        lines = (new or "").splitlines()[:max_lines]
        return "\n".join(f"+{ln}" for ln in lines) + ("\n" if lines else "")
    old_l = old.splitlines(keepends=True)
    new_l = new.splitlines(keepends=True)
    chunks = list(
        difflib.unified_diff(
            old_l,
            new_l,
            fromfile=f"eski/{path}",
            tofile=f"yeni/{path}",
            n=2,
            lineterm="",
        )
    )
    if not chunks:
        return "(değişiklik yok)\n"
    out: list[str] = []
    for line in chunks:
        if line.startswith(("---", "+++", "@@")) or line[:1] in ("+", "-", " "):
            out.append(line)
        if len(out) >= max_lines:
            out.append("…")
            break
    return "\n".join(out) + "\n"


def preview_writes(
    text: str,
    workspace_root: str | Path | None = None,
) -> dict[str, Any]:
    jobs = extract_write_jobs(text)
    items: list[dict[str, Any]] = []
    tools = ProgramlamaAraclari(workspace_root)
    for rel, body in jobs:
        old = ""
        if tools.root is not None:
            rep = tools.read(rel, max_chars=12000)
            old = rep.content if rep.ok else ""
        diff = unified_diff_text(old, body, rel)
        items.append(
            {
                "path": rel,
                "new_lines": len(body.splitlines()),
                "old_lines": len(old.splitlines()) if old else 0,
                "preview_chars": min(400, len(body)),
                "diff": diff,
                "is_new_file": not (old or "").strip(),
            }
        )
    return {
        "ok": bool(items),
        "count": len(items),
        "items": items,
        "version": FAZ10_VERSION,
    }


def stage_pending_from_text(
    text: str,
    workspace_root: str | Path | None,
    *,
    source: str = "assistant",
) -> dict[str, Any]:
    jobs = extract_write_jobs(text)
    if not jobs:
        return {"ok": False, "error": "@@write bloğu yok"}
    rows = [{"path": rel, "content": body} for rel, body in jobs]
    save_pending(
        workspace_root,
        {"jobs": rows, "source": source, "staged_at": time.time()},
    )
    return {"ok": True, "count": len(rows), "paths": [r["path"] for r in rows]}


def apply_pending(
    workspace_root: str | Path | None,
    *,
    run_verify: bool = True,
    scope_rel: str | None = None,
) -> dict[str, Any]:
    pending = load_pending(workspace_root)
    rows = list(pending.get("jobs") or [])
    if not rows:
        return {"ok": False, "error": "Bekleyen patch yok. Önce model cevabı veya patch önizle."}
    tools = ProgramlamaAraclari(workspace_root)
    applied: list[str] = []
    errors: list[str] = []
    for row in rows:
        rel = _norm_rel(str(row.get("path") or ""))
        body = str(row.get("content") or "")
        if not rel:
            continue
        w = tools.write(rel, body)
        if w.ok:
            applied.append(rel)
        else:
            errors.append(f"{rel}: {w.detail}")
    clear_pending(workspace_root)
    verify: dict[str, Any] = {}
    if run_verify and applied:
        verify = run_project_verify(workspace_root, scope_rel or applied[0])
    try:
        from ilim_assistant.motorlar.programlama_faz5 import record_tool_summary

        record_tool_summary(workspace_root, writes=applied)
    except Exception:
        pass
    return {
        "ok": not errors,
        "applied": applied,
        "errors": errors,
        "verify": verify,
        "version": FAZ10_VERSION,
    }


def format_patch_preview_report(preview: dict[str, Any]) -> str:
    if not preview.get("items"):
        return "Ümit abi, önizlenecek @@write bloğu yok."
    lines = [
        f"Ümit abi, **{preview.get('count', 0)} dosya** patch önizlemesi (Faz 10):",
        "",
    ]
    for it in preview.get("items") or []:
        tag = "yeni dosya" if it.get("is_new_file") else f"eski ~{it.get('old_lines')} satır"
        lines.append(
            f"• `{it.get('path')}` — yeni ~{it.get('new_lines')} satır ({tag})"
        )
        diff = str(it.get("diff") or "").strip()
        if diff:
            lines.extend(["", "```diff", diff[:2400], "```", ""])
    lines.extend(
        [
            "",
            "Uygulamak için: `patch onayla` veya `patch uygula`",
            f"({FAZ10_VERSION})",
        ]
    )
    return "\n".join(lines)


def format_apply_report(result: dict[str, Any]) -> str:
    if result.get("error") and not result.get("applied"):
        return f"Patch uygulanamadı: {result.get('error')}"
    lines = ["Ümit abi, patch uygulandı (Faz 10):", ""]
    for p in result.get("applied") or []:
        lines.append(f"✓ `{p}`")
    for e in result.get("errors") or []:
        lines.append(f"✗ {e}")
    ver = result.get("verify") or {}
    if ver.get("report"):
        lines.extend(["", str(ver["report"])[:2500]])
    lines.append(f"\n({FAZ10_VERSION})")
    return "\n".join(lines)


def detect_project_tooling(
    workspace_root: str | Path | None,
    scope_rel: str,
) -> dict[str, Any]:
    root = repo_root(workspace_root)
    scope = _norm_rel(scope_rel)
    out: dict[str, Any] = {
        "scope_rel": scope,
        "python": False,
        "pytest": False,
        "npm": False,
        "package_json": False,
    }
    if root is None or not scope:
        return out
    sp = root / scope.replace("/", os.sep)
    if not sp.is_dir():
        return out
    if (sp / "pyproject.toml").is_file() or (sp / "requirements.txt").is_file():
        out["python"] = True
    if (sp / "tests").is_dir() or list(sp.glob("test_*.py")):
        out["pytest"] = True
    pj = sp / "package.json"
    if pj.is_file():
        out["npm"] = True
        out["package_json"] = True
    return out


def run_project_verify(
    workspace_root: str | Path | None,
    scope_rel: str,
) -> dict[str, Any]:
    """Faz 10.3 — kapsam dizininde pytest veya npm test."""
    root = repo_root(workspace_root)
    scope = _norm_rel(scope_rel)
    if root is None:
        return {"ok": False, "error": "workspace_root yok"}
    if scope.startswith(f"{_projects_base()}/"):
        cwd = root / scope.replace("/", os.sep)
    else:
        proj = resolve_scope_rel(workspace_root, active_file=scope)
        if not proj:
            return {"ok": False, "error": "Proje kapsamı bulunamadı (projects/ altı açın)."}
        cwd = root / proj.replace("/", os.sep)
        scope = proj
    if not cwd.is_dir():
        return {"ok": False, "error": f"Dizin yok: {scope}"}

    tooling = detect_project_tooling(workspace_root, scope)
    steps: list[dict[str, Any]] = []

    if tooling.get("npm") and (cwd / "package.json").is_file():
        pj = (cwd / "package.json").read_text(encoding="utf-8", errors="replace").lower()
        if "vite" in pj and (cwd / "node_modules").is_dir():
            npm_argv = ["npm", "run", "build"]
            step_name = "npm_build"
        else:
            npm_argv = ["npm", "test", "--if-present"]
            step_name = "npm_test"
        if not (cwd / "node_modules").is_dir() and "vite" in pj:
            run_argv(["npm", "install"], timeout_sec=300, cwd=str(cwd))
        code, out, err = run_argv(npm_argv, timeout_sec=300, cwd=str(cwd))
        steps.append(
            {
                "step": step_name,
                "exit_code": code,
                "output": (out or err or "")[:6000],
            }
        )
        ok = code == 0
        report = f"{step_name} @ {scope}: exit {code}"
    elif tooling.get("pytest"):
        code, out, err = run_argv(
            [os.environ.get("RUZGAR_PYTHON", "python") or "python", "-m", "pytest", "-q", "--tb=short"],
            timeout_sec=300,
            cwd=str(cwd),
        )
        steps.append(
            {
                "step": "pytest",
                "exit_code": code,
                "output": (out or err or "")[:6000],
            }
        )
        ok = code == 0
        report = f"pytest @ {scope}: exit {code}"
    else:
        return {
            "ok": True,
            "skipped": True,
            "report": f"{scope}: otomatik test profili yok (pytest/npm).",
        }

    lines = [f"Ümit abi, doğrulama **{scope}**:", ""]
    for st in steps:
        mark = "✓" if st.get("exit_code") == 0 else "✗"
        lines.append(f"{mark} {st.get('step')}")
        if st.get("output"):
            lines.append(str(st["output"])[:1800])
    return {
        "ok": ok,
        "scope_rel": scope,
        "steps": steps,
        "report": "\n".join(lines),
    }


def process_assistant_reply_patches(
    reply_body: str,
    workspace_root: str | Path | None,
    *,
    scope_rel: str | None = None,
    skip_if_debug_loop: bool = False,
) -> dict[str, Any]:
    """
    Tur sonu: @@write varsa uygula veya beklet (Faz 10.2 / 10.6).
    debug döngüsü zaten yazdıysa skip_if_debug_loop=True.
    """
    try:
        from ilim_assistant.motorlar.programlama_faz16 import (
            _enabled as faz16_on,
            process_reply_patches_v16,
        )

        if faz16_on():
            return process_reply_patches_v16(
                reply_body,
                workspace_root,
                scope_rel=scope_rel,
                skip_if_debug_loop=skip_if_debug_loop,
            )
    except Exception:
        pass
    if not _faz10_enabled() or skip_if_debug_loop:
        return {"action": "skip"}
    jobs = extract_write_jobs(reply_body)
    if not jobs:
        return {"action": "none"}

    if not _auto_patch_enabled():
        staged = stage_pending_from_text(reply_body, workspace_root)
        return {
            "action": "staged",
            "count": staged.get("count", 0),
            "footer": (
                "\n\n---\n**Faz 10:** Patch hazır — diske yazmak için sohbette "
                "`patch onayla` yaz.\n"
            ),
        }

    tools = ProgramlamaAraclari(workspace_root)
    applied: list[str] = []
    errors: list[str] = []
    diff_items: list[dict[str, Any]] = []
    for rel, body in jobs:
        old = ""
        if tools.root is not None:
            rep = tools.read(rel, max_chars=12000)
            old = rep.content if rep.ok else ""
        w = tools.write(rel, body)
        if w.ok:
            applied.append(rel)
            diff_items.append(
                {
                    "path": rel,
                    "diff": unified_diff_text(old, body, rel),
                    "is_new_file": not (old or "").strip(),
                }
            )
        else:
            errors.append(f"{rel}: {w.detail}")
    verify: dict[str, Any] = {}
    if applied and os.environ.get("RUZGAR_FAZ10_VERIFY_AFTER_PATCH", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    ):
        scope = scope_rel or (applied[0] if applied else None)
        if scope:
            verify = run_project_verify(workspace_root, scope)
    try:
        from ilim_assistant.motorlar.programlama_faz5 import record_tool_summary

        record_tool_summary(workspace_root, writes=applied)
    except Exception:
        pass
    footer_parts = ["\n\n---\n**Faz 10 — otomatik patch:**"]
    for p in applied:
        footer_parts.append(f"\n✓ `{p}`")
    for e in errors:
        footer_parts.append(f"\n✗ {e}")
    if verify.get("report"):
        footer_parts.append("\n" + str(verify["report"])[:2000])
    return {
        "action": "applied",
        "applied": applied,
        "errors": errors,
        "items": diff_items,
        "verify": verify,
        "footer": "".join(footer_parts) if applied or errors else "",
    }


def should_delegate_to_programlama(
    message: str,
    mode_norm: str,
    *,
    coding_mode: bool = False,
    motor_flags: dict[str, bool] | None = None,
) -> bool:
    """Faz 10.5 — genel modda kod işini programlamaya yönlendir."""
    if not _delegate_enabled():
        return False
    if coding_mode or mode_norm == "programlama":
        return False
    if mode_norm not in ("genel", "gelisim", "uretim", ""):
        return False
    flags = motor_flags or {}
    if flags.get("programlama"):
        return True
    low = _ascii_fold(message)
    if "@@write" in low or "@@read" in low:
        return True
    code_cues = (
        "traceback",
        "pytest",
        "dosyasinda",
        "dosyasında",
        "projede",
        "github",
        "refactor",
        "bug fix",
        "hata ayikla",
        "hata ayıkla",
        "patch",
        "main.py",
        "app.py",
        ".py ",
        ".js ",
        ".ts ",
        "fastapi",
        "uvicorn",
        "npm test",
    )
    if any(c in low for c in code_cues):
        return True
    if re.search(r"projects/[\w.\-]+", message or "", re.I):
        return True
    if low.startswith("gorev:") or low.startswith("görev:"):
        return True
    if "gorev:" in low or "görev:" in low:
        return True
    return False


def delegate_notice() -> str:
    return (
        "[Ana Motor → Programlama delege — Faz 10.5]\n"
        "Kod/patch/test isteği programlama motoruna yönlendirildi.\n"
    )


def faz10_directive() -> str:
    return (
        "[Faz 10 — Cursor hattı]\n"
        "Akış: kısa plan → `@@read` / harita → `@@write` patch → `patch onayla` veya otomatik yazım → pytest/npm.\n"
        "Komutlar: `patch önizle` · `patch onayla` · `patch iptal` · `proje test` · `workspace indeks`\n"
    )


# --- Anında komutlar ---


def wants_patch_preview(message: str) -> bool:
    low = _ascii_fold(message)
    return any(k in low for k in ("patch onizle", "patch önizle", "yama onizle", "yama önizle"))


def wants_patch_apply(message: str) -> bool:
    low = _ascii_fold(message)
    return any(
        k in low
        for k in (
            "patch onayla",
            "patch uygula",
            "yamayi uygula",
            "yamayı uygula",
            "bekleyen patch",
        )
    )


def wants_patch_cancel(message: str) -> bool:
    low = _ascii_fold(message)
    return any(k in low for k in ("patch iptal", "patch sil", "bekleyen patch iptal"))


def wants_workspace_index(message: str) -> bool:
    low = _ascii_fold(message)
    return any(
        k in low
        for k in (
            "workspace indeks",
            "proje haritasi",
            "proje haritası",
            "proje indeks",
            "dosya agaci",
            "dosya ağacı",
        )
    )


def wants_project_verify_cmd(message: str) -> bool:
    low = _ascii_fold(message)
    return any(
        k in low
        for k in (
            "proje test",
            "projeyi test",
            "npm test",
            "pytest calistir",
            "pytest çalıştır",
            "dogrula",
            "doğrula",
        )
    )


def maybe_instant_faz10(
    message: str,
    workspace_root: str | Path | None,
    *,
    active_file: str | None = None,
    last_assistant_reply: str | None = None,
) -> str | None:
    if not _faz10_enabled():
        return None
    scope = resolve_scope_rel(workspace_root, active_file=active_file)

    if wants_workspace_index(message):
        idx = build_workspace_index(workspace_root, scope_rel=scope)
        return f"Ümit abi, workspace indeksi:\n\n```\n{idx}\n```\n\n({FAZ10_VERSION})"

    if wants_patch_cancel(message):
        clear_pending(workspace_root)
        return "Ümit abi, bekleyen patch iptal edildi."

    if wants_patch_preview(message):
        src = (last_assistant_reply or message or "").strip()
        prev = preview_writes(src, workspace_root)
        return format_patch_preview_report(prev)

    if wants_patch_apply(message):
        res = apply_pending(workspace_root, scope_rel=scope)
        return format_apply_report(res)

    if wants_project_verify_cmd(message):
        if not scope:
            return (
                "Ümit abi, `proje test` için atölyede `projects/...` dosyası aç "
                "veya yol yaz."
            )
        ver = run_project_verify(workspace_root, scope)
        return str(ver.get("report") or ver.get("error") or "Test bitti.")

    return None
