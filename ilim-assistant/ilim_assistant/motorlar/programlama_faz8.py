# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 8: şablon sonrası odaklama, proje ağacı, arka plan API.

- Scaffold sonrası oturum + istemci odak dosyası
- `api başlat` / `api durdur` (yalnızca FastAPI şablonları, projects/ altı)
"""

from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import time
import unicodedata
from pathlib import Path
from typing import Any

from ilim_assistant.motorlar.programlama_motoru import repo_root

FAZ8_VERSION = "programlama-faz8-v1-2026-05-24"
_SERVE_FILENAME = "faz8_serve.json"
_SKIP_DIRS = frozenset(
    {
        ".git",
        ".ruzgar",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".venv",
        "venv",
        "node_modules",
        ".idea",
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


def _bg_serve_enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ8_BG_SERVE", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def pick_focus_rel(scaffold_result: dict[str, Any]) -> str | None:
    """Şablon türüne göre atölyede açılacak birincil dosya."""
    if not scaffold_result.get("ok"):
        return None
    base = _norm_rel(str(scaffold_result.get("base_dir") or ""))
    tid = str(scaffold_result.get("template_id") or "")
    slug = str(scaffold_result.get("project_slug") or "")
    written = [_norm_rel(str(p)) for p in (scaffold_result.get("written") or [])]
    if not base.startswith(f"{_projects_base()}/"):
        return written[0] if written else None

    candidates: list[str] = []
    if tid == "fastapi_api":
        candidates = [f"{base}/app/main.py", f"{base}/requirements.txt"]
    elif tid == "cli_python":
        candidates = [f"{base}/main.py"]
    elif tid == "mini_ai_bot":
        candidates = [f"{base}/bot.py"]
    elif tid == "python_package":
        pkg = slug.replace("-", "_")
        candidates = [
            f"{base}/tests/test_core.py",
            f"{base}/{pkg}/core.py",
            f"{base}/pyproject.toml",
        ]
    elif tid == "static_site":
        candidates = [f"{base}/index.html", f"{base}/css/styles.css", f"{base}/js/app.js"]
    elif tid == "react_vite":
        candidates = [
            f"{base}/src/App.jsx",
            f"{base}/src/main.jsx",
            f"{base}/package.json",
        ]
    elif tid == "mobile_expo":
        candidates = [
            f"{base}/App.js",
            f"{base}/app.json",
            f"{base}/package.json",
        ]
    for c in candidates:
        if c in written:
            return c
    for w in written:
        if w.endswith(".py"):
            return w
    return written[0] if written else None


def apply_scaffold_focus(
    workspace_root: str | Path | None,
    scaffold_result: dict[str, Any],
) -> dict[str, Any]:
    """Oturum active_file + istemci odak meta."""
    focus_rel = pick_focus_rel(scaffold_result)
    base_dir = _norm_rel(str(scaffold_result.get("base_dir") or ""))
    project_rel = base_dir if base_dir.startswith(f"{_projects_base()}/") else ""
    if focus_rel:
        try:
            from ilim_assistant.motorlar.programlama_faz5 import sync_client_editor_state

            sync_client_editor_state(workspace_root, active_file=focus_rel)
        except Exception:
            pass
    return {
        "focus_rel": focus_rel or "",
        "project_rel": project_rel,
        "expand_tree": bool(project_rel),
        "version": FAZ8_VERSION,
    }


def enrich_scaffold_report(
    scaffold_result: dict[str, Any],
    focus_meta: dict[str, Any] | None = None,
) -> str:
    from ilim_assistant.motorlar.programlama_faz6 import format_scaffold_report

    text = format_scaffold_report(scaffold_result)
    fm = focus_meta or {}
    focus = str(fm.get("focus_rel") or "").strip()
    if focus and scaffold_result.get("ok"):
        text += (
            f"\n\n**Faz 8:** Atölye odak dosyası: `{focus}`"
            "\n(Sohbetten scaffold sonrası ağaç otomatik açılır.)"
        )
        if _bg_serve_enabled():
            text += "\nFastAPI ise: `api başlat` · `api durdur`"
    return text


def _serve_store_path(workspace_root: str | Path | None) -> Path | None:
    root = repo_root(workspace_root)
    if root is None:
        return None
    return root / ".ruzgar" / _SERVE_FILENAME


def _load_serve_store(workspace_root: str | Path | None) -> dict[str, Any]:
    path = _serve_store_path(workspace_root)
    if path is None or not path.is_file():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return raw if isinstance(raw, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _save_serve_store(workspace_root: str | Path | None, data: dict[str, Any]) -> None:
    path = _serve_store_path(workspace_root)
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError:
        pass


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _stop_pid(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/F", "/T"],
                capture_output=True,
                timeout=12,
                check=False,
            )
        else:
            os.kill(pid, signal.SIGTERM)
        return True
    except (OSError, subprocess.SubprocessError):
        return False


def list_project_tree(
    workspace_root: str | Path | None,
    project_rel: str,
    *,
    max_depth: int = 4,
    max_entries: int = 120,
) -> dict[str, Any]:
    root = repo_root(workspace_root)
    proj = _norm_rel(project_rel)
    base = _projects_base()
    if root is None:
        return {"ok": False, "error": "workspace_root bulunamadı"}
    if not proj.startswith(f"{base}/"):
        return {"ok": False, "error": f"Yalnızca {base}/<ad>/ altı listelenir."}
    proj_path = (root / proj.replace("/", os.sep)).resolve()
    root_res = root.resolve()
    if not str(proj_path).startswith(str(root_res)):
        return {"ok": False, "error": "Geçersiz yol"}
    if not proj_path.is_dir():
        return {"ok": False, "error": f"Dizin yok: {proj}"}

    entries: list[dict[str, Any]] = []
    count = 0

    def walk(dir_path: Path, rel_prefix: str, depth: int) -> None:
        nonlocal count
        if depth > max_depth or count >= max_entries:
            return
        try:
            children = sorted(
                dir_path.iterdir(),
                key=lambda p: (not p.is_dir(), p.name.lower()),
            )
        except OSError:
            return
        for child in children:
            if count >= max_entries:
                return
            name = child.name
            if name.startswith(".") and name not in (".env.example",):
                continue
            if child.is_dir() and name in _SKIP_DIRS:
                continue
            rel = f"{rel_prefix}/{name}".replace("\\", "/")
            if child.is_dir():
                entries.append({"name": name, "rel": rel, "kind": "dir"})
                count += 1
                walk(child, rel, depth + 1)
            else:
                entries.append({"name": name, "rel": rel, "kind": "file"})
                count += 1

    walk(proj_path, proj, 0)
    return {
        "ok": True,
        "project_rel": proj,
        "entries": entries,
        "truncated": count >= max_entries,
        "version": FAZ8_VERSION,
    }


def serve_status(
    workspace_root: str | Path | None,
    project_rel: str | None = None,
) -> dict[str, Any]:
    store = _load_serve_store(workspace_root)
    proj = _norm_rel(project_rel or "")
    rows: list[dict[str, Any]] = []
    for key, row in store.items():
        if not isinstance(row, dict):
            continue
        pid = int(row.get("pid") or 0)
        alive = _pid_alive(pid)
        if not alive and pid:
            store.pop(key, None)
            continue
        if proj and key != proj:
            continue
        rows.append(
            {
                "project_rel": key,
                "pid": pid,
                "alive": alive,
                "port": row.get("port"),
                "urls": row.get("urls") or [],
                "started_at": row.get("started_at"),
            }
        )
    if proj and not rows:
        _save_serve_store(workspace_root, store)
    return {"ok": True, "processes": rows, "version": FAZ8_VERSION}


def start_background_api(
    workspace_root: str | Path | None,
    rel_or_dir: str,
) -> dict[str, Any]:
    if not _bg_serve_enabled():
        return {
            "ok": False,
            "error": "Arka plan API kapalı (RUZGAR_FAZ8_BG_SERVE=0).",
        }
    from ilim_assistant.motorlar.programlama_faz7 import detect_run_profile

    profile = detect_run_profile(workspace_root, rel_or_dir)
    if not profile:
        return {"ok": False, "error": "FastAPI profili bulunamadı (projects/ şablonu)."}
    pid = profile.get("profile_id")
    if pid not in ("fastapi_api", "static_site", "react_vite"):
        return {
            "ok": False,
            "error": "Arka plan: fastapi_api, static_site veya react_vite gerekli.",
        }
    root = repo_root(workspace_root)
    if root is None:
        return {"ok": False, "error": "workspace_root bulunamadı"}
    proj_rel = _norm_rel(str(profile.get("project_rel") or ""))
    store = _load_serve_store(workspace_root)
    existing = store.get(proj_rel)
    if isinstance(existing, dict):
        pid = int(existing.get("pid") or 0)
        if _pid_alive(pid):
            return {
                "ok": True,
                "already_running": True,
                "project_rel": proj_rel,
                "pid": pid,
                "urls": existing.get("urls") or profile.get("urls") or [],
                "report": f"Ümit abi, API zaten çalışıyor (pid {pid}).",
            }

    cwd = root / proj_rel.replace("/", os.sep)
    if pid == "react_vite" and not (cwd / "node_modules").is_dir():
        install = profile.get("install_argv")
        if install:
            code_i, _, err_i = run_argv(install, timeout_sec=300, cwd=str(cwd))
            if code_i != 0:
                return {
                    "ok": False,
                    "error": f"npm install gerekli: {(err_i or '')[:120]}",
                }
    argv = list(profile.get("run_argv") or [])
    if not argv:
        return {"ok": False, "error": "run_argv yok"}
    port = int(
        os.environ.get("RUZGAR_FAZ7_VITE_PORT", "5173")
        if pid == "react_vite"
        else os.environ.get("RUZGAR_FAZ7_STATIC_PORT", "5500")
        if pid == "static_site"
        else os.environ.get("RUZGAR_FAZ7_API_PORT", "8080")
    )

    popen_kw: dict[str, Any] = {
        "cwd": str(cwd),
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
    }
    if os.name == "nt":
        popen_kw["creationflags"] = (
            getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            | getattr(subprocess, "CREATE_NO_WINDOW", 0)
        )
    try:
        proc = subprocess.Popen(argv, **popen_kw)  # noqa: S603
    except OSError as exc:
        return {"ok": False, "error": str(exc)[:200]}

    store[proj_rel] = {
        "pid": proc.pid,
        "port": port,
        "urls": profile.get("urls") or [],
        "started_at": time.time(),
        "argv": " ".join(str(x) for x in argv),
    }
    _save_serve_store(workspace_root, store)
    urls = profile.get("urls") or []
    kind = {"fastapi_api": "API", "static_site": "statik site", "react_vite": "Vite dev"}.get(
        pid, "sunucu"
    )
    lines = [
        f"Ümit abi, **{proj_rel}** {kind} arka planda başlatıldı (pid {proc.pid}).",
        "",
        "Tarayıcı:",
    ]
    for u in urls:
        lines.append(f"- {u}")
    lines.extend(
        [
            "",
            "Durdurmak için: `api durdur`",
            f"({FAZ8_VERSION})",
        ]
    )
    return {
        "ok": True,
        "project_rel": proj_rel,
        "pid": proc.pid,
        "urls": urls,
        "report": "\n".join(lines),
    }


def stop_background_api(
    workspace_root: str | Path | None,
    rel_or_dir: str,
) -> dict[str, Any]:
    from ilim_assistant.motorlar.programlama_faz7 import detect_run_profile

    profile = detect_run_profile(workspace_root, rel_or_dir)
    proj_rel = _norm_rel(str((profile or {}).get("project_rel") or rel_or_dir))
    if not proj_rel.startswith(f"{_projects_base()}/"):
        rel = _norm_rel(rel_or_dir)
        if rel.startswith(f"{_projects_base()}/"):
            proj_rel = "/".join(rel.split("/")[:2])
    store = _load_serve_store(workspace_root)
    row = store.get(proj_rel)
    if not isinstance(row, dict):
        return {
            "ok": False,
            "error": f"Kayıtlı arka plan süreci yok: {proj_rel}",
        }
    pid = int(row.get("pid") or 0)
    stopped = _stop_pid(pid)
    store.pop(proj_rel, None)
    _save_serve_store(workspace_root, store)
    return {
        "ok": stopped,
        "project_rel": proj_rel,
        "pid": pid,
        "report": (
            f"Ümit abi, **{proj_rel}** API durduruldu (pid {pid})."
            if stopped
            else f"pid {pid} zaten kapalıydı; kayıt temizlendi."
        ),
    }


def wants_api_serve(message: str) -> bool:
    low = _ascii_fold(message)
    return any(
        k in low
        for k in (
            "api baslat",
            "api başlat",
            "sunucu baslat",
            "sunucuyu baslat",
            "uvicorn baslat",
            "fastapi baslat",
            "arka planda api",
            "api arka planda",
        )
    )


def wants_api_stop(message: str) -> bool:
    low = _ascii_fold(message)
    return any(
        k in low
        for k in (
            "api durdur",
            "sunucu durdur",
            "sunucuyu durdur",
            "uvicorn durdur",
            "api kapat",
        )
    )


def wants_project_tree_focus(message: str) -> bool:
    low = _ascii_fold(message)
    return any(
        k in low
        for k in (
            "proje agacini ac",
            "proje ağacını aç",
            "projeyi ac",
            "projeyi aç",
            "proje odak",
            "dosyayi ac",
            "dosyayı aç",
        )
    ) and "projects/" in low


def format_serve_status_report(workspace_root: str | Path | None) -> str | None:
    st = serve_status(workspace_root)
    rows = st.get("processes") or []
    if not rows:
        return "Ümit abi, kayıtlı arka plan API yok. FastAPI projesinde: `api başlat`"
    lines = ["Ümit abi, arka plan API süreçleri (Faz 8):", ""]
    for r in rows:
        mark = "çalışıyor" if r.get("alive") else "kapalı"
        lines.append(f"• `{r.get('project_rel')}` — pid {r.get('pid')} ({mark})")
        for u in r.get("urls") or []:
            lines.append(f"  → {u}")
    lines.append(f"\n({FAZ8_VERSION})")
    return "\n".join(lines)


def maybe_instant_api_command(
    message: str,
    workspace_root: str | Path | None,
    *,
    active_file: str | None = None,
) -> dict[str, Any] | None:
    from ilim_assistant.motorlar.programlama_faz7 import resolve_target_rel

    if wants_api_stop(message):
        rel = resolve_target_rel(message, active_file=active_file, workspace_root=workspace_root)
        if not rel:
            return {
                "text": "Ümit abi, hangi API? `projects/...` yolunu yaz veya dosyayı atölyede aç.",
            }
        res = stop_background_api(workspace_root, rel)
        return {"text": res.get("report") or res.get("error") or "Tamam."}

    if wants_api_serve(message):
        rel = resolve_target_rel(message, active_file=active_file, workspace_root=workspace_root)
        if not rel:
            return {
                "text": (
                    "Ümit abi, FastAPI projesi için dosya yolunu yaz veya "
                    "`projects/benim-api/app/main.py` aç; sonra `api başlat`."
                ),
            }
        res = start_background_api(workspace_root, rel)
        return {"text": res.get("report") or res.get("error") or "Tamam."}

    low = _ascii_fold(message)
    if "api durum" in low or "sunucu durum" in low:
        rep = format_serve_status_report(workspace_root)
        return {"text": rep} if rep else None

    if wants_project_tree_focus(message):
        m = re.search(r"(projects/[\w.\-/]+)", message, re.I)
        rel = _norm_rel(m.group(1)) if m else ""
        if rel.endswith(".py") or "." in rel.split("/")[-1]:
            proj = "/".join(rel.split("/")[:2])
            focus = rel
        else:
            proj = rel if rel.startswith(f"{_projects_base()}/") else ""
            focus = pick_focus_rel(
                {"ok": True, "base_dir": proj, "template_id": "fastapi_api", "written": []}
            ) or (f"{proj}/app/main.py" if proj else "")
        if proj:
            return {
                "text": f"Ümit abi, proje odak: `{proj}`" + (f" · dosya `{focus}`" if focus else ""),
                "focus_rel": focus,
                "project_rel": proj,
                "expand_tree": True,
            }
    return None


def focus_directive() -> str:
    return (
        "[PROJE ODAK — Faz 8]\n"
        "Şablon sonrası atölye odak dosyası; `api başlat` / `api durdur` / `api durum`.\n"
        f"Yalnızca `{_projects_base()}/` altı.\n"
    )
