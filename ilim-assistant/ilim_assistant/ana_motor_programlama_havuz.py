# Created by Ümit & Gökçenur
"""Ana Motor Faz B4 — programlama turu sonrası merkezi havuz (motor_kv)."""

from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from typing import Any


def programlama_havuz_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_MOTOR_PROG_HAVUZ", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _extract_patch_files(patch_meta: dict[str, Any] | None) -> list[str]:
    if not patch_meta:
        return []
    files: list[str] = []
    for key in ("written", "patches", "files"):
        val = patch_meta.get(key)
        if isinstance(val, list):
            for item in val:
                if isinstance(item, str):
                    files.append(item)
                elif isinstance(item, dict):
                    p = item.get("path") or item.get("rel") or item.get("file")
                    if p:
                        files.append(str(p))
    footer = str(patch_meta.get("footer") or "")
    for m in re.finditer(r"@@write\s+(\S+)", footer):
        files.append(m.group(1))
    return list(dict.fromkeys(files))[:12]


def _summarize_turn(user_message: str, reply: str, patch_meta: dict[str, Any] | None) -> str:
    um = (user_message or "").strip().replace("\n", " ")[:200]
    rp = (reply or "").strip().replace("\n", " ")[:280]
    files = _extract_patch_files(patch_meta)
    parts = [f"İstek: {um}"]
    if files:
        parts.append("Dosyalar: " + ", ".join(files[:6]))
    if rp:
        parts.append(f"Yanıt özeti: {rp}")
    return " | ".join(parts)[:900]


def persist_programlama_turn(
    user_message: str,
    reply: str,
    *,
    workspace_root: str | None = None,
    active_file: str | None = None,
    patch_meta: dict[str, Any] | None = None,
) -> bool:
    """Kod turu bitince merkezi havuza motor_kv yazar."""
    if not programlama_havuz_enabled():
        return False
    try:
        from ilim_assistant.motorlar.merkezi_zihin_havuzu import get_havuz

        havuz = get_havuz()
        ts = _utc_now_iso()
        summary = _summarize_turn(user_message, reply, patch_meta)
        files = _extract_patch_files(patch_meta)
        record = {
            "ts": ts,
            "workspace": (workspace_root or "")[:260],
            "active_file": (active_file or "")[:260],
            "files": files,
            "summary": summary,
            "user_preview": (user_message or "").strip()[:300],
            "reply_preview": (reply or "").strip()[:500],
        }
        havuz.motor_set("programlama", "last_turn", record)
        havuz.motor_set("programlama", f"turn:{ts[:19]}", record)
        havuz.publish_shared(
            "programlama",
            f"kod_turu:{ts[:19]}",
            summary,
            priority=4,
            ttl_sec=int(os.environ.get("RUZGAR_PROG_SHARED_TTL", "172800")),
        )
        return True
    except Exception:
        return False
