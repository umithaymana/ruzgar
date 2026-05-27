from __future__ import annotations

import os
import time
from typing import Any


def _enabled() -> bool:
    return os.environ.get("RUZGAR_SESSION_MEMORY_CONTEXT", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _clip(text: str, limit: int) -> str:
    t = " ".join((text or "").split())
    return t if len(t) <= limit else t[: max(0, limit - 1)].rstrip() + "…"


def _personal_notes(limit: int) -> list[str]:
    try:
        from ilim_assistant.hafiza_i_ruzgar import get_hafiza_motor

        items = get_hafiza_motor().tum_bilgiler(motor_tipi="Hafıza")
    except Exception:
        return []
    notes: list[str] = []
    for key, val in items.items():
        if key.startswith("Kişisel not:"):
            notes.append(_clip(str(val), 220))
    return notes[-limit:]


def _shared_memory(limit: int) -> list[str]:
    try:
        from ilim_assistant.motorlar.merkezi_zihin_havuzu import get_havuz

        rows = get_havuz().read_shared(limit=limit)
    except Exception:
        return []
    out: list[str] = []
    for row in rows:
        key = _clip(getattr(row, "key", ""), 80)
        val = _clip(getattr(row, "value", ""), 260)
        src = _clip(getattr(row, "source_motor", "motor"), 40)
        if key or val:
            out.append(f"[{src}] {key}: {val}".strip())
    return out


def _active_tasks(limit: int) -> list[str]:
    try:
        from ilim_assistant.gorev_yoneticisi import list_tasks

        rows = list_tasks(limit=50)
    except Exception:
        return []
    out: list[str] = []
    for row in rows:
        status = str(row.get("status") or "")
        if status in {"done", "cancelled"}:
            continue
        title = _clip(str(row.get("title") or ""), 160)
        if title:
            out.append(f"#{row.get('id')} [{status or 'pending'}] {title}")
        if len(out) >= limit:
            break
    return out


def _pending_reminders(limit: int) -> list[str]:
    try:
        from ilim_assistant.dinamit_hatirlatici import fetch_due_reminders

        rows = fetch_due_reminders(time.time() + 60 * 60 * 24 * 365)
    except Exception:
        return []
    out: list[str] = []
    for row in rows[:limit]:
        msg = _clip(str(row.get("mesaj") or ""), 160)
        if msg:
            out.append(f"#{row.get('id')} {msg}")
    return out


def memory_capacity_snapshot() -> dict[str, Any]:
    """Sistem raporu için aktif hafıza kapasitesi ve yüklenen kalıcı bağlam özeti."""
    try:
        from ilim_assistant.hafiza_i_ruzgar import get_hafiza_motor

        all_hafiza = get_hafiza_motor().tum_bilgiler(motor_tipi="Hafıza")
        personal_count = sum(1 for k in all_hafiza if str(k).startswith("Kişisel not:"))
        hafiza_total = len(all_hafiza)
    except Exception:
        personal_count = 0
        hafiza_total = 0

    shared_count = 0
    try:
        from ilim_assistant.motorlar.merkezi_zihin_havuzu import get_havuz

        shared_count = len(get_havuz().read_shared(limit=200))
    except Exception:
        pass

    tasks = _active_tasks(200)
    reminders = _pending_reminders(200)
    return {
        "session_memory_context_enabled": _enabled(),
        "hafiza_total": hafiza_total,
        "personal_notes": personal_count,
        "shared_sqlite_context": shared_count,
        "active_tasks": len(tasks),
        "pending_reminders": len(reminders),
        "context_limits": {
            "personal_notes": int(os.environ.get("RUZGAR_SESSION_PERSONAL_LIMIT", "8")),
            "shared_sqlite_context": int(os.environ.get("RUZGAR_SESSION_SHARED_LIMIT", "8")),
            "active_tasks": int(os.environ.get("RUZGAR_SESSION_TASK_LIMIT", "6")),
            "pending_reminders": int(os.environ.get("RUZGAR_SESSION_REMINDER_LIMIT", "5")),
        },
    }


def build_session_memory_context(
    message: str,
    *,
    mode_norm: str = "genel",
    history: list | None = None,
) -> str:
    """Her sohbet turuna kısa kalıcı hafıza bloğu ekler; yeni oturumda da disk/SQLite'tan yüklenir."""
    if not _enabled():
        return ""
    personal = _personal_notes(int(os.environ.get("RUZGAR_SESSION_PERSONAL_LIMIT", "8")))
    shared = _shared_memory(int(os.environ.get("RUZGAR_SESSION_SHARED_LIMIT", "8")))
    tasks = _active_tasks(int(os.environ.get("RUZGAR_SESSION_TASK_LIMIT", "6")))
    reminders = _pending_reminders(int(os.environ.get("RUZGAR_SESSION_REMINDER_LIMIT", "5")))

    egitim_block = ""
    try:
        from ilim_assistant.ruzgar_egitim import build_egitim_context_block

        egitim_block = build_egitim_context_block()
    except Exception:
        egitim_block = ""

    bilissel_block = ""
    try:
        from ilim_assistant.ruzgar_bilissel_analiz import build_bilissel_turn_context

        bilissel_block = build_bilissel_turn_context(
            message, history=history
        ).strip()
    except Exception:
        bilissel_block = ""

    if (
        not any((personal, shared, tasks, reminders))
        and not egitim_block.strip()
        and not bilissel_block
    ):
        try:
            from ilim_assistant.kullanici_baglami import build_context_block

            kb = (build_context_block() or "").strip()
            if kb:
                return kb + "\n"
        except Exception:
            pass
        return ""

    sections: list[str] = [
        "[RÜZGAR KALICI HAFIZA — yeni oturumda otomatik yüklendi]",
        f"Mod: {mode_norm or 'genel'}",
    ]
    if bilissel_block:
        sections.append(bilissel_block)
    try:
        from ilim_assistant.kullanici_baglami import build_context_block

        kb = (build_context_block() or "").strip()
        if kb:
            sections.append(kb)
    except Exception:
        pass
    if egitim_block.strip():
        sections.append(egitim_block.strip())
    if personal:
        sections.append("Kişisel profil notları:")
        sections.extend(f"- {x}" for x in personal)
    if shared:
        sections.append("SQLite merkezi zihin / son oturum bağlamı:")
        sections.extend(f"- {x}" for x in shared)
    if tasks:
        sections.append("Aktif görevler:")
        sections.extend(f"- {x}" for x in tasks)
    if reminders:
        sections.append("Bekleyen hatırlatıcılar:")
        sections.extend(f"- {x}" for x in reminders)
    sections.append(
        "Talimat: Bu bloğu kullanıcıya aynen okuma; kişisel asistan hafızası olarak kullan. "
        "Kullanıcı 'beni hatırlıyor musun' derse bu notlardan doğal ve kısa cevap ver."
    )
    sections.append("[/RÜZGAR KALICI HAFIZA]")
    return "\n".join(sections) + "\n"
