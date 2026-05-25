# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 14: otonom görev döngüsü.

Komut: görev: <proje> <iş>  — plan → oku → @@write → doğrula → tekrar (max N tur).
Durdurma: görev durdur · Durum: görev durum
"""

from __future__ import annotations

import json
import os
import re
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

from ilim_assistant.motorlar.programlama_motoru import (
    ExecReport,
    ToolRunSummary,
    apply_assistant_reply_tools,
    repo_root,
)

FAZ14_VERSION = "programlama-faz14-v3-2026-05-25"

_PYTEST_NO_TESTS_EXIT = 5

_TASK_PREFIX_RE = re.compile(
    r"^\s*(?:görev|gorev)\s*:\s*(.+)$",
    re.I | re.M,
)
_TASK_INLINE_RE = re.compile(
    r"^\s*(?:görev|gorev)\s+([\w.\-]+)\s+(.+)$",
    re.I | re.M,
)
_SCOPE_RE = re.compile(r"(projects/[\w.\-]+)", re.I)


def _ascii_fold(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ14", "1").strip().lower() not in ("0", "false", "no")


def _projects_base() -> str:
    return (
        os.environ.get("RUZGAR_SCAFFOLD_BASE", "projects").strip().replace("\\", "/").strip("/")
        or "projects"
    )


def _norm_rel(rel: str) -> str:
    return (rel or "").strip().replace("\\", "/").lstrip("/")


def code_agent_max_turns() -> int:
    try:
        v = int(os.environ.get("RUZGAR_CODE_AGENT_MAX_TURNS", "8"))
    except ValueError:
        v = 8
    return max(1, min(v, 16))


def _state_path(workspace_root: str | Path | None) -> Path | None:
    root = repo_root(workspace_root)
    if root is None:
        return None
    d = root / ".ruzgar"
    d.mkdir(parents=True, exist_ok=True)
    return d / "code_agent_state.json"


def load_agent_state(workspace_root: str | Path | None) -> dict[str, Any]:
    p = _state_path(workspace_root)
    if p is None or not p.is_file():
        return {"status": "idle"}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {"status": "idle"}
    except (OSError, json.JSONDecodeError):
        return {"status": "idle"}


def save_agent_state(workspace_root: str | Path | None, state: dict[str, Any]) -> None:
    p = _state_path(workspace_root)
    if p is None:
        return
    try:
        p.write_text(
            json.dumps(state, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError:
        pass


def request_agent_stop(workspace_root: str | Path | None) -> None:
    st = load_agent_state(workspace_root)
    st["stop_requested"] = True
    st["status"] = "stopping"
    save_agent_state(workspace_root, st)


def clear_agent_state(workspace_root: str | Path | None) -> None:
    save_agent_state(
        workspace_root,
        {"status": "idle", "stop_requested": False},
    )


def is_stop_requested(workspace_root: str | Path | None) -> bool:
    return bool(load_agent_state(workspace_root).get("stop_requested"))


@dataclass
class CodeAgentTask:
    scope_rel: str
    goal: str
    project_slug: str


def _scope_from_slug(slug: str) -> str:
    s = (slug or "").strip().strip("/")
    if s.startswith(f"{_projects_base()}/"):
        return _norm_rel(s)
    return f"{_projects_base()}/{s}"


def parse_code_agent_task(message: str) -> CodeAgentTask | None:
    raw = (message or "").strip()
    try:
        from ilim_assistant.motorlar.programlama_faz19 import normalize_agent_message

        raw = normalize_agent_message(raw, mode_norm="programlama")
    except Exception:
        pass
    if not raw:
        return None

    m_path = _SCOPE_RE.search(raw)
    if m_path:
        scope = _norm_rel(m_path.group(1))
        slug = scope.split("/")[-1] if "/" in scope else scope
    else:
        scope = ""
        slug = ""

    m = _TASK_PREFIX_RE.search(raw)
    if m:
        rest = m.group(1).strip()
        parts = rest.split(None, 1)
        if not parts:
            return None
        first = parts[0].strip()
        goal = parts[1].strip() if len(parts) > 1 else rest
        if first.startswith(f"{_projects_base()}/"):
            scope = _norm_rel(first)
            slug = scope.split("/")[-1]
        elif not scope:
            scope = _scope_from_slug(first)
            slug = first
        else:
            goal = rest
        if scope and goal:
            return CodeAgentTask(scope_rel=scope, goal=goal, project_slug=slug)
        return None

    m2 = _TASK_INLINE_RE.search(raw)
    if m2:
        slug = m2.group(1).strip()
        goal = m2.group(2).strip()
        scope = _scope_from_slug(slug)
        if scope and goal:
            return CodeAgentTask(scope_rel=scope, goal=goal, project_slug=slug)

    return None


def wants_code_agent_stop(message: str) -> bool:
    low = _ascii_fold(message)
    return any(
        k in low
        for k in (
            "gorev durdur",
            "görev durdur",
            "gorev dur",
            "görev dur",
            "gorev iptal",
            "görev iptal",
            "stop gorev",
            "stop görev",
            "agent durdur",
        )
    )


def wants_code_agent_status(message: str) -> bool:
    low = _ascii_fold(message)
    return any(
        k in low
        for k in (
            "gorev durum",
            "görev durum",
            "gorev status",
            "görev status",
            "gorev ne durumda",
            "görev ne durumda",
        )
    )


def should_run_code_agent_loop(
    message: str,
    mode_norm: str = "",
    *,
    workspace_root: str | Path | None = None,
    active_file: str | None = None,
) -> bool:
    if not _enabled():
        return False
    if mode_norm != "programlama":
        return False
    if wants_code_agent_stop(message) or wants_code_agent_status(message):
        return False
    try:
        from ilim_assistant.motorlar.programlama_faz33 import should_auto_programming_agent

        return should_auto_programming_agent(
            message,
            mode_norm,
            workspace_root=workspace_root,
            active_file=active_file,
        )
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz19 import normalize_agent_message

        msg = normalize_agent_message(message, mode_norm=mode_norm)
    except Exception:
        msg = message
    return parse_code_agent_task(msg) is not None


def format_agent_status_report(workspace_root: str | Path | None) -> str:
    st = load_agent_state(workspace_root)
    lines = [
        "Ümit abi, **otonom görev durumu** (Faz 14):",
        "",
        f"Durum: `{st.get('status', 'idle')}`",
    ]
    if st.get("scope_rel"):
        lines.append(f"Proje: `{st.get('scope_rel')}`")
    if st.get("goal"):
        lines.append(f"Hedef: {st.get('goal')}")
    if st.get("turn"):
        lines.append(f"Tur: {st.get('turn')} / {st.get('max_turns', code_agent_max_turns())}")
    if st.get("last_verify_ok") is not None:
        lines.append(f"Son doğrulama: {'OK' if st.get('last_verify_ok') else 'kırmızı'}")
    if st.get("stop_requested"):
        lines.append("Durdurma istendi: evet")
    lines.append(f"\n({FAZ14_VERSION})")
    return "\n".join(lines)


def format_stop_report() -> str:
    return (
        "Ümit abi, otonom görev durdurma işaretlendi. "
        "Aktif tur bitince döngü kapanır.\n\n"
        f"({FAZ14_VERSION})"
    )


def maybe_instant_faz14(
    message: str,
    workspace_root: str | Path | None,
) -> str | None:
    if not _enabled():
        return None
    if wants_code_agent_stop(message):
        request_agent_stop(workspace_root)
        return format_stop_report()
    if wants_code_agent_status(message):
        return format_agent_status_report(workspace_root)
    return None


def build_agent_turn_user_message(
    task: CodeAgentTask,
    *,
    turn: int,
    max_turns: int,
    failure_snippet: str = "",
) -> str:
    if turn <= 1:
        return (
            f"[OTONOM GÖREV — Faz 14 — tur {turn}/{max_turns}]\n"
            f"Proje: `{task.scope_rel}`\n"
            f"Hedef: {task.goal}\n\n"
            "Adımlar:\n"
            "1) Kısa plan (madde)\n"
            "2) Gerekli dosyaları `@@read` ile oku (veya zaten bağlamda)\n"
            "3) `@@write yol` + kod bloğu ile patch\n"
            "4) Test isteniyorsa `tests/test_health.py` ve health'te `version` alanı\n"
            "5) Gereksiz refaktör yok\n"
        )
    return (
        f"[OTONOM GÖREV — tur {turn}/{max_turns} — düzeltme]\n"
        "Doğrulama kırmızı. Traceback/çıktı:\n\n"
        f"```text\n{failure_snippet[:14000]}\n```\n\n"
        "Yalnızca gerekli `@@write` patch; kabuk komutu yazma.\n"
    )


def _goal_wants_tests(goal: str) -> bool:
    low = _ascii_fold(goal or "")
    return any(
        k in low
        for k in (
            "test",
            "pytest",
            "gecir",
            "geçir",
            "dogrula",
            "doğrula",
        )
    )


def _scope_project_dir(workspace_root: str | Path | None, scope_rel: str) -> Path | None:
    root = repo_root(workspace_root)
    if root is None:
        return None
    proj = root / scope_rel.replace("/", os.sep)
    return proj if proj.is_dir() else None


def _scope_has_tests(workspace_root: str | Path | None, scope_rel: str) -> bool:
    proj = _scope_project_dir(workspace_root, scope_rel)
    if proj is None:
        return False
    tests_dir = proj / "tests"
    if tests_dir.is_dir():
        for p in tests_dir.rglob("test_*.py"):
            if p.is_file():
                return True
    for p in proj.rglob("test_*.py"):
        if p.is_file() and "node_modules" not in p.parts:
            return True
    return False


def _service_slug_from_scope(scope_rel: str) -> str:
    parts = _norm_rel(scope_rel).split("/")
    return parts[-1].replace("-", "_") if parts else "app"


def ensure_pytest_bootstrap(
    workspace_root: str | Path | None,
    scope_rel: str,
    *,
    goal: str = "",
) -> list[str]:
    """Test yoksa FastAPI projelerine minimal pytest iskeleti yazar."""
    if not _goal_wants_tests(goal):
        return []
    if _scope_has_tests(workspace_root, scope_rel):
        return []
    proj = _scope_project_dir(workspace_root, scope_rel)
    if proj is None:
        return []
    from ilim_assistant.motorlar.programlama_faz7 import detect_run_profile

    profile = detect_run_profile(workspace_root, scope_rel)
    if not profile or profile.get("profile_id") != "fastapi_api":
        return []
    mod = _service_slug_from_scope(scope_rel)
    written: list[str] = []
    tests_dir = proj / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    test_rel = f"{_norm_rel(scope_rel)}/tests/test_health.py"
    test_path = proj / "tests" / "test_health.py"
    if not test_path.is_file():
        test_path.write_text(
            f'''"""pytest — {scope_rel} health."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok() -> None:
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") == "true"
    assert data.get("service") == "{mod}"


def test_health_has_version() -> None:
    r = client.get("/health")
    data = r.json()
    assert "version" in data and str(data.get("version", "")).strip()
''',
            encoding="utf-8",
        )
        written.append(test_rel)
    req = proj / "requirements.txt"
    if req.is_file():
        body = req.read_text(encoding="utf-8", errors="replace")
        if "httpx" not in body.lower():
            req.write_text(body.rstrip() + "\nhttpx>=0.27\n", encoding="utf-8")
            written.append(f"{_norm_rel(scope_rel)}/requirements.txt")
    return written


def _run_pytest_in_scope(
    workspace_root: str | Path | None,
    scope_rel: str,
) -> ExecReport | None:
    proj = _scope_project_dir(workspace_root, scope_rel)
    if proj is None:
        return None
    from ilim_assistant.approved_executor import run_argv

    code, out, err = run_argv(
        ["python", "-m", "pytest", "-q", "--tb=short"],
        timeout_sec=300,
        cwd=str(proj),
    )
    combined = "\n".join(x for x in (out, err) if x).strip()
    if code == _PYTEST_NO_TESTS_EXIT:
        return ExecReport(
            preset="pytest_scope",
            exit_code=code,
            output=(
                combined
                + "\n[pytest exit=5: proje altında test_*.py yok — tests/ iskeleti gerekli]"
            ),
        )
    return ExecReport(
        preset="pytest_scope",
        exit_code=code,
        output=combined[:16000],
    )


def run_project_verify(
    workspace_root: str | Path | None,
    scope_rel: str,
    *,
    goal: str = "",
) -> ExecReport | None:
    """projects/<ad>/ içinde pytest; yoksa iskelet + smoke yedek."""
    from ilim_assistant.motorlar.programlama_faz7 import (
        detect_run_profile,
        run_project_profile,
    )

    ensure_pytest_bootstrap(workspace_root, scope_rel, goal=goal)

    if _scope_has_tests(workspace_root, scope_rel):
        rep = _run_pytest_in_scope(workspace_root, scope_rel)
        if rep and (rep.ok or rep.exit_code != _PYTEST_NO_TESTS_EXIT):
            return rep
        if rep and rep.exit_code == _PYTEST_NO_TESTS_EXIT:
            ensure_pytest_bootstrap(workspace_root, scope_rel, goal="pytest")
            rep2 = _run_pytest_in_scope(workspace_root, scope_rel)
            if rep2:
                return rep2

    profile = detect_run_profile(workspace_root, scope_rel)
    if profile:
        result = run_project_profile(
            workspace_root,
            scope_rel,
            smoke_only=True,
        )
        ok = bool(result.get("ok"))
        out = str(result.get("output") or result.get("detail") or "")
        hint = ""
        if _goal_wants_tests(goal) and not _scope_has_tests(
            workspace_root, scope_rel
        ):
            hint = "\n[Test yok — smoke OK sayıldı; tests/test_health.py eklenmeli]"
        return ExecReport(
            preset=str(result.get("profile_id") or "project_smoke"),
            exit_code=0 if ok else 1,
            output=(out + hint)[:16000],
        )
    return _run_pytest_in_scope(workspace_root, scope_rel)


def run_scoped_verify(
    workspace_root: str | Path | None,
    scope_rel: str,
    *,
    goal: str = "",
) -> ExecReport | None:
    return run_project_verify(workspace_root, scope_rel, goal=goal)


def format_turn_report(
    *,
    turn: int,
    max_turns: int,
    summary: ToolRunSummary,
    verify: ExecReport | None,
    elapsed_sec: float,
) -> str:
    writes = [w.path for w in summary.writes if w.ok and w.path]
    lines = [
        f"**Tur {turn}/{max_turns}** ({elapsed_sec:.1f}s)",
        f"Yazılan: {len(writes)} dosya",
    ]
    if writes:
        for p in writes[:8]:
            lines.append(f"  · `{p}`")
        if len(writes) > 8:
            lines.append("  · …")
    if verify is None:
        lines.append("Doğrulama: atlandı (workspace yok)")
    elif verify.ok:
        lines.append(f"Doğrulama: OK ({verify.preset})")
    else:
        lines.append(f"Doğrulama: kırmızı ({verify.preset}, exit={verify.exit_code})")
    return "\n".join(lines)


def format_final_agent_report(
    task: CodeAgentTask,
    *,
    turns_used: int,
    success: bool,
    turn_reports: list[str],
    total_sec: float,
) -> str:
    lines = [
        "Ümit abi, **otonom görev raporu** (Faz 14)",
        "",
        f"Proje: `{task.scope_rel}`",
        f"Hedef: {task.goal}",
        f"Tur: {turns_used} · Süre: {total_sec:.1f}s",
        f"Sonuç: **{'tamam' if success else 'kırmızı / limit'}**",
        "",
    ]
    for tr in turn_reports:
        lines.append(tr)
        lines.append("")
    lines.append(f"({FAZ14_VERSION})")
    return "\n".join(lines)


def faz14_directive() -> str:
    base = (
        "[OTONOM GÖREV — Faz 14]\n"
        "Başlat: `görev:` / `iş:` / `yap:` veya doğal cümle — örn. "
        "`görev: benim-api health endpointine versiyon ekle ve test geçir`\n"
        "Durdur: `görev durdur` · Durum: `görev durum`\n"
    )
    try:
        from ilim_assistant.motorlar.programlama_faz19 import faz19_directive

        return base + faz19_directive()
    except Exception:
        return base


def _read_scope_snippets(
    workspace_root: str | Path | None,
    scope_rel: str,
    *,
    max_files: int = 4,
    max_chars: int = 6000,
) -> str:
    """Görev turu için kısa dosya önizlemesi (devasa bağlam yerine)."""
    from ilim_assistant.motorlar.programlama_faz13 import detect_entrypoints, scan_project_files
    from ilim_assistant.motorlar.programlama_motoru import ProgramlamaAraclari

    scan = scan_project_files(workspace_root, scope_rel, max_files=80)
    if not scan.get("ok"):
        return ""
    entries = scan.get("entries") or []
    rels: list[str] = []
    for ep in detect_entrypoints(scope_rel, entries):
        if ep not in rels:
            rels.append(ep)
    code_ext = (".py", ".js", ".jsx", ".ts", ".tsx", ".html")
    for ent in entries:
        rel = str(ent.get("rel") or "")
        if rel.endswith(code_ext) and rel not in rels:
            rels.append(rel)
        if len(rels) >= max_files + 4:
            break
    rels = rels[:max_files]

    tools = ProgramlamaAraclari(workspace_root)
    if tools.root is None:
        return ""
    blocks: list[str] = []
    used = 0
    for rel in rels:
        if used >= max_chars:
            break
        rep = tools.read(rel, max_chars=max_chars - used)
        if rep.ok and rep.content.strip():
            chunk = rep.content.strip()
            blocks.append(f"=== {rel} ===\n{chunk}")
            used += len(chunk)
    return "\n\n".join(blocks)


def _is_llm_failure_reply(text: str) -> bool:
    low = _ascii_fold(text or "")
    return (
        "yanit uretemedi" in low
        or "kotasi" in low
        or "rate limit" in low
        or ("programlama motoru" in low and "denenen" in low)
        or "gemini kotasi" in low
    )


def _stream_agent_llm_turn(
    *,
    agent_system: str,
    round_payload: str,
    model: str,
    active_prior: list,
    message: str,
    turn_plan: Any | None,
) -> tuple[str, list[str]]:
    """LLM akışı; Gemini kota/hata ise Groq (sonra kod) ile tekrar dener."""
    from ilim_assistant.llm_brain import select_brain_chain, stream_chat_with_brain

    profiles_tried: list[str] = []
    body = ""

    def _collect() -> None:
        nonlocal body
        sel = select_brain_chain(
            message=message,
            mode_norm="programlama",
            coding_mode=True,
            question_plan=turn_plan,
            legacy_model=model,
        )
        for e in sel.chain:
            if e.profile_id not in profiles_tried:
                profiles_tried.append(e.profile_id)
        body = ""
        for piece in stream_chat_with_brain(
            agent_system,
            round_payload,
            model=model,
            prior_messages=active_prior,
            mode_norm="programlama",
            coding_mode=True,
            message=message,
            question_plan=turn_plan,
        ):
            body += piece

    try:
        from ilim_assistant.motorlar.programlama_faz39 import (
            programming_brain_chain_for_task,
            task_brain_profile_override,
        )

        override = task_brain_profile_override()
        preferred = programming_brain_chain_for_task()
        if override and override not in preferred:
            preferred = [override] + preferred
    except Exception:
        try:
            from ilim_assistant.motorlar.programlama_faz19 import code_agent_brain_profiles

            preferred = code_agent_brain_profiles()
        except Exception:
            preferred = ["groq", "kod", "denge"]

    for profile in preferred:
        old = os.environ.get("RUZGAR_BRAIN_PROFILE")
        os.environ["RUZGAR_BRAIN_PROFILE"] = profile
        try:
            _collect()
            if body.strip() and not _is_llm_failure_reply(body):
                if f"{profile}(oncelik)" not in profiles_tried:
                    profiles_tried.append(f"{profile}(oncelik)")
                return body, profiles_tried
        finally:
            if old is None:
                os.environ.pop("RUZGAR_BRAIN_PROFILE", None)
            else:
                os.environ["RUZGAR_BRAIN_PROFILE"] = old

    _collect()
    if body.strip() and not _is_llm_failure_reply(body):
        return body, profiles_tried

    for fallback in ("groq", "kod", "denge"):
        if fallback in preferred:
            continue
        old = os.environ.get("RUZGAR_BRAIN_PROFILE")
        os.environ["RUZGAR_BRAIN_PROFILE"] = fallback
        try:
            _collect()
            if body.strip() and not _is_llm_failure_reply(body):
                profiles_tried.append(f"{fallback}(zorla)")
                return body, profiles_tried
        finally:
            if old is None:
                os.environ.pop("RUZGAR_BRAIN_PROFILE", None)
            else:
                os.environ["RUZGAR_BRAIN_PROFILE"] = old

    return body, profiles_tried


def build_compact_agent_system(
    workspace_root: str | Path | None,
    task: CodeAgentTask,
) -> str:
    """LLM için kısa sistem bağlamı (Faz 21 hafif bağlam)."""
    try:
        from ilim_assistant.motorlar.programlama_faz21 import build_light_programming_context

        return build_light_programming_context(
            task.goal,
            workspace_root=workspace_root,
            active_file=None,
            include_tools=False,
        ).split("[Kullanıcı]")[0].strip() + (
            "\n\n[ZORUNLU — OTONOM GÖREV]\n"
            f"Proje: `{task.scope_rel}`\n"
            "Her turda `ruzgar-tool` veya `@@write` ile dosya yaz.\n"
            "Plan max 3 madde.\n"
        )
    except Exception:
        pass
    from ilim_assistant.prompts import pick_system

    lines = [
        pick_system(True, "programlama").strip(),
        faz14_directive().strip(),
    ]
    try:
        from ilim_assistant.motorlar.programlama_faz13 import build_project_summary_block

        summary = build_project_summary_block(
            workspace_root, scope_rel=task.scope_rel
        ).strip()
        if summary:
            lines.append(summary)
    except Exception:
        pass
    snippets = _read_scope_snippets(workspace_root, task.scope_rel)
    if snippets:
        lines.append("[PROJE DOSYALARI — ön okuma]\n" + snippets)
    lines.append(
        "\n[ZORUNLU ÇIKTI]\n"
        "Yanıtta mutlaka `@@write projects/.../dosya` + kod bloğu veya ruzgar-tool kullan. "
        "Planı 5 satırdan kısa tut.\n"
    )
    return "\n\n".join(lines)


def iter_code_agent_turn_events(
    *,
    message: str,
    req: Any,
    system: str,
    user_payload: str,
    model: str,
    prior: list,
    mode_norm: str,
    coding: bool,
    turn_plan: Any | None,
    hits: list,
    new_wake: bool,
    orch: dict[str, Any] | None,
    delegated_from_genel: bool = False,
) -> Iterator[dict[str, Any]]:
    """desktop_server SSE — çok turlu görev döngüsü."""
    from ilim_assistant.llm_brain import select_brain_chain, stream_chat_with_brain
    from ilim_assistant.motorlar.programlama_faz10 import (
        process_assistant_reply_patches,
        resolve_scope_rel,
    )
    from ilim_assistant.motorlar.programlama_faz11 import merge_orchestra_programlama
    from ilim_assistant.motorlar.programlama_faz13 import build_project_summary_block
    from ilim_assistant.text_encoding import finalize_assistant_reply
    from ilim_assistant.chat_core import rag_footer

    norm_msg = message
    try:
        from ilim_assistant.motorlar.programlama_faz33 import normalize_for_agent

        norm_msg = normalize_for_agent(
            message,
            mode_norm,
            workspace_root=req.workspace_root,
            active_file=getattr(req, "programlama_active_file", None),
        )
    except Exception:
        try:
            from ilim_assistant.motorlar.programlama_faz19 import normalize_agent_message

            norm_msg = normalize_agent_message(message, mode_norm=mode_norm)
        except Exception:
            pass

    task = parse_code_agent_task(norm_msg)
    if task is None:
        try:
            from ilim_assistant.motorlar.programlama_faz20 import resolve_agent_task

            task = resolve_agent_task(
                message,
                req.workspace_root,
                active_file=getattr(req, "programlama_active_file", None),
                mode_norm=mode_norm,
            )
        except Exception:
            task = None
    if task is None:
        yield {
            "type": "error",
            "text": (
                "Görev ayrıştırılamadı — `projects/<proje>/` açın veya "
                "«benim-api health'e version ekle» yazın."
            ),
        }
        return

    workspace = req.workspace_root
    try:
        from ilim_assistant.motorlar.programlama_faz39 import code_agent_max_turns_effective

        max_turns = code_agent_max_turns_effective()
    except Exception:
        max_turns = code_agent_max_turns()
    t0 = time.perf_counter()
    _budget_tracker = None
    try:
        from ilim_assistant.motorlar.programlama_faz41 import create_budget_tracker

        _budget_tracker = create_budget_tracker(t0)
    except Exception:
        _budget_tracker = None
    turn_reports: list[str] = []
    last_fail_snippet = ""
    reply_body = ""
    success = False
    active_prior: list = list(prior) if prior else []
    loop_state = None
    try:
        from ilim_assistant.motorlar.programlama_faz19 import AgentLoopState

        loop_state = AgentLoopState()
    except Exception:
        loop_state = None

    _exit_task_mode = None
    try:
        from ilim_assistant.motorlar.programlama_faz23 import (
            code_agent_budget_sec,
            enter_task_mode,
            exit_task_mode,
            format_task_mode_status,
        )

        enter_task_mode()
        _exit_task_mode = exit_task_mode
    except Exception:
        pass

    save_agent_state(
        workspace,
        {
            "status": "running",
            "scope_rel": task.scope_rel,
            "goal": task.goal,
            "turn": 0,
            "max_turns": max_turns,
            "stop_requested": False,
            "started_at": time.time(),
            "version": FAZ14_VERSION,
        },
    )

    try:
        budget_hint = int(code_agent_budget_sec())
    except Exception:
        budget_hint = 120

    step_tracker = None
    try:
        from ilim_assistant.motorlar.programlama_faz24 import create_tracker

        step_tracker = create_tracker(
            scope_rel=task.scope_rel,
            goal=task.goal,
            max_turns=max_turns,
            budget_sec=float(budget_hint),
        )
    except Exception:
        step_tracker = None

    yield {
        "type": "status",
        "text": (
            f"Otonom görev başladı — `{task.scope_rel}` "
            f"(max {max_turns} tur, {budget_hint} sn)…"
        ),
    }
    try:
        from ilim_assistant.motorlar.programlama_faz23 import format_task_mode_status

        try:
            from ilim_assistant.motorlar.programlama_faz41 import (
                format_long_task_status,
                long_task_enabled,
            )

            if long_task_enabled():
                yield {"type": "status", "text": format_long_task_status(task.scope_rel)}
            else:
                yield {
                    "type": "status",
                    "text": format_task_mode_status(task.scope_rel, float(budget_hint)),
                }
        except Exception:
            yield {
                "type": "status",
                "text": format_task_mode_status(task.scope_rel, float(budget_hint)),
            }
    except Exception:
        pass
    yield {
        "type": "meta",
        "code_agent": {
            "phase": "started",
            "scope_rel": task.scope_rel,
            "goal": task.goal,
            "max_turns": max_turns,
        },
    }
    if delegated_from_genel:
        try:
            from ilim_assistant.motorlar.programlama_faz38 import delegation_status_text

            yield {
                "type": "status",
                "text": delegation_status_text(
                    scope_rel=task.scope_rel,
                    goal=task.goal,
                ),
            }
            yield {
                "type": "meta",
                "programlama_delegated": True,
                "delegation_chain": "faz35-37-38",
            }
        except Exception:
            pass

    def _emit_agent_step(raw: dict[str, Any] | None) -> dict[str, Any] | None:
        if raw is None:
            return None
        ev = raw
        try:
            from ilim_assistant.motorlar.programlama_faz38 import maybe_enrich_yield

            ev = maybe_enrich_yield(ev, workspace, scope_rel=task.scope_rel) or ev
        except Exception:
            pass
        try:
            if _budget_tracker is not None:
                ev = _budget_tracker.enrich_sse(ev) or ev
        except Exception:
            pass
        return ev

    agent_system = build_compact_agent_system(workspace, task)
    try:
        from ilim_assistant.motorlar.programlama_faz34 import augment_agent_system

        agent_system = augment_agent_system(agent_system)
    except Exception:
        pass
    brain_sel = select_brain_chain(
        message=message,
        mode_norm=mode_norm,
        coding_mode=True,
        question_plan=turn_plan,
        legacy_model=model,
    )
    brain_chain = [e.profile_id for e in brain_sel.chain]
    yield {
        "type": "meta",
        "brain": brain_sel.to_public_dict(),
        "code_agent": {
            "phase": "brain",
            "scope_rel": task.scope_rel,
            "chain": brain_chain,
        },
    }
    if step_tracker is not None:
        yield _emit_agent_step(step_tracker.on_started(brain_chain=brain_chain))

    for turn in range(1, max_turns + 1):
        if is_stop_requested(workspace):
            yield {"type": "status", "text": "Görev durduruldu (Ümit abi isteği)."}
            break

        try:
            from ilim_assistant.motorlar.programlama_faz19 import budget_exceeded, code_agent_budget_sec

            if budget_exceeded(t0):
                yield {
                    "type": "status",
                    "text": (
                        f"Süre sınırı ({int(code_agent_budget_sec())} sn) doldu — "
                        "görev durdu (Faz 19)."
                    ),
                }
                break
        except Exception:
            pass

        save_agent_state(
            workspace,
            {
                **load_agent_state(workspace),
                "status": "running",
                "turn": turn,
                "scope_rel": task.scope_rel,
                "goal": task.goal,
            },
        )

        _tur_status = f"Görev tur {turn}/{max_turns} — plan / patch…"
        if _budget_tracker is not None:
            _tur_status += _budget_tracker.status_suffix()
        yield {"type": "status", "text": _tur_status}
        if step_tracker is not None:
            yield _emit_agent_step(step_tracker.on_turn_start(turn))
            yield _emit_agent_step(step_tracker.on_llm_start(turn))

        turn_user = build_agent_turn_user_message(
            task,
            turn=turn,
            max_turns=max_turns,
            failure_snippet=last_fail_snippet,
        )
        try:
            from ilim_assistant.motorlar.programlama_faz34 import augment_turn_user_message

            turn_user = augment_turn_user_message(
                turn_user, turn=turn, goal=task.goal
            )
        except Exception:
            pass
        round_payload = turn_user

        round_body = ""
        t_turn = time.perf_counter()
        llm_body, profiles_used = _stream_agent_llm_turn(
            agent_system=agent_system,
            round_payload=round_payload,
            model=model,
            active_prior=active_prior,
            message=message,
            turn_plan=turn_plan,
        )
        if _is_llm_failure_reply(llm_body) and not llm_body.strip():
            yield {
                "type": "status",
                "text": (
                    "Gemini/Groq yanıt vermedi — GROQ_API_KEY veya "
                    "RUZGAR_CODE_AGENT_BRAIN=groq,kod deneyin."
                ),
            }
        round_body = llm_body
        if step_tracker is not None:
            yield _emit_agent_step(step_tracker.on_llm_done(turn, llm_body))
        _tool_res: list = []
        _faz34_violations: list[str] = []
        try:
            from ilim_assistant.motorlar.programlama_faz40 import (
                augment_reply_tools,
                structured_tools_enabled,
            )

            if structured_tools_enabled():
                round_body, _tool_res, _tool_block = augment_reply_tools(
                    llm_body,
                    workspace,
                    scope_rel=task.scope_rel,
                    goal=task.goal,
                )
                if not _tool_res:
                    from ilim_assistant.motorlar.programlama_faz40 import (
                        run_structured_tool_loop,
                    )

                    _st_text, _st_res, _st_block = run_structured_tool_loop(
                        system=agent_system,
                        user=f"Hedef: {task.goal}\nProje: {task.scope_rel}",
                        workspace_root=workspace,
                        scope_rel=task.scope_rel,
                        goal=task.goal,
                    )
                    if _st_res:
                        _tool_res = _st_res
                        _tool_block = _st_block
                        if _st_text:
                            llm_body = (llm_body or "").rstrip() + "\n\n" + _st_text
                            round_body = llm_body.rstrip() + "\n\n" + _tool_block
                elif _tool_block:
                    round_body = round_body if round_body != llm_body else (
                        llm_body.rstrip() + "\n\n" + _tool_block
                    )
            else:
                from ilim_assistant.motorlar.programlama_faz20 import run_tools_from_reply

                _tool_res, _tool_block = run_tools_from_reply(
                    llm_body,
                    workspace,
                    scope_rel=task.scope_rel,
                )
                if _tool_block:
                    round_body = llm_body.rstrip() + "\n\n" + _tool_block
            if _tool_block or _tool_res:
                yield {
                    "type": "status",
                    "text": (
                        f"Tur {turn}: {len(_tool_res)} araç "
                        f"(Faz {'40' if structured_tools_enabled() else '20'})."
                    ),
                }
            if step_tracker is not None and _tool_res:
                yield _emit_agent_step(step_tracker.on_tools(turn, len(_tool_res)))
        except Exception:
            pass
        try:
            from ilim_assistant.motorlar.programlama_faz34 import (
                apply_turn_tool_first,
                build_tool_first_nudge,
            )

            _tool_res, _faz34_block, _faz34_violations = apply_turn_tool_first(
                _tool_res,
                llm_body,
                workspace,
                task.scope_rel,
                task.goal,
                turn,
            )
            if _faz34_block:
                round_body = (round_body or llm_body).rstrip() + "\n\n" + _faz34_block
                yield {
                    "type": "status",
                    "text": f"Tur {turn}: Faz 34 araç-öncelik tamamlandı.",
                }
            if step_tracker is not None and _tool_res:
                yield _emit_agent_step(step_tracker.on_tools(turn, len(_tool_res)))
        except Exception:
            _faz34_violations = []
        _faz35_followup = False
        _faz38_nested = 0
        _tool_block_combined = ""
        try:
            from ilim_assistant.motorlar.programlama_faz20 import run_tools_from_reply as _rtfr

            _, _tb0 = _rtfr(llm_body, workspace, scope_rel=task.scope_rel)
            _tool_block_combined = _tb0 or ""
        except Exception:
            pass
        if not _tool_block_combined and round_body:
            idx = round_body.find("[ARAÇ SONUÇLARI]")
            if idx >= 0:
                _tool_block_combined = round_body[idx:]
            idx2 = round_body.find("[Faz 34")
            if idx2 >= 0 and idx2 < (idx if idx >= 0 else len(round_body)):
                _tool_block_combined = round_body[idx2:]
        try:
            from ilim_assistant.motorlar.programlama_faz38 import run_nested_tool_loop

            llm_body, round_body, _tool_res, _f35_profiles, _faz38_nested = (
                run_nested_tool_loop(
                    llm_body=llm_body,
                    round_body=round_body,
                    tool_results=_tool_res,
                    tool_block=_tool_block_combined,
                    goal=task.goal,
                    turn=turn,
                    agent_system=agent_system,
                    round_payload=round_payload,
                    model=model,
                    active_prior=active_prior,
                    message=message,
                    turn_plan=turn_plan,
                    workspace_root=workspace,
                    scope_rel=task.scope_rel,
                    stream_fn=_stream_agent_llm_turn,
                )
            )
            _faz35_followup = _faz38_nested > 0
            if _faz35_followup:
                yield {
                    "type": "status",
                    "text": (
                        f"Tur {turn}: Faz 38 iç araç döngüsü "
                        f"({_faz38_nested} takip LLM)."
                    ),
                }
                if _f35_profiles:
                    profiles_used = list(profiles_used) + _f35_profiles
                yield {"type": "token", "text": "\n\n[Faz 38 tur-içi takip]\n"}
            try:
                from ilim_assistant.motorlar.programlama_faz39 import (
                    run_write_mandate_followup,
                )

                llm_body, round_body, _tool_res, _f39_prof, _faz39_mandate = (
                    run_write_mandate_followup(
                        llm_body=llm_body,
                        round_body=round_body,
                        tool_results=_tool_res,
                        tool_block=_tool_block_combined,
                        goal=task.goal,
                        turn=turn,
                        scope_rel=task.scope_rel,
                        agent_system=agent_system,
                        round_payload=round_payload,
                        model=model,
                        active_prior=active_prior,
                        message=message,
                        turn_plan=turn_plan,
                        workspace_root=workspace,
                        stream_fn=_stream_agent_llm_turn,
                    )
                )
                if _faz39_mandate:
                    _faz35_followup = True
                    yield {
                        "type": "status",
                        "text": f"Tur {turn}: Faz 39 zorunlu yazım turu.",
                    }
                    if _f39_prof:
                        profiles_used = list(profiles_used) + _f39_prof
                    yield {"type": "token", "text": "\n\n[Faz 39 zorunlu yazım]\n"}
            except Exception:
                pass
        except Exception:
            _faz35_followup = False
            _faz38_nested = 0
        reply_body += round_body
        if llm_body.strip():
            yield {"type": "token", "text": llm_body}
        yield {
            "type": "meta",
            "code_agent": {
                "phase": "llm_profiles",
                "turn": turn,
                "profiles": profiles_used,
            },
        }

        summ, _ = apply_assistant_reply_tools(
            round_body,
            workspace,
            run_pytest=False,
        )
        try:
            from ilim_assistant.motorlar.programlama_faz23 import apply_agent_turn_patches

            scope_turn = resolve_scope_rel(
                workspace,
                active_file=getattr(req, "programlama_active_file", None),
            ) or task.scope_rel
            turn_patch = apply_agent_turn_patches(
                round_body,
                workspace,
                scope_rel=scope_turn,
            )
            if turn_patch.get("action") == "applied" and turn_patch.get("applied"):
                for rel in turn_patch.get("applied") or []:
                    if rel and not any(w.path == rel and w.ok for w in summ.writes):
                        from ilim_assistant.motorlar.programlama_motoru import WriteReport

                        summ.writes.append(
                            WriteReport(path=rel, ok=True, detail="Faz 23 otomatik patch")
                        )
        except Exception:
            pass
        verify = run_project_verify(
            workspace,
            task.scope_rel,
            goal=task.goal,
        )

        writes_ok = len([w for w in summ.writes if w.ok])
        ok = verify.ok if verify else bool(writes_ok)
        elapsed = time.perf_counter() - t_turn
        if step_tracker is not None:
            write_paths = [w.path for w in summ.writes if w.ok and w.path]
            yield _emit_agent_step(step_tracker.on_writes(turn, writes_ok, write_paths))
            yield _emit_agent_step(
                step_tracker.on_verify(
                    turn,
                    ok,
                    (verify.output if verify else "")[:80],
                )
            )

        try:
            from ilim_assistant.motorlar.programlama_faz37 import record_turn_metrics

            record_turn_metrics(
                workspace,
                scope_rel=task.scope_rel,
                turn=turn,
                tool_results=_tool_res,
                violations=_faz34_violations,
                mid_turn_followup=_faz35_followup,
                verify_ok=bool(verify.ok if verify else False),
                writes_ok=writes_ok,
            )
        except Exception:
            pass

        if loop_state is not None:
            try:
                from ilim_assistant.motorlar.programlama_faz19 import (
                    classify_llm_turn,
                    should_abort_loop,
                )

                kind = classify_llm_turn(
                    llm_body,
                    writes_ok,
                    is_failure_fn=_is_llm_failure_reply,
                )
                loop_state.record_turn(wrote_files=writes_ok, llm_kind=kind)
                try:
                    from ilim_assistant.motorlar.programlama_faz39 import (
                        should_abort_loop_relaxed,
                    )

                    abort, reason = should_abort_loop_relaxed(
                        loop_state,
                        last_tool_results=_tool_res,
                        max_turns=max_turns,
                    )
                except Exception:
                    abort, reason = should_abort_loop(loop_state)
                if not abort:
                    try:
                        from ilim_assistant.motorlar.programlama_faz41 import (
                            should_abort_empty_streak,
                        )

                        abort, reason = should_abort_empty_streak(
                            loop_state,
                            last_tool_results=_tool_res,
                        )
                    except Exception:
                        pass
                if abort and not ok:
                    yield {"type": "status", "text": reason}
                    break
            except Exception:
                pass

        tr = format_turn_report(
            turn=turn,
            max_turns=max_turns,
            summary=summ,
            verify=verify,
            elapsed_sec=elapsed,
        )
        turn_reports.append(tr)

        save_agent_state(
            workspace,
            {
                **load_agent_state(workspace),
                "last_verify_ok": ok,
                "turn": turn,
            },
        )

        yield {
            "type": "meta",
            "code_agent": {
                "phase": "turn_done",
                "turn": turn,
                "verify_ok": ok,
                "writes": len([w for w in summ.writes if w.ok]),
            },
        }
        yield {"type": "status", "text": tr[:1200]}

        try:
            from ilim_assistant.motorlar.programlama_faz23 import (
                task_mode_active,
                task_success_met,
            )

            if task_mode_active():
                v_ok = bool(verify.ok if verify else False)
                if task_success_met(verify_ok=v_ok, writes_ok=writes_ok):
                    st47 = load_agent_state(workspace)
                    strict_verify = bool(
                        st47.get("proje_uret")
                        and st47.get("require_verify_pass")
                    )
                    if strict_verify and not v_ok:
                        yield {
                            "type": "status",
                            "text": (
                                "Faz 47: pytest yeşil olmadan proje üretimi "
                                "bitmiyor — düzeltme turu…"
                            ),
                        }
                    else:
                        success = True
                        break
            elif ok:
                success = True
                break
        except Exception:
            if ok:
                success = True
                break

        if writes_ok == 0:
            yield {
                "type": "status",
                "text": "Tur atlandı — model @@write yazmadı; tekrar deneniyor…",
            }

        if turn >= max_turns:
            break

        last_fail_snippet = (verify.output if verify else "") or "Doğrulama başarısız."
        snippet = last_fail_snippet
        fail_msg = build_agent_turn_user_message(
            task,
            turn=turn + 1,
            max_turns=max_turns,
            failure_snippet=snippet,
        )
        try:
            from ilim_assistant.motorlar.programlama_faz34 import (
                augment_turn_user_message,
                build_tool_first_nudge,
            )

            fail_msg = augment_turn_user_message(
                fail_msg, turn=turn + 1, goal=task.goal
            )
            nudge = build_tool_first_nudge(_faz34_violations, turn + 1)
            if nudge:
                fail_msg = fail_msg.rstrip() + "\n\n" + nudge
        except Exception:
            pass
        active_prior = list(active_prior) + [
            {"role": "assistant", "content": round_body},
            {"role": "user", "content": fail_msg},
        ]

    total_sec = time.perf_counter() - t0
    if step_tracker is not None:
        yield _emit_agent_step(
            step_tracker.on_finish(
                success=success,
                elapsed_sec=total_sec,
                turns_used=len(turn_reports),
            )
        )
    report = format_final_agent_report(
        task,
        turns_used=len(turn_reports),
        success=success,
        turn_reports=turn_reports,
        total_sec=total_sec,
    )
    reply_body = reply_body.rstrip() + "\n\n" + report
    if delegated_from_genel:
        try:
            from ilim_assistant.motorlar.programlama_faz38 import delegation_footer

            reply_body += delegation_footer(
                workspace,
                scope_rel=task.scope_rel,
                success=success,
                turns_used=len(turn_reports),
            )
        except Exception:
            pass
    try:
        from ilim_assistant.motorlar.programlama_faz32 import append_post_task_to_reply

        st = load_agent_state(workspace)
        verify_ok = bool(success and st.get("last_verify_ok"))
        reply_body = append_post_task_to_reply(
            reply_body,
            workspace,
            task.scope_rel,
            success=success,
            verify_ok=verify_ok,
            elapsed_sec=total_sec,
        )
    except Exception:
        pass

    clear_agent_state(workspace)

    try:
        if _exit_task_mode is not None:
            _exit_task_mode()
    except Exception:
        pass

    footer = rag_footer(hits)
    body_fixed = finalize_assistant_reply(reply_body)
    code_patch_meta: dict[str, Any] = {}
    try:
        scope = resolve_scope_rel(
            workspace,
            active_file=getattr(req, "programlama_active_file", None),
        ) or task.scope_rel
        try:
            from ilim_assistant.motorlar.programlama_faz23 import finalize_agent_patches

            code_patch_meta = finalize_agent_patches(
                reply_body,
                workspace,
                scope_rel=scope,
                skip_if_debug_loop=False,
            )
        except Exception:
            code_patch_meta = process_assistant_reply_patches(
                reply_body,
                workspace,
                scope_rel=scope,
                skip_if_debug_loop=True,
            )
        patch_footer = str(code_patch_meta.get("footer") or "")
        if patch_footer:
            body_fixed = body_fixed.rstrip() + patch_footer
    except Exception:
        pass

    full_out = body_fixed + footer
    done: dict[str, Any] = {
        "type": "done",
        "full_reply": full_out,
        "user_message": message,
        "new_wake_used": new_wake,
        "code_agent": {
            "success": success,
            "scope_rel": task.scope_rel,
            "turns": len(turn_reports),
            "elapsed_sec": total_sec,
        },
    }
    if orch is not None or step_tracker is not None:
        try:
            base_orch = dict(orch or {})
            if orch is not None:
                base_orch = merge_orchestra_programlama(
                    base_orch,
                    message,
                    workspace,
                    active_file=getattr(req, "programlama_active_file", None),
                    phase="done",
                    patch_meta=code_patch_meta,
                )
            if step_tracker is not None:
                base_orch["agent_steps"] = step_tracker.snapshot()
            done["orchestra"] = base_orch
        except Exception:
            if step_tracker is not None:
                done["orchestra"] = {
                    **(orch or {}),
                    "agent_steps": step_tracker.snapshot(),
                }
            elif orch is not None:
                done["orchestra"] = orch
    if code_patch_meta and code_patch_meta.get("action") not in ("skip", "none"):
        done["code_patch"] = {
            "action": code_patch_meta.get("action"),
            "applied": list(code_patch_meta.get("applied") or []),
            "errors": list(code_patch_meta.get("errors") or []),
            "items": list(code_patch_meta.get("items") or []),
        }
    if delegated_from_genel:
        done["programlama_delegated"] = True
    yield done
