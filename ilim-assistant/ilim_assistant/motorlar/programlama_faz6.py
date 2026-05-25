# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 6: onaylı proje şablonları (scaffold).

Şablonlar workspace altında `projects/<proje-adı>/` dizinine yazılır.
Mevcut dizin doluysa yazma yapılmaz (güvenlik).
"""

from __future__ import annotations

import os
import re
import time
from pathlib import Path
from typing import Any

from ilim_assistant.motorlar.programlama_motoru import ProgramlamaAraclari, repo_root

FAZ6_VERSION = "programlama-faz6-v2-2026-05-24"

_TEMPLATE_ALIASES: dict[str, str] = {
    "cli": "cli_python",
    "python_cli": "cli_python",
    "cli_python": "cli_python",
    "fastapi": "fastapi_api",
    "fastapi_api": "fastapi_api",
    "api": "fastapi_api",
    "rest": "fastapi_api",
    "paket": "python_package",
    "package": "python_package",
    "python_package": "python_package",
    "bot": "mini_ai_bot",
    "mini_ai": "mini_ai_bot",
    "mini_ai_bot": "mini_ai_bot",
    "ai_bot": "mini_ai_bot",
    "asistan": "mini_ai_bot",
    "site": "static_site",
    "web": "static_site",
    "static": "static_site",
    "static_site": "static_site",
    "vitrin": "static_site",
    "react": "react_vite",
    "vite": "react_vite",
    "spa": "react_vite",
    "react_vite": "react_vite",
    "frontend": "react_vite",
}


def _scaffold_base_dir() -> str:
    return (
        os.environ.get("RUZGAR_SCAFFOLD_BASE", "projects").strip().replace("\\", "/").strip("/")
        or "projects"
    )


def _slug(name: str) -> str:
    s = re.sub(r"[^\w\-]+", "-", (name or "").strip().lower())
    s = re.sub(r"-+", "-", s).strip("-")
    return (s[:48] or "proje")


def list_templates() -> list[dict[str, Any]]:
    return [
        {
            "id": "cli_python",
            "label": "Python CLI aracı",
            "stack": ["python"],
            "desc": "argparse ile komut satırı aracı + README",
        },
        {
            "id": "fastapi_api",
            "label": "FastAPI REST API",
            "stack": ["python", "fastapi", "uvicorn"],
            "desc": "health + örnek /items uçları, requirements.txt",
        },
        {
            "id": "python_package",
            "label": "Python paket iskeleti",
            "stack": ["python", "pytest"],
            "desc": "__init__, modül, test, pyproject.toml",
        },
        {
            "id": "mini_ai_bot",
            "label": "Mini AI asistan iskeleti",
            "stack": ["python"],
            "desc": "Basit sohbet döngüsü + genişletme noktaları (LLM bağlantısı için)",
        },
        {
            "id": "static_site",
            "label": "Statik web sitesi",
            "stack": ["html", "css", "javascript"],
            "desc": "Tek sayfa vitrin + form; python -m http.server ile önizleme",
        },
        {
            "id": "react_vite",
            "label": "React + Vite SPA",
            "stack": ["javascript", "react", "vite"],
            "desc": "Modern tek sayfa uygulama; npm run dev / build",
        },
    ]


def _template_files(template_id: str, slug: str, title: str) -> dict[str, str]:
    t = _TEMPLATE_ALIASES.get(template_id, template_id)
    base = f"{_scaffold_base_dir()}/{slug}"
    if t == "cli_python":
        return {
            f"{base}/main.py": f'''#!/usr/bin/env python3
"""CLI — {title} (Rüzgar Faz 6 şablonu)"""
from __future__ import annotations

import argparse


def run(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="{title}")
    p.add_argument("name", nargs="?", default="dünya", help="Selamlanacak isim")
    args = p.parse_args(argv)
    print(f"Merhaba, {{args.name}}!")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
''',
            f"{base}/README.md": f"# {title}\n\nPython CLI — `python main.py`\n",
        }
    if t == "fastapi_api":
        mod = slug.replace("-", "_")
        return {
            f"{base}/requirements.txt": "fastapi>=0.110\nuvicorn[standard]>=0.27\nhttpx>=0.27\n",
            f"{base}/tests/test_health.py": f'''"""pytest — {title} health uçları."""
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
            f"{base}/app/main.py": f'''"""FastAPI — {title}"""
from __future__ import annotations

from fastapi import FastAPI

app = FastAPI(title="{title}")


@app.get("/health")
def health() -> dict[str, str]:
    return {{"ok": "true", "service": "{mod}"}}


@app.get("/items")
def list_items() -> list[dict[str, str]]:
    return [{{"id": "1", "name": "örnek"}}]
''',
            f"{base}/README.md": f"# {title}\n\n```bash\npip install -r requirements.txt\nuvicorn app.main:app --reload --port 8080\n```\n",
        }
    if t == "python_package":
        pkg = slug.replace("-", "_")
        return {
            f"{base}/pyproject.toml": f'''[project]
name = "{slug}"
version = "0.1.0"
description = "{title}"
requires-python = ">=3.10"

[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
''',
            f"{base}/{pkg}/__init__.py": f'"""{title}"""\n\n__version__ = "0.1.0"\n',
            f"{base}/{pkg}/core.py": f'''"""Çekirdek modül — {title}"""


def greet(name: str) -> str:
    return f"Merhaba, {{name}}!"
''',
            f"{base}/tests/test_core.py": f'''from {pkg}.core import greet


def test_greet():
    assert "Merhaba" in greet("Rüzgar")
''',
            f"{base}/README.md": f"# {title}\n\n`pytest` ile test edin.\n",
        }
    if t == "mini_ai_bot":
        pkg = slug.replace("-", "_")
        return {
            f"{base}/bot.py": f'''"""Mini AI asistan iskeleti — {title}

Genişletme: `reply()` içine Gemini/Groq/Ollama çağrısı ekleyin.
"""
from __future__ import annotations


def reply(user_text: str, history: list[dict[str, str]] | None = None) -> str:
  """Yer tutucu — gerçek LLM entegrasyonu buraya."""
  _ = history
  t = (user_text or "").strip()
  if not t:
    return "Boş mesaj."
  if t.lower() in ("çık", "cik", "exit", "quit"):
    return "__EXIT__"
  return f"[iskelet yanıt] Mesajını aldım ({len(t)} karakter). LLM bağlantısını `reply()` içine ekleyin."


def chat_loop() -> None:
  hist: list[dict[str, str]] = []
  print("{title} — mini bot (çıkmak için: çık)")
  while True:
    try:
      msg = input("Sen> ").strip()
    except (EOFError, KeyboardInterrupt):
      print()
      break
    if not msg:
      continue
    out = reply(msg, hist)
    if out == "__EXIT__":
      break
    print(f"Bot> {{out}}")
    hist.append({{"role": "user", "content": msg}})
    hist.append({{"role": "assistant", "content": out}})


if __name__ == "__main__":
  chat_loop()
''',
            f"{base}/README.md": f"# {title}\n\nMini AI bot iskeleti — `python bot.py` sonra `reply()` genişletin.\n",
        }
    if t == "static_site":
        return {
            f"{base}/index.html": f'''<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
  <link rel="stylesheet" href="css/styles.css" />
</head>
<body>
  <header class="hero">
    <h1>{title}</h1>
    <p class="lead">Rüzgar Faz 6 — statik site şablonu (Ümit &amp; Gökçenur)</p>
    <button type="button" id="btn-hello">Merhaba</button>
    <p id="out" class="out" aria-live="polite"></p>
  </header>
  <main>
    <section class="card">
      <h2>İletişim</h2>
      <form id="contact">
        <label>Ad <input name="name" required /></label>
        <label>E-posta <input name="email" type="email" required /></label>
        <button type="submit">Gönder</button>
      </form>
    </section>
  </main>
  <script src="js/app.js"></script>
</body>
</html>
''',
            f"{base}/css/styles.css": '''/* Statik site — Rüzgar */
:root {{
  font-family: system-ui, Segoe UI, sans-serif;
  --bg: #0f1419;
  --fg: #e7ecf3;
  --accent: #3d8bfd;
}}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: var(--bg); color: var(--fg); }}
.hero {{ padding: 2.5rem 1.5rem; text-align: center; }}
.lead {{ opacity: 0.85; }}
.card {{ max-width: 28rem; margin: 1rem auto; padding: 1.25rem; border-radius: 12px; background: #1a2332; }}
label {{ display: block; margin: 0.5rem 0; }}
input {{ width: 100%; padding: 0.5rem; margin-top: 0.25rem; }}
button {{ cursor: pointer; padding: 0.5rem 1rem; border-radius: 8px; border: none; background: var(--accent); color: #fff; }}
.out {{ margin-top: 1rem; min-height: 1.2em; }}
''',
            f"{base}/js/app.js": f'''/** {title} — statik site */
document.getElementById("btn-hello")?.addEventListener("click", () => {{
  const out = document.getElementById("out");
  if (out) out.textContent = "Merhaba, Ümit abi! Site çalışıyor.";
}});
document.getElementById("contact")?.addEventListener("submit", (e) => {{
  e.preventDefault();
  const fd = new FormData(e.target);
  alert(`Teşekkürler, ${{fd.get("name") || "ziyaretçi"}}!`);
}});
''',
            f"{base}/README.md": f"""# {title}

Statik web sitesi (HTML/CSS/JS).

```bash
cd projects/{slug}
python -m http.server 5500
```

Tarayıcı: http://127.0.0.1:5500
""",
        }
    if t == "react_vite":
        return {
            f"{base}/package.json": f'''{{
  "name": "{slug}",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {{
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  }},
  "dependencies": {{
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  }},
  "devDependencies": {{
    "@vitejs/plugin-react": "^4.3.1",
    "vite": "^5.4.0"
  }}
}}
''',
            f"{base}/vite.config.js": '''import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: { host: "127.0.0.1", port: 5173 },
});
''',
            f"{base}/index.html": f'''<!DOCTYPE html>
<html lang="tr">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{title}</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
''',
            f"{base}/src/main.jsx": '''import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App.jsx";
import "./index.css";

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
''',
            f"{base}/src/App.jsx": f'''import {{ useState }} from "react";

export default function App() {{
  const [n, setN] = useState(0);
  return (
    <div className="app">
      <h1>{title}</h1>
      <p>Rüzgar React+Vite şablonu — Ümit &amp; Gökçenur</p>
      <button type="button" onClick={{() => setN((x) => x + 1)}}>
        Tık: {{n}}
      </button>
    </div>
  );
}}
''',
            f"{base}/src/index.css": '''body {
  margin: 0;
  font-family: system-ui, sans-serif;
  background: #0f1419;
  color: #e7ecf3;
}
.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
}
button {
  padding: 0.5rem 1rem;
  border-radius: 8px;
  border: none;
  background: #3d8bfd;
  color: #fff;
  cursor: pointer;
}
''',
            f"{base}/README.md": f"""# {title}

React + Vite SPA.

```bash
cd projects/{slug}
npm install
npm run dev
```

Önizleme: http://127.0.0.1:5173
""",
        }
    return {}


def wants_template_list(message: str) -> bool:
    low = (message or "").lower()
    return any(
        k in low
        for k in (
            "şablon listele",
            "sablon listele",
            "şablonları listele",
            "sablonlari listele",
            "template list",
            "hangi şablon",
            "hangi sablon",
        )
    )


def parse_scaffold_command(message: str) -> tuple[str, str] | None:
    raw = (message or "").strip()
    if len(raw) < 8:
        return None
    patterns = [
        r"(?:şablon|sablon)\s+olu[şs]tur\s*:?\s*(\S+)\s+(.+)",
        r"(?:proje\s+)?(?:şablon|sablon)(?:u)?\s*:?\s*(\S+)\s+(.+)",
        r"scaffold\s*:?\s*(\S+)\s+(.+)",
        r"template\s*:?\s*(\S+)\s+(.+)",
    ]
    for pat in patterns:
        m = re.search(pat, raw, re.I)
        if not m:
            continue
        tid = _TEMPLATE_ALIASES.get(m.group(1).strip().lower(), m.group(1).strip().lower())
        name = m.group(2).strip().strip('"').strip("'")
        if tid and name:
            return tid, name
    return None


def format_template_list_report() -> str:
    lines = [
        "Ümit abi, Programlama şablonları (Faz 6):",
        "",
    ]
    for row in list_templates():
        lines.append(f"• **{row['id']}** — {row['label']}: {row['desc']}")
    lines.extend(
        [
            "",
            "Kullanım:",
            "  şablon oluştur: fastapi_api benim-api",
            "  şablon oluştur: static_site vitrinim",
            "  şablon oluştur: react_vite panelim",
            "",
            f"Dizin: `{_scaffold_base_dir()}/<proje-adı>/`",
            f"Sürüm: {FAZ6_VERSION}",
        ]
    )
    return "\n".join(lines)


def run_scaffold(
    template_id: str,
    project_name: str,
    workspace_root: str | Path | None = None,
    *,
    force: bool = False,
) -> dict[str, Any]:
    root = repo_root(workspace_root)
    if root is None:
        return {"ok": False, "error": "workspace_root bulunamadı"}
    tid = _TEMPLATE_ALIASES.get(template_id.strip().lower(), template_id.strip().lower())
    slug = _slug(project_name)
    title = (project_name or slug).strip()[:80]
    files = _template_files(tid, slug, title)
    if not files:
        return {
            "ok": False,
            "error": f"Bilinmeyen şablon: {template_id}",
            "templates": [t["id"] for t in list_templates()],
        }
    target_dir = root / _scaffold_base_dir() / slug
    if target_dir.exists() and any(target_dir.iterdir()) and not force:
        return {
            "ok": False,
            "error": f"Dizin dolu: {target_dir.relative_to(root)} — başka ad seçin.",
        }
    tools = ProgramlamaAraclari(workspace_root)
    written: list[str] = []
    errors: list[str] = []
    for rel, body in files.items():
        w = tools.write(rel.replace("\\", "/"), body)
        if w.ok:
            written.append(rel.replace("\\", "/"))
        else:
            errors.append(f"{rel}: {w.detail}")
    try:
        from ilim_assistant.motorlar.programlama_faz5 import apply_project_patch, record_tool_summary

        tpl = next((x for x in list_templates() if x["id"] == tid), None)
        stack = list(tpl["stack"]) if tpl else ["python"]
        apply_project_patch(
            workspace_root,
            {
                "name": title,
                "goal": f"Faz 6 şablon: {tid}",
                "stack": stack,
                "notes": f"Oluşturulan dosyalar: {', '.join(written[:6])}",
            },
        )
        record_tool_summary(workspace_root, writes=written)
    except Exception:
        pass
    ok = bool(written) and not errors
    return {
        "ok": ok,
        "template_id": tid,
        "project_slug": slug,
        "project_name": title,
        "base_dir": f"{_scaffold_base_dir()}/{slug}",
        "written": written,
        "errors": errors,
        "version": FAZ6_VERSION,
    }


def format_scaffold_report(result: dict[str, Any]) -> str:
    if not result.get("ok"):
        err = result.get("error") or "Bilinmeyen hata"
        hint = ""
        if result.get("templates"):
            hint = "\nŞablonlar: " + ", ".join(result["templates"])
        return f"Şablon oluşturulamadı: {err}{hint}"
    lines = [
        f"Ümit abi, **{result.get('template_id')}** şablonu hazır.",
        "",
        f"Proje: `{result.get('base_dir')}`",
        "",
        "Yazılan dosyalar:",
    ]
    for p in result.get("written") or []:
        lines.append(f"  · {p}")
    lines.extend(
        [
            "",
            "Sonraki adım: atölyede dosyayı açın; «proje çalıştır» veya **Çalıştır** (Faz 7).",
            f"Faz 5 oturum bağlamı güncellendi. ({FAZ6_VERSION})",
        ]
    )
    return "\n".join(lines)


def scaffold_directive() -> str:
    return (
        "[ŞABLON PROJELER — Faz 6]\n"
        "Yeni proje: «şablon listele» · «şablon oluştur: fastapi_api ad»\n"
        f"Çıktı dizini: `{_scaffold_base_dir()}/<ad>/` — mevcut dolu dizine yazılmaz.\n"
    )
