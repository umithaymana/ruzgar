# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 51: CRUD API, JWT auth, dashboard statik şablonları + offline bootstrap.

Cursor'sız: scaffold → offline bootstrap → pytest/smoke verify.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

FAZ51_VERSION = "programlama-faz51-v1-2026-05-26"

FAZ51_TEMPLATE_IDS = ("crud_api", "auth_jwt", "dashboard_static")

FAZ51_ALIASES: dict[str, str] = {
    "crud": "crud_api",
    "crud_api": "crud_api",
    "api_crud": "crud_api",
    "jwt": "auth_jwt",
    "auth": "auth_jwt",
    "auth_jwt": "auth_jwt",
    "login_api": "auth_jwt",
    "dashboard": "dashboard_static",
    "dashboard_static": "dashboard_static",
    "admin_panel": "dashboard_static",
    "panel": "dashboard_static",
}


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ51", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz51_enabled() -> bool:
    return _enabled()


def merge_template_aliases() -> dict[str, str]:
    if not _enabled():
        return {}
    return dict(FAZ51_ALIASES)


def extra_template_catalog() -> list[dict[str, Any]]:
    if not _enabled():
        return []
    return [
        {
            "id": "crud_api",
            "label": "FastAPI CRUD API",
            "stack": ["python", "fastapi", "pytest"],
            "desc": "health + /items CRUD (bellek içi), pytest",
            "faz": 51,
        },
        {
            "id": "auth_jwt",
            "label": "FastAPI JWT giriş",
            "stack": ["python", "fastapi", "jwt", "pytest"],
            "desc": "health + /login token (HMAC demo), pytest",
            "faz": 51,
        },
        {
            "id": "dashboard_static",
            "label": "Statik yönetim paneli",
            "stack": ["html", "css", "javascript"],
            "desc": "Dashboard kartları + menü; pytest smoke",
            "faz": 51,
        },
    ]


def resolve_faz51_template(template_id: str) -> str:
    return FAZ51_ALIASES.get((template_id or "").strip().lower(), template_id.strip().lower())


def faz51_template_files(
    template_id: str,
    slug: str,
    title: str,
    *,
    projects_base: str = "projects",
) -> dict[str, str] | None:
    if not _enabled():
        return None
    tid = resolve_faz51_template(template_id)
    if tid not in FAZ51_TEMPLATE_IDS:
        return None
    base = f"{projects_base}/{slug}"
    mod = slug.replace("-", "_")

    if tid == "crud_api":
        return {
            f"{base}/requirements.txt": (
                "fastapi>=0.110\nuvicorn[standard]>=0.27\nhttpx>=0.27\npytest>=8.0\n"
            ),
            f"{base}/app/__init__.py": "",
            f"{base}/app/store.py": f'''"""In-memory CRUD store — {title}"""
from __future__ import annotations

_ITEMS: list[dict[str, str]] = []
_NEXT = 1


def list_items() -> list[dict[str, str]]:
    return list(_ITEMS)


def create_item(name: str) -> dict[str, str]:
    global _NEXT
    row = {{"id": str(_NEXT), "name": name.strip()}}
    _NEXT += 1
    _ITEMS.append(row)
    return row


def get_item(item_id: str) -> dict[str, str] | None:
    for row in _ITEMS:
        if row["id"] == str(item_id):
            return row
    return None


def delete_item(item_id: str) -> bool:
    global _ITEMS
    before = len(_ITEMS)
    _ITEMS = [r for r in _ITEMS if r["id"] != str(item_id)]
    return len(_ITEMS) < before
''',
            f"{base}/app/main.py": f'''"""FastAPI CRUD — {title}"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.store import create_item, delete_item, get_item, list_items

app = FastAPI(title="{title}")


class ItemIn(BaseModel):
    name: str


@app.get("/health")
def health() -> dict[str, str]:
    return {{"ok": "true", "service": "{mod}", "version": "0.1.0"}}


@app.get("/items")
def items_list() -> list[dict[str, str]]:
    return list_items()


@app.post("/items", status_code=201)
def items_create(body: ItemIn) -> dict[str, str]:
    if not body.name.strip():
        raise HTTPException(400, "name required")
    return create_item(body.name)


@app.get("/items/{{item_id}}")
def items_get(item_id: str) -> dict[str, str]:
    row = get_item(item_id)
    if row is None:
        raise HTTPException(404, "not found")
    return row


@app.delete("/items/{{item_id}}")
def items_delete(item_id: str) -> dict[str, bool]:
    if not delete_item(item_id):
        raise HTTPException(404, "not found")
    return {{"deleted": True}}
''',
            f"{base}/tests/test_crud.py": f'''"""CRUD smoke — {title}"""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json().get("ok") == "true"


def test_crud_flow() -> None:
    r = client.post("/items", json={{"name": "kitap"}})
    assert r.status_code == 201
    item_id = r.json()["id"]
    r2 = client.get(f"/items/{{item_id}}")
    assert r2.status_code == 200
    assert r2.json()["name"] == "kitap"
    r3 = client.delete(f"/items/{{item_id}}")
    assert r3.status_code == 200
''',
            f"{base}/README.md": f"""# {title}

FastAPI CRUD (bellek içi).

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
pytest -q
```
""",
        }

    if tid == "auth_jwt":
        return {
            f"{base}/requirements.txt": (
                "fastapi>=0.110\nuvicorn[standard]>=0.27\nhttpx>=0.27\npytest>=8.0\n"
            ),
            f"{base}/app/__init__.py": "",
            f"{base}/app/auth.py": f'''"""JWT benzeri token (HMAC demo) — {title}"""
from __future__ import annotations

import hashlib
import hmac
import os
import time

_SECRET = os.environ.get("APP_SECRET", "ruzgar-faz51-demo-secret")
_USERS = {{"admin": "admin123", "demo": "demo123"}}


def authenticate(username: str, password: str) -> bool:
    return _USERS.get(username) == password


def issue_token(username: str, *, ttl_sec: int = 3600) -> str:
    exp = int(time.time()) + ttl_sec
    payload = f"{{username}}:{{exp}}"
    sig = hmac.new(_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{{payload}}.{{sig}}"


def verify_token(token: str) -> str | None:
    try:
        payload, sig = token.rsplit(".", 1)
        username, exp_s = payload.split(":", 1)
        exp = int(exp_s)
    except (ValueError, AttributeError):
        return None
    if exp < int(time.time()):
        return None
    expected = hmac.new(_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig):
        return None
    return username
''',
            f"{base}/app/main.py": f'''"""FastAPI auth — {title}"""
from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, Header
from pydantic import BaseModel

from app.auth import authenticate, issue_token, verify_token

app = FastAPI(title="{title}")


class LoginIn(BaseModel):
    username: str
    password: str


@app.get("/health")
def health() -> dict[str, str]:
    return {{"ok": "true", "service": "{mod}", "version": "0.1.0"}}


@app.post("/login")
def login(body: LoginIn) -> dict[str, str]:
    if not authenticate(body.username, body.password):
        raise HTTPException(401, "invalid credentials")
    return {{"access_token": issue_token(body.username), "token_type": "bearer"}}


def _require_user(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    user = verify_token(token)
    if user is None:
        raise HTTPException(401, "invalid token")
    return user


@app.get("/me")
def me(user: str = Depends(_require_user)) -> dict[str, str]:
    return {{"username": user}}
''',
            f"{base}/tests/test_auth.py": f'''"""Auth smoke — {title}"""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    r = client.get("/health")
    assert r.status_code == 200


def test_login_and_me() -> None:
    r = client.post("/login", json={{"username": "admin", "password": "admin123"}})
    assert r.status_code == 200
    token = r.json()["access_token"]
    r2 = client.get("/me", headers={{"Authorization": f"Bearer {{token}}"}})
    assert r2.status_code == 200
    assert r2.json()["username"] == "admin"
''',
            f"{base}/README.md": f"""# {title}

Demo kullanıcı: `admin` / `admin123`

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
pytest -q
```
""",
        }

    if tid == "dashboard_static":
        return {
            f"{base}/index.html": f'''<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title} — Panel</title>
  <link rel="stylesheet" href="css/dashboard.css" />
</head>
<body>
  <div class="layout">
    <nav class="sidebar">
      <h1>{title}</h1>
      <a href="#" class="active">Özet</a>
      <a href="#">Kayıtlar</a>
      <a href="#">Ayarlar</a>
    </nav>
    <main class="content">
      <h2>Özet</h2>
      <div class="cards" id="cards"></div>
    </main>
  </div>
  <script src="js/dashboard.js"></script>
</body>
</html>
''',
            f"{base}/css/dashboard.css": '''/* Faz 51 dashboard */
:root { font-family: system-ui, sans-serif; --bg: #0d1117; --card: #161b22; --fg: #e6edf3; --accent: #58a6ff; }
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--fg); }
.layout { display: flex; min-height: 100vh; }
.sidebar { width: 220px; padding: 1.5rem; background: #010409; }
.sidebar a { display: block; color: var(--fg); text-decoration: none; padding: 0.5rem 0; opacity: 0.85; }
.sidebar a.active { color: var(--accent); font-weight: 600; }
.content { flex: 1; padding: 2rem; }
.cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 1rem; }
.card { background: var(--card); padding: 1.25rem; border-radius: 12px; border: 1px solid #30363d; }
.card strong { font-size: 1.75rem; display: block; }
''',
            f"{base}/js/dashboard.js": f'''/** {title} dashboard */
const stats = [
  {{ label: "Kullanıcı", value: "128" }},
  {{ label: "Sipariş", value: "42" }},
  {{ label: "Gelir", value: "₺12.4K" }},
];
const root = document.getElementById("cards");
if (root) {{
  root.innerHTML = stats.map((s) =>
    `<article class="card"><span>${{s.label}}</span><strong>${{s.value}}</strong></article>`
  ).join("");
}}
''',
            f"{base}/tests/smoke_dashboard.py": f'''"""Dashboard statik smoke — {title}"""
from pathlib import Path


def test_dashboard_files_exist() -> None:
    root = Path(__file__).resolve().parent.parent
    assert (root / "index.html").is_file()
    assert (root / "css" / "dashboard.css").is_file()
    assert (root / "js" / "dashboard.js").is_file()
''',
            f"{base}/README.md": f"""# {title}

Statik yönetim paneli.

```bash
python -m http.server 8080
pytest -q
```
""",
        }
    return None


def _write_file(workspace_root, rel: str, content: str) -> bool:
    from ilim_assistant.motorlar.programlama_motoru import ProgramlamaAraclari

    return bool(ProgramlamaAraclari(workspace_root).write(rel.replace("\\", "/"), content).ok)


def bootstrap_crud_api(
    workspace_root,
    scope: str,
    slug: str,
    goal: str,
) -> tuple[bool, str]:
    from ilim_assistant.motorlar.programlama_faz14 import ensure_pytest_bootstrap

    ensure_pytest_bootstrap(workspace_root, scope, goal=goal or "pytest")
    return True, "crud bootstrap (scaffold korundu)"


def bootstrap_auth_jwt(workspace_root, scope: str, slug: str, goal: str) -> tuple[bool, str]:
    from ilim_assistant.motorlar.programlama_faz14 import ensure_pytest_bootstrap

    ensure_pytest_bootstrap(workspace_root, scope, goal=goal or "pytest")
    return True, "auth bootstrap (scaffold korundu)"


def bootstrap_dashboard_static(workspace_root, scope: str, slug: str) -> tuple[bool, str]:
    rel = f"{scope}/tests/test_dashboard_extra.py"
    body = f'''"""Dashboard ek smoke — {slug}."""
from pathlib import Path

def test_readme() -> None:
    assert (Path(__file__).resolve().parent.parent / "README.md").is_file()
'''
    ok = _write_file(workspace_root, rel, body)
    return ok, "dashboard bootstrap"


def run_faz51_offline_bootstrap(
    workspace_root,
    scope: str,
    template_id: str,
    slug: str,
    goal: str = "",
) -> tuple[bool, str]:
    if not _enabled():
        return False, "faz51 kapalı"
    tid = resolve_faz51_template(template_id)
    if tid == "crud_api":
        return bootstrap_crud_api(workspace_root, scope, slug, goal)
    if tid == "auth_jwt":
        return bootstrap_auth_jwt(workspace_root, scope, slug, goal)
    if tid == "dashboard_static":
        return bootstrap_dashboard_static(workspace_root, scope, slug)
    return True, f"faz51 skip {tid}"


def verify_faz51_template(
    workspace_root,
    scope_rel: str,
    template_id: str,
    *,
    goal: str = "",
) -> bool:
    if not _enabled():
        return False
    tid = resolve_faz51_template(template_id)
    if tid in ("crud_api", "auth_jwt"):
        from ilim_assistant.motorlar.programlama_faz14 import run_project_verify

        rep = run_project_verify(workspace_root, scope_rel, goal=goal or "pytest")
        return bool(rep and rep.ok)
    if tid == "dashboard_static":
        from ilim_assistant.motorlar.programlama_faz14 import _run_pytest_in_scope

        rep = _run_pytest_in_scope(workspace_root, scope_rel)
        return bool(rep and rep.ok)
    return False


def faz51_directive() -> str:
    return (
        "[FAZ 51 — şablonlar]\n"
        "crud_api · auth_jwt · dashboard_static — scaffold + offline pytest.\n"
    )
