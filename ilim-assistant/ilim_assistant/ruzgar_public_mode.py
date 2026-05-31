"""Rüzgar halka açılış — ortak sunucu havuzu vs kişisel kullanıcı verisi."""

from __future__ import annotations

import os
import re
from contextvars import ContextVar, Token
from pathlib import Path
from typing import Any

PUBLIC_MODE_VERSION = "ruzgar-public-mode-v1-2026-05-31"

_USER_CTX: ContextVar[str] = ContextVar("ruzgar_user_id", default="anon")
_USER_TOKEN: ContextVar[Token[str] | None] = ContextVar("ruzgar_user_token", default=None)

_USER_SLUG_RE = re.compile(r"[^a-z0-9_-]+")


def is_public_mode() -> bool:
    return os.environ.get("RUZGAR_PUBLIC_MODE", "0").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def ilim_assistant_root() -> Path:
    return Path(__file__).resolve().parents[1]


def data_root() -> Path:
    raw = os.environ.get("RUZGAR_DATA_ROOT", "").strip()
    if raw:
        p = Path(raw)
        p.mkdir(parents=True, exist_ok=True)
        return p.resolve()
    if is_public_mode():
        p = Path("/app/data")
        p.mkdir(parents=True, exist_ok=True)
        return p.resolve()
    return ilim_assistant_root()


def shared_root() -> Path:
    """Salt okunur ortak külliyat (knowledge, isteğe bağlı arşiv alt kümesi)."""
    raw = os.environ.get("RUZGAR_SHARED_ROOT", "").strip()
    if raw:
        return Path(raw).resolve()
    return ilim_assistant_root()


def normalize_user_id(raw: str | None) -> str:
    s = (raw or "").strip().lower()
    if not s:
        return "anon"
    s = s.replace("ı", "i").replace("ğ", "g").replace("ş", "s").replace("ö", "o").replace(
        "ü", "u"
    ).replace("ç", "c")
    s = _USER_SLUG_RE.sub("-", s).strip("-_")
    if not s:
        return "anon"
    return s[:64]


def current_user_id() -> str:
    env_uid = os.environ.get("RUZGAR_USER_ID", "").strip()
    if env_uid and not is_public_mode():
        return normalize_user_id(env_uid)
    return _USER_CTX.get()


def bind_request_user(raw_header: str | None) -> None:
    uid = normalize_user_id(raw_header or os.environ.get("RUZGAR_USER_ID", "") or "anon")
    token = _USER_CTX.set(uid)
    _USER_TOKEN.set(token)


def clear_request_user() -> None:
    token = _USER_TOKEN.get()
    if token is not None:
        _USER_CTX.reset(token)
        _USER_TOKEN.set(None)


def personal_dir(user_id: str | None = None) -> Path:
    uid = normalize_user_id(user_id or current_user_id())
    d = data_root() / "users" / uid
    d.mkdir(parents=True, exist_ok=True)
    return d


def personal_json_path(filename: str, user_id: str | None = None) -> Path:
    name = (filename or "").strip().lstrip("/\\")
    if not name or ".." in name.replace("\\", "/"):
        raise ValueError("Geçersiz kişisel dosya adı")
    return personal_dir(user_id) / name


def genel_hafiza_path(user_id: str | None = None) -> Path:
    if is_public_mode():
        return personal_json_path("ruzgar_genel_hafiza.json", user_id)
    return ilim_assistant_root() / "ruzgar_genel_hafiza.json"


def kullanici_baglami_path(user_id: str | None = None) -> Path:
    if is_public_mode():
        return personal_json_path("ruzgar_kullanici_baglami.json", user_id)
    return ilim_assistant_root() / "ruzgar_kullanici_baglami.json"


def shared_knowledge_root() -> Path:
    custom = os.environ.get("RUZGAR_KNOWLEDGE_ROOT", "").strip()
    if custom:
        return Path(custom).resolve()
    return shared_root() / "knowledge"


def shared_rag_index_dir() -> Path:
    raw = os.environ.get("RUZGAR_RAG_INDEX_DIR", "").strip()
    if raw:
        p = Path(raw)
        p.mkdir(parents=True, exist_ok=True)
        return p.resolve()
    bundled = shared_root() / ".rag_index"
    if is_public_mode() and bundled.is_dir():
        return bundled
    idx = ilim_assistant_root() / ".rag_index"
    idx.mkdir(parents=True, exist_ok=True)
    return idx


def shared_arsiv_root() -> Path | None:
    raw = os.environ.get("RUZGAR_SHARED_ARSIV_ROOT", "").strip()
    if raw:
        p = Path(raw)
        return p.resolve() if p.is_dir() else None
    candidate = shared_root() / "arsiv"
    return candidate.resolve() if candidate.is_dir() else None


def public_mode_health() -> dict[str, Any]:
    dr = data_root()
    sr = shared_root()
    kr = shared_knowledge_root()
    idx = shared_rag_index_dir()
    arsiv = shared_arsiv_root()
    return {
        "public_mode": is_public_mode(),
        "version": PUBLIC_MODE_VERSION,
        "data_root": str(dr),
        "shared_root": str(sr),
        "knowledge_root": str(kr),
        "knowledge_exists": kr.is_dir(),
        "rag_index_dir": str(idx),
        "rag_index_ready": (idx / "manifest.json").is_file(),
        "shared_arsiv": str(arsiv) if arsiv else None,
        "user_header": "X-Ruzgar-User",
        "personal_hafiza_pattern": str(dr / "users" / "{user_id}" / "ruzgar_genel_hafiza.json"),
    }
