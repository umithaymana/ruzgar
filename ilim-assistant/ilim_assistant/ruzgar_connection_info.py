"""Rüzgar UI: beyin zinciri (Gemini / Groq / Ollama) ve bellek dosya yolları."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def _ilim_assistant_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _repo_root() -> Path | None:
    raw = (
        os.environ.get("RUZGAR_EXEC_CWD", "").strip()
        or os.environ.get("LOCAL_TOOLS_ROOT", "").strip()
    )
    if raw:
        p = Path(raw)
        if p.is_dir():
            return p.resolve()
    parent = _ilim_assistant_root().parent
    return parent.resolve() if parent.is_dir() else None


def _file_row(label: str, path: Path, *, note: str = "") -> dict[str, Any]:
    exists = path.is_file()
    size_kb = int(path.stat().st_size // 1024) if exists else 0
    row: dict[str, Any] = {
        "id": label.lower().replace(" ", "_"),
        "label": label,
        "path": str(path),
        "exists": exists,
        "size_kb": size_kb,
    }
    if note:
        row["note"] = note
    return row


def build_storage_paths() -> list[dict[str, Any]]:
    ia = _ilim_assistant_root()
    rows: list[dict[str, Any]] = []
    rows.append(
        _file_row(
            "Genel hafıza (soru=cevap)",
            ia / "ruzgar_genel_hafiza.json",
            note="Ana sohbet öğrenme dosyası",
        )
    )
    try:
        from ilim_assistant.hizir.bellek import merkezi_bellek_path

        rows.append(
            _file_row("Merkezi bellek (HIZIR)", merkezi_bellek_path(), note="Ticaret + önbellek")
        )
    except Exception:
        pass
    try:
        from ilim_assistant.kuvve_hafiza import DB_PATH

        rows.append(
            _file_row(
                "Kuvve-i Hafıza (sohbet DB)",
                DB_PATH,
                note="gecmis_sohbetler.db",
            )
        )
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.merkezi_zihin_havuzu import MerkeziZihinHavuzu

        pool = MerkeziZihinHavuzu()
        rows.append(_file_row("Merkezi zihin (SQLite)", pool.db_path))
        for store, fname in (
            ("ruzgar_genel", "ruzgar_genel_hafiza.json"),
            ("ogrenme", "ogrenme_merkezi.json"),
        ):
            try:
                p = pool.json_store_path(store)
                rows.append(_file_row(f"Zihin havuzu · {store}", p))
            except Exception:
                pass
    except Exception:
        pass
    repo = _repo_root()
    if repo:
        rows.append(
            {
                "id": "workspace",
                "label": "Çalışma kökü (workspace)",
                "path": str(repo),
                "exists": True,
                "is_dir": True,
                "note": "Dosya ağacı ve @@dosya okuma",
            }
        )
    return rows


def build_brain_status(super_brain: dict[str, Any] | None) -> dict[str, Any]:
    sb = super_brain if isinstance(super_brain, dict) else {}
    gd = sb.get("gemini_daemon") if isinstance(sb.get("gemini_daemon"), dict) else {}
    gp = sb.get("gemini_model_ping") if isinstance(sb.get("gemini_model_ping"), dict) else {}
    ollama_model = str(sb.get("profiles", {}).get("ollama_local", {}).get("model") or "")
    if not ollama_model:
        ollama_model = os.environ.get("OLLAMA_CHAT_MODEL", "llama3.2:3b")
    return {
        "default_chain": list(sb.get("default_chain") or []),
        "cloud_provider": str(sb.get("cloud_provider") or ""),
        "gemini": {
            "configured": bool(sb.get("gemini_configured")),
            "daemon_ok": bool(gd.get("ok")),
            "model": str(gd.get("model") or sb.get("gemini_model_default") or ""),
            "reason": str(gd.get("reason") or gp.get("reason") or ""),
            "cooldown": bool(sb.get("gemini_cooldown_active")),
        },
        "groq": {
            "configured": bool(sb.get("groq_configured")),
            "model": str(sb.get("groq_model") or ""),
        },
        "ollama": {
            "reachable": bool(sb.get("ollama_reachable")),
            "model": ollama_model,
            "only_mode": bool(sb.get("ollama_only")),
        },
    }


def build_connection_info(*, super_brain: dict[str, Any] | None = None) -> dict[str, Any]:
    brains = build_brain_status(super_brain)
    storage = build_storage_paths()
    return {
        "ok": True,
        "api_base_hint": f"http://127.0.0.1:{os.environ.get('RUZGAR_API_PORT', '8779')}",
        "brains": brains,
        "storage": storage,
    }
