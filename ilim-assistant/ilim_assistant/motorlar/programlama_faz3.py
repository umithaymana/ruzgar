# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 3–4: seçmeli onay, Windows ortam taraması, yazım güvenliği.
"""

from __future__ import annotations

import os
import re
import shutil
import sys
from pathlib import Path
from typing import Any

from ilim_assistant.motorlar.programlama_motoru import repo_root
from ilim_assistant.safety_policy import path_is_forbidden

FAZ3_VERSION = "programlama-faz3-v1-2026-05-20"

# @@write ile dokunulmaması gereken göreli yollar (programlama modu)
_PROG_WRITE_DENY_FRAGMENTS = (
    ".env",
    "hafiza/",
    "hafiza\\",
    "/merkezi_bellek.json",
    "merkezi_bellek.json",
    "ruzgar_genel_hafiza.json",
    "ruzgar_egitim_durum.json",
    "video_hafiza.json",
    ".db",
    ".sqlite",
    ".pem",
    ".key",
    "credentials",
    "secret",
)

_FIX_HINTS: dict[str, str] = {
    "workspace_root": "Electron workspace_root veya LOCAL_TOOLS_ROOT / RUZGAR_EXEC_CWD ayarla.",
    "desktop_server_entry": "ilim-assistant klasörünün proje kökünde olduğunu doğrula.",
    "ruzgar_desktop_entry": "ruzgar-desktop klasörünün proje kökünde olduğunu doğrula.",
    "owner_phrase_match": "ruzgar_owner_lock modülünü kontrol et (sunucuyu yeniden başlat).",
    "python_on_path": "Python PATH'te olmalı; Ruzgar.ps1 ile başlat.",
    "pytest_available": "pip install pytest veya proje venv'i etkinleştir.",
    "ruff_available": "pip install ruff (isteğe bağlı lint).",
    "git_available": "Git kurulu olmalı (sürüm kontrolü için).",
    "disk_free_gb": "Diskte en az ~2 GB boş alan bırak.",
    "prog_write_policy": "Hassas dosyalara @@write yasak — politika dosyasını kontrol et.",
    "gemini_configured": "Bilgi: GEMINI_API_KEY yoksa Groq/Ollama kullanılır (otomatik düzeltme gerekmez).",
}


def programlama_write_allowed(root: Path, rel_path: str) -> tuple[bool, str]:
    """Programlama modu ek yazım güvenliği (Faz 4)."""
    if os.environ.get("RUZGAR_PROG_WRITE_GUARD", "1").strip().lower() in (
        "0",
        "false",
        "no",
    ):
        return True, ""
    rel = rel_path.replace("\\", "/").lstrip("/").lower()
    if not rel:
        return False, "Boş dosya yolu."
    if ".." in Path(rel).parts:
        return False, "Path traversal reddedildi."
    for frag in _PROG_WRITE_DENY_FRAGMENTS:
        if frag.lower() in rel:
            return (
                False,
                f"Güvenlik: «{rel_path}» programlama modunda yazılamaz ({frag}).",
            )
    cand = (root / rel_path).resolve()
    if path_is_forbidden(cand):
        return False, "Sistem yolu — yazım reddedildi."
    return True, ""


def run_windows_env_scan(workspace_root: str | Path | None = None) -> list[dict[str, Any]]:
    """Windows / yerel geliştirme ortamı hızlı kontrolü."""
    tests: list[dict[str, Any]] = []

    def add(name: str, ok: bool, detail: str = "") -> None:
        tests.append({"name": name, "ok": bool(ok), "detail": detail})

    add("python_on_path", bool(sys.executable), sys.executable or "yok")
    try:
        ver = f"{sys.version_info.major}.{sys.version_info.minor}"
        add("python_version", sys.version_info >= (3, 10), ver)
    except Exception:
        add("python_version", False, "?")

    add("pytest_available", shutil.which("pytest") is not None, shutil.which("pytest") or "yok")
    add("ruff_available", shutil.which("ruff") is not None, shutil.which("ruff") or "isteğe bağlı")
    add("git_available", shutil.which("git") is not None, shutil.which("git") or "yok")

    root = repo_root(workspace_root)
    if root is not None:
        try:
            usage = shutil.disk_usage(root.anchor if root.anchor else root.drive or "C:\\")
            free_gb = usage.free / (1024**3)
            add("disk_free_gb", free_gb >= 2.0, f"{free_gb:.1f} GB boş")
        except Exception as exc:
            add("disk_free_gb", False, str(exc))
        try:
            ok_pol, _ = programlama_write_allowed(root, "ilim-assistant/ilim_assistant/safety_policy.py")
            add("prog_write_policy", ok_pol, "politika yüklü")
        except Exception as exc:
            add("prog_write_policy", False, str(exc))

    return tests


def attach_failure_catalog(data: dict[str, Any]) -> dict[str, Any]:
    """Başarısız maddelere numara ve düzeltme ipucu ekle."""
    numbered: list[dict[str, Any]] = []
    idx = 0
    for t in data.get("tests") or []:
        if t.get("ok"):
            continue
        name = str(t.get("name") or "?")
        if name == "gemini_configured":
            continue
        idx += 1
        numbered.append(
            {
                "id": idx,
                "name": name,
                "detail": (t.get("detail") or "")[:200],
                "hint": _FIX_HINTS.get(name, "LLM patch veya ortam ayarı gerekebilir."),
            }
        )
    data["numbered_failures"] = numbered
    data["failures"] = [n["name"] for n in numbered]
    data["ok"] = len(numbered) == 0
    return data


def parse_approved_failures(message: str, state: dict[str, Any] | None) -> list[str] | None:
    """
    Onaylanan madde adlarını çıkar.
    None: onay ifadesi yok; []: onay var ama eşleşme yok; liste: onaylı adlar.
    """
    from ilim_assistant.motorlar.programlama_faz2 import wants_scan_fix_approval

    if not wants_scan_fix_approval(message):
        return None
    if not state:
        return []
    all_names = [str(n.get("name", "")) for n in state.get("numbered_failures") or []]
    if not all_names:
        legacy = list(state.get("failures") or [])
        all_names = legacy
    low = (message or "").lower()
    if any(k in low for k in ("hepsini onayla", "tümünü onayla", "tumunu onayla")):
        return list(all_names)

    picked: list[str] = []
    for n in all_names:
        if n in low or n.replace("_", " ") in low:
            picked.append(n)

    nums = [int(x) for x in re.findall(r"\b(\d+)\b", message or "") if x.isdigit()]
    numbered = state.get("numbered_failures") or []
    for num in nums:
        for row in numbered:
            if row.get("id") == num:
                name = str(row.get("name", ""))
                if name and name not in picked:
                    picked.append(name)

    if picked:
        return picked
    if wants_scan_fix_approval(message) and all_names:
        return list(all_names)
    return []


def format_numbered_scan_report(data: dict[str, Any]) -> str:
    lines = [
        "Ümit abi, Programlama öz-denetim raporu (Faz 3):",
        f"Genel: {'GEÇTİ' if data.get('ok') else 'UYARI — onaylı düzeltme gerekir'}",
        "",
    ]
    for t in data.get("tests") or []:
        mark = "✓" if t.get("ok") else "✗"
        name = t.get("name", "?")
        detail = (t.get("detail") or "").strip()
        lines.append(f"{mark} {name}" + (f" — {detail[:100]}" if detail else ""))

    numbered = data.get("numbered_failures") or []
    if numbered:
        lines.extend(["", "Onay için numaralı maddeler:"])
        for row in numbered:
            lines.append(
                f"  {row['id']}. {row['name']} — {row.get('hint', '')[:100]}"
            )
        lines.extend(
            [
                "",
                "Örnek: «onayla 1 2» veya «onaylıyorum workspace_root düzelt»",
                "Tümü: «hepsini onayla düzelt»",
            ]
        )
    else:
        lines.append("")
        lines.append("Kritik madde yok (Gemini anahtarı bilgi amaçlıdır).")

    technical = "\n".join(lines)
    try:
        from ilim_assistant.motorlar.programlama_faz97 import (
            choose_report,
            format_sade_self_scan,
            sade_rapor_enabled,
        )

        if sade_rapor_enabled():
            return choose_report(technical, format_sade_self_scan(data))
    except Exception:
        pass
    return technical
