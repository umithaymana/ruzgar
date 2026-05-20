# Created by Ümit & Gökçenur
"""
Rüzgar ortam yükleme — mevcut .env / yapılandırma dosyalarından Gemini anahtarını otomatik alır.

Taranan konumlar (sırayla; mevcut ortam değişkenini ezmez):
  - ilim-assistant/.env
  - repo kökü/.env
  - ilim-assistant/RUZGAR_BRAIN.env
  - ruzgar-desktop/google_api_key.txt (yalnızca anahtar satırı)
"""

from __future__ import annotations

import os
from pathlib import Path

from ilim_assistant.defaults import DEFAULT_GEMINI_MODEL

_ILIM_ROOT = Path(__file__).resolve().parent.parent
_REPO_ROOT = _ILIM_ROOT.parent

_GEMINI_KEY_NAMES = (
    "GLOBAL_API_KEY",
    "GOOGLE_GEMINI_API_KEY",
    "GEMINI_API_KEY",
    "RUZGAR_GEMINI_API_KEY",
)

_GEMINI_DEFAULTS: dict[str, str] = {
    "RUZGAR_GEMINI_MODEL": DEFAULT_GEMINI_MODEL,
    "RUZGAR_SUPER_BRAIN": "1",
    "RUZGAR_BRAIN_PROFILE": "auto",
}

_loaded_once = False


def _parse_env_line(raw: str) -> tuple[str, str] | None:
    line = raw.strip()
    if not line or line.startswith("#") or "=" not in line:
        return None
    key, _, val = line.partition("=")
    key = key.strip()
    val = val.strip()
    if (val.startswith('"') and val.endswith('"')) or (
        val.startswith("'") and val.endswith("'")
    ):
        val = val[1:-1]
    if not key:
        return None
    return key, val


def sync_global_api_key_aliases() -> str:
    """GLOBAL_API_KEY → tüm Gemini alias'ları (tek oturum, tekrar sorma)."""
    key = ""
    for name in _GEMINI_KEY_NAMES:
        key = os.environ.get(name, "").strip()
        if key:
            break
    if not key:
        return ""
    for name in _GEMINI_KEY_NAMES:
        os.environ[name] = key
    if not os.environ.get("GLOBAL_API_KEY", "").strip():
        os.environ["GLOBAL_API_KEY"] = key
    return key


def _apply_kv(key: str, val: str, *, source: str, loaded: list[str]) -> None:
    if not val:
        return
    if key in _GEMINI_KEY_NAMES:
        if not os.environ.get("GLOBAL_API_KEY", "").strip():
            os.environ["GLOBAL_API_KEY"] = val
            loaded.append(f"{source}:{key}")
        return
    if key not in os.environ:
        os.environ[key] = val
        if key.startswith("RUZGAR_GEMINI") or key.startswith("RUZGAR_SUPER"):
            loaded.append(f"{source}:{key}")


def _load_dotenv_file(path: Path, loaded: list[str]) -> None:
    if not path.is_file():
        return
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        try:
            text = path.read_text(encoding="utf-8-sig")
        except OSError:
            return
    for raw in text.splitlines():
        parsed = _parse_env_line(raw)
        if parsed is None:
            continue
        key, val = parsed
        _apply_kv(key, val, source=path.name, loaded=loaded)


def _load_google_api_key_txt(path: Path, loaded: list[str]) -> None:
    if not path.is_file():
        return
    if os.environ.get("GLOBAL_API_KEY", "").strip():
        return
    try:
        for raw in path.read_text(encoding="utf-8").splitlines():
            val = raw.strip()
            if val and not val.startswith("#"):
                os.environ["GLOBAL_API_KEY"] = val
                loaded.append(f"{path.name}:raw")
                return
    except OSError:
        pass


def ensure_ruzgar_env() -> list[str]:
    """Tüm bilinen yapılandırma dosyalarını tara; varsayılanları uygula."""
    global _loaded_once
    loaded: list[str] = []

    candidates = [
        _ILIM_ROOT / ".env",
        _REPO_ROOT / ".env",
        _ILIM_ROOT / "RUZGAR_BRAIN.env",
    ]
    for p in candidates:
        _load_dotenv_file(p, loaded)

    _load_google_api_key_txt(_REPO_ROOT / "ruzgar-desktop" / "google_api_key.txt", loaded)

    for key, val in _GEMINI_DEFAULTS.items():
        if not os.environ.get(key, "").strip():
            os.environ[key] = val

    if not os.environ.get("RUZGAR_GEMINI_MODEL", "").strip():
        os.environ["RUZGAR_GEMINI_MODEL"] = DEFAULT_GEMINI_MODEL

    sync_global_api_key_aliases()

    if loaded:
        os.environ["RUZGAR_ENV_LOADED_FROM"] = ",".join(loaded[:12])
    _loaded_once = True
    return loaded


def env_bootstrap_done() -> bool:
    return _loaded_once
