# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 85: Yerel öncelik + LLM'siz hızlı görev (Ümit planı).

- Kod ajanında önce yerel Ollama (kod/denge), Groq/Gemini yedek.
- Basit görevlerde LLM turu atlanır; kırmızıysa varsayılan olarak ajan döngüsüne düşer.
"""

from __future__ import annotations

import os
import re
import time
import unicodedata
from pathlib import Path
from typing import Any, Callable, Iterator

FAZ85_VERSION = "programlama-faz85-v3-2026-05-27"

_MAIN_CANDIDATES = (
    "app/main.py",
    "main.py",
    "src/main.py",
)
_INLINE_RETURN_RE = re.compile(
    r"(def\s+health\s*\([^)]*\)\s*(?:->[^:]+)?:\s*return\s+)(\{[^}]+\})",
    re.I | re.M,
)
_MULTILINE_RETURN_RE = re.compile(
    r"(def\s+health\s*\([^)]*\)\s*(?:->[^:]+)?:\s*\n\s*return\s+)(\{[^}]+\})",
    re.I | re.M,
)
_CREATE_GOAL_RE = re.compile(
    r"(?:yeni\s+proje|sifirdan|sıfırdan|api\s+yap|site\s+yap|uygulama\s+yap|olustur|oluştur|kur)",
    re.I,
)


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ85", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz85_enabled() -> bool:
    return _enabled()


def local_first_enabled() -> bool:
    return _enabled() and os.environ.get("RUZGAR_PROG_LOCAL_FIRST", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def fallback_to_agent_on_fail() -> bool:
    return os.environ.get("RUZGAR_FAZ85_FALLBACK_ON_FAIL", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _ascii_fold(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def ollama_available() -> bool:
    try:
        from ilim_assistant.llm_ollama import ollama_reachable

        return bool(ollama_reachable())
    except Exception:
        return False


def local_first_brain_chain(chain: list[str]) -> list[str]:
    if not local_first_enabled() or not ollama_available():
        return chain
    priority = ["kod", "denge", "hizli", "groq", "gemini"]
    out: list[str] = []
    for p in priority:
        if p not in out:
            out.append(p)
    for x in chain:
        if x not in out:
            out.append(x)
    return out


def _project_slug_from_scope(scope_rel: str) -> str:
    """projects/ altındaki klasör adı (tire korunur)."""
    parts = (scope_rel or "").strip().replace("\\", "/").rstrip("/").split("/")
    if len(parts) >= 2 and parts[0] == _projects_base():
        return parts[1]
    return parts[-1] if parts else "app"


def _service_slug_from_scope(scope_rel: str) -> str:
    """Health JSON service alanı — Python tanımlayıcı uyumu."""
    return _project_slug_from_scope(scope_rel).replace("-", "_")


def _projects_base() -> str:
    return (
        os.environ.get("RUZGAR_SCAFFOLD_BASE", "projects").strip().replace("\\", "/").strip("/")
        or "projects"
    )


def _scope_project_dir(workspace_root: str | Path | None, scope_rel: str) -> Path | None:
    try:
        from ilim_assistant.motorlar.programlama_motoru import repo_root

        root = repo_root(workspace_root)
        if root is None:
            return None
        scope = (scope_rel or "").strip().replace("\\", "/").rstrip("/")
        if not scope.startswith(_projects_base() + "/") and scope != _projects_base():
            scope = f"{_projects_base()}/{scope.lstrip('/')}"
        proj = root / scope.replace("/", os.sep)
        return proj if proj.is_dir() else None
    except Exception:
        return None


def _find_main_py(workspace_root: str | Path | None, scope_rel: str) -> tuple[str, Path] | None:
    proj = _scope_project_dir(workspace_root, scope_rel)
    if proj is None:
        return None
    scope = (scope_rel or "").strip().replace("\\", "/").rstrip("/")
    if not scope.startswith(_projects_base()):
        scope = f"{_projects_base()}/{scope.lstrip('/')}"
    for rel in _MAIN_CANDIDATES:
        p = proj / rel.replace("/", os.sep)
        if p.is_file():
            return f"{scope}/{rel}", p
    return None


def _goal_wants_tests(goal: str) -> bool:
    low = _ascii_fold(goal)
    return any(k in low for k in ("pytest", "test", "gecir", "geçir", "dogrula", "doğrula"))


def _goal_wants_health_version(goal: str) -> bool:
    low = _ascii_fold(goal)
    has_health = any(k in low for k in ("health", "endpoint", "/health"))
    has_version = any(k in low for k in ("version", "versiyon"))
    return has_health and has_version


def _goal_wants_create(goal: str) -> bool:
    return bool(_CREATE_GOAL_RE.search(_ascii_fold(goal or "")))


def _goal_wants_health_fix(goal: str) -> bool:
    low = _ascii_fold(goal)
    return any(k in low for k in ("duzelt", "düzelt", "fix", "kirmizi", "kırmızı")) and "health" in low


def _extract_version(goal: str) -> str:
    text = goal or ""
    m = re.search(r"version\s*[=:]\s*['\"]?([\w.\-]+)", text, re.I)
    if m:
        return m.group(1)
    m = re.search(r"version\s+['\"]?(\d+(?:\.\d+)*)", text, re.I)
    return m.group(1) if m else "1.0.0"


def _patch_health_return_block(block: str, *, service: str, version: str) -> tuple[str, bool]:
    if not block.strip().startswith("{"):
        return block, False
    if re.search(r"""['"]version['"]\s*:""", block):
        patched, n = re.subn(
            r"""(['"]version['"]\s*:\s*)['"][^'"]*['"]""",
            rf'\1"{version}"',
            block,
            count=1,
        )
        if n and patched != block:
            return patched, True
        return block, False
    inner = block.strip()
    if not inner.endswith("}"):
        return block, False
    body = inner[1:-1].strip()
    if body and not body.endswith(","):
        body += ","
    add = f' "version": "{version}"'
    if "service" not in body and service:
        add = f' "service": "{service}",' + add
    return "{" + body + add + " }", True


def patch_main_py_content(content: str, *, service: str, version: str) -> tuple[str, bool]:
    out = content
    for pat in (_INLINE_RETURN_RE, _MULTILINE_RETURN_RE):
        m = pat.search(out)
        if not m:
            continue
        new_dict, did = _patch_health_return_block(m.group(2), service=service, version=version)
        if did:
            return out[: m.start(2)] + new_dict + out[m.end(2) :], True
    return out, False


def _run_verify_block(
    workspace_root: str | Path | None,
    scope_rel: str,
    goal: str,
    lines: list[str],
) -> tuple[bool, Any | None]:
    from ilim_assistant.motorlar.programlama_faz14 import (
        ensure_pytest_bootstrap,
        run_project_verify,
    )

    boot = ensure_pytest_bootstrap(workspace_root, scope_rel, goal=goal)
    if boot:
        lines.append(f"· test iskeleti: {len(boot)} dosya.")
    verify = run_project_verify(workspace_root, scope_rel, goal=goal)
    verify_ok = bool(verify and verify.ok)
    if verify_ok:
        lines.append(f"· doğrulama OK ({verify.preset}).")
    else:
        code = verify.exit_code if verify else "?"
        lines.append(f"· doğrulama kırmızı (exit={code}).")
    return verify_ok, verify


def _finalize_result(result: dict[str, Any] | None) -> dict[str, Any] | None:
    """Başarısız hızlı yol → ajan döngüsüne düş (E1)."""
    if result is None:
        return None
    if result.get("ok"):
        return result
    if fallback_to_agent_on_fail():
        return None
    return result


def _resolve_preferred_scope(
    workspace_root: str | Path | None,
    scope_rel: str,
    goal: str,
) -> str:
    """Kullanıcı niyetindeki mevcut proje, oturum kapsamından önceliklidir."""
    try:
        from ilim_assistant.motorlar.programlama_faz10 import extract_user_intent_message
        from ilim_assistant.motorlar.programlama_faz14 import parse_code_agent_task

        intent = (extract_user_intent_message(goal) or goal or "").strip()
        task = parse_code_agent_task(intent)
        if task and _scope_project_dir(workspace_root, task.scope_rel) is not None:
            return task.scope_rel
    except Exception:
        pass
    return scope_rel


def _try_scaffold_fastapi(
    workspace_root: str | Path | None,
    scope_rel: str,
    goal: str,
) -> dict[str, Any] | None:
    scope_rel = _resolve_preferred_scope(workspace_root, scope_rel, goal)
    if _scope_project_dir(workspace_root, scope_rel) is not None:
        return None
    if not (_goal_wants_create(goal) or _goal_wants_health_version(goal)):
        return None
    slug = _project_slug_from_scope(scope_rel)
    lines = ["[Faz 85 — şablon — LLM yok]"]
    try:
        from ilim_assistant.motorlar.programlama_faz6 import run_scaffold
        from ilim_assistant.motorlar.programlama_faz47 import infer_template_from_text

        tid = infer_template_from_text(goal) or "fastapi_api"
        sc = run_scaffold(tid, slug, workspace_root, force=False)
        if not sc.get("ok"):
            return {
                "ok": False,
                "writes_ok": 0,
                "verify_ok": False,
                "detail": f"Şablon kurulamadı: {sc.get('error', '?')}",
                "source": "fast_scaffold_faz85",
            }
        n = len(sc.get("written") or [])
        lines.append(f"· `{tid}` şablonu — {n} dosya (`projects/{slug}`).")
        writes_ok = n
    except Exception as exc:
        return None
    hv = _try_health_version(workspace_root, scope_rel, goal)
    if hv is not None:
        lines.append(str(hv.get("detail") or ""))
        writes_ok += int(hv.get("writes_ok") or 0)
        if hv.get("ok"):
            return {
                "ok": True,
                "writes_ok": writes_ok,
                "verify_ok": bool(hv.get("verify_ok")),
                "detail": "\n".join(lines),
                "source": "fast_scaffold_faz85",
            }
        verify_ok = bool(hv.get("verify_ok"))
    else:
        verify_ok, _ = _run_verify_block(workspace_root, scope_rel, goal, lines)
    return {
        "ok": verify_ok,
        "writes_ok": writes_ok,
        "verify_ok": verify_ok,
        "detail": "\n".join(lines),
        "source": "fast_scaffold_faz85",
    }


def _try_fix_health_ok(
    workspace_root: str | Path | None,
    scope_rel: str,
    goal: str,
) -> dict[str, Any] | None:
    if not _goal_wants_health_fix(goal):
        return None
    found = _find_main_py(workspace_root, scope_rel)
    if not found:
        return None
    rel_main, path_main = found
    try:
        original = path_main.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    if not re.search(r"""['"]ok['"]\s*:\s*['"]false['"]""", original, re.I):
        if '"ok": false' not in original.lower() and "'ok': false" not in original.lower():
            return None
    patched = re.sub(
        r"""(['"]ok['"]\s*:\s*)['"]false['"]""",
        r'\1"true"',
        original,
        count=1,
        flags=re.I,
    )
    patched = re.sub(
        r"""(['"]ok['"]\s*:\s*)\bFalse\b""",
        r'\1"true"',
        patched,
        count=1,
    )
    if patched == original:
        return None
    service = _service_slug_from_scope(scope_rel)
    version = _extract_version(goal)
    if _goal_wants_tests(goal):
        patched, _ = patch_main_py_content(
            patched, service=service, version=version
        )
    from ilim_assistant.motorlar.programlama_motoru import ProgramlamaAraclari

    wrep = ProgramlamaAraclari(workspace_root).write(rel_main, patched)
    lines = ["[Faz 85 — health ok düzeltme — LLM yok]"]
    writes_ok = 1 if wrep.ok else 0
    if not wrep.ok:
        return {
            "ok": False,
            "writes_ok": 0,
            "verify_ok": False,
            "detail": wrep.detail,
            "source": "fast_fix_health_faz85",
        }
    lines.append(f"· `{rel_main}` içinde ok=false → true.")
    if _goal_wants_tests(goal):
        lines.append(f"· service/version pytest uyumu ({service}, {version}).")
    verify_ok, _ = _run_verify_block(workspace_root, scope_rel, goal, lines)
    return {
        "ok": verify_ok,
        "writes_ok": writes_ok,
        "verify_ok": verify_ok,
        "detail": "\n".join(lines),
        "source": "fast_fix_health_faz85",
    }


def _try_health_version(
    workspace_root: str | Path | None,
    scope_rel: str,
    goal: str,
) -> dict[str, Any] | None:
    if not (_goal_wants_health_version(goal) and _goal_wants_tests(goal)):
        return None
    found = _find_main_py(workspace_root, scope_rel)
    if not found:
        return None
    rel_main, path_main = found
    service = _service_slug_from_scope(scope_rel)
    version = _extract_version(goal)
    try:
        original = path_main.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    patched, changed = patch_main_py_content(original, service=service, version=version)
    lines = ["[Faz 85 — health+version — LLM yok]"]
    from ilim_assistant.motorlar.programlama_motoru import ProgramlamaAraclari

    tools = ProgramlamaAraclari(workspace_root)
    writes_ok = 0
    if changed:
        wrep = tools.write(rel_main, patched)
        if not wrep.ok:
            return {
                "ok": False,
                "writes_ok": 0,
                "verify_ok": False,
                "detail": f"Yazım reddedildi: {wrep.detail}",
                "source": "fast_health_faz85",
            }
        writes_ok = 1
        lines.append(f"· `{rel_main}` güncellendi (version).")
    elif '"version"' in original or "'version'" in original:
        lines.append(f"· `{rel_main}` zaten version içeriyor.")
    else:
        return None
    verify_ok, _ = _run_verify_block(workspace_root, scope_rel, goal, lines)
    return {
        "ok": verify_ok,
        "writes_ok": writes_ok,
        "verify_ok": verify_ok,
        "detail": "\n".join(lines),
        "source": "fast_health_faz85",
    }


def _try_verify_only(
    workspace_root: str | Path | None,
    scope_rel: str,
    goal: str,
) -> dict[str, Any] | None:
    if not _goal_wants_tests(goal):
        return None
    if _goal_wants_health_version(goal) or _goal_wants_create(goal):
        return None
    if _scope_project_dir(workspace_root, scope_rel) is None:
        return None
    lines = ["[Faz 85 — sadece doğrulama — LLM yok]"]
    verify_ok, _ = _run_verify_block(workspace_root, scope_rel, goal, lines)
    return {
        "ok": verify_ok,
        "writes_ok": 0,
        "verify_ok": verify_ok,
        "detail": "\n".join(lines),
        "source": "fast_verify_faz85",
    }


def try_fast_deterministic_task(
    workspace_root: str | Path | None,
    scope_rel: str,
    goal: str,
    *,
    allow_agent_fallback: bool = True,
) -> dict[str, Any] | None:
    if not _enabled():
        return None
    scope_rel = _resolve_preferred_scope(workspace_root, scope_rel, goal)
    handlers: list[Callable[..., dict[str, Any] | None]] = [
        _try_scaffold_fastapi,
        _try_fix_health_ok,
        _try_health_version,
        _try_verify_only,
    ]
    for fn in handlers:
        try:
            raw = fn(workspace_root, scope_rel, goal)
            if allow_agent_fallback:
                finalized = _finalize_result(raw)
            else:
                finalized = raw
            if finalized is not None:
                return finalized
        except Exception:
            continue
    return None


def iter_fast_task_events(
    *,
    message: str,
    task: Any,
    fast: dict[str, Any],
    new_wake: bool = False,
    workspace_root: str | Path | None = None,
) -> Iterator[dict[str, Any]]:
    t0 = time.perf_counter()
    src = str(fast.get("source") or "fast_local_faz85")
    yield {
        "type": "status",
        "text": (
            f"Yerel hızlı yol (Faz 85 · {src}) — `{task.scope_rel}` "
            "(dış AI turu atlandı)…"
        ),
    }
    elapsed = time.perf_counter() - t0
    success = bool(fast.get("ok"))
    detail = str(fast.get("detail") or "")
    try:
        from ilim_assistant.motorlar.programlama_faz55 import record_task_outcome

        record_task_outcome(
            workspace_root,
            scope_rel=task.scope_rel,
            goal=task.goal,
            success=success,
            turns_used=0,
            verify_ok=bool(fast.get("verify_ok")),
            writes_ok=int(fast.get("writes_ok") or 0),
            elapsed_sec=elapsed,
            source=src,
            detail=detail[:500],
        )
    except Exception:
        pass
    body = (
        "Ümit abi, **görev yerel hızlı yoldan** işlendi (Faz 85).\n\n"
        f"Proje: `{task.scope_rel}`\n"
        f"Hedef: {task.goal}\n\n"
        f"{detail}\n\n"
        f"({'tamam' if success else 'kırmızı'}) · {elapsed:.1f}s · LLM turu yok"
    )
    yield {
        "type": "done",
        "full_reply": body,
        "user_message": message,
        "new_wake_used": new_wake,
        "code_agent": {
            "success": success,
            "scope_rel": task.scope_rel,
            "turns": 0,
            "elapsed_sec": elapsed,
            "fast_local": True,
            "fast_source": src,
        },
    }


def faz85_directive() -> str:
    chain = "kod,denge,groq,gemini" if ollama_available() else "groq,kod,gemini"
    return (
        "[Faz 85 — yerel öncelik]\n"
        f"Zincir: {chain} · hızlı yol: şablon, health+version, verify.\n"
        "Hızlı yol kırmızıysa otomatik ajan devam eder.\n"
        f"Kapat: RUZGAR_FAZ85=0 · {FAZ85_VERSION}\n"
    )


def enrich_health_build(build: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(build or {})
    out["programlama_faz85"] = faz85_enabled()
    out["prog_local_first"] = local_first_enabled()
    out["ollama_available"] = ollama_available()
    out["faz85_fallback_on_fail"] = fallback_to_agent_on_fail()
    return out
