# Created by Ümit & Gökçenur
"""Tercüme Faz 14D — kayıt yolu hafızası ve dosya çakışmasında sürümleme."""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any

SAVE_PREFS_VERSION = "tercume-save-prefs-v14d-2026-05-29"
_DEFAULT_DIR = "ilim-assistant/arsiv/tercume-output"
_MAX_VERSION = 99
_STEM_VER_RE = re.compile(r"^(.+)_v(\d+)$", re.I)


def _repo_root() -> Path:
    try:
        from ilim_assistant.motorlar.programlama_motoru import repo_root

        r = repo_root(None)
        if r:
            return Path(r)
    except Exception:
        pass
    return Path(__file__).resolve().parents[2]


def _prefs_path() -> Path:
    d = _repo_root() / ".ruzgar"
    d.mkdir(parents=True, exist_ok=True)
    return d / "tercume_save_prefs.json"


def _load_prefs() -> dict[str, Any]:
    path = _prefs_path()
    if not path.is_file():
        return {"version": SAVE_PREFS_VERSION}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {"version": SAVE_PREFS_VERSION}


def _save_prefs(data: dict[str, Any]) -> None:
    payload = {
        "version": SAVE_PREFS_VERSION,
        "updated_at": time.time(),
        **data,
    }
    path = _prefs_path()
    tmp = path.with_suffix(".tmp")
    try:
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=0), encoding="utf-8")
        tmp.replace(path)
    except OSError:
        pass


def save_prefs_enabled() -> bool:
    return os.environ.get("RUZGAR_TERCUME_SAVE_PREFS", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def collision_versioning_enabled() -> bool:
    return os.environ.get("RUZGAR_TERCUME_SAVE_VERSION", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _norm_rel(rel: str) -> str:
    return (rel or "").strip().replace("\\", "/").lstrip("/")


def _dir_from_rel(rel: str) -> str:
    raw = _norm_rel(rel)
    if not raw:
        return _DEFAULT_DIR
    parent = Path(raw).parent.as_posix()
    return parent if parent and parent != "." else _DEFAULT_DIR


def last_save_dir() -> str:
    if not save_prefs_enabled():
        return _DEFAULT_DIR
    prefs = _load_prefs()
    d = _norm_rel(str(prefs.get("last_save_dir") or ""))
    if d and ("arsiv" in d or d.startswith("ilim-assistant/")):
        return d
    last = _norm_rel(str(prefs.get("last_save_rel") or ""))
    if last:
        return _dir_from_rel(last)
    return _DEFAULT_DIR


def last_save_rel() -> str:
    prefs = _load_prefs()
    return _norm_rel(str(prefs.get("last_save_rel") or ""))


def remember_save_rel(rel: str) -> None:
    if not save_prefs_enabled():
        return
    raw = _norm_rel(rel)
    if not raw:
        return
    prefs = _load_prefs()
    prefs["last_save_rel"] = raw
    prefs["last_save_dir"] = _dir_from_rel(raw)
    _save_prefs(prefs)


def get_save_prefs() -> dict[str, Any]:
    return {
        "ok": True,
        "version": SAVE_PREFS_VERSION,
        "enabled": save_prefs_enabled(),
        "versioning": collision_versioning_enabled(),
        "last_save_dir": last_save_dir(),
        "last_save_rel": last_save_rel(),
        "default_dir": _DEFAULT_DIR,
    }


def _base_stem(stem: str) -> str:
    m = _STEM_VER_RE.match(stem)
    if m:
        return str(m.group(1))
    return stem


def resolve_collision_path(target: Path, root: Path) -> tuple[Path, str, bool]:
    """Dosya varsa _v2, _v3 … ile boş yol bul."""
    if not collision_versioning_enabled() or not target.is_file():
        rel = target.relative_to(root.resolve()).as_posix()
        return target, rel, False

    stem = target.stem
    suffix = target.suffix
    parent = target.parent
    base = _base_stem(stem) or stem or "ceviri"

    for n in range(2, _MAX_VERSION + 1):
        candidate = parent / f"{base}_v{n}{suffix}"
        if not candidate.is_file():
            rel = candidate.relative_to(root.resolve()).as_posix()
            return candidate, rel, True

    raise OSError(f"Çok fazla sürüm ({base}_v2 …); klasörü temizleyin.")


def prepare_save_path(rel: str, *, root: Path | None = None) -> dict[str, Any]:
    """İzin verilmiş göreli yol → yazılacak Path (+ isteğe bağlı sürüm)."""
    repo = (root or _repo_root()).resolve()
    raw = _norm_rel(rel)
    target = (repo / raw.replace("/", os.sep)).resolve()
    try:
        target.relative_to(repo)
    except ValueError as exc:
        raise ValueError("Geçersiz yol (proje dışı).") from exc

    final, final_rel, versioned = resolve_collision_path(target, repo)
    return {
        "path": final,
        "rel": final_rel,
        "versioned": versioned,
        "requested_rel": raw,
    }
