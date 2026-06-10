# Created by Ümit & Gökçenur
"""Ana Motor Faz R2 — timeline hatırla geçmişi paneli."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

_PKG_ROOT = Path(__file__).resolve().parent.parent
_HISTORY_PATH = _PKG_ROOT / ".ruzgar" / "ana_motor_remember_history.jsonl"
_MAX_STORE = 200


def remember_history_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_REMEMBER_HISTORY", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _history_limit() -> int:
    try:
        return max(5, min(50, int(os.environ.get("RUZGAR_ANA_REMEMBER_HISTORY_LIMIT", "20"))))
    except ValueError:
        return 20


def append_remember_history(
    *,
    session_id: str,
    event_type: str = "",
    topic: str = "",
    file_count: int | None = None,
    ok: bool = True,
    source: str = "timeline",
) -> None:
    if not remember_history_enabled():
        return
    entry: dict[str, Any] = {
        "ts": time.time(),
        "session_id": str(session_id or "")[:64],
        "event_type": str(event_type or "")[:32],
        "topic": str(topic or "")[:200],
        "ok": bool(ok),
        "source": str(source or "timeline")[:24],
    }
    if file_count is not None:
        entry["file_count"] = int(file_count)
    try:
        _HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _HISTORY_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        _trim_history_file()
    except Exception:
        pass


def _trim_history_file() -> None:
    if not _HISTORY_PATH.is_file():
        return
    try:
        lines = _HISTORY_PATH.read_text(encoding="utf-8").splitlines()
        if len(lines) <= _MAX_STORE:
            return
        _HISTORY_PATH.write_text("\n".join(lines[-_MAX_STORE:]) + "\n", encoding="utf-8")
    except Exception:
        pass


def list_remember_history(*, limit: int | None = None) -> dict[str, Any]:
    if not remember_history_enabled():
        return {"ok": True, "items": [], "count": 0, "disabled": True}
    cap = int(limit if limit is not None else _history_limit())
    items: list[dict[str, Any]] = []
    if _HISTORY_PATH.is_file():
        try:
            for line in reversed(_HISTORY_PATH.read_text(encoding="utf-8").splitlines()):
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except Exception:
                    continue
                if isinstance(row, dict):
                    items.append(row)
                if len(items) >= cap:
                    break
        except Exception:
            pass
    return {"ok": True, "items": items, "count": len(items)}


def remember_history_export_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_REMEMBER_HISTORY_EXPORT", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _read_all_items(*, limit: int = 200) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    if not _HISTORY_PATH.is_file():
        return items
    try:
        for line in reversed(_HISTORY_PATH.read_text(encoding="utf-8").splitlines()):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except Exception:
                continue
            if isinstance(row, dict):
                items.append(row)
            if len(items) >= limit:
                break
    except Exception:
        pass
    return items


def export_remember_history_json(*, limit: int = 200) -> dict[str, Any]:
    if not remember_history_export_enabled():
        return {"ok": False, "error": "Hatırla geçmişi dışa aktarım kapalı."}
    items = _read_all_items(limit=limit)
    payload = {"generated_at": time.time(), "count": len(items), "items": items}
    return {
        "ok": True,
        "json": json.dumps(payload, ensure_ascii=False, indent=2),
        "count": len(items),
        "filename": "ruzgar_ana_motor_hatirla_gecmisi.json",
    }


def export_remember_history_csv(*, limit: int = 200) -> dict[str, Any]:
    if not remember_history_export_enabled():
        return {"ok": False, "error": "Hatırla geçmişi dışa aktarım kapalı."}
    import csv
    import io

    items = _read_all_items(limit=limit)
    if not items:
        return {"ok": False, "error": "Dışa aktarılacak hatırla geçmişi yok."}
    buf = io.StringIO()
    buf.write("\ufeff")
    writer = csv.DictWriter(
        buf,
        fieldnames=["ts", "session_id", "event_type", "topic", "ok", "source", "file_count"],
        extrasaction="ignore",
    )
    writer.writeheader()
    for row in items:
        writer.writerow(row)
    return {
        "ok": True,
        "csv": buf.getvalue(),
        "count": len(items),
        "filename": "ruzgar_ana_motor_hatirla_gecmisi.csv",
    }


def clear_remember_history() -> dict[str, Any]:
    if not remember_history_enabled():
        return {"ok": False, "error": "Hatırla geçmişi kapalı."}
    try:
        if _HISTORY_PATH.is_file():
            _HISTORY_PATH.unlink()
        return {"ok": True, "hint": "Hatırla geçmişi temizlendi."}
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:200]}
