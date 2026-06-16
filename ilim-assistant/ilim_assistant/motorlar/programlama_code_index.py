# Created by Ümit & Gökçenur
"""
Programlama motoru — semantik kod indeksi (Adım 6).

Nebula/RAG'den ayrı: `.ruzgar/code_index/` altında kod dosyaları.
Arama: embedding kosinüsü (rag_store ile aynı model).
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

import numpy as np

from ilim_assistant.motorlar.programlama_motoru import repo_root

CODE_INDEX_VERSION = "programlama-code-index-v1-2026-06-16"

_CODE_EXTS = frozenset({".py", ".js", ".ts", ".tsx", ".jsx", ".md"})
_SKIP_DIRS = frozenset(
    {
        ".git",
        ".cursor",
        ".venv",
        "venv",
        "__pycache__",
        "node_modules",
        "dist",
        "build",
        ".pytest_cache",
        "hafiza",
        "knowledge",
        "arsiv",
        "code_index",
    }
)
_CHUNK_CHARS = 880
_CHUNK_OVERLAP = 72


@dataclass
class CodeChunk:
    text: str
    source: str
    scope: str


def code_index_enabled() -> bool:
    return os.environ.get("RUZGAR_PROG_CODE_INDEX", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _index_roots() -> list[str]:
    raw = (os.environ.get("RUZGAR_CODE_INDEX_SCOPES") or "projects").strip()
    roots = [x.strip().replace("\\", "/").strip("/") for x in raw.split(",") if x.strip()]
    return roots or ["projects"]


def _index_dir(workspace_root: str | Path | None) -> Path | None:
    root = repo_root(workspace_root)
    if root is None:
        return None
    d = root / ".ruzgar" / "code_index"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _paths(workspace_root: str | Path | None) -> tuple[Path | None, Path | None, Path | None]:
    d = _index_dir(workspace_root)
    if d is None:
        return None, None, None
    return d / "chunks.jsonl", d / "embeddings.npy", d / "manifest.json"


def _file_hash(path: Path) -> str:
    try:
        data = path.read_bytes()
    except OSError:
        return ""
    return hashlib.sha256(data).hexdigest()[:16]


def _split_text(text: str, max_chars: int = _CHUNK_CHARS, overlap: int = _CHUNK_OVERLAP) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []
    parts: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        chunk = text[start:end].strip()
        if chunk:
            parts.append(chunk)
        if end >= len(text):
            break
        start = end - overlap
    return parts


def _scope_for_rel(rel: str) -> str:
    n = rel.replace("\\", "/").lstrip("/")
    parts = n.split("/")
    if len(parts) >= 2 and parts[0] == "projects":
        return f"{parts[0]}/{parts[1]}"
    return parts[0] if parts else ""


def _skip_project_name(name: str) -> bool:
    n = (name or "").strip().lower()
    if not n or n.startswith("."):
        return True
    skip_prefixes = (
        "agent-bat-",
        "debug-",
        "fdm-bracket-",
        ".ruzgar",
        "smoke-parity-",
        "smoke-autonomy-",
    )
    if any(n.startswith(p) for p in skip_prefixes):
        return True
    raw = (os.environ.get("RUZGAR_CODE_INDEX_SKIP_PROJECTS") or "").strip()
    if raw:
        blocked = {x.strip().lower() for x in raw.split(",") if x.strip()}
        if n in blocked:
            return True
    return False


def _max_files_total() -> int:
    try:
        return max(80, int(os.environ.get("RUZGAR_CODE_INDEX_MAX_FILES", "1200")))
    except ValueError:
        return 1200


def _max_files_per_scope() -> int:
    try:
        return max(12, int(os.environ.get("RUZGAR_CODE_INDEX_MAX_PER_SCOPE", "48")))
    except ValueError:
        return 48


def _walk_tree(
    workspace_root: Path,
    base: Path,
    *,
    max_files: int,
) -> Iterator[tuple[str, str]]:
    count = 0
    for dirpath, dirnames, filenames in os.walk(base):
        if count >= max_files:
            return
        dirnames[:] = [
            d for d in dirnames if d not in _SKIP_DIRS and not d.startswith(".")
        ]
        for name in filenames:
            if count >= max_files:
                return
            fp = Path(dirpath) / name
            if fp.suffix.lower() not in _CODE_EXTS:
                continue
            try:
                if fp.stat().st_size > 180_000:
                    continue
                body = fp.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            rel = str(fp.relative_to(workspace_root)).replace("\\", "/")
            yield rel, body
            count += 1


def _iter_code_files(
    workspace_root: Path,
    *,
    scope_rel: str | None = None,
    max_files: int | None = None,
) -> Iterator[tuple[str, str]]:
    total_cap = max_files if max_files is not None else _max_files_total()
    per_scope = _max_files_per_scope()
    count = 0
    scope = (scope_rel or "").replace("\\", "/").strip("/")

    if scope:
        base = workspace_root / scope.replace("/", os.sep)
        if base.is_dir():
            yield from _walk_tree(workspace_root, base, max_files=per_scope)
        return

    for top in _index_roots():
        base = workspace_root / top.replace("/", os.sep)
        if not base.is_dir():
            continue
        if top == "projects":
            proj_dirs = [
                p
                for p in base.iterdir()
                if p.is_dir() and not _skip_project_name(p.name)
            ]
            proj_dirs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            for proj in proj_dirs:
                if count >= total_cap:
                    return
                for rel, body in _walk_tree(
                    workspace_root, proj, max_files=per_scope
                ):
                    yield rel, body
                    count += 1
                    if count >= total_cap:
                        return
            continue
        for rel, body in _walk_tree(workspace_root, base, max_files=total_cap - count):
            yield rel, body
            count += 1
            if count >= total_cap:
                return


def _load_chunks(path: Path) -> list[CodeChunk]:
    if not path.is_file():
        return []
    out: list[CodeChunk] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
            out.append(
                CodeChunk(
                    text=str(row.get("text") or ""),
                    source=str(row.get("source") or ""),
                    scope=str(row.get("scope") or ""),
                )
            )
        except json.JSONDecodeError:
            continue
    return out


def _embedder():
    from ilim_assistant.rag_store import _get_embedder

    return _get_embedder()


def _save_index(
    root: Path,
    chunks: list[CodeChunk],
    emb: np.ndarray,
    file_rows: list[dict[str, str]],
) -> None:
    chunks_fp, emb_fp, manifest_fp = _paths(root)
    if chunks_fp is None or emb_fp is None or manifest_fp is None:
        return
    with chunks_fp.open("w", encoding="utf-8") as f:
        for c in chunks:
            f.write(
                json.dumps(
                    {"text": c.text, "source": c.source, "scope": c.scope},
                    ensure_ascii=False,
                )
                + "\n"
            )
    np.save(emb_fp, np.asarray(emb, dtype=np.float32))
    manifest_fp.write_text(
        json.dumps(
            {
                "version": CODE_INDEX_VERSION,
                "built_at": time.time(),
                "chunk_count": len(chunks),
                "file_count": len(file_rows),
                "files": file_rows,
                "scopes": _index_roots(),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def _chunks_to_rows(root: Path, chunks: list[CodeChunk]) -> list[dict[str, str]]:
    seen: set[str] = set()
    rows: list[dict[str, str]] = []
    for c in chunks:
        if c.source in seen:
            continue
        seen.add(c.source)
        rows.append(
            {
                "rel": c.source,
                "hash": _file_hash(root / c.source.replace("/", os.sep)),
            }
        )
    return rows


def merge_scope_index(
    workspace_root: str | Path | None,
    scope_rel: str,
) -> dict[str, Any]:
    """Tek proje kapsamını mevcut indekse ekler/günceller."""
    root = repo_root(workspace_root)
    scope = (scope_rel or "").replace("\\", "/").strip("/")
    if root is None or not scope:
        return {"ok": False, "error": "workspace_root veya scope yok"}
    chunks_fp, emb_fp, _ = _paths(root)
    if chunks_fp is None or emb_fp is None:
        return {"ok": False, "error": "index path yok"}

    new_pairs = list(
        _iter_code_files(root, scope_rel=scope, max_files=_max_files_per_scope())
    )
    if not new_pairs:
        return {"ok": False, "error": f"kapsamda kod yok: {scope}"}

    existing = _load_chunks(chunks_fp)
    existing_emb: np.ndarray | None = None
    if emb_fp.is_file() and existing:
        try:
            existing_emb = np.load(emb_fp)
        except OSError:
            existing_emb = None
    if existing_emb is not None and len(existing_emb) != len(existing):
        existing = []
        existing_emb = None

    kept_chunks: list[CodeChunk] = []
    kept_emb: list[np.ndarray] = []
    if existing and existing_emb is not None:
        for c, row in zip(existing, existing_emb):
            if c.scope == scope or c.source.startswith(scope + "/"):
                continue
            kept_chunks.append(c)
            kept_emb.append(row)

    new_chunks: list[CodeChunk] = []
    for rel, body in new_pairs:
        sc = _scope_for_rel(rel)
        for piece in _split_text(body):
            new_chunks.append(CodeChunk(text=piece, source=rel, scope=sc))

    texts = [c.text for c in new_chunks]
    model = _embedder()
    new_emb = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)

    merged_chunks = kept_chunks + new_chunks
    if kept_emb:
        merged_emb = np.vstack([np.asarray(kept_emb, dtype=np.float32), np.asarray(new_emb, dtype=np.float32)])
    else:
        merged_emb = np.asarray(new_emb, dtype=np.float32)

    file_rows = _chunks_to_rows(root, merged_chunks)
    _save_index(root, merged_chunks, merged_emb, file_rows)
    return {
        "ok": True,
        "scope_rel": scope,
        "added_chunks": len(new_chunks),
        "chunk_count": len(merged_chunks),
        "version": CODE_INDEX_VERSION,
    }


def build_code_index(
    workspace_root: str | Path | None,
    *,
    force: bool = False,
) -> dict[str, Any]:
    """Kod dosyalarını `.ruzgar/code_index/` altına indeksler."""
    root = repo_root(workspace_root)
    if root is None:
        return {"ok": False, "error": "workspace_root yok"}
    chunks_fp, emb_fp, manifest_fp = _paths(root)
    if chunks_fp is None:
        return {"ok": False, "error": "index dir yok"}

    file_rows: list[dict[str, str]] = []
    chunks: list[CodeChunk] = []
    for rel, body in _iter_code_files(root):
        file_rows.append({"rel": rel, "hash": _file_hash(root / rel.replace("/", os.sep))})
        scope = _scope_for_rel(rel)
        for piece in _split_text(body):
            chunks.append(CodeChunk(text=piece, source=rel, scope=scope))

    if not force and manifest_fp.is_file() and chunks_fp.is_file() and emb_fp.is_file():
        try:
            old = json.loads(manifest_fp.read_text(encoding="utf-8"))
            if old.get("files") == file_rows and old.get("chunk_count") == len(chunks):
                return {
                    "ok": True,
                    "skipped": True,
                    "chunk_count": len(chunks),
                    "file_count": len(file_rows),
                    "version": CODE_INDEX_VERSION,
                }
        except (OSError, json.JSONDecodeError):
            pass

    if not chunks:
        return {"ok": False, "error": "indekslenecek kod dosyası yok"}

    texts = [c.text for c in chunks]
    model = _embedder()
    emb = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    _save_index(root, chunks, np.asarray(emb, dtype=np.float32), file_rows)
    return {
        "ok": True,
        "skipped": False,
        "chunk_count": len(chunks),
        "file_count": len(file_rows),
        "version": CODE_INDEX_VERSION,
    }


def _ensure_index(workspace_root: str | Path | None) -> bool:
    if not code_index_enabled():
        return False
    root = repo_root(workspace_root)
    if root is None:
        return False
    _, _, manifest_fp = _paths(root)
    if manifest_fp is None or not manifest_fp.is_file():
        rep = build_code_index(workspace_root, force=False)
        return bool(rep.get("ok"))
    if os.environ.get("RUZGAR_CODE_INDEX_AUTO", "1").strip().lower() in (
        "0",
        "false",
        "no",
    ):
        return True
    try:
        age_h = (time.time() - manifest_fp.stat().st_mtime) / 3600.0
        if age_h > float(os.environ.get("RUZGAR_CODE_INDEX_MAX_AGE_H", "24")):
            build_code_index(workspace_root, force=True)
    except OSError:
        pass
    return True


def search_code_index(
    workspace_root: str | Path | None,
    query: str,
    *,
    scope_rel: str | None = None,
    top_k: int = 5,
) -> dict[str, Any]:
    """Semantik kod araması — dosya + skor + snippet."""
    if not code_index_enabled():
        return {"ok": False, "error": "RUZGAR_PROG_CODE_INDEX=0"}
    q = (query or "").strip()
    if len(q) < 2:
        return {"ok": False, "error": "sorgu çok kısa"}
    if not _ensure_index(workspace_root):
        return {"ok": False, "error": "indeks hazır değil"}

    root = repo_root(workspace_root)
    chunks_fp, emb_fp, _ = _paths(root)
    if root is None or chunks_fp is None or emb_fp is None:
        return {"ok": False, "error": "index path yok"}
    chunks = _load_chunks(chunks_fp)
    if not chunks:
        return {"ok": False, "error": "chunk yok"}
    try:
        emb = np.load(emb_fp)
    except OSError:
        return {"ok": False, "error": "embeddings yok"}
    if len(chunks) != len(emb):
        build_code_index(workspace_root, force=True)
        chunks = _load_chunks(chunks_fp)
        try:
            emb = np.load(emb_fp)
        except OSError:
            return {"ok": False, "error": "embeddings yenileme hatası"}

    scope = (scope_rel or "").replace("\\", "/").strip("/")
    row_ids = list(range(len(chunks)))
    if scope:
        row_ids = [
            i
            for i, c in enumerate(chunks)
            if c.source.startswith(scope + "/") or c.scope == scope
        ]
        if not row_ids:
            merge_scope_index(workspace_root, scope)
            chunks = _load_chunks(chunks_fp)
            try:
                emb = np.load(emb_fp)
            except OSError:
                return {"ok": False, "error": "embeddings yok"}
            if len(chunks) != len(emb):
                return {"ok": False, "error": "chunk/embedding uyumsuz"}
            row_ids = [
                i
                for i, c in enumerate(chunks)
                if c.source.startswith(scope + "/") or c.scope == scope
            ]
    if not row_ids:
        return {"ok": True, "query": q, "scope_rel": scope, "hits": [], "version": CODE_INDEX_VERSION}

    model = _embedder()
    qv = model.encode([q], normalize_embeddings=True, show_progress_bar=False)[0]
    sub = emb[row_ids]
    sim = sub @ qv
    order = np.argsort(-sim)[: max(1, top_k)]

    hits: list[dict[str, Any]] = []
    seen_files: set[str] = set()
    for j in order:
        i = row_ids[int(j)]
        src = chunks[i].source
        if src in seen_files and len(hits) >= top_k:
            continue
        seen_files.add(src)
        snippet = chunks[i].text.replace("\n", " ")[:220]
        hits.append(
            {
                "rel": src,
                "path": src,
                "score": round(float(sim[int(j)]), 4),
                "text": snippet,
            }
        )
        if len(hits) >= top_k:
            break

    return {
        "ok": True,
        "query": q,
        "scope_rel": scope or None,
        "hits": hits,
        "version": CODE_INDEX_VERSION,
    }


def format_semantic_block(
    workspace_root: str | Path | None,
    query: str,
    *,
    scope_rel: str | None = None,
    top_k: int = 4,
) -> str:
    res = search_code_index(
        workspace_root, query, scope_rel=scope_rel, top_k=top_k
    )
    if not res.get("ok") or not res.get("hits"):
        return ""
    lines = [f"[SEMANTİK KOD ARAMA — {CODE_INDEX_VERSION}]"]
    for h in res.get("hits") or []:
        lines.append(
            f"- `{h.get('rel')}` (skor {h.get('score')}) — {str(h.get('text') or '')[:180]}"
        )
    return "\n".join(lines)[:4000]


def run_code_index_smoke(workspace_root: str | Path | None) -> dict[str, Any]:
    """Bench: indeks yükle + basit arama."""
    rep = build_code_index(workspace_root, force=False)
    if not rep.get("ok"):
        return {"ok": False, "build": rep, "version": CODE_INDEX_VERSION}
    sample = search_code_index(
        workspace_root,
        "health endpoint version",
        scope_rel="projects/smoke-live-test",
        top_k=3,
    )
    ok = bool(sample.get("ok")) and len(sample.get("hits") or []) > 0
    return {
        "ok": ok,
        "build": rep,
        "sample": sample,
        "version": CODE_INDEX_VERSION,
    }
