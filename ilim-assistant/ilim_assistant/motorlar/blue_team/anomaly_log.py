# Created by Ümit & Gökçenur
"""Anomali / uyarı loglama — JSONL + Rüzgar threat log ile uyumlu kayıt."""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def alerts_path(repo_root: Path | None = None) -> Path:
    root = repo_root or _repo_root()
    p = root / "ilim-assistant" / "arsiv" / "_virus_guard_staging" / "blue_team_alerts.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def log_alert(
    *,
    kind: str,
    severity: str,
    path: str = "",
    detail: dict[str, Any] | None = None,
    source: str = "Rüzgar Blue Team",
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Şüpheli bulguyu standart formatta kaydet; threat log'a da yansıt."""
    record = {
        "ts": time.time(),
        "iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "alert_id": uuid.uuid4().hex[:12],
        "kind": kind,
        "severity": severity,
        "path": path[:1000],
        "source": source,
        "detail": detail or {},
        "purpose": "defense",
    }
    ap = alerts_path(repo_root)
    try:
        with ap.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass

    # Virüs kalkanı threat log ile aynı kanala uyarı bırak (gözlem birliği)
    try:
        from ilim_assistant.motorlar.ruzgar_antivirus import _threat_log_path

        root = repo_root or _repo_root()
        bridge = {
            "ts": record["ts"],
            "alert_id": record["alert_id"],
            "kind": f"blue_team:{kind}",
            "severity": severity,
            "path": path[:500],
            "threats": [f"blue_team/{kind}/{severity}"],
            "risk_score": {"low": 10, "medium": 25, "high": 45, "critical": 70}.get(
                severity, 20
            ),
            "engine": source,
            "detail": detail or {},
        }
        with _threat_log_path(root).open("a", encoding="utf-8") as log:
            log.write(json.dumps(bridge, ensure_ascii=False) + "\n")
    except Exception:
        pass

    return record


def list_alerts(limit: int = 50, *, repo_root: Path | None = None) -> dict[str, Any]:
    p = alerts_path(repo_root)
    rows: list[dict[str, Any]] = []
    if p.is_file():
        try:
            lines = p.read_text(encoding="utf-8").strip().splitlines()
            for line in lines[-limit:]:
                try:
                    rows.append(json.loads(line))
                except Exception:
                    continue
        except OSError:
            pass
    return {"ok": True, "items": rows, "count": len(rows), "path": str(p)}
