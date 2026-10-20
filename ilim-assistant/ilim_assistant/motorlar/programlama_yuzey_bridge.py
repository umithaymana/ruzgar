# Created by Ümit & Gökçenur
"""
Programlama — Yüzey → görev satırı köprüsü (Faz88 E1).

Ana Motor yüzeyinden (belge/kod/not) gelen metni ajanın anlayacağı
`görev: …` satırına çevirir; handoff workbench paketini aynı turda doldurur.
Serbest kod çalıştırma yok — yalnız satır çıkarımı + handoff özeti.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

YUZEY_BRIDGE_VERSION = "programlama-yuzey-bridge-v1-2026-10-20"

_HEADER_RE = re.compile(
    r"^#\s*(?:Yüzey|Yuzey|Kaynak yetenek|Faz85|Programlama)\b",
    re.I,
)
_EXPLICIT_GOREV_RE = re.compile(
    r"^(?:görev|gorev|iş|is|yap)\s*:\s*(.+)$",
    re.I,
)
_ACTION_HINT_RE = re.compile(
    r"(?:pytest|health|endpoint|smoke|version|düzelt|duzelt|ekle|yaz|"
    r"geçir|gecir|oluştur|olustur|refactor|fix|add|create|build|"
    r"güncelle|guncelle|test)",
    re.I,
)
_CODE_HEAVY_RE = re.compile(
    r"(?:^\s*(?:def|class|import|from|function|const|let|var)\b|"
    r"[{};]\s*$|^\s*[@#]{2}write\b)",
    re.I | re.M,
)
_TODO_RE = re.compile(
    r"^(?:#|//)\s*(?:TODO|FIXME|görev|gorev)\s*[:\-]?\s*(.+)$",
    re.I,
)


def extract_surface_goal(surface_text: str) -> str:
    """Yüzey metninden ham hedef metni (görev: öneki olmadan)."""
    raw = (surface_text or "").replace("\r\n", "\n").replace("\r", "\n")
    lines = [ln.strip() for ln in raw.split("\n")]
    body_lines: list[str] = []
    for ln in lines:
        if not ln:
            continue
        # "# görev: …" veya düz "görev: …"
        stripped_hash = ln.lstrip("# ").strip() if ln.lstrip().startswith("#") else ln
        m = _EXPLICIT_GOREV_RE.match(stripped_hash)
        if m:
            return (m.group(1) or "").strip()[:500]
        if _HEADER_RE.search(ln):
            continue
        if ln.startswith("#") and not _TODO_RE.match(ln):
            continue
        body_lines.append(ln)

    body = " ".join(body_lines).strip()
    if not body:
        return ""

    # Kod ağırlıklı paket: TODO / eylem satırı, yoksa güvenli iskelet
    if _CODE_HEAVY_RE.search(body) and len(body) > 220:
        for ln in body_lines[:12]:
            todo = _TODO_RE.match(ln)
            if todo:
                return todo.group(1).strip()[:400]
            if _ACTION_HINT_RE.search(ln) and not _CODE_HEAVY_RE.search(ln) and len(ln) < 180:
                return ln[:400]
        return "bu kodu gözden geçir ve pytest geçir"

    if _ACTION_HINT_RE.search(body) or len(body) <= 400:
        return body[:500]
    return body[:400]


def build_surface_task_line(
    surface_text: str,
    workspace_root: str | Path | None = None,
    *,
    active_file: str | None = None,
) -> str:
    """
    Yüzey metni → sohbet kutusuna konacak `görev: …` satırı.
    Aktif proje varsa Faz68 `build_agent_task_line` ile zenginleştirilir.
    """
    goal = extract_surface_goal(surface_text)
    if not goal:
        return ""

    low = goal.lower()
    if low.startswith(("görev:", "gorev:", "iş:", "is:", "yap:")):
        return goal[:600]

    try:
        from ilim_assistant.motorlar.programlama_faz68 import build_agent_task_line

        line = build_agent_task_line(
            goal,
            workspace_root,
            active_file=active_file,
        )
        if line:
            return line[:600]
    except Exception:
        pass

    return f"görev: {goal}"[:600]


def build_surface_handoff_payload(
    surface_text: str,
    workspace_root: str | Path | None = None,
    *,
    active_file: str | None = None,
) -> dict[str, Any]:
    """Yüzey → görev satırı + handoff workbench (tek paket)."""
    from ilim_assistant.motorlar.programlama_handoff_workbench import (
        build_handoff_workbench_payload,
    )

    goal = extract_surface_goal(surface_text)
    task_line = build_surface_task_line(
        surface_text,
        workspace_root,
        active_file=active_file,
    )
    wb = build_handoff_workbench_payload(
        workspace_root,
        message=task_line or goal or "programlama görevi",
        active_file=active_file,
    )
    # Dosya yazmadan ipucu: bilinen Faz85 kalıpları vs ajan
    path_hint = _path_hint_for_goal(goal)

    return {
        "ok": True,
        "version": YUZEY_BRIDGE_VERSION,
        "goal": goal,
        "task_line": task_line,
        "path_hint": path_hint,
        "handoff_workbench": wb,
        "note": (
            "Faz85 hızlı yol adayı"
            if path_hint == "faz85_fast"
            else "Karmaşık / eşleşmeyen → ajan yolu (Faz14/88)"
        ),
    }


def _path_hint_for_goal(goal: str) -> str:
    """Çalıştırmadan: basit health/version/verify → faz85; aksi ajan."""
    g = (goal or "").lower()
    if not g:
        return "agent"
    try:
        from ilim_assistant.motorlar.programlama_faz85 import goal_wants_agent_path

        if goal_wants_agent_path(goal):
            return "agent"
    except Exception:
        pass
    simple = (
        ("health" in g and ("version" in g or "ok" in g or "düzelt" in g or "duzelt" in g))
        or ("pytest" in g and "geçir" in g and len(g) < 80)
        or ("pytest" in g and "gecir" in g and len(g) < 80)
        or ("yeni" in g and "api" in g and "health" in g)
    )
    return "faz85_fast" if simple else "agent"
