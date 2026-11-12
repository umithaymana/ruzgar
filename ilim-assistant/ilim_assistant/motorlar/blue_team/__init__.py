# Created by Ümit & Gökçenur
"""
Rüzgar Blue Team — savunma odaklı bütünlük / statik imza / anomali uyarıları.

Amaç: sistem bütünlüğünü izlemek ve şüpheli değişimleri raporlamak.
Saldırı, exploit, malware üretimi veya yetkisiz erişim YOKTUR.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .anomaly_log import list_alerts, log_alert
from .integrity import FileIntegrityMonitor
from .static_scan import StaticSignatureScanner, scan_file_static

ENGINE_NAME = "Rüzgar Blue Team"
ENGINE_VERSION = "blue-team-v1-2026-11-03"


def default_db_path() -> Path:
    return Path(__file__).resolve().parents[3] / "data" / "blue_team_integrity.sqlite3"


def default_rules_path() -> Path:
    return Path(__file__).resolve().parent / "rules" / "default_signatures.json"


def run_defense_scan(
    roots: list[str | Path],
    *,
    baseline: bool = False,
    db_path: Path | None = None,
    rules_path: Path | None = None,
    max_files: int = 5000,
    log_findings: bool = True,
) -> dict[str, Any]:
    """
    Belirtilen dizinlerde:
      1) SHA-256 bütünlük (baseline veya diff)
      2) Statik imza / PE başlık kontrolü
      3) Bulguları anomali loguna yaz
    """
    fim = FileIntegrityMonitor(db_path or default_db_path())
    scanner = StaticSignatureScanner(rules_path or default_rules_path())

    integrity = (
        fim.baseline(roots, max_files=max_files)
        if baseline
        else fim.check(roots, max_files=max_files)
    )
    static_hits: list[dict[str, Any]] = []
    scanned = 0
    for root in roots:
        r = Path(root)
        if not r.exists():
            continue
        for path in fim.iter_files(r, max_files=max_files - scanned):
            scanned += 1
            hit = scanner.scan_path(path)
            if hit.get("suspicious"):
                static_hits.append(hit)
                if log_findings:
                    log_alert(
                        kind="static_signature",
                        severity=str(hit.get("severity") or "medium"),
                        path=str(path),
                        detail=hit,
                        source=ENGINE_NAME,
                    )

    for ch in integrity.get("changes") or []:
        if log_findings and ch.get("status") in ("modified", "deleted", "new"):
            log_alert(
                kind="integrity",
                severity="high" if ch.get("status") == "modified" else "medium",
                path=str(ch.get("path") or ""),
                detail=ch,
                source=ENGINE_NAME,
            )

    summary = {
        "ok": True,
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "purpose": "defense-only",
        "integrity": integrity,
        "static": {
            "files_scanned": scanned,
            "suspicious_count": len(static_hits),
            "hits": static_hits[:200],
        },
        "alerts_logged": bool(log_findings),
    }
    return summary


__all__ = [
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "FileIntegrityMonitor",
    "StaticSignatureScanner",
    "scan_file_static",
    "log_alert",
    "list_alerts",
    "run_defense_scan",
    "default_db_path",
    "default_rules_path",
]
