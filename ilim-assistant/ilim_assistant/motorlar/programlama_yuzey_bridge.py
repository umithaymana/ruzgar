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

YUZEY_BRIDGE_VERSION = "programlama-yuzey-bridge-v1.5-ray-p2-2026-10-23"
_EPHEMERAL_PROJECT_RE = re.compile(
    r"^(?:smoke[-_]|e2-bat-|e2-boot-|agent-bat-|e2-bat)",
    re.I,
)

_HEADER_RE = re.compile(
    r"^#\s*(?:Yüzey|Yuzey|Kaynak yetenek|Faz85|Programlama)\b",
    re.I,
)
_KAYNAK_TUR_RE = re.compile(
    r"^#\s*Kaynak yetenek\s*:\s*(belge|tablo|kod|notlar|cizim|çizim|sunum)\b",
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
_TABLO_CELL_RE = re.compile(
    r"^([A-La-l])(\d{1,2})\s*[\t:=]\s*(.+)$",
)


def _detect_kaynak_tur(lines: list[str]) -> str:
    for ln in lines[:8]:
        m = _KAYNAK_TUR_RE.match(ln.strip())
        if m:
            raw = (m.group(1) or "").strip().lower()
            return (
                raw.replace("ç", "c")
                .replace("ı", "i")
                .replace("ş", "s")
                .replace("ğ", "g")
                .replace("ü", "u")
                .replace("ö", "o")
            )
    return ""


def _goal_from_tablo_cells(body_lines: list[str]) -> str:
    """A1=… / A1\\t… hücrelerinden görev veya eylem özeti."""
    cells: list[str] = []
    for ln in body_lines:
        m = _TABLO_CELL_RE.match(ln.strip())
        if m:
            cells.append((m.group(3) or "").strip())
            continue
        if "\t" in ln:
            parts = [p.strip() for p in ln.split("\t") if p.strip()]
            cells.extend(parts)
    if not cells:
        return ""
    for c in cells:
        em = _EXPLICIT_GOREV_RE.match(c)
        if em:
            return (em.group(1) or "").strip()[:500]
        if _ACTION_HINT_RE.search(c) and len(c) <= 220:
            return c[:400]
    joined = " · ".join(cells[:12])
    if _ACTION_HINT_RE.search(joined):
        return joined[:500]
    return f"tablodaki satırları uygula: {joined}"[:500]


def _goal_from_belge_lines(body_lines: list[str]) -> str:
    """Belge gövdesi — görev satırı veya eylem ipucu."""
    for ln in body_lines[:20]:
        em = _EXPLICIT_GOREV_RE.match(ln)
        if em:
            return (em.group(1) or "").strip()[:500]
        todo = _TODO_RE.match(ln)
        if todo:
            return todo.group(1).strip()[:400]
    body = " ".join(body_lines).strip()
    if not body:
        return ""
    if _ACTION_HINT_RE.search(body) or len(body) <= 400:
        return body[:500]
    # Uzun belge: ilk anlamlı satır + eylem yoksa güvenli iskelet
    for ln in body_lines:
        if len(ln) >= 12 and not ln.startswith("#"):
            if _ACTION_HINT_RE.search(ln):
                return ln[:400]
            return f"{ln[:180]} — belgedeki talimatı uygula"[:400]
    return body[:400]


def _goal_from_sunum_lines(body_lines: list[str]) -> str:
    """Slayt başlık/metin — görev veya eylem özeti."""
    for ln in body_lines[:30]:
        em = _EXPLICIT_GOREV_RE.match(ln)
        if em:
            return (em.group(1) or "").strip()[:500]
        todo = _TODO_RE.match(ln)
        if todo:
            return todo.group(1).strip()[:400]
        if _ACTION_HINT_RE.search(ln) and len(ln) <= 220:
            return ln[:400]
    # Slayt N: başlık — anlamlı içerik
    slides: list[str] = []
    for ln in body_lines:
        if re.match(r"^slayt\s+\d+", ln, re.I) or ln:
            if not ln.startswith("#") and len(ln.strip()) >= 3:
                slides.append(ln.strip())
    joined = " · ".join(slides[:16])
    if not joined:
        return ""
    if _ACTION_HINT_RE.search(joined):
        return joined[:500]
    return f"sunumdaki slayt metinlerini uygula: {joined}"[:500]


def _goal_from_cizim_lines(body_lines: list[str]) -> str:
    """Çizim özeti — görev satırı veya güvenli iskelet."""
    for ln in body_lines[:20]:
        em = _EXPLICIT_GOREV_RE.match(ln)
        if em:
            return (em.group(1) or "").strip()[:500]
        if _ACTION_HINT_RE.search(ln) and len(ln) <= 220:
            return ln[:400]
    low = " ".join(body_lines).lower()
    if any(k in low for k in ("dolu", "iz var", "kalem", "şekil", "sekil")):
        return "çizim yüzeyindeki içeriği özetle ve kısa uygulama notu yaz"
    if any(k in low for k in ("boş", "bos", "empty")):
        return ""
    body = " ".join(body_lines).strip()
    return body[:400] if body else ""


def extract_surface_goal(surface_text: str) -> str:
    """Yüzey metninden ham hedef metni (görev: öneki olmadan)."""
    raw = (surface_text or "").replace("\r\n", "\n").replace("\r", "\n")
    lines = [ln.strip() for ln in raw.split("\n")]
    kaynak = _detect_kaynak_tur(lines)
    body_lines: list[str] = []
    for ln in lines:
        if not ln:
            continue
        # "# görev: …" veya düz "görev: …"
        stripped_hash = ln.lstrip("# ").strip() if ln.lstrip().startswith("#") else ln
        m = _EXPLICIT_GOREV_RE.match(stripped_hash)
        if m:
            return (m.group(1) or "").strip()[:500]
        if _HEADER_RE.search(ln) or _KAYNAK_TUR_RE.match(ln):
            continue
        if ln.startswith("#") and not _TODO_RE.match(ln):
            continue
        body_lines.append(ln)

    if not body_lines:
        return ""

    if kaynak == "tablo" or (
        not kaynak and any(_TABLO_CELL_RE.match(ln) for ln in body_lines[:6])
    ):
        tablo_goal = _goal_from_tablo_cells(body_lines)
        if tablo_goal:
            return tablo_goal

    if kaynak == "belge":
        return _goal_from_belge_lines(body_lines)

    if kaynak == "sunum":
        return _goal_from_sunum_lines(body_lines)

    if kaynak == "cizim":
        return _goal_from_cizim_lines(body_lines)

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


def _slug_named_in_goal(goal: str, slug: str) -> bool:
    g = (goal or "").lower()
    s = (slug or "").lower().strip()
    if not s or len(s) < 2:
        return False
    return s in g


def _is_ephemeral_project_slug(slug: str) -> bool:
    return bool(_EPHEMERAL_PROJECT_RE.match((slug or "").strip()))


def build_surface_task_line(
    surface_text: str,
    workspace_root: str | Path | None = None,
    *,
    active_file: str | None = None,
) -> str:
    """
    Yüzey metni → sohbet kutusuna konacak `görev: …` satırı.

    Belge/Tablo köprüsünde oturumdaki eski smoke/e2 test projesini YAPISTIRMA.
    Proje adı yalnızca hedef metinde geçiyorsa veya açık dosya gerçek projeyse eklenir.
    """
    goal = extract_surface_goal(surface_text)
    if not goal:
        return ""

    low = goal.lower()
    if low.startswith(("görev:", "gorev:", "iş:", "is:", "yap:")):
        # Zaten görev satırı — ephemeral slug enjekte edilmişse sadeleştir
        try:
            from ilim_assistant.motorlar.programlama_faz14 import parse_code_agent_task

            task = parse_code_agent_task(goal)
            if task and _is_ephemeral_project_slug(getattr(task, "project_slug", "") or ""):
                body = (getattr(task, "goal", None) or goal).strip()
                if body.lower().startswith(("görev:", "gorev:")):
                    return body[:600]
                return f"görev: {body}"[:600]
        except Exception:
            pass
        return goal[:600]

    # Oturum active_project / son smoke testi YAPISTIRMA.
    # Proje adı yalnızca hedef metinde geçiyorsa eklenir (belge/tablo metni esas).
    _ = active_file, workspace_root  # API imzası korunur; yüzey bağlamı metinden gelir
    try:
        from ilim_assistant.motorlar.programlama_faz33 import resolve_project_slug

        named = resolve_project_slug(goal, workspace_root, active_file=None)
        if named and not _is_ephemeral_project_slug(named) and _slug_named_in_goal(goal, named):
            rest = goal
            if rest.lower().startswith(named.lower()):
                rest = rest[len(named) :].lstrip(" :-\t,.") or goal
            return f"görev: {named} {rest.strip()}"[:600]
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
    # Dosya yazmadan ipucu: bilinen Faz85 kalıpları vs ajan / E2 çok dosya
    path_hint = _path_hint_for_goal(goal)
    multi_preview = ""
    named_paths: list[str] = []
    try:
        from ilim_assistant.motorlar.programlama_faz56 import (
            build_multi_file_plan_block,
            extract_named_paths,
            looks_like_multi_file_task,
        )

        if looks_like_multi_file_task(goal) or path_hint.startswith("agent"):
            named_paths = extract_named_paths(goal)
            scope = ""
            try:
                scope = str((wb.get("handoff") or {}).get("scope_rel") or "")
            except Exception:
                scope = ""
            multi_preview = build_multi_file_plan_block(
                workspace_root,
                scope_rel=scope,
                message=task_line or goal,
                goal=goal,
                turn=1,
                touched_files=[],
            )
    except Exception:
        pass

    note = {
        "faz85_fast": "Faz85 hızlı yol adayı",
        "agent_mega": "E2 mega refactor → ajan (Faz80 limitleri)",
        "agent_multi": "E2 çok dosya → ajan + Faz56 plan",
        "agent": "Karmaşık / eşleşmeyen → ajan yolu (Faz14/88)",
    }.get(path_hint, "Ajan yolu")

    return {
        "ok": True,
        "version": YUZEY_BRIDGE_VERSION,
        "goal": goal,
        "task_line": task_line,
        "path_hint": path_hint,
        "named_paths": named_paths,
        "multi_file_plan": multi_preview,
        "handoff_workbench": wb,
        "note": note,
    }


def _path_hint_for_goal(goal: str) -> str:
    """P2 ray sınıflayıcı — scaffold/faz85/agent_boot/multi/mega."""
    try:
        from ilim_assistant.motorlar.programlama_ray_siniflandirici import (
            path_hint_for_goal,
        )

        return path_hint_for_goal(goal or "")
    except Exception:
        g = (goal or "").lower()
        if not g:
            return "agent"
        return "faz85_fast" if "health" in g and "version" in g else "agent"
