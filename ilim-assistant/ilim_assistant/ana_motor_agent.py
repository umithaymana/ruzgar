# Created by Ümit & Gökçenur
"""Ana Motor mini ajan (D): plan → workspace okuma → retrieval (prefetch ile)."""

from __future__ import annotations

import os
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from ilim_assistant.local_tools import extract_at_paths, safe_read_file_under_root


def _agent_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_MOTOR_AGENT", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


@dataclass
class AgentStep:
    id: str
    label: str
    status: str  # done | skip | active
    detail: str = ""

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass
class AgentRunResult:
    context_block: str
    steps: list[AgentStep] = field(default_factory=list)
    status_events: list[dict[str, Any]] = field(default_factory=list)


_RE_REL_PATH = re.compile(
    r"(?:^|[\s\"'(\[])"
    r"((?:ruzgar-desktop|ilim-assistant|ilim-mobile|umit-beyin-sidebar)"
    r"[/\\][\w.\-/\\]+|"
    r"[\w][\w.\-]*\.(?:py|js|ts|tsx|mjs|md|json|txt|html|css|ps1|bat|yml|yaml))"
    r"(?=[\s\"')\],.!?;:]|$)",
    re.IGNORECASE,
)


def _repo_root(workspace_root: str | None) -> Path | None:
    raw = (workspace_root or os.environ.get("LOCAL_TOOLS_ROOT", "") or "").strip()
    if raw:
        p = Path(raw)
        if p.is_dir():
            return p.resolve()
    try:
        from ilim_assistant.ruzgar_hafiza_koprusu import ilim_assistant_root

        parent = ilim_assistant_root().parent
        if parent.is_dir():
            return parent.resolve()
    except Exception:
        pass
    return None


def infer_workspace_rel_paths(message: str, repo_root: Path) -> list[str]:
    """@@ yolları + mesajdaki göreli dosya adları."""
    seen: set[str] = set()
    out: list[str] = []

    def add(rel: str) -> None:
        r = rel.replace("\\", "/").lstrip("/")
        if not r or r in seen:
            return
        seen.add(r)
        out.append(r)

    for p in extract_at_paths(message):
        add(p)

    for m in _RE_REL_PATH.finditer(message or ""):
        add(_clean_token(m.group(1)))

    bare = re.findall(
        r"(?<![/\\.\w])([\w][\w.\-]*\.(?:py|js|ts|tsx|mjs|md|json|txt|html|css|ps1))\b",
        message or "",
        re.IGNORECASE,
    )
    for name in bare:
        if name.count(".") > 2:
            continue
        for prefix in (
            f"ruzgar-desktop/{name}",
            f"ilim-assistant/{name}",
            name,
        ):
            cand = repo_root / prefix.replace("/", os.sep)
            if cand.is_file():
                add(prefix)
                break

    return out[: int(os.environ.get("RUZGAR_AGENT_MAX_FILES", "3"))]


def _clean_token(raw: str) -> str:
    return raw.strip().rstrip(".,;:!?)]}\"'")


def _workspace_step_for_turn(
    message: str,
    plan_primary: str,
    repo_root: Path,
) -> tuple[str, AgentStep]:
    rels = infer_workspace_rel_paths(message, repo_root)
    if not rels:
        if plan_primary in ("islem", "dosya"):
            return "", AgentStep(
                id="workspace",
                label="Workspace",
                status="skip",
                detail="Dosya yolu bulunamadı",
            )
        return "", AgentStep(
            id="workspace",
            label="Workspace",
            status="skip",
            detail="Gerek yok",
        )

    max_one = max(500, int(os.environ.get("LOCAL_TOOLS_FILE_MAX_CHARS", "6000")))
    blocks: list[str] = []
    ok_n = 0
    for rel in rels:
        body, err = safe_read_file_under_root(repo_root, rel, max_one)
        if err:
            blocks.append(f"[{rel}] Okunamadı: {err}")
        else:
            ok_n += 1
            blocks.append(f"[Workspace: {rel}]\n{body}")

    if not blocks:
        return "", AgentStep(
            id="workspace",
            label="Workspace",
            status="skip",
            detail="Okunan dosya yok",
        )

    ctx = (
        "=== Ana Motor ajan — workspace ===\n"
        + "\n\n".join(blocks)
        + "\n\n[TALİMAT — WORKSPACE]\n"
        "Üstteki dosya parçaları proje kökünden okunmuştur. "
        "Kod veya yapı sorularında önce bunlara dayan; kullanıcıya dosya yolunu kısaca belirt.\n"
    )
    return ctx, AgentStep(
        id="workspace",
        label="Workspace",
        status="done",
        detail=f"{ok_n} dosya okundu",
    )


def _plan_primary(question_plan: Any | None) -> str:
    if question_plan is None:
        return ""
    if hasattr(question_plan, "primary"):
        return str(question_plan.primary or "")
    if isinstance(question_plan, dict):
        return str(question_plan.get("primary") or "")
    return ""


def run_agent_workspace_phase(
    message: str,
    mode_norm: str,
    question_plan: Any | None,
    *,
    workspace_root: str | None = None,
) -> tuple[str, AgentStep | None, list[dict[str, Any]]]:
    """D1 — workspace dosya okuma (@@ veya mesajdaki yol)."""
    if not _agent_enabled() or mode_norm not in ("genel", "uretim", "gelisim"):
        return "", None, []

    primary = _plan_primary(question_plan)
    repo = _repo_root(workspace_root)
    if repo is None:
        return "", None, []

    if not (
        primary in ("bilgi", "islem", "dosya", "programlama", "bilim")
        or extract_at_paths(message)
    ):
        return "", None, []

    events = [
        {
            "type": "status",
            "phase": "agent_workspace",
            "text": "Ajan — proje dosyaları okunuyor…",
        }
    ]
    ctx, wstep = _workspace_step_for_turn(message, primary, repo)
    return ctx, wstep, events


def build_agent_steps(
    question_plan: Any | None,
    workspace_step: AgentStep | None,
    retrieval_notes: list[str] | None = None,
) -> list[AgentStep]:
    """Dashboard için adım listesi."""
    primary = _plan_primary(question_plan)
    steps: list[AgentStep] = [
        AgentStep(
            id="plan",
            label="Plan",
            status="done",
            detail=primary or "genel",
        ),
    ]
    if workspace_step is not None:
        steps.append(workspace_step)
    notes = [n for n in (retrieval_notes or []) if n]
    if notes:
        steps.append(
            AgentStep(
                id="retrieval",
                label="Kaynak tarama",
                status="done",
                detail=" · ".join(notes[:3]),
            )
        )
    elif primary in ("gundelik", "hava", "hafiza"):
        steps.append(
            AgentStep(
                id="retrieval",
                label="Kaynak tarama",
                status="skip",
                detail="Atlandı",
            )
        )
    else:
        steps.append(
            AgentStep(
                id="retrieval",
                label="Kaynak tarama",
                status="done",
                detail="İndeks / arşiv",
            )
        )
    steps.append(
        AgentStep(
            id="answer",
            label="Yanıt",
            status="active",
            detail="LLM üretiyor",
        )
    )
    return steps


def mark_agent_answer_done(steps: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    if not steps:
        return []
    out = []
    for s in steps:
        d = dict(s)
        if d.get("id") == "answer":
            d["status"] = "done"
            d["detail"] = "Tamam"
        out.append(d)
    return out
