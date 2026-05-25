# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 22: sembol indeks v2.

- Proje kapsamında fonksiyon/sınıf/export tanımları (satır numaralı)
- Önbellek: `.ruzgar/symbol_index.json`
- Komut: `sembol health` · `@@symbol health` · `sembol indeks yenile`
"""

from __future__ import annotations

import ast
import json
import os
import re
import time
import unicodedata
from pathlib import Path
from typing import Any

from ilim_assistant.motorlar.programlama_motoru import repo_root

FAZ22_VERSION = "programlama-faz22-v1-2026-05-25"
_INDEX_FILE = "symbol_index.json"

_CODE_EXT = frozenset({".py", ".js", ".jsx", ".ts", ".tsx"})
_SKIP_DIRS = frozenset(
    {
        ".git",
        ".cursor",
        ".ruzgar",
        ".venv",
        "venv",
        "__pycache__",
        "node_modules",
        "dist",
        "build",
        ".pytest_cache",
    }
)

_SYMBOL_CMD_RE = re.compile(
    r"(?:@@symbol|sembol|symbol)\s*[:\"]?\s*([\w.\-$]{1,80})",
    re.I,
)
_SYMBOL_REBUILD_RE = re.compile(
    r"(?:sembol|symbol)\s+(?:indeks|index)\s*(?:yenile|guncelle|güncelle|olustur|oluştur|build)?",
    re.I,
)
_JS_DEF_RE = re.compile(
    r"^\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)",
    re.M,
)
_JS_CLASS_RE = re.compile(r"^\s*(?:export\s+)?class\s+(\w+)", re.M)
_JS_CONST_RE = re.compile(
    r"^\s*export\s+(?:const|let|var)\s+(\w+)\s*=",
    re.M,
)


def _ascii_fold(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ22", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _projects_base() -> str:
    return (
        os.environ.get("RUZGAR_SCAFFOLD_BASE", "projects").strip().replace("\\", "/").strip("/")
        or "projects"
    )


def _norm_rel(rel: str) -> str:
    return (rel or "").strip().replace("\\", "/").lstrip("/")


def _index_ttl_sec() -> float:
    try:
        return max(30.0, float(os.environ.get("RUZGAR_SYMBOL_INDEX_TTL_SEC", "300")))
    except ValueError:
        return 300.0


def _index_path(workspace_root: str | Path | None) -> Path | None:
    root = repo_root(workspace_root)
    if root is None:
        return None
    cache_dir = root / ".ruzgar"
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        return None
    return cache_dir / _INDEX_FILE


def _load_store(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _save_store(path: Path, store: dict[str, Any]) -> None:
    store["version"] = FAZ22_VERSION
    store["saved_at"] = time.time()
    path.write_text(
        json.dumps(store, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _extract_py_symbols(rel: str, text: str, *, cap: int = 80) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    try:
        tree = ast.parse(text or "")
    except SyntaxError:
        from ilim_assistant.motorlar.programlama_faz13 import extract_symbols_from_text

        for name in extract_symbols_from_text(rel, text, cap=cap):
            out.append({"name": name, "kind": "symbol", "line": 0, "rel": rel})
        return out

    class _V(ast.NodeVisitor):
        def _add_func(self, node: ast.AST, kind: str) -> None:
            if len(out) >= cap:
                return
            name = getattr(node, "name", None)
            if not name:
                return
            out.append(
                {
                    "name": str(name),
                    "kind": kind,
                    "line": int(getattr(node, "lineno", 0) or 0),
                    "rel": rel,
                }
            )

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            self._add_func(node, "def")

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            self._add_func(node, "async def")

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            if len(out) >= cap:
                return
            out.append(
                {
                    "name": node.name,
                    "kind": "class",
                    "line": int(getattr(node, "lineno", 0) or 0),
                    "rel": rel,
                }
            )

    _V().visit(tree)
    return out[:cap]


def _extract_js_symbols(rel: str, text: str, *, cap: int = 80) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    body = text or ""

    def add(name: str, kind: str, line: int) -> None:
        if not name or len(out) >= cap:
            return
        if any(x["name"] == name and x["line"] == line for x in out):
            return
        out.append({"name": name, "kind": kind, "line": line, "rel": rel})

    for m in _JS_DEF_RE.finditer(body):
        line = body[: m.start()].count("\n") + 1
        add(m.group(1), "function", line)
    for m in _JS_CLASS_RE.finditer(body):
        line = body[: m.start()].count("\n") + 1
        add(m.group(1), "class", line)
    for m in _JS_CONST_RE.finditer(body):
        line = body[: m.start()].count("\n") + 1
        add(m.group(1), "const", line)
    return out[:cap]


def extract_file_symbols(rel: str, text: str, *, cap: int = 80) -> list[dict[str, Any]]:
    path = _norm_rel(rel)
    if path.endswith(".py"):
        return _extract_py_symbols(path, text, cap=cap)
    if path.endswith((".js", ".jsx", ".ts", ".tsx")):
        return _extract_js_symbols(path, text, cap=cap)
    return []


def _iter_code_files(
    workspace_root: str | Path | None,
    scope_rel: str,
    *,
    max_files: int = 80,
) -> list[str]:
    root = repo_root(workspace_root)
    scope = _norm_rel(scope_rel)
    if root is None or not scope.startswith(f"{_projects_base()}/"):
        return []
    base = root / scope.replace("/", os.sep)
    if not base.is_dir():
        return []
    rels: list[str] = []
    for dirpath, dirnames, filenames in os.walk(base):
        if len(rels) >= max_files:
            break
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS and not d.startswith(".")]
        for name in filenames:
            if len(rels) >= max_files:
                break
            if Path(name).suffix.lower() not in _CODE_EXT:
                continue
            fp = Path(dirpath) / name
            try:
                if fp.stat().st_size > 250_000:
                    continue
            except OSError:
                continue
            rels.append(_norm_rel(str(fp.relative_to(root))))
    return rels


def build_symbol_index(
    workspace_root: str | Path | None,
    scope_rel: str,
    *,
    force: bool = False,
    max_files: int = 80,
) -> dict[str, Any]:
    """Kapsam için sembol indeksini oluştur veya yenile."""
    scope = _norm_rel(scope_rel)
    root = repo_root(workspace_root)
    if root is None:
        return {"ok": False, "error": "workspace_root yok"}
    if not scope.startswith(f"{_projects_base()}/"):
        return {"ok": False, "error": f"Yalnızca {_projects_base()}/ altı"}

    idx_path = _index_path(workspace_root)
    store: dict[str, Any] = {"scopes": {}}
    if idx_path and idx_path.is_file() and not force:
        store = _load_store(idx_path)
        scopes = store.get("scopes") if isinstance(store.get("scopes"), dict) else {}
        cached = scopes.get(scope) if isinstance(scopes, dict) else None
        if isinstance(cached, dict):
            age = time.time() - float(cached.get("updated_at") or 0)
            if age < _index_ttl_sec() and cached.get("entries"):
                return {
                    "ok": True,
                    "scope_rel": scope,
                    "cached": True,
                    "symbol_count": sum(len(v) for v in (cached.get("entries") or {}).values()),
                    "file_count": cached.get("file_count", 0),
                    "version": FAZ22_VERSION,
                }

    entries: dict[str, list[dict[str, Any]]] = {}
    file_count = 0
    for rel in _iter_code_files(workspace_root, scope, max_files=max_files):
        fp = root / rel.replace("/", os.sep)
        try:
            body = fp.read_text(encoding="utf-8", errors="replace")[:80_000]
        except OSError:
            continue
        file_count += 1
        for sym in extract_file_symbols(rel, body):
            key = str(sym.get("name") or "").strip()
            if not key:
                continue
            bucket = entries.setdefault(key.lower(), [])
            if len(bucket) < 12:
                bucket.append(sym)

    scope_data = {
        "updated_at": time.time(),
        "file_count": file_count,
        "entries": entries,
        "version": FAZ22_VERSION,
    }
    if idx_path:
        store = _load_store(idx_path) if idx_path.is_file() else {"scopes": {}}
        if not isinstance(store.get("scopes"), dict):
            store["scopes"] = {}
        store["scopes"][scope] = scope_data
        try:
            _save_store(idx_path, store)
        except OSError as exc:
            return {"ok": False, "error": str(exc)[:200]}

    return {
        "ok": True,
        "scope_rel": scope,
        "cached": False,
        "symbol_count": sum(len(v) for v in entries.values()),
        "file_count": file_count,
        "version": FAZ22_VERSION,
    }


def lookup_symbols(
    workspace_root: str | Path | None,
    scope_rel: str,
    query: str,
    *,
    max_hits: int = 24,
) -> dict[str, Any]:
    """İsim veya parça eşleşmesi — tanım listesi."""
    scope = _norm_rel(scope_rel)
    q = (query or "").strip()
    if len(q) < 1:
        return {"ok": False, "error": "Sembol adı gerekli"}

    built = build_symbol_index(workspace_root, scope)
    if not built.get("ok"):
        return built

    idx_path = _index_path(workspace_root)
    if idx_path is None or not idx_path.is_file():
        return {"ok": False, "error": "indeks dosyası yok"}

    store = _load_store(idx_path)
    scopes = store.get("scopes") if isinstance(store.get("scopes"), dict) else {}
    scope_data = scopes.get(scope) if isinstance(scopes, dict) else None
    if not isinstance(scope_data, dict):
        return {"ok": False, "error": "kapsam indeksi yok"}

    entries = scope_data.get("entries") if isinstance(scope_data.get("entries"), dict) else {}
    q_fold = _ascii_fold(q)
    hits: list[dict[str, Any]] = []

    exact = entries.get(q_fold)
    if isinstance(exact, list):
        hits.extend(exact)

    if len(hits) < max_hits:
        for name_key, defs in entries.items():
            if q_fold in name_key or name_key in q_fold:
                for d in defs:
                    if d not in hits:
                        hits.append(d)
                    if len(hits) >= max_hits:
                        break
            if len(hits) >= max_hits:
                break

    return {
        "ok": True,
        "scope_rel": scope,
        "query": q,
        "hits": hits[:max_hits],
        "version": FAZ22_VERSION,
    }


def format_symbol_report(result: dict[str, Any]) -> str:
    if not result.get("ok"):
        return f"Sembol araması başarısız: {result.get('error')}"
    hits = result.get("hits") or []
    lines = [
        f"Ümit abi, **{result.get('scope_rel')}** içinde `{result.get('query')}`:",
        "",
    ]
    if not hits:
        lines.append("Tanım bulunamadı. `sembol indeks yenile` deneyin.")
    else:
        for h in hits:
            rel = h.get("rel") or "?"
            line = int(h.get("line") or 0)
            kind = h.get("kind") or "symbol"
            name = h.get("name") or "?"
            loc = f"`{rel}`:{line}" if line else f"`{rel}`"
            lines.append(f"· **{name}** ({kind}) @ {loc}")
    lines.append(f"\n({FAZ22_VERSION})")
    return "\n".join(lines)


def format_rebuild_report(result: dict[str, Any]) -> str:
    if not result.get("ok"):
        return f"İndeks yenilenemedi: {result.get('error')}"
    cached = "önbellek" if result.get("cached") else "yenilendi"
    return (
        f"Ümit abi, `{result.get('scope_rel')}` sembol indeksi {cached}.\n"
        f"Dosya: **{result.get('file_count')}** · "
        f"Sembol kaydı: **{result.get('symbol_count')}**\n"
        f"({FAZ22_VERSION})"
    )


def parse_symbol_query(message: str) -> str | None:
    m = _SYMBOL_CMD_RE.search(message or "")
    if m:
        return m.group(1).strip()
    low = _ascii_fold(message)
    if low.startswith("sembol ") or low.startswith("symbol "):
        parts = (message or "").strip().split(None, 2)
        if len(parts) >= 2 and parts[1].lower() not in (
            "indeks",
            "index",
            "ara",
            "yenile",
        ):
            return parts[1].strip().strip(":").strip('"')
    return None


def wants_symbol_command(message: str) -> bool:
    if not _enabled():
        return False
    low = _ascii_fold(message)
    if _SYMBOL_REBUILD_RE.search(message or ""):
        return True
    if "@@symbol" in low:
        return True
    if _SYMBOL_CMD_RE.search(message or ""):
        return True
    if low.startswith("sembol ") and " indeks" not in low:
        q = parse_symbol_query(message)
        return bool(q)
    return False


def wants_symbol_rebuild(message: str) -> bool:
    return bool(_SYMBOL_REBUILD_RE.search(message or ""))


def maybe_instant_faz22(
    message: str,
    workspace_root: str | Path | None,
    *,
    active_file: str | None = None,
) -> str | None:
    if not _enabled():
        return None
    from ilim_assistant.motorlar.programlama_faz13 import resolve_scope_rel

    scope = resolve_scope_rel(workspace_root, active_file=active_file, message=message)
    if not scope:
        if wants_symbol_command(message):
            return (
                "Ümit abi, `sembol <ad>` için `projects/<proje>/` aç "
                "veya yol yaz."
            )
        return None

    if wants_symbol_rebuild(message):
        return format_rebuild_report(
            build_symbol_index(workspace_root, scope, force=True)
        )

    if wants_symbol_command(message):
        q = parse_symbol_query(message)
        if not q:
            return "Ümit abi, `sembol health` veya `@@symbol health` yaz."
        return format_symbol_report(lookup_symbols(workspace_root, scope, q))

    return None


def _guess_symbol_names(message: str, *, cap: int = 5) -> list[str]:
    q = parse_symbol_query(message)
    if q:
        return [q]
    skip = frozenset(
        {
            "benim",
            "api",
            "test",
            "pytest",
            "ekle",
            "gecir",
            "version",
            "endpoint",
            "endpointine",
            "health",
            "the",
            "and",
            "for",
        }
    )
    names: list[str] = []
    for m in re.finditer(r"\b([A-Za-z_][\w]{2,40})\b", message or ""):
        w = m.group(1)
        low = w.lower()
        if low in skip:
            continue
        if w[0].isupper() or low in ("health", "router", "main", "app"):
            if w not in names:
                names.append(w)
        if len(names) >= cap:
            break
    if not names:
        for hint in ("health", "main", "router"):
            if hint in _ascii_fold(message):
                names.append(hint)
                break
    return names[:cap]


def compact_symbol_context(
    workspace_root: str | Path | None,
    scope_rel: str,
    message: str,
    *,
    max_symbols: int = 5,
) -> str:
    """LLM bağlamına kısa sembol ipucu (mesajdaki tanımlar)."""
    lines: list[str] = []
    for name in _guess_symbol_names(message, cap=max_symbols):
        res = lookup_symbols(workspace_root, scope_rel, name, max_hits=4)
        for h in res.get("hits") or []:
            rel = h.get("rel")
            line = h.get("line")
            kind = h.get("kind")
            lines.append(f"  · {h.get('name')} ({kind}) `{rel}`:{line}")
    if not lines:
        return ""
    return "[SEMBOL İPUCU — Faz 22]\n" + "\n".join(lines[:12])


def faz22_directive() -> str:
    return (
        "[SEMBOL — Faz 22]\n"
        "Komutlar: `sembol <ad>` · `@@symbol <ad>` · `sembol indeks yenile`\n"
        "Örnek: `sembol health` → tanım listesi (dosya:satır).\n"
    )
