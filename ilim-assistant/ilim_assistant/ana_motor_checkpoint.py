# Created by Ümit & Gökçenur
"""
Ana Motor — Faz 93: uzun görev checkpoint (kopmama).

Durum: `.ruzgar/ana_motor_session.json`
Kapat: RUZGAR_ANA_CHECKPOINT=0
"""

from __future__ import annotations

import json
import os
import re
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

FAZ93_VERSION = "ana-motor-checkpoint-faz93-v1"
_SESSION_FILE = "ana_motor_session.json"
_RESUME_CUES = (
    "devam et",
    "devam",
    "kaldığın yerden",
    "kaldigin yerden",
    "checkpoint",
    "yarım kaldı",
    "yarim kaldi",
    "son görev",
    "son gorev",
    "tamamla",
    "bitir",
)


def checkpoint_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_CHECKPOINT", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _ruzgar_dir(workspace_root: str | Path | None) -> Path | None:
    raw = (workspace_root or os.environ.get("LOCAL_TOOLS_ROOT", "") or "").strip()
    if raw:
        root = Path(raw)
    else:
        try:
            from ilim_assistant.ruzgar_hafiza_koprusu import ilim_assistant_root

            root = ilim_assistant_root().parent
        except Exception:
            return None
    if not root.is_dir():
        return None
    d = root / ".ruzgar"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _session_path(workspace_root: str | Path | None) -> Path | None:
    d = _ruzgar_dir(workspace_root)
    return d / _SESSION_FILE if d else None


@dataclass
class AnaMotorCheckpoint:
    version: str = FAZ93_VERSION
    session_id: str = ""
    turn_index: int = 0
    max_turns: int = 3
    last_user: str = ""
    last_reply: str = ""
    plan_primary: str = ""
    mode_norm: str = "genel"
    agent_phase: str = "idle"  # idle | planning | patch | verify | done
    agent_steps: list[dict[str, str]] = field(default_factory=list)
    patch_applied: list[str] = field(default_factory=list)
    patch_errors: list[str] = field(default_factory=list)
    updated_at: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> AnaMotorCheckpoint:
        cp = cls()
        for k, v in raw.items():
            if hasattr(cp, k):
                setattr(cp, k, v)
        return cp


def load_checkpoint(workspace_root: str | Path | None) -> AnaMotorCheckpoint | None:
    if not checkpoint_enabled():
        return None
    path = _session_path(workspace_root)
    if path is None or not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return None
        cp = AnaMotorCheckpoint.from_dict(raw)
        if not cp.session_id:
            return None
        return cp
    except Exception:
        return None


def save_checkpoint(
    workspace_root: str | Path | None,
    *,
    turn_index: int,
    last_user: str,
    last_reply: str = "",
    plan_primary: str = "",
    mode_norm: str = "genel",
    agent_phase: str = "planning",
    agent_steps: list[dict[str, str]] | None = None,
    patch_applied: list[str] | None = None,
    patch_errors: list[str] | None = None,
    max_turns: int = 3,
    session_id: str | None = None,
) -> AnaMotorCheckpoint | None:
    if not checkpoint_enabled():
        return None
    path = _session_path(workspace_root)
    if path is None:
        return None
    prev = load_checkpoint(workspace_root)
    sid = session_id or (prev.session_id if prev else "") or uuid.uuid4().hex[:12]
    cp = AnaMotorCheckpoint(
        session_id=sid,
        turn_index=int(turn_index),
        max_turns=int(max_turns),
        last_user=(last_user or "")[:2000],
        last_reply=(last_reply or "")[:12000],
        plan_primary=plan_primary or "",
        mode_norm=mode_norm or "genel",
        agent_phase=agent_phase,
        agent_steps=list(agent_steps or []),
        patch_applied=list(patch_applied or []),
        patch_errors=list(patch_errors or []),
        updated_at=time.time(),
    )
    try:
        path.write_text(
            json.dumps(cp.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        return None
    return cp


def clear_checkpoint(workspace_root: str | Path | None) -> bool:
    path = _session_path(workspace_root)
    if path is None:
        return False
    try:
        if path.is_file():
            path.unlink()
        return True
    except Exception:
        return False


def is_resume_message(message: str) -> bool:
    low = (message or "").strip().casefold().strip(" .,!?\t\r\n")
    if not low or len(low) > 48:
        return False
    if low in _RESUME_CUES:
        return True
    return bool(re.fullmatch(r"(?:devam\s+et|kald[iı]ğ[iı]n\s+yerden|yarım\s+kald[iı])", low))


def build_resume_context(checkpoint: AnaMotorCheckpoint) -> str:
    lines = [
        "[CHECKPOINT — Faz 93 — kullanıcıya yazdırma]",
        f"Oturum: {checkpoint.session_id} · tur {checkpoint.turn_index}/{checkpoint.max_turns}",
        f"Son kullanıcı: {checkpoint.last_user[:400]}",
        f"Aşama: {checkpoint.agent_phase}",
    ]
    if checkpoint.patch_applied:
        lines.append("Uygulanan dosyalar: " + ", ".join(checkpoint.patch_applied[:6]))
    if checkpoint.patch_errors:
        lines.append("Hatalar: " + "; ".join(checkpoint.patch_errors[:4]))
    if checkpoint.last_reply:
        lines.append("Son asistan özeti:\n" + checkpoint.last_reply[:1500])
    lines.append(
        "Talimat: Kullanıcı «devam et» dedi — yarım kalan görevi tamamla; "
        "gereksiz tekrar yapma; @@write ile kalan patch'i uygula."
    )
    lines.append("[/CHECKPOINT]")
    return "\n".join(lines)


def maybe_resume_agent_context(
    message: str,
    workspace_root: str | Path | None,
) -> tuple[str, AnaMotorCheckpoint | None]:
    """«Devam et» + kayıtlı checkpoint → LLM bağlamı."""
    if not checkpoint_enabled() or not is_resume_message(message):
        return "", None
    cp = load_checkpoint(workspace_root)
    if cp is None or cp.agent_phase == "done":
        return "", cp
    return build_resume_context(cp), cp
