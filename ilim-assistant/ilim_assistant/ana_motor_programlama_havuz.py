# Created by Ümit & Gökçenur
"""Ana Motor Faz B4 — programlama turu merkezi havuz (yazma + aktif okuma)."""

from __future__ import annotations

import os
import re
import unicodedata
from datetime import datetime, timezone
from typing import Any

ANA_MOTOR_PROG_HAVUZ_VERSION = "ana-motor-prog-havuz-read-v1-2026-06-15"
_MOTOR = "programlama"

_CODE_HINT_RE = re.compile(
    r"(?:görev|gorev|@@write|@@patch|@@read|pytest|projects/|\.py\b|kod|patch|"
    r"refactor|endpoint|commit|git\s|lint|debug|hata\s*ayik)",
    re.I,
)


def programlama_havuz_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_MOTOR_PROG_HAVUZ", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def programlama_havuz_read_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_MOTOR_PROG_HAVUZ_READ", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ascii_fold(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def should_inject_programlama_havuz(
    mode_norm: str,
    message: str = "",
    *,
    coding_mode: bool = False,
) -> bool:
    """Ana motor bu turda programlama havuzunu LLM bağlamına eklesin mi?"""
    if not programlama_havuz_enabled() or not programlama_havuz_read_enabled():
        return False
    if (mode_norm or "").strip().lower() == "programlama":
        return True
    if coding_mode:
        return True
    return bool(_CODE_HINT_RE.search(message or ""))


def read_programlama_havuz_snapshot() -> dict[str, Any]:
    """motor_kv + paylaşımlı pencereden programlama geçmişi."""
    out: dict[str, Any] = {
        "last_turn": None,
        "last_tool_outcome": None,
        "shared": [],
        "version": ANA_MOTOR_PROG_HAVUZ_VERSION,
    }
    if not programlama_havuz_read_enabled():
        return out
    try:
        from ilim_assistant.motorlar.merkezi_zihin_havuzu import get_havuz

        havuz = get_havuz()
        out["last_turn"] = havuz.motor_get(_MOTOR, "last_turn", default=None)
        out["last_tool_outcome"] = havuz.motor_get(_MOTOR, "last_tool_outcome", default=None)
        shared_rows = []
        for e in havuz.read_shared(limit=20):
            if (e.source_motor or "").strip().lower() == _MOTOR:
                shared_rows.append(
                    {
                        "key": e.key,
                        "value": (e.value or "")[:500],
                        "ts": e.ts,
                        "priority": e.priority,
                    }
                )
        out["shared"] = shared_rows[:6]
    except Exception:
        pass
    return out


def _format_last_turn(record: dict[str, Any] | None) -> str:
    if not isinstance(record, dict):
        return ""
    lines: list[str] = []
    if record.get("summary"):
        lines.append(str(record["summary"])[:700])
    elif record.get("user_preview"):
        lines.append(f"İstek: {str(record.get('user_preview'))[:220]}")
    files = record.get("files") or []
    if files:
        lines.append("Dosyalar: " + ", ".join(str(f) for f in files[:6]))
    if record.get("active_file"):
        lines.append(f"Aktif dosya: `{record.get('active_file')}`")
    if record.get("ts"):
        lines.append(f"Zaman: {record.get('ts')}")
    return " · ".join(lines)[:900]


def _format_tool_outcome(record: dict[str, Any] | None) -> str:
    if not isinstance(record, dict):
        return ""
    parts: list[str] = []
    if record.get("scope_rel"):
        parts.append(f"Proje: `{record.get('scope_rel')}`")
    if record.get("goal"):
        parts.append(f"Hedef: {str(record.get('goal'))[:240]}")
    writes = record.get("writes") or []
    patches = record.get("patches") or []
    if writes:
        parts.append("Yazılan: " + ", ".join(str(x) for x in writes[:5]))
    if patches:
        parts.append("Patch: " + ", ".join(str(x) for x in patches[:5]))
    if record.get("pytest_ok") is not None:
        parts.append(f"pytest: {'OK' if record.get('pytest_ok') else 'kırmızı'}")
    return " · ".join(parts)[:900]


def build_programlama_havuz_context_block(
    *,
    message: str = "",
    mode_norm: str = "programlama",
    workspace_root: str | None = None,
    active_file: str | None = None,
    compact: bool = False,
) -> str:
    """
    Ana motor aktif okuma — LLM bağlam bloğu.

    compact=True: programlama hafif bağlam (Faz 21) için kısa özet.
    """
    if not should_inject_programlama_havuz(mode_norm, message):
        return ""
    snap = read_programlama_havuz_snapshot()
    last_turn = snap.get("last_turn")
    last_tool = snap.get("last_tool_outcome")
    shared = snap.get("shared") or []
    if not last_turn and not last_tool and not shared:
        return ""

    cap = 800 if compact else 2200
    lines = [
        "[ANA MOTOR — Programlama hafızası — aktif okuma]",
        f"Mod: {mode_norm}",
    ]
    if workspace_root:
        lines.append(f"Workspace: `{str(workspace_root)[:180]}`")
    if active_file:
        lines.append(f"Editör: `{active_file}`")

    turn_txt = _format_last_turn(last_turn if isinstance(last_turn, dict) else None)
    if turn_txt:
        lines.append(f"Son kod turu: {turn_txt}")

    tool_txt = _format_tool_outcome(last_tool if isinstance(last_tool, dict) else None)
    if tool_txt:
        lines.append(f"Son araç işlemi: {tool_txt}")

    if shared and not compact:
        lines.append("Paylaşımlı notlar:")
        for row in shared[:4]:
            if isinstance(row, dict):
                lines.append(f"• {row.get('key')}: {str(row.get('value') or '')[:280]}")

    lines.append(
        "Talimat: Geçmiş kod işlerini kullanıcı istemedikçe tekrarlama; "
        "«devam et», «aynı proje» veya dosya adı geçince bağlam say."
    )
    lines.append(f"({ANA_MOTOR_PROG_HAVUZ_VERSION})")
    block = "\n".join(lines)
    return block[:cap]


def inject_programlama_havuz_into_payload(
    user_payload: str,
    *,
    message: str = "",
    mode_norm: str = "programlama",
    workspace_root: str | None = None,
    active_file: str | None = None,
    compact: bool = False,
) -> str:
    """user_payload önüne havuz bloğu ekler (yoksa aynen döner)."""
    blk = build_programlama_havuz_context_block(
        message=message,
        mode_norm=mode_norm,
        workspace_root=workspace_root,
        active_file=active_file,
        compact=compact,
    ).strip()
    if not blk:
        return user_payload
    if blk in user_payload:
        return user_payload
    return blk + "\n\n---\n" + (user_payload or "").lstrip()


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
