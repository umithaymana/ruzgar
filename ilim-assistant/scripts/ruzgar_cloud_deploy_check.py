#!/usr/bin/env python3
"""Bulut deploy öncesi dosya yapısı kontrolü (Docker derlemeden)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IA = ROOT / "ilim-assistant"
UI = ROOT / "ruzgar-desktop"


def main() -> int:
    errors: list[str] = []
    checks = [
        (ROOT / "railway.json", "Repo kökü railway.json"),
        (IA / "Dockerfile", "Dockerfile"),
        (IA / "desktop_server.py", "API sunucusu"),
        (IA / "knowledge", "Ortak knowledge/"),
        (IA / "env.halk.example", "Halk env şablonu"),
        (UI / "index.html", "Web arayüzü"),
        (ROOT / ".dockerignore", "Docker ignore (arsiv hariç)"),
    ]
    for path, label in checks:
        if not path.exists():
            errors.append(f"Eksik: {label} ({path.relative_to(ROOT)})")

    docker = (IA / "Dockerfile").read_text(encoding="utf-8") if (IA / "Dockerfile").is_file() else ""
    for needle in ("ruzgar-desktop", "ilim-assistant/knowledge", "RUZGAR_PUBLIC_MODE"):
        if needle not in docker:
            errors.append(f"Dockerfile içinde yok: {needle}")

    railway = (ROOT / "railway.json").read_text(encoding="utf-8") if (ROOT / "railway.json").is_file() else ""
    if "healthcheckPath" not in railway:
        errors.append("railway.json: healthcheckPath eksik")

    if errors:
        for e in errors:
            print("FAIL", e)
        return 1

    print("OK ruzgar cloud deploy — dosya yapisi hazir")
    print("  docker build -f ilim-assistant/Dockerfile .")
    print("  Railway: repo kokunu bagla, env.halk.example degiskenlerini ekle")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
