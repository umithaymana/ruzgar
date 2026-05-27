# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 19: otonom görev v2 (SLO, erken dur, beyin sırası).

Faz 14 döngüsünü güçlendirir; ayrı SSE yok.
"""

from __future__ import annotations

import os
import re
import time
import unicodedata
from dataclasses import dataclass, field
from typing import Any

FAZ19_VERSION = "programlama-faz19-v1-2026-05-25"

_TASK_ALIAS_RE = re.compile(
    r"^\s*(?:görev|gorev|iş|is|yap|task)\s*:\s*(.+)$",
    re.I | re.M,
)
_IMPLICIT_PROJECT_RE = re.compile(
    r"\b(?:projects/)?([\w][\w.\-]{1,48})\b",
    re.I,
)
_ACTION_VERBS_RE = re.compile(
    r"(?:yap|olustur|oluştur|ekle|duzelt|düzelt|geçir|gecir|bitir|tamamla|yaz|güncelle|guncelle|test)",
    re.I,
)


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ19", "1").strip().lower() not in ("0", "false", "no")


def _ascii_fold(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def code_agent_budget_sec() -> float:
    try:
        from ilim_assistant.motorlar.programlama_faz23 import resolve_code_agent_budget_sec

        return resolve_code_agent_budget_sec()
    except Exception:
        pass
    try:
        return float(os.environ.get("RUZGAR_CODE_AGENT_BUDGET_SEC", "120"))
    except ValueError:
        return 120.0


def code_agent_empty_streak_max() -> int:
    try:
        from ilim_assistant.motorlar.programlama_faz41 import long_task_empty_streak_max

        return long_task_empty_streak_max()
    except Exception:
        pass
    try:
        return max(1, min(int(os.environ.get("RUZGAR_CODE_AGENT_EMPTY_STREAK", "2")), 5))
    except ValueError:
        return 2


def code_agent_brain_profiles() -> list[str]:
    raw = os.environ.get("RUZGAR_CODE_AGENT_BRAIN", "kod,groq,gemini").strip()
    if not raw:
        return ["kod", "groq", "gemini"]
    return [p.strip() for p in raw.split(",") if p.strip()]


@dataclass
class AgentLoopState:
    empty_streak: int = 0
    quota_streak: int = 0
    total_writes: int = 0
    turns_done: int = 0

    def record_turn(
        self,
        *,
        wrote_files: int,
        llm_kind: str,
    ) -> None:
        self.turns_done += 1
        self.total_writes += wrote_files
        if llm_kind == "quota":
            self.quota_streak += 1
            if wrote_files == 0:
                self.empty_streak += 1
            else:
                self.empty_streak = 0
        elif llm_kind == "empty":
            self.empty_streak += 1
            self.quota_streak = 0
        else:
            self.empty_streak = 0
            self.quota_streak = 0


def classify_llm_turn(
    llm_body: str,
    writes_ok: int,
    *,
    is_failure_fn: Any,
) -> str:
    if writes_ok > 0:
        return "write"
    if is_failure_fn(llm_body):
        return "quota"
    if not (llm_body or "").strip() or "@@write" not in (llm_body or "").lower():
        return "empty"
    return "no_write"


def should_abort_loop(state: AgentLoopState) -> tuple[bool, str]:
    limit = code_agent_empty_streak_max()
    if state.quota_streak >= 1 and state.total_writes == 0 and state.turns_done >= 1:
        return (
            True,
            "LLM kotası / yanıt yok — GROQ_API_KEY veya `RUZGAR_CODE_AGENT_BRAIN=groq,kod` "
            "deneyin; boş turlarla devam edilmiyor.",
        )
    if state.empty_streak >= limit and state.total_writes == 0:
        return (
            True,
            f"{limit} tur üst üste dosya yazılmadı — görev durdu (erken çıkış).",
        )
    return False, ""


def budget_exceeded(start_mono: float) -> bool:
    try:
        from ilim_assistant.motorlar.programlama_faz23 import budget_exceeded as _f23_budget

        return _f23_budget(start_mono)
    except Exception:
        return (time.perf_counter() - start_mono) >= code_agent_budget_sec()


def parse_task_aliases(message: str) -> str | None:
    """iş: / yap: / task: → görev: ile aynı."""
    raw = (message or "").strip()
    m = _TASK_ALIAS_RE.search(raw)
    if m:
        return f"görev: {m.group(1).strip()}"
    return None


def parse_implicit_programming_task(message: str) -> str | None:
    """
    Programlama modunda doğal cümle → görev satırı.
    Örn: «benim-api health endpointine version ekle ve test geçir»
    """
    if not _enabled():
        return None
    raw = (message or "").strip()
    if len(raw) < 12 or len(raw) > 500:
        return None
    low = _ascii_fold(raw)
    if parse_task_aliases(raw):
        return None
    if any(
        k in low
        for k in (
            "gorev:",
            "görev:",
            "patch onayla",
            "git durum",
            "sablon",
            "şablon",
            "@@find",
            "proje tara",
            "?",
            "nedir",
            "nasil",
            "nasıl",
        )
    ):
        return None
    if not _ACTION_VERBS_RE.search(raw):
        return None

    slug = ""
    m_proj = _IMPLICIT_PROJECT_RE.search(raw)
    if m_proj:
        slug = m_proj.group(1).strip().strip("/")
        if slug.lower() in ("projects", "src", "app", "tests", "test"):
            slug = ""

    if not slug:
        words = re.findall(r"[\w.\-]{2,32}", raw)
        for w in words:
            if "-" in w or w.endswith("api") or w.isidentifier():
                if w.lower() not in ("health", "version", "endpoint", "test", "pytest"):
                    slug = w
                    break

    if not slug:
        return None

    goal = raw
    low_raw = _ascii_fold(raw)
    low_slug = _ascii_fold(slug)
    if low_raw.startswith(low_slug):
        goal = raw[len(slug) :].lstrip(" :-\t")
    if not goal:
        goal = raw
    return f"görev: {slug} {goal}"


def normalize_agent_message(message: str, mode_norm: str = "") -> str:
    """Görev takma adları ve doğal cümleyi tek forma çevirir."""
    aliased = parse_task_aliases(message)
    if aliased:
        return aliased
    if mode_norm == "programlama":
        implicit = parse_implicit_programming_task(message)
        if implicit:
            return implicit
    return message


def faz19_directive() -> str:
    return (
        "[GÖREV v2 — Faz 19]\n"
        f"Süre üst sınırı: {int(code_agent_budget_sec())} sn · "
        f"boş tur limiti: {code_agent_empty_streak_max()}.\n"
        "Komutlar: `görev:` · `iş:` · `yap:` — veya doğal: "
        "`benim-api health'e version ekle ve test geçir`.\n"
        f"Beyin önceliği: {','.join(code_agent_brain_profiles())} "
        "(RUZGAR_CODE_AGENT_BRAIN).\n"
    )
