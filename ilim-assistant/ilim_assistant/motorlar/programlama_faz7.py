# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 7: proje çalıştırma profilleri ve yerel açıklama/rehber.

Şablon projeler (Faz 6) için LLM olmadan «açıkla / nasıl çalıştırırım» yanıtı;
«proje çalıştır» ile güvenli smoke/çalıştırma (yalnızca projects/ altı).
"""

from __future__ import annotations

import os
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

from ilim_assistant.approved_executor import run_argv
from ilim_assistant.motorlar.programlama_motoru import ProgramlamaAraclari, repo_root

FAZ7_VERSION = "programlama-faz7-v2-2026-05-24"

_PATH_RE = re.compile(
    r"(projects/[\w.\-/\\]+(?:\.py|\.md|\.txt)?)",
    re.IGNORECASE,
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


def extract_path_from_message(message: str) -> str | None:
    m = _PATH_RE.search(message or "")
    if m:
        return _norm_rel(m.group(1))
    return None


def resolve_target_rel(
    message: str,
    *,
    active_file: str | None = None,
    workspace_root: str | Path | None = None,
) -> str | None:
    rel = extract_path_from_message(message)
    if rel:
        return rel
    af = _norm_rel(active_file or "")
    if af:
        return af
    try:
        from ilim_assistant.motorlar.programlama_faz5 import load_session

        sess = load_session(workspace_root)
        af2 = _norm_rel(str(sess.get("active_file") or ""))
        if af2:
            return af2
    except Exception:
        pass
    return None


def _project_dir_from_rel(rel: str) -> str | None:
    r = _norm_rel(rel)
    base = _projects_base()
    if not r.startswith(f"{base}/"):
        return None
    parts = r.split("/")
    if len(parts) < 2:
        return None
    return f"{base}/{parts[1]}"


def detect_run_profile(
    workspace_root: str | Path | None,
    rel_or_dir: str,
) -> dict[str, Any] | None:
    root = repo_root(workspace_root)
    if root is None:
        return None
    rel = _norm_rel(rel_or_dir)
    proj_rel = _project_dir_from_rel(rel) if rel.startswith(_projects_base()) else _norm_rel(rel)
    if not proj_rel or not proj_rel.startswith(f"{_projects_base()}/"):
        if rel.startswith(f"{_projects_base()}/"):
            proj_rel = "/".join(rel.split("/")[:2])
        else:
            return None
    proj_path = root / proj_rel.replace("/", os.sep)
    if not proj_path.is_dir():
        return None

    slug = proj_path.name
    req = proj_path / "requirements.txt"
    main_py = proj_path / "main.py"
    bot_py = proj_path / "bot.py"
    app_main = proj_path / "app" / "main.py"
    pyproject = proj_path / "pyproject.toml"
    package_json = proj_path / "package.json"
    index_html = proj_path / "index.html"
    pj_text = ""
    if package_json.is_file():
        try:
            pj_text = package_json.read_text(encoding="utf-8", errors="replace").lower()
        except OSError:
            pj_text = ""
        if "vite" in pj_text and "react" in pj_text:
            port = int(os.environ.get("RUZGAR_FAZ7_VITE_PORT", "5173"))
            return {
                "profile_id": "react_vite",
                "project_rel": proj_rel.replace("\\", "/"),
                "slug": slug,
                "title": slug,
                "install_argv": ["npm", "install"],
                "run_argv": ["npm", "run", "dev"],
                "smoke_argv": ["npm", "run", "build"],
                "urls": [f"http://127.0.0.1:{port}/"],
                "manual": (
                    f"cd projects/{slug}\n"
                    "npm install\n"
                    "npm run dev"
                ),
            }

    if index_html.is_file() and "vite" not in pj_text:
        static_port = int(os.environ.get("RUZGAR_FAZ7_STATIC_PORT", "5500"))
        return {
            "profile_id": "static_site",
            "project_rel": proj_rel.replace("\\", "/"),
            "slug": slug,
            "title": slug,
            "install_argv": None,
            "run_argv": [
                sys.executable,
                "-m",
                "http.server",
                str(static_port),
                "--bind",
                "127.0.0.1",
            ],
            "smoke_argv": [
                sys.executable,
                "-c",
                "from pathlib import Path; p=Path('index.html'); assert p.is_file(); print('static_ok')",
            ],
            "urls": [f"http://127.0.0.1:{static_port}/"],
            "manual": (
                f"cd projects/{slug}\n"
                f"python -m http.server {static_port}"
            ),
        }

    if app_main.is_file() and req.is_file():
        text = req.read_text(encoding="utf-8", errors="replace").lower()
        if "fastapi" in text or "uvicorn" in text:
            port = int(os.environ.get("RUZGAR_FAZ7_API_PORT", "8080"))
            return {
                "profile_id": "fastapi_api",
                "project_rel": proj_rel.replace("\\", "/"),
                "slug": slug,
                "title": slug,
                "install_argv": [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                "run_argv": [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "app.main:app",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(port),
                ],
                "smoke_argv": [
                    sys.executable,
                    "-c",
                    "from app.main import app; print('import_ok', getattr(app, 'title', ''))",
                ],
                "urls": [
                    f"http://127.0.0.1:{port}/health",
                    f"http://127.0.0.1:{port}/docs",
                ],
                "manual": (
                    f"cd projects/{slug}\n"
                    f"python -m pip install -r requirements.txt\n"
                    f"python -m uvicorn app.main:app --reload --port {port}"
                ),
            }
    if main_py.is_file() and not app_main.is_file():
        return {
            "profile_id": "cli_python",
            "project_rel": proj_rel.replace("\\", "/"),
            "slug": slug,
            "title": slug,
            "install_argv": None,
            "run_argv": [sys.executable, "main.py"],
            "smoke_argv": [sys.executable, "-c", "import main; print('import_ok')"],
            "urls": [],
            "manual": f"cd projects/{slug}\npython main.py",
        }
    if bot_py.is_file():
        return {
            "profile_id": "mini_ai_bot",
            "project_rel": proj_rel.replace("\\", "/"),
            "slug": slug,
            "title": slug,
            "install_argv": None,
            "run_argv": [sys.executable, "bot.py"],
            "smoke_argv": [sys.executable, "-c", "import bot; print('import_ok')"],
            "urls": [],
            "manual": f"cd projects/{slug}\npython bot.py",
        }
    if pyproject.is_file():
        return {
            "profile_id": "python_package",
            "project_rel": proj_rel.replace("\\", "/"),
            "slug": slug,
            "title": slug,
            "install_argv": None,
            "run_argv": [sys.executable, "-m", "pytest", "-q", "--tb=short"],
            "smoke_argv": [sys.executable, "-m", "pytest", "-q", "--tb=line", "-x"],
            "urls": [],
            "manual": f"cd projects/{slug}\npython -m pytest",
        }
    return None


def wants_file_help(message: str) -> bool:
    low = _ascii_fold(message)
    if wants_project_run(message):
        return True
    explain = any(
        k in low
        for k in (
            "acikla",
            "anlat",
            "ozetle",
            "ne yapiyor",
            "ne yapar",
            "dosyasini acikla",
        )
    )
    run_hint = any(
        k in low
        for k in (
            "nasil calistir",
            "calistiririm",
            "calistirayim",
            "uvicorn",
            "pytest",
            "calistirma komut",
        )
    )
    has_path = "projects/" in low or ".py" in (message or "")
    return explain or (run_hint and has_path) or (run_hint and "main.py" in low)


def wants_project_run(message: str) -> bool:
    low = _ascii_fold(message)
    return any(
        k in low
        for k in (
            "proje calistir",
            "projeyi calistir",
            "calistir projeyi",
            "projeyi baslat",
            "proje baslat",
        )
    )


def _read_file_summary(workspace_root: str | Path | None, rel: str, cap: int = 1200) -> str:
    tools = ProgramlamaAraclari(workspace_root)
    rep = tools.read(rel, max_chars=cap)
    if rep.ok and rep.content.strip():
        return rep.content.strip()
    return ""


def format_explain_run_report(
    message: str,
    workspace_root: str | Path | None = None,
    *,
    active_file: str | None = None,
) -> str | None:
    if not wants_file_help(message):
        return None
    rel = resolve_target_rel(message, active_file=active_file, workspace_root=workspace_root)
    if not rel:
        return (
            "Ümit abi, hangi dosyayı veya projeyi kastediyorsun?\n\n"
            "Atölyede dosyayı aç veya yol yaz: `projects/benim-api/app/main.py`\n"
            "Komutlar: `proje çalıştır` · `nasıl çalıştırırım`"
        )
    profile = detect_run_profile(workspace_root, rel)
    if not profile:
        snippet = _read_file_summary(workspace_root, rel)
        lines = [
            f"Ümit abi, `{rel}` için otomatik çalıştırma profili bulamadım (Faz 7).",
            "",
            "Bu yol `projects/<ad>/` altında bir Faz 6 şablonu değilse elle çalıştır.",
        ]
        if snippet:
            lines.extend(["", "Dosya özeti:", "```", snippet[:900], "```"])
        return "\n".join(lines)

    pid = profile["profile_id"]
    slug = profile["slug"]
    lines = [
        f"Ümit abi, **{profile['project_rel']}** — Faz 7 rehberi",
        "",
    ]
    if rel.endswith(".py"):
        snippet = _read_file_summary(workspace_root, rel, cap=800)
        if snippet:
            lines.extend([f"### `{rel}`", "```python", snippet[:700], "```", ""])

    if pid == "fastapi_api":
        lines.extend(
            [
                "**Ne yapıyor:** FastAPI servisi; `/health` ve `/items` uçları, Swagger `/docs`.",
                "",
                "**Terminal (proje kökü):**",
                "```bash",
                profile["manual"],
                "```",
                "",
                "**Tarayıcı:**",
            ]
        )
        for u in profile.get("urls") or []:
            lines.append(f"- {u}")
    elif pid == "cli_python":
        lines.extend(
            [
                "**Ne yapıyor:** Komut satırı aracı (`argparse`).",
                "",
                "```bash",
                profile["manual"],
                "```",
            ]
        )
    elif pid == "mini_ai_bot":
        lines.extend(
            [
                "**Ne yapıyor:** Mini sohbet döngüsü; `reply()` içine LLM bağlanır.",
                "",
                "```bash",
                profile["manual"],
                "```",
            ]
        )
    elif pid == "python_package":
        lines.extend(
            [
                "**Ne yapıyor:** Python paket iskeleti + pytest.",
                "",
                "```bash",
                profile["manual"],
                "```",
            ]
        )
    elif pid == "static_site":
        lines.extend(
            [
                "**Ne yapıyor:** Statik HTML/CSS/JS vitrin sitesi.",
                "",
                "```bash",
                profile["manual"],
                "```",
                "",
                "**Tarayıcı:**",
            ]
        )
        for u in profile.get("urls") or []:
            lines.append(f"- {u}")
    elif pid == "react_vite":
        lines.extend(
            [
                "**Ne yapıyor:** React + Vite tek sayfa uygulama (SPA).",
                "",
                "İlk kurulum: `npm install` (bir kez).",
                "",
                "```bash",
                profile["manual"],
                "```",
                "",
                "**Geliştirme sunucusu:**",
            ]
        )
        for u in profile.get("urls") or []:
            lines.append(f"- {u}")

    lines.extend(
        [
            "",
            "Atölyede **Çalıştır** → Faz 7 smoke/çalıştırma dener.",
            "Sohbette: `proje çalıştır`",
            f"({FAZ7_VERSION})",
        ]
    )
    return "\n".join(lines)


def run_project_profile(
    workspace_root: str | Path | None,
    rel_or_dir: str,
    *,
    smoke_only: bool = False,
) -> dict[str, Any]:
    profile = detect_run_profile(workspace_root, rel_or_dir)
    if not profile:
        return {"ok": False, "error": "Çalıştırma profili yok (yalnızca projects/ şablonları)."}
    root = repo_root(workspace_root)
    if root is None:
        return {"ok": False, "error": "workspace_root bulunamadı"}
    proj_rel = profile["project_rel"]
    cwd = root / proj_rel.replace("/", os.sep)
    if not cwd.is_dir():
        return {"ok": False, "error": f"Dizin yok: {proj_rel}"}

    steps: list[dict[str, Any]] = []
    install = profile.get("install_argv")
    pid = profile["profile_id"]
    if install and not smoke_only:
        inst_step = "npm_install" if pid == "react_vite" else "pip_install"
        inst_timeout = 300 if pid == "react_vite" else 120
        code, out, err = run_argv(install, timeout_sec=inst_timeout, cwd=str(cwd))
        steps.append(
            {
                "step": inst_step,
                "exit_code": code,
                "output": (out or err or "")[:4000],
            }
        )
        if code != 0:
            err_msg = (
                "npm install başarısız (Node.js kurulu mu?)"
                if pid == "react_vite"
                else "pip install başarısız"
            )
            return {
                "ok": False,
                "profile_id": pid,
                "project_rel": proj_rel,
                "steps": steps,
                "error": err_msg,
            }

    if pid == "fastapi_api":
        argv = profile["smoke_argv"]
        label = "import_smoke"
        timeout = 30
    elif pid == "react_vite":
        argv = profile["smoke_argv"] if smoke_only else profile["run_argv"]
        label = "npm_build" if smoke_only else "npm_dev"
        timeout = 120 if smoke_only else 15
    elif pid == "static_site":
        argv = profile["smoke_argv"] if smoke_only else profile["run_argv"]
        label = "static_smoke" if smoke_only else "http_server"
        timeout = 20 if smoke_only else 8
    elif smoke_only:
        argv = profile.get("smoke_argv") or profile["run_argv"]
        label = "smoke"
        timeout = 25
    else:
        argv = profile["run_argv"]
        label = "run"
        timeout = 15 if pid in ("cli_python", "mini_ai_bot") else 90

    code, out, err = run_argv(argv, timeout_sec=timeout, cwd=str(cwd))
    combined = (out or err or "").strip()
    steps.append(
        {
            "step": label,
            "argv": " ".join(argv),
            "exit_code": code,
            "output": combined[:6000],
        }
    )

    ok = code == 0
    if pid == "fastapi_api" and not smoke_only:
        ok = code == 0 or "import_ok" in combined
    if pid == "static_site" and not smoke_only:
        ok = True
        report_lines.extend(
            [
                "",
                "Statik sunucu kısa süre çalıştı (önizleme için ayrı terminalde http.server bırakın):",
            ]
        )
    if pid == "react_vite" and not smoke_only:
        ok = code == 0 or code == -1
        report_lines.extend(
            [
                "",
                "Vite dev sunucusu arka planda kısa deneme — sürekli çalışsın dersen ayrı terminalde `npm run dev`:",
            ]
        )
    report_lines = [
        f"Ümit abi, **{proj_rel}** çalıştırma ({profile['profile_id']}):",
        "",
    ]
    for st in steps:
        mark = "✓" if st.get("exit_code") == 0 else "✗"
        report_lines.append(f"{mark} {st.get('step')}")
        if st.get("output"):
            report_lines.append(st["output"][:2000])
    if pid == "fastapi_api":
        report_lines.extend(
            [
                "",
                "API sürekli çalışsın dersen ayrı terminalde:",
                "```bash",
                profile["manual"],
                "```",
            ]
        )
        for u in profile.get("urls") or []:
            report_lines.append(f"→ {u}")

    return {
        "ok": ok,
        "profile_id": profile["profile_id"],
        "project_rel": proj_rel,
        "steps": steps,
        "report": "\n".join(report_lines),
        "manual": profile.get("manual"),
        "urls": profile.get("urls") or [],
        "version": FAZ7_VERSION,
    }


def format_run_report(result: dict[str, Any]) -> str:
    if result.get("report"):
        return str(result["report"])
    return result.get("error") or "Çalıştırma tamamlanamadı."


def run_directive() -> str:
    return (
        "[PROJE ÇALIŞTIRMA — Faz 7]\n"
        "Şablon projeler: «açıkla» / «nasıl çalıştırırım» / «proje çalıştır»\n"
        f"Yalnızca `{_projects_base()}/<ad>/` altı; uvicorn/CLI/pytest güvenli preset.\n"
    )
