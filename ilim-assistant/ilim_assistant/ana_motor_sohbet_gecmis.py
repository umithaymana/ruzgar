# Created by Ümit & Gökçenur
"""Ana Motor Faz AA1 — sohbet geçmişi arama (jsonl + API)."""

from __future__ import annotations

import json
import os
import re
import time
import unicodedata
from pathlib import Path
from typing import Any

FAZ_AA_CHAT_VERSION = "ana-motor-sohbet-gecmis-aa1-2026-06-10"

_PKG_ROOT = Path(__file__).resolve().parent.parent
_HISTORY_PATH = _PKG_ROOT / ".ruzgar" / "ana_motor_chat_history.jsonl"
_MAX_STORE = 500


def chat_history_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_CHAT_HISTORY", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _default_limit() -> int:
    try:
        return max(5, min(int(os.environ.get("RUZGAR_ANA_CHAT_HISTORY_LIMIT", "30")), 100))
    except ValueError:
        return 30


def _normalize_query(q: str) -> str:
    t = unicodedata.normalize("NFKC", (q or "").strip().lower())
    t = re.sub(r"\s+", " ", t)
    return t


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


def append_chat_turn(
    *,
    user_message: str,
    assistant_message: str,
    mode_norm: str = "genel",
    session_id: str | None = None,
    plan_primary: str = "",
) -> dict[str, Any]:
    if not chat_history_enabled():
        return {"ok": True, "stored": False, "reason": "disabled"}
    user = (user_message or "").strip()
    reply = (assistant_message or "").strip()
    if not user or not reply or reply.startswith("["):
        return {"ok": True, "stored": False, "reason": "empty"}
    entry: dict[str, Any] = {
        "ts": time.time(),
        "mode": str(mode_norm or "genel")[:24],
        "user": user[:2000],
        "assistant": reply[:4000],
        "plan_primary": str(plan_primary or "")[:32],
    }
    if session_id:
        entry["session_id"] = str(session_id)[:64]
    try:
        _HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _HISTORY_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        _trim_history_file()
        return {"ok": True, "stored": True, "version": FAZ_AA_CHAT_VERSION}
    except Exception as exc:
        return {"ok": False, "stored": False, "error": str(exc)[:160]}


def _load_entries(*, limit: int | None = None) -> list[dict[str, Any]]:
    cap = int(limit if limit is not None else _default_limit())
    if not _HISTORY_PATH.is_file():
        return []
    items: list[dict[str, Any]] = []
    try:
        lines = _HISTORY_PATH.read_text(encoding="utf-8").splitlines()
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                items.append(row)
            if len(items) >= cap:
                break
    except Exception:
        return []
    return items


def recent_chat_history(*, limit: int | None = None) -> dict[str, Any]:
    if not chat_history_enabled():
        return {"ok": True, "items": [], "count": 0, "disabled": True}
    items = _load_entries(limit=limit)
    return {
        "ok": True,
        "version": FAZ_AA_CHAT_VERSION,
        "items": items,
        "count": len(items),
    }


def try_past_conversation_reply(message: str, *, limit: int = 8) -> str | None:
    """«Dün ne konuştuk» — kayıtlı jsonl geçmişinden özet (LLM beklemeden)."""
    if not chat_history_enabled():
        return None
    try:
        from ilim_assistant.ana_motor_plan import looks_like_past_conversation_query

        if not looks_like_past_conversation_query(message):
            return None
    except Exception:
        return None
    data = recent_chat_history(limit=limit)
    items = list(data.get("items") or [])
    if not items:
        return (
            "Ümit abi, kayıtlı önceki oturum sohbeti bulamadım — "
            "bugünkü penceredeki konuşmalara bakabiliriz; istersen önemli bir şeyi «hatırla» ile yazdır."
        )
    lines = [
        "Ümit abi, kayıtlı son sohbetlerden hatırladıklarım:",
        "",
    ]
    for row in items[: min(5, len(items))]:
        u = str(row.get("user") or "").strip()
        a = str(row.get("assistant") or "").strip()
        if not u:
            continue
        lines.append(f"· **Sen:** {u[:120]}")
        if a:
            lines.append(f"  **Rüzgar:** {a[:200]}")
        lines.append("")
    lines.append(
        "(Bunlar diske kayıtlı son turlar; bilgisayar kapandıysa yalnızca «hatırla» ile yazdıkların kalıcıdır.)"
    )
    return "\n".join(lines).strip()


def search_chat_history(
    query: str,
    *,
    limit: int | None = None,
    mode: str | None = None,
) -> dict[str, Any]:
    if not chat_history_enabled():
        return {"ok": True, "items": [], "count": 0, "disabled": True}
    q = _normalize_query(query)
    if len(q) < 2:
        return {"ok": False, "error": "sorgu_kisa", "items": [], "count": 0}
    cap = int(limit if limit is not None else _default_limit())
    mode_f = (mode or "").strip().lower()
    hits: list[dict[str, Any]] = []
    for row in _load_entries(limit=_MAX_STORE):
        blob = _normalize_query(
            f"{row.get('user', '')} {row.get('assistant', '')} {row.get('plan_primary', '')}"
        )
        if mode_f and str(row.get("mode") or "").lower() != mode_f:
            continue
        if q not in blob:
            continue
        snippet_u = str(row.get("user") or "")[:160]
        snippet_a = str(row.get("assistant") or "")[:240]
        hits.append(
            {
                "ts": row.get("ts"),
                "mode": row.get("mode"),
                "user_snippet": snippet_u,
                "assistant_snippet": snippet_a,
                "plan_primary": row.get("plan_primary"),
                "session_id": row.get("session_id"),
            }
        )
        if len(hits) >= cap:
            break
    return {
        "ok": True,
        "version": FAZ_AA_CHAT_VERSION,
        "query": query,
        "items": hits,
        "count": len(hits),
    }
