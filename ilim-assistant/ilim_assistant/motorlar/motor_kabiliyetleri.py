# Created by Ümit & Gökçenur
"""
Merkezi motor kabiliyet kaydı — Ana Motor hub (Faz B).

Tek kaynak: ``ilim_assistant/data/motor_kabiliyetleri.json``
"""

from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any

KABILIYET_VERSION = "motor-kabiliyetleri-v1-2026-06-07"

_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "motor_kabiliyetleri.json"


def _ascii_fold(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


@lru_cache(maxsize=1)
def load_registry() -> dict[str, Any]:
    try:
        raw = _DATA_PATH.read_text(encoding="utf-8")
        data = json.loads(raw)
        if isinstance(data, dict) and isinstance(data.get("motors"), dict):
            return data
    except OSError:
        pass
    except json.JSONDecodeError:
        pass
    return {"version": KABILIYET_VERSION, "motors": {}}


def list_motor_ids() -> list[str]:
    motors = load_registry().get("motors") or {}
    return list(motors.keys())


def motor_capability(motor_id: str) -> dict[str, Any] | None:
    mid = (motor_id or "").strip().lower()
    if mid == "okuma":
        mid = "mimar"
    motors = load_registry().get("motors") or {}
    spec = motors.get(mid)
    return dict(spec) if isinstance(spec, dict) else None


def score_message_for_motor(message: str, motor_id: str) -> int:
    """Kabiliyet kaydındaki route_regex ile skor (0 = eşleşme yok)."""
    spec = motor_capability(motor_id)
    if not spec:
        return 0
    raw = (message or "").strip()
    if not raw:
        return 0
    blob = _ascii_fold(raw)
    patterns = spec.get("route_regex") or []
    score = 0
    for pat in patterns:
        try:
            if re.search(pat, blob, re.I):
                score += 2
        except re.error:
            continue
    if score:
        score += int(spec.get("priority") or 0) // 3
    return score


def resolve_target_from_registry(message: str) -> tuple[str | None, dict[str, Any]]:
    """En yüksek skorlu motor; eşitlikte priority."""
    raw = (message or "").strip()
    meta: dict[str, Any] = {"source": "motor_kabiliyetleri", "candidates": []}
    if not raw:
        return None, meta

    motors = load_registry().get("motors") or {}
    best_id: str | None = None
    best_score = 0
    best_pri = -1

    for mid, spec in motors.items():
        if not isinstance(spec, dict):
            continue
        sc = score_message_for_motor(raw, mid)
        pri = int(spec.get("priority") or 0)
        meta["candidates"].append({"motor": mid, "score": sc, "priority": pri})
        if sc > best_score or (sc == best_score and sc > 0 and pri > best_pri):
            best_score = sc
            best_pri = pri
            best_id = mid

    if best_id and best_score > 0:
        meta["winner"] = best_id
        meta["score"] = best_score
        return best_id, meta
    return None, meta


def format_capabilities_help() -> str:
    motors = load_registry().get("motors") or {}
    lines = [
        "Ümit abi, **Ana Motor kabiliyet kaydı** — tek sohbetten:",
        "",
    ]
    order = sorted(
        motors.items(),
        key=lambda kv: (-int((kv[1] or {}).get("priority") or 0), kv[0]),
    )
    for mid, spec in order:
        if not isinstance(spec, dict):
            continue
        label = spec.get("label_tr") or mid
        examples = spec.get("examples") or []
        ex = examples[0] if examples else "…"
        lines.append(f"· **{label}** — örn. «{ex}»")
    lines.extend(["", f"({load_registry().get('version') or KABILIYET_VERSION})"])
    return "\n".join(lines)


def registry_snapshot() -> dict[str, Any]:
    data = load_registry()
    motors = data.get("motors") or {}
    out_motors: dict[str, Any] = {}
    for mid, spec in motors.items():
        if not isinstance(spec, dict):
            continue
        out_motors[mid] = {
            "label_tr": spec.get("label_tr") or mid,
            "priority": spec.get("priority"),
            "examples": spec.get("examples") or [],
            "dispatch": spec.get("dispatch"),
            "route_count": len(spec.get("route_regex") or []),
        }
    learned_block: dict[str, Any] = {}
    try:
        from ilim_assistant.motorlar.motor_ogrenilen_eylemler import learned_actions_snapshot

        learned_block = learned_actions_snapshot(None)
    except Exception:
        pass
    return {
        "ok": True,
        "version": data.get("version") or KABILIYET_VERSION,
        "motors": out_motors,
        "learned_actions": {
            "count": learned_block.get("count", 0),
            "approved_count": learned_block.get("approved_count", 0),
            "version": learned_block.get("version"),
        },
        "teach_hint": "eylem öğret: «tetik» → video",
    }
