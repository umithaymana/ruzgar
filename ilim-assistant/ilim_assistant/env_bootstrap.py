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

# Varsayılan: yalnızca yerel Ollama (tam bağımsız)
_BRAIN_DEFAULTS: dict[str, str] = {
    "RUZGAR_OLLAMA_ONLY": "0",
    "RUZGAR_DISABLE_GEMINI": "0",
    "RUZGAR_DISABLE_GROQ": "0",
    "RUZGAR_FREE_BRAIN": "1",
    "RUZGAR_BRAIN_FALLBACK_CHAIN": "denge,hizli,kod",
    "RUZGAR_GEMINI_DAEMON": "0",
    "RUZGAR_FAST_BILGI_GEMINI": "0",
    "RUZGAR_CASUAL_FAST_GEMINI": "0",
    "RUZGAR_GEMINI_ONLY": "0",
    "RUZGAR_TARIH_GEMINI_FIRST": "0",
    "RUZGAR_FAZ9_GEMINI_FIRST_FOR_FACTS": "0",
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


def _apply_kv(
    key: str,
    val: str,
    *,
    source: str,
    loaded: list[str],
    force_secrets: bool = False,
) -> None:
    if not val:
        return
    if key in _GEMINI_KEY_NAMES:
        if force_secrets or not os.environ.get("GLOBAL_API_KEY", "").strip():
            os.environ["GLOBAL_API_KEY"] = val
            loaded.append(f"{source}:{key}")
        return
    if key == "GROQ_API_KEY" and force_secrets:
        os.environ["GROQ_API_KEY"] = val
        loaded.append(f"{source}:{key}")
        return
    if force_secrets and key.startswith(("RUZGAR_", "GROQ_", "OLLAMA_")):
        os.environ[key] = val
        return
    if key not in os.environ:
        os.environ[key] = val
        if key.startswith("RUZGAR_GEMINI") or key.startswith("RUZGAR_SUPER"):
            loaded.append(f"{source}:{key}")


def _load_dotenv_file(path: Path, loaded: list[str], *, force_secrets: bool = False) -> None:
    if not path.is_file():
        return
    force_project = path.name in (".env", "RUZGAR_BRAIN.env")
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
        if force_project and val and (
            key.startswith("RUZGAR_")
            or key.startswith("OLLAMA_")
            or key.startswith("GROQ_")
            or key in _GEMINI_KEY_NAMES
        ):
            os.environ[key] = val
            loaded.append(f"{path.name}:{key}")
            continue
        _apply_kv(
            key,
            val,
            source=path.name,
            loaded=loaded,
            force_secrets=force_secrets,
        )


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
    brain_env = _ILIM_ROOT / "RUZGAR_BRAIN.env"
    if brain_env.is_file():
        _load_dotenv_file(brain_env, loaded, force_secrets=True)

    _load_google_api_key_txt(_REPO_ROOT / "ruzgar-desktop" / "google_api_key.txt", loaded)

    for key, val in _GEMINI_DEFAULTS.items():
        if not os.environ.get(key, "").strip():
            os.environ[key] = val

    for key, val in _BRAIN_DEFAULTS.items():
        if not os.environ.get(key, "").strip():
            os.environ[key] = val

    if not os.environ.get("RUZGAR_GEMINI_MODEL", "").strip():
        os.environ["RUZGAR_GEMINI_MODEL"] = DEFAULT_GEMINI_MODEL

    # Ümit abi kesin emri v2 — hafıza → yerel Ollama → Groq → Gemini (varsayılan açık)
    if os.environ.get("RUZGAR_UMED_CEVAP_EMRI", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    ):
        os.environ.setdefault("RUZGAR_FREE_BRAIN", "1")
        os.environ.setdefault("RUZGAR_DISABLE_LOCAL_OLLAMA", "0")
        os.environ.setdefault("RUZGAR_GENEL_LOCAL_FIRST", "1")
        os.environ.setdefault("RUZGAR_BRAIN_FALLBACK_CHAIN", "denge,hizli,groq,gemini")
        os.environ.setdefault("RUZGAR_FAST_BILGI_GEMINI", "0")
        os.environ.setdefault("RUZGAR_CASUAL_FAST_GEMINI", "0")
        os.environ.setdefault("RUZGAR_TARIH_GEMINI_FIRST", "0")
        os.environ.setdefault("RUZGAR_FAZ9_GEMINI_FIRST_FOR_FACTS", "0")
        os.environ.setdefault("RUZGAR_EGITIM_MISS_SEC", "15")
        os.environ.setdefault("RUZGAR_UMED_BUDGET_SEC", "15")
        os.environ.setdefault("RUZGAR_UMED_ILIM_BUDGET_SEC", "22")
        os.environ.setdefault("RUZGAR_DOGAL_SOHBET", "1")
        os.environ.setdefault("RUZGAR_DOGAL_BUDGET_SEC", "32")
        os.environ.setdefault("RUZGAR_DOGAL_MAX_TOKENS", "720")
        os.environ.setdefault("RUZGAR_ANA_AGENT_LOOP", "1")
        os.environ.setdefault("RUZGAR_ANA_AGENT_V2", "1")
        os.environ.setdefault("RUZGAR_ANA_AGENT_MAX_TURNS", "5")
        os.environ.setdefault("RUZGAR_ANA_MULTIHOP_RAG", "1")
        os.environ.setdefault("RUZGAR_ANA_CHAT_SIMPLE", "1")
        os.environ.setdefault("RUZGAR_ANA_ARCHIVE_FOLD", "1")
        os.environ.setdefault("RUZGAR_ANA_MOTOR_REHBERI", "1")
        os.environ.setdefault("RUZGAR_ANA_CHAT_HISTORY", "1")
        os.environ.setdefault("RUZGAR_ANA_KAYNAK_PANEL", "1")
        os.environ.setdefault("RUZGAR_ANA_KAYNAK_PANEL_FOLD", "1")
        os.environ.setdefault("RUZGAR_ANA_CHECKPOINT", "1")
        os.environ.setdefault("RUZGAR_ANA_PROGRESS_ETA", "1")
        os.environ.setdefault("RUZGAR_CASUAL_OLLAMA_READ_TIMEOUT_SEC", "22")
        os.environ.setdefault("RUZGAR_CASUAL_BRAIN_CHAIN", "groq,hizli,denge,gemini")
        os.environ.setdefault("RUZGAR_WEB_ARASTIRMA_PRO", "1")
        os.environ.setdefault("RUZGAR_WEB_SECONDARY_ONLY_ON_EMPTY", "0")
        os.environ.setdefault("RUZGAR_WEB_PRO_MAX_RESULTS", "14")
        os.environ.setdefault("RUZGAR_WEB_PRO_FETCH_URLS", "6")
        os.environ.setdefault("RUZGAR_WEB_PRO_MULTI_QUERY", "1")
        os.environ.setdefault("RUZGAR_WEB_PRO_PER_QUERY", "8")
        os.environ.setdefault("ENABLE_WEB_SEARCH", "1")
        os.environ.setdefault("WEB_MAX_RESULTS", "12")

    sync_global_api_key_aliases()
    try:
        from ilim_assistant.config import (
            gemini_disabled,
            groq_disabled,
            suppress_cloud_runtime_keys,
        )

        suppress_cloud_runtime_keys()
        if not gemini_disabled() and brain_env.is_file():
            _load_dotenv_file(brain_env, loaded, force_secrets=True)
            sync_global_api_key_aliases()
        if not groq_disabled() and brain_env.is_file():
            _load_dotenv_file(brain_env, loaded, force_secrets=True)
    except Exception:
        pass
    try:
        from ilim_assistant.defaults import (
            DEFAULT_OLLAMA_CHAT_MODEL,
            DEFAULT_OLLAMA_FAST_MODEL,
        )

        if not os.environ.get("OLLAMA_CHAT_MODEL", "").strip():
            os.environ["OLLAMA_CHAT_MODEL"] = DEFAULT_OLLAMA_CHAT_MODEL
        if not os.environ.get("RUZGAR_BRAIN_DENGE_MODEL", "").strip():
            os.environ["RUZGAR_BRAIN_DENGE_MODEL"] = DEFAULT_OLLAMA_CHAT_MODEL
        if not os.environ.get("RUZGAR_BRAIN_HIZLI_MODEL", "").strip():
            os.environ["RUZGAR_BRAIN_HIZLI_MODEL"] = DEFAULT_OLLAMA_FAST_MODEL
    except Exception:
        pass

    if loaded:
        os.environ["RUZGAR_ENV_LOADED_FROM"] = ",".join(loaded[:12])
    _loaded_once = True
    return loaded


def env_bootstrap_done() -> bool:
    return _loaded_once
