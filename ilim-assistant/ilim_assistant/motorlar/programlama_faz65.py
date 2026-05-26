# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 65: Best-of-N + tam kod ajanı (Dalga G — v2).

Faz 64 manifest üzerinde her adayda `iter_code_agent_turn_events` çalıştırır,
pytest ile yeniden skorlar, kazananı seçer; isteğe bağlı ana `projects/` kopyası.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any

FAZ65_VERSION = "programlama-faz65-v1-2026-05-26"
_RUNS_DIR = "best-of-n"
_MANIFEST = "manifest.json"
_BON_AGENT_RE = re.compile(
    r"^\s*best-of-n-agent\s*:?\s*([\w.\-]+)\s*$",
    re.I,
)
_BON_PLUS_RE = re.compile(
    r"^\s*best-of-n\+\s*:?\s*"
    r"(?:(\d+)\s+)?(?:projects/)?([\w.\-]+)\s+(.+)$",
    re.I | re.S,
)


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ65", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz65_enabled() -> bool:
    return _enabled()


def max_agent_turns() -> int:
    try:
        return max(1, min(12, int(os.environ.get("RUZGAR_FAZ65_MAX_TURNS", "4"))))
    except ValueError:
        return 4


def auto_merge_winner() -> bool:
    return os.environ.get("RUZGAR_FAZ65_MERGE", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def _runs_root(workspace_root: str | Path | None) -> Path | None:
    try:
        from ilim_assistant.motorlar.programlama_motoru import repo_root

        root = repo_root(workspace_root)
        if root is None:
            return None
        return root / ".ruzgar" / _RUNS_DIR
    except Exception:
        return None


def load_manifest(
    workspace_root: str | Path | None,
    run_id: str,
) -> dict[str, Any] | None:
    runs = _runs_root(workspace_root)
    if runs is None:
        return None
    rid = (run_id or "").strip()
    if not rid:
        return None
    mf = runs / rid / _MANIFEST
    if not mf.is_file():
        for d in runs.iterdir():
            if d.is_dir() and (d.name == rid or rid in d.name):
                mf = d / _MANIFEST
                if mf.is_file():
                    break
        else:
            return None
    try:
        return json.loads(mf.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def save_manifest(
    workspace_root: str | Path | None,
    manifest: dict[str, Any],
) -> bool:
    run_id = str(manifest.get("run_id") or "").strip()
    runs = _runs_root(workspace_root)
    if not runs or not run_id:
        return False
    mf = runs / run_id / _MANIFEST
    try:
        mf.parent.mkdir(parents=True, exist_ok=True)
        manifest["updated_at"] = time.time()
        manifest["faz65_version"] = FAZ65_VERSION
        mf.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return True
    except OSError:
        return False


def parse_best_of_n_agent_command(message: str) -> dict[str, Any] | None:
    raw = (message or "").strip()
    m = _BON_AGENT_RE.match(raw)
    if not m:
        return None
    return {"run_id": m.group(1).strip()}


def parse_best_of_n_plus_command(message: str) -> dict[str, Any] | None:
    raw = (message or "").strip()
    m = _BON_PLUS_RE.match(raw)
    if not m:
        return None
    n_s, slug, goal = m.group(1), m.group(2).strip(), m.group(3).strip()
    n = int(n_s) if n_s and n_s.isdigit() else 2
    try:
        from ilim_assistant.motorlar.programlama_faz64 import max_candidates

        n = max(2, min(max_candidates(), n))
    except Exception:
        n = max(2, min(3, n))
    scope = f"projects/{slug}".replace("\\", "/")
    return {"n": n, "scope_rel": scope, "project_slug": slug, "goal": goal[:2000]}


def wants_best_of_n_agent(message: str) -> bool:
    low = (message or "").lower()
    if parse_best_of_n_agent_command(message):
        return True
    if parse_best_of_n_plus_command(message):
        return True
    return "best-of-n-agent" in low or "best-of-n+" in low


def candidate_workspace_root(
    repo_root: Path,
    manifest: dict[str, Any],
    candidate: dict[str, Any],
) -> Path | None:
    """Ajanın `görev:` slug çözümlemesi için workspace kökü (projects/ üstü)."""
    run_id = str(manifest.get("run_id") or "")
    cid = str(candidate.get("id") or "")
    method = str(candidate.get("method") or "copy")
    if method == "copy" and run_id and cid:
        p = repo_root / ".ruzgar" / _RUNS_DIR / run_id / cid
        if (p / "projects").is_dir() or any(p.glob("projects/*")):
            return p
    scope_rel = str(candidate.get("scope_rel") or "")
    if scope_rel.startswith("projects/"):
        sp = repo_root / scope_rel.replace("/", os.sep)
        if sp.is_dir():
            return sp.parent.parent if sp.parent.name == "projects" else repo_root
    if scope_rel.startswith(".ruzgar/"):
        parts = scope_rel.split("/")
        try:
            idx = parts.index("cand-0") if "cand-0" in parts else parts.index(cid)
            cand_path = repo_root.joinpath(*parts[: idx + 1])
            if cand_path.is_dir():
                return cand_path
        except ValueError:
            pass
        sp = repo_root / scope_rel.replace("/", os.sep)
        if sp.is_dir():
            parent = sp.parent
            if parent.name == "projects":
                return parent.parent
    if run_id and cid:
        p = repo_root / ".ruzgar" / _RUNS_DIR / run_id / cid
        if p.is_dir():
            return p
    return repo_root


def _scope_dir(repo_root: Path, scope_rel: str) -> Path | None:
    p = repo_root / scope_rel.replace("/", os.sep)
    return p if p.is_dir() else None


def _rescore_candidate(repo_root: Path, candidate: dict[str, Any]) -> dict[str, Any]:
    scope_rel = str(candidate.get("scope_rel") or "")
    goal = ""
    try:
        from ilim_assistant.motorlar.programlama_faz14 import run_project_verify

        rep = run_project_verify(str(repo_root), scope_rel, goal=goal or "pytest")
        if rep is not None:
            ok = bool(getattr(rep, "ok", False))
            return {
                "ok": True,
                "pytest_ok": ok,
                "exit_code": getattr(rep, "exit_code", -1),
                "output_tail": (getattr(rep, "output", "") or "")[-800:],
            }
    except Exception as exc:
        return {"ok": False, "pytest_ok": False, "detail": str(exc)[:120]}
    try:
        from ilim_assistant.motorlar.programlama_faz64 import _run_pytest_in

        sp = _scope_dir(repo_root, scope_rel)
        if sp is None and scope_rel.startswith(".ruzgar/"):
            sp = repo_root / scope_rel.replace("/", os.sep)
        if sp is not None:
            return _run_pytest_in(sp)
    except Exception as exc:
        return {"ok": False, "pytest_ok": False, "detail": str(exc)[:120]}
    return {"ok": False, "pytest_ok": False, "detail": "scope yok"}


def _pick_winner(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    def _key(c: dict[str, Any]) -> tuple:
        agent = c.get("agent") or {}
        py = c.get("pytest") or {}
        return (
            1 if py.get("pytest_ok") else 0,
            1 if agent.get("success") else 0,
            int(c.get("score", 0)),
            str(c.get("id", "")),
        )

    return max(candidates, key=_key)


def run_code_agent_on_workspace(
    workspace_root: str,
    project_slug: str,
    goal: str,
    *,
    scope_rel: str | None = None,
) -> dict[str, Any]:
    """Tek adayda senkron kod ajanı (SSE olaylarını tüketir)."""
    from ilim_assistant.chat_core import prepare_turn, prior_messages_for_turn
    from ilim_assistant.motorlar.programlama_faz14 import iter_code_agent_turn_events

    message = f"görev: {project_slug} {goal}".strip()
    req = SimpleNamespace(
        workspace_root=str(workspace_root),
        programlama_active_file=None,
        programlama_editor_snippet=None,
        session_wake_used=False,
    )
    prep = prepare_turn(
        message,
        [],
        use_web=False,
        fetch_pages=0,
        coding_mode=True,
        session_wake_used=False,
        mode="programlama",
        workspace_root=str(workspace_root),
    )
    if prep is None:
        return {"ok": False, "error": "prep_none"}
    msg, hits, user_payload, system, model, og_direct = prep
    if og_direct is not None:
        return {
            "ok": False,
            "error": "instant_only",
            "detail": str(og_direct)[:400],
        }
    prior = prior_messages_for_turn([], "programlama")
    prev_turns = os.environ.get("RUZGAR_CODE_AGENT_MAX_TURNS")
    os.environ["RUZGAR_CODE_AGENT_MAX_TURNS"] = str(max_agent_turns())
    t0 = time.perf_counter()
    out: dict[str, Any] = {
        "ok": False,
        "success": False,
        "turns": 0,
        "elapsed_sec": 0.0,
        "scope_rel": scope_rel or f"projects/{project_slug}",
    }
    try:
        for ev in iter_code_agent_turn_events(
            message=msg,
            req=req,
            system=system or "",
            user_payload=user_payload or "",
            model=model or "",
            prior=prior,
            mode_norm="programlama",
            coding=True,
            turn_plan=None,
            hits=hits or [],
            new_wake=False,
            orch=None,
        ):
            if ev.get("type") == "error":
                out["error"] = str(ev.get("text") or "")[:500]
            elif ev.get("type") == "done":
                ca = ev.get("code_agent") or {}
                out["ok"] = True
                out["success"] = bool(ca.get("success"))
                out["turns"] = int(ca.get("turns") or 0)
                out["scope_rel"] = ca.get("scope_rel") or out["scope_rel"]
                out["reply_tail"] = (ev.get("full_reply") or "")[-1200:]
    except Exception as exc:
        out["error"] = str(exc)[:300]
    finally:
        if prev_turns is None:
            os.environ.pop("RUZGAR_CODE_AGENT_MAX_TURNS", None)
        else:
            os.environ["RUZGAR_CODE_AGENT_MAX_TURNS"] = prev_turns
    out["elapsed_sec"] = round(time.perf_counter() - t0, 2)
    return out


def execute_best_of_n_agents(
    workspace_root: str | Path | None,
    run_id: str,
    *,
    merge: bool | None = None,
) -> dict[str, Any]:
    if not _enabled():
        return {"ok": False, "error": "faz65 kapalı"}
    manifest = load_manifest(workspace_root, run_id)
    if not manifest or not manifest.get("ok"):
        return {"ok": False, "error": f"manifest yok: {run_id}"}
    try:
        from ilim_assistant.motorlar.programlama_motoru import repo_root

        root = repo_root(workspace_root)
    except Exception:
        root = None
    if root is None:
        return {"ok": False, "error": "workspace"}
    goal = str(manifest.get("goal") or "pytest")
    scope_main = str(manifest.get("scope_rel") or "")
    slug = scope_main.split("/")[-1] if scope_main else "project"
    candidates: list[dict[str, Any]] = list(manifest.get("candidates") or [])
    if not candidates:
        return {"ok": False, "error": "aday yok"}
    max_run = 5
    try:
        max_run = max(1, min(5, int(os.environ.get("RUZGAR_FAZ65_MAX_CANDIDATES", "5"))))
    except ValueError:
        pass
    lines: list[str] = []
    for c in candidates[:max_run]:
        cid = c.get("id", "?")
        cw = candidate_workspace_root(root, manifest, c)
        if cw is None:
            c["agent"] = {"ok": False, "error": "workspace"}
            continue
        lines.append(f"Ajan {cid} @ `{cw}` …")
        agent = run_code_agent_on_workspace(
            str(cw),
            slug,
            goal,
            scope_rel=str(c.get("scope_rel") or ""),
        )
        c["agent"] = agent
        c["pytest"] = _rescore_candidate(root, c)
        sc = 0
        if (c.get("pytest") or {}).get("pytest_ok"):
            sc += 100
        if agent.get("success"):
            sc += 50
        c["score"] = sc
    winner = _pick_winner(candidates)
    manifest["candidates"] = candidates
    manifest["winner_id"] = winner.get("id")
    manifest["winner_scope_rel"] = winner.get("scope_rel")
    manifest["winner_mode"] = "faz65_agent_pytest"
    manifest["agent_phase"] = {
        "ok": True,
        "at": time.time(),
        "version": FAZ65_VERSION,
    }
    save_manifest(workspace_root, manifest)
    merged = None
    do_merge = auto_merge_winner() if merge is None else bool(merge)
    if do_merge:
        merged = merge_winner_to_main_scope(workspace_root, manifest)
        manifest["merge"] = merged
        save_manifest(workspace_root, manifest)
    return {
        "ok": True,
        "run_id": manifest.get("run_id"),
        "manifest": manifest,
        "report": format_best_of_n_agent_report(manifest),
        "merge": merged,
        "log": lines,
    }


def merge_winner_to_main_scope(
    workspace_root: str | Path | None,
    manifest: dict[str, Any],
) -> dict[str, Any]:
    try:
        from ilim_assistant.motorlar.programlama_motoru import repo_root

        root = repo_root(workspace_root)
    except Exception:
        root = None
    if root is None:
        return {"ok": False, "error": "workspace"}
    scope_main = str(manifest.get("scope_rel") or "").replace("\\", "/")
    if not scope_main.startswith("projects/"):
        return {"ok": False, "error": "scope"}
    wid = manifest.get("winner_id")
    winner = None
    for c in manifest.get("candidates") or []:
        if c.get("id") == wid:
            winner = c
            break
    if winner is None:
        return {"ok": False, "error": "kazanan yok"}
    src = _scope_dir(root, str(winner.get("scope_rel") or ""))
    if src is None:
        src = root / str(winner.get("scope_rel") or "").replace("/", os.sep)
    if not src.is_dir():
        return {"ok": False, "error": "kazanan dizin yok"}
    dest = root / scope_main.replace("/", os.sep)
    bak = dest.with_suffix(dest.suffix + ".bon-bak")
    try:
        if dest.is_dir():
            if bak.is_dir():
                shutil.rmtree(bak, ignore_errors=True)
            dest.rename(bak)
        shutil.copytree(
            src,
            dest,
            ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", "*.pyc"),
        )
        return {"ok": True, "from": str(winner.get("scope_rel")), "to": scope_main, "backup": str(bak)}
    except OSError as exc:
        return {"ok": False, "error": str(exc)[:200]}


def format_best_of_n_agent_report(manifest: dict[str, Any]) -> str:
    if not manifest.get("ok"):
        return f"Ümit abi, Best-of-N ajan başarısız: {manifest.get('error', '?')}"
    lines = [
        f"Ümit abi, **Best-of-N ajan** (Faz 65) — `{manifest.get('run_id')}`",
        "",
        f"Proje: `{manifest.get('scope_rel')}` · mod: {manifest.get('winner_mode', 'faz65')}",
        "",
        "Adaylar (ajan + pytest):",
    ]
    for c in manifest.get("candidates") or []:
        py = c.get("pytest") or {}
        ag = c.get("agent") or {}
        pmark = "✓" if py.get("pytest_ok") else "✗"
        amark = "✓" if ag.get("success") else "✗"
        lines.append(
            f"  pytest{pmark} ajan{amark} **{c.get('id')}** — skor {c.get('score', 0)} "
            f"({ag.get('turns', 0)} tur, {ag.get('elapsed_sec', 0)} sn)"
        )
    lines.extend(
        [
            "",
            f"**Kazanan:** `{manifest.get('winner_id')}` → `{manifest.get('winner_scope_rel')}`",
        ]
    )
    mg = manifest.get("merge")
    if isinstance(mg, dict) and mg.get("ok"):
        lines.append(f"Ana kopya güncellendi: `{mg.get('to')}` (yedek: `{mg.get('backup', '')}`)")
    elif isinstance(mg, dict) and mg.get("error"):
        lines.append(f"Birleştirme atlandı: {mg.get('error')}")
    else:
        lines.append(
            "Birleştirme: `RUZGAR_FAZ65_MERGE=1` veya `best-of-n merge: <run_id>`"
        )
    lines.append(f"\n({FAZ65_VERSION})")
    return "\n".join(lines)


def run_best_of_n_plus(
    workspace_root: str | Path | None,
    *,
    scope_rel: str,
    goal: str,
    n: int = 2,
    merge: bool | None = None,
) -> dict[str, Any]:
    from ilim_assistant.motorlar.programlama_faz64 import plan_best_of_n_run

    manifest = plan_best_of_n_run(
        workspace_root,
        scope_rel=scope_rel,
        goal=goal,
        n=n,
    )
    if not manifest.get("ok"):
        return manifest
    rid = str(manifest.get("run_id") or "")
    agent_out = execute_best_of_n_agents(workspace_root, rid, merge=merge)
    if not agent_out.get("ok"):
        manifest["agent_error"] = agent_out.get("error")
        return {
            "ok": False,
            "error": agent_out.get("error"),
            "plan": manifest,
        }
    return agent_out


def maybe_instant_faz65(
    message: str,
    workspace_root: str | Path | None,
) -> str | None:
    if not _enabled():
        return None
    low = (message or "").lower().strip()
    if low.startswith("best-of-n merge:") or low.startswith("best-of-n birleştir:"):
        rid = message.split(":", 1)[-1].strip().split()[0]
        man = load_manifest(workspace_root, rid)
        if not man:
            return f"Ümit abi, koşu bulunamadı: `{rid}`"
        mg = merge_winner_to_main_scope(workspace_root, man)
        man["merge"] = mg
        save_manifest(workspace_root, man)
        if mg.get("ok"):
            return (
                f"Ümit abi, kazanan `{man.get('winner_id')}` → `{man.get('scope_rel')}` "
                f"kopyalandı.\n({FAZ65_VERSION})"
            )
        return f"Ümit abi, birleştirme olmadı: {mg.get('error', '?')}"
    parsed_plus = parse_best_of_n_plus_command(message)
    if parsed_plus:
        out = run_best_of_n_plus(
            workspace_root,
            scope_rel=parsed_plus["scope_rel"],
            goal=parsed_plus["goal"],
            n=parsed_plus["n"],
        )
        if out.get("report"):
            return str(out["report"])
        return format_best_of_n_agent_report(out.get("manifest") or out)
    parsed = parse_best_of_n_agent_command(message)
    if parsed:
        out = execute_best_of_n_agents(workspace_root, parsed["run_id"])
        return str(out.get("report") or format_best_of_n_agent_report(out.get("manifest") or out))
    return None


def enrich_health_build(build: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(build or {})
    out["faz65"] = faz65_enabled()
    out["best_of_n_agent_max_turns"] = max_agent_turns()
    return out


def faz65_directive() -> str:
    return (
        "[BEST-OF-N AJAN — Faz 65]\n"
        "Plan+ajan: `best-of-n+: 2 proje-adi hedef` · Mevcut koşu: `best-of-n-agent: bon-...`\n"
        "Birleştir: `best-of-n merge: bon-...` · Kapat: RUZGAR_FAZ65=0\n"
    )
