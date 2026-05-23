"""Rüzgar yerel API portu — tek kaynak (varsayılan 8779)."""

from __future__ import annotations

import os
import re
from pathlib import Path

DEFAULT_API_PORT = 8779
LEGACY_API_PORT = 8777


def _read_port_from_dotenv() -> int | None:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.is_file():
        return None
    try:
        raw = env_path.read_text(encoding="utf-8")
    except OSError:
        return None
    for line in raw.splitlines():
        t = line.strip()
        if not t or t.startswith("#") or "=" not in t:
            continue
        key, val = t.split("=", 1)
        if key.strip() != "RUZGAR_API_PORT":
            continue
        val = val.strip().strip('"').strip("'")
        if val.isdigit():
            return int(val)
    return None


def resolve_api_port() -> int:
    for key in ("PORT", "RUZGAR_API_PORT"):
        raw = (os.environ.get(key) or "").strip()
        if raw.isdigit():
            return int(raw)
    from_env = _read_port_from_dotenv()
    if from_env is not None:
        return from_env
    return DEFAULT_API_PORT


def default_api_base() -> str:
    return f"http://127.0.0.1:{resolve_api_port()}"


def migrate_legacy_api_url(url: str) -> str:
    """Eski 8777 kökünü 8779'a çevirir."""
    if not url:
        return url
    return re.sub(
        r"(127\.0\.0\.1|localhost):8777\b",
        lambda m: f"{m.group(1)}:{DEFAULT_API_PORT}",
        url,
        flags=re.I,
    )
