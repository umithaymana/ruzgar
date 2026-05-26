# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 64: Best-of-N worktree (Dalga G — v1).

N aday workspace (kopya veya git worktree) + pytest skoru + kazanan seçimi.
Tam paralel LLM turu Faz 65; bu faz altyapı + skor + `best-of-n:` komutu.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any

FAZ64_VERSION = "programlama-faz64-v1-2026-05-26"
_RUNS_DIR = "best-of-n"
_MANIFEST = "manifest.json"
_BON_CMD_RE = re.compile(
    r"^\s*(?:best-of-n|best\s+of\s+n|paralel\s+ajan)\s*:?\s*"
    r"(?:(\d+)\s+)?(?:projects/)?([\w.\-]+)\s+(.+)$",
    re.I | re.S,
)


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ64", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz64_enabled() -> bool:
    return _enabled()


def max_candidates() -> int:
    try:
        return max(2, min(5, int(os.environ.get("RUZGAR_FAZ64_MAX_N", "3"))))
    except ValueError:
        return 3


def _runs_root(workspace_root: str | Path | None) -> Path | None:
    try:
        from ilim_assistant.motorlar.programlama_motoru import repo_root

        root = repo_root(workspace_root)
        if root is None:
            return None
        d = root / ".ruzgar" / _RUNS_DIR
        d.mkdir(parents=True, exist_ok=True)
        return d
    except Exception:
        return None


def parse_best_of_n_command(message: str) -> dict[str, Any] | None:
    raw = (message or "").strip()
    if not raw:
        return None
    m = _BON_CMD_RE.match(raw)
    if not m:
        return None
    n_s, slug, goal = m.group(1), m.group(2).strip(), m.group(3).strip()
    n = int(n_s) if n_s and n_s.isdigit() else 2
    n = max(2, min(max_candidates(), n))
    scope = f"projects/{slug}".replace("\\", "/")
    return {"n": n, "scope_rel": scope, "project_slug": slug, "goal": goal[:2000]}


def wants_best_of_n(message: str) -> bool:
    low = (message or "").lower()
    if parse_best_of_n_command(message):
        return True
    return any(
        k in low
        for k in (
            "best-of-n durum",
            "best of n durum",
            "paralel ajan durum",
            "best-of-n liste",
        )
    )


def _scope_src_path(workspace_root: str | Path | None, scope_rel: str) -> Path | None:
    try:
        from ilim_assistant.motorlar.programlama_motoru import repo_root

        root = repo_root(workspace_root)
        if root is None:
            return None
        p = root / scope_rel.replace("/", os.sep)
        return p if p.is_dir() else None
    except Exception:
        return None


def _run_pytest_in(scope_dir: Path, *, timeout: int = 120) -> dict[str, Any]:
    if not (scope_dir / "tests").is_dir() and not list(scope_dir.glob("test_*.py")):
        return {"ok": False, "pytest_ok": False, "detail": "test yok", "exit_code": -1}
    try:
        cp = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "--tb=no"],
            cwd=str(scope_dir),
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
        )
        out = ((cp.stdout or "") + (cp.stderr or "")).strip()
        return {
            "ok": True,
            "pytest_ok": cp.returncode == 0,
            "exit_code": cp.returncode,
            "output_tail": out[-800:],
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "pytest_ok": False, "detail": "pytest zaman aşımı"}
    except OSError as exc:
        return {"ok": False, "pytest_ok": False, "detail": str(exc)[:120]}


def _try_git_worktree(
    repo_root: Path,
    run_dir: Path,
    candidate_id: str,
    branch: str,
) -> Path | None:
    if os.environ.get("RUZGAR_FAZ64_SKIP_GIT_WORKTREE", "").strip() in (
        "1",
        "true",
        "yes",
    ):
        return None
    wt_path = run_dir / candidate_id
    if wt_path.exists():
        shutil.rmtree(wt_path, ignore_errors=True)
    try:
        cp = subprocess.run(
            ["git", "worktree", "add", "-b", branch, str(wt_path)],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=90,
            shell=False,
        )
        if cp.returncode == 0 and wt_path.is_dir():
            return wt_path
    except (subprocess.TimeoutExpired, OSError):
        pass
    return None


def _copy_scope_candidate(
    src: Path,
    run_dir: Path,
    candidate_id: str,
    scope_rel: str,
) -> Path | None:
    """projects/foo → run_dir/cand-N/projects/foo"""
    cand_root = run_dir / candidate_id
    if cand_root.exists():
        shutil.rmtree(cand_root, ignore_errors=True)
    dest_scope = cand_root / scope_rel.replace("/", os.sep)
    try:
        dest_scope.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(
            src,
            dest_scope,
            ignore=shutil.ignore_patterns(
                "__pycache__",
                ".pytest_cache",
                "*.pyc",
                ".git",
            ),
        )
        return dest_scope
    except OSError:
        return None


def plan_best_of_n_run(
    workspace_root: str | Path | None,
    *,
    scope_rel: str,
    goal: str,
    n: int = 2,
) -> dict[str, Any]:
    if not _enabled():
        return {"ok": False, "error": "faz64 kapalı"}
    n = max(2, min(max_candidates(), int(n)))
    scope = scope_rel.replace("\\", "/").strip().lstrip("/")
    if not scope.startswith("projects/"):
        scope = f"projects/{scope.split('/')[-1]}"
    src = _scope_src_path(workspace_root, scope)
    if src is None:
        return {"ok": False, "error": f"kaynak proje yok: {scope}"}
    runs = _runs_root(workspace_root)
    if runs is None:
        return {"ok": False, "error": "workspace"}
    run_id = f"bon-{int(time.time())}-{uuid.uuid4().hex[:6]}"
    run_dir = runs / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    try:
        from ilim_assistant.motorlar.programlama_motoru import repo_root

        root = repo_root(workspace_root)
    except Exception:
        root = None
    candidates: list[dict[str, Any]] = []
    for i in range(n):
        cid = f"cand-{i}"
        branch = f"ruzgar/bon-{run_id}-{i}"
        method = "copy"
        scope_path: Path | None = None
        if root is not None and (root / ".git").is_dir():
            wt = _try_git_worktree(root, run_dir, cid, branch)
            if wt is not None:
                method = "git_worktree"
                scope_path = wt / scope.replace("/", os.sep)
        if scope_path is None or not scope_path.is_dir():
            method = "copy"
            scope_path = _copy_scope_candidate(src, run_dir, cid, scope)
        if scope_path is None:
            continue
        if method == "copy":
            rel_scope = f".ruzgar/{_RUNS_DIR}/{run_id}/{cid}/{scope}"
        elif root is not None:
            try:
                rel_scope = str(scope_path.relative_to(root)).replace("\\", "/")
            except ValueError:
                rel_scope = scope
        else:
            rel_scope = scope
        score = _run_pytest_in(scope_path)
        candidates.append(
            {
                "id": cid,
                "method": method,
                "scope_rel": rel_scope,
                "branch": branch if method == "git_worktree" else "",
                "pytest": score,
                "score": 100 if score.get("pytest_ok") else 0,
            }
        )
    if not candidates:
        return {"ok": False, "error": "aday oluşturulamadı"}
    winner = max(candidates, key=lambda c: (c.get("score", 0), c.get("id", "")))
    manifest = {
        "ok": True,
        "run_id": run_id,
        "scope_rel": scope,
        "goal": goal,
        "n": n,
        "candidates": candidates,
        "winner_id": winner.get("id"),
        "winner_scope_rel": winner.get("scope_rel"),
        "created_at": time.time(),
        "version": FAZ64_VERSION,
        "note": "Faz 64: pytest skoru ile kazanan; LLM turu her adayda Faz 65.",
    }
    (run_dir / _MANIFEST).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return manifest


def list_best_of_n_runs(workspace_root: str | Path | None) -> dict[str, Any]:
    runs = _runs_root(workspace_root)
    if runs is None:
        return {"ok": False, "runs": []}
    out: list[dict[str, Any]] = []
    for d in sorted(runs.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if not d.is_dir():
            continue
        mf = d / _MANIFEST
        if not mf.is_file():
            continue
        try:
            data = json.loads(mf.read_text(encoding="utf-8"))
            out.append(
                {
                    "run_id": data.get("run_id") or d.name,
                    "scope_rel": data.get("scope_rel"),
                    "winner_id": data.get("winner_id"),
                    "n": data.get("n"),
                    "created_at": data.get("created_at"),
                }
            )
        except (OSError, json.JSONDecodeError):
            continue
        if len(out) >= 10:
            break
    return {"ok": True, "runs": out}


def format_best_of_n_report(manifest: dict[str, Any]) -> str:
    if not manifest.get("ok"):
        return f"Ümit abi, Best-of-N başarısız: {manifest.get('error', '?')}"
    lines = [
        f"Ümit abi, **Best-of-N** (Faz 64) — `{manifest.get('run_id')}`",
        "",
        f"Proje: `{manifest.get('scope_rel')}` · {manifest.get('n')} aday",
        f"Hedef: {(manifest.get('goal') or '')[:200]}",
        "",
        "Adaylar (pytest skoru):",
    ]
    for c in manifest.get("candidates") or []:
        py = c.get("pytest") or {}
        mark = "✓" if py.get("pytest_ok") else "✗"
        lines.append(
            f"  {mark} **{c.get('id')}** ({c.get('method')}) — "
            f"`{c.get('scope_rel', '?')}`"
        )
    lines.extend(
        [
            "",
            f"**Kazanan (pytest):** `{manifest.get('winner_id')}` → "
            f"`{manifest.get('winner_scope_rel')}`",
            "",
            "Sonraki: kazanan kopyada `görev:` ile düzeltme veya Faz 65 tam paralel LLM.",
            f"({FAZ64_VERSION})",
        ]
    )
    return "\n".join(lines)


def maybe_instant_faz64(
    message: str,
    workspace_root: str | Path | None,
) -> str | None:
    if not _enabled():
        return None
    low = (message or "").lower()
    if any(k in low for k in ("best-of-n durum", "best of n durum", "paralel ajan durum")):
        lst = list_best_of_n_runs(workspace_root)
        if not lst.get("runs"):
            return "Ümit abi, kayıtlı Best-of-N koşusu yok. `best-of-n: 2 proje-adı hedef` ile başlat."
        lines = ["Ümit abi, **Best-of-N koşuları:**", ""]
        for r in lst.get("runs") or []:
            lines.append(
                f"  · `{r.get('run_id')}` — {r.get('scope_rel')} "
                f"→ kazanan {r.get('winner_id')}"
            )
        lines.append(f"\n({FAZ64_VERSION})")
        return "\n".join(lines)
    parsed = parse_best_of_n_command(message)
    if not parsed:
        return None
    manifest = plan_best_of_n_run(
        workspace_root,
        scope_rel=parsed["scope_rel"],
        goal=parsed["goal"],
        n=parsed["n"],
    )
    return format_best_of_n_report(manifest)


def enrich_health_build(build: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(build or {})
    out["faz64"] = faz64_enabled()
    out["best_of_n_max"] = max_candidates()
    return out


def faz64_directive() -> str:
    return (
        "[BEST-OF-N — Faz 64]\n"
        "Komut: `best-of-n: 2 proje-adi hedef metin` — N aday kopya/worktree + pytest skoru.\n"
        "Durum: `best-of-n durum` · Kapat: RUZGAR_FAZ64=0\n"
    )
