# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 2: açılış brifingi, öz-bilgi manifesti, onaylı düzeltme.

Yalnızca programlama atölyesi; diğer motorlara dokunmaz.
"""

from __future__ import annotations

import contextvars
import os
import re
import time
from pathlib import Path
from typing import Any

from ilim_assistant.motorlar.programlama_motoru import (
    build_repo_map,
    repo_root,
)

FAZ2_VERSION = "programlama-faz2-v1-2026-05-20"

_last_scan_state: dict[str, Any] | None = None
_force_debug_turn: contextvars.ContextVar[bool] = contextvars.ContextVar(
    "prog_scan_fix_debug", default=False
)

_STATIC_MANIFEST = """
[RÜZGAR — ÖZ-BİLGİ MANİFESTİ — Programlama]
- Mimari: ilim-assistant (Python/FastAPI, port 8779) + ruzgar-desktop (Electron).
- Bu mod: yerel ilim indeksi atlanır; güvenli dosya okuma/yazma + onaylı pytest/ruff.
- Patch biçimi: @@write göreli/yol + fenced kod bloğu; her yazımda .bak yedeği.
- Otonom döngü: «otomatik debug», «kendin düzelt», traceback veya onaylı tarama sonrası.
- Sahip: «rüzgar ben ümit» → yönetici oturumu (Ümit abi).
- Komutlar: «kendini tara» → numaralı rapor; «onayla 1 2» / «hepsini onayla düzelt».
- Güvenlik (Faz 4): .env/hafiza yasak; patch içinde os.system/eval yasak; «güvenlik tara».
- Oturum (Faz 5): .ruzgar/programlama_oturum.json — açık dosya, hedef, son patch/test.
- Şablon (Faz 6): «şablon listele» · «şablon oluştur: fastapi_api ad» → projects/<ad>/
- Çalıştırma (Faz 7): «açıkla» / «nasıl çalıştırırım» / «proje çalıştır» → yerel rehber + smoke
- Hafıza JSON/DB git'e gitmez; yalnızca bu makinede kalır.
""".strip()


def compact_self_knowledge() -> str:
    return _STATIC_MANIFEST


def wants_briefing(message: str) -> bool:
    low = (message or "").lower()
    return any(
        k in low
        for k in (
            "brifing",
            "briefing",
            "açılış özeti",
            "acilis ozeti",
            "kendini tanıt kod",
            "programlama özeti",
        )
    )


def build_startup_briefing(workspace_root: str | Path | None = None) -> dict[str, Any]:
    """API/UI için yapılandırılmış açılış brifingi."""
    root = repo_root(workspace_root)
    root_s = str(root) if root else None
    try:
        from ilim_assistant.llm_gemini import gemini_configured

        gemini = gemini_configured()
    except Exception:
        gemini = False
    try:
        from ilim_assistant.ruzgar_owner_lock import OWNER_LOCK_VERSION

        owner_ver = OWNER_LOCK_VERSION
    except Exception:
        owner_ver = "?"

    lines = [
        "Ümit abi, Programlama atölyesi hazır (Faz 7).",
        "",
        "Ne yapabilirim:",
        "• Proje dosyalarını okur/yazarım (@@write + pytest/ruff)",
        "• «kendini tara» → öz-denetim raporu",
        "• «sistem analizi» / «hataları bul onar» → P11 otonom analiz + güvenli onarım (Faz 96)",
        "• Dosya taşı/kopyala/kur → önce önizleme, «tamam yap» ile uygula (Faz 98 — onaysız müdahale yok)",
        "• «kendini tara» → numaralı rapor; «onayla 1 2» veya «hepsini onayla düzelt»",
        "• «rüzgar ben ümit» → yönetici oturumu",
        "• «proje özeti» / «proje kaydet: Ad | hedef: …» → oturum bağlamı (Faz 5)",
        "• «şablon listele» / «şablon oluştur: fastapi_api ad» → proje iskeleti (Faz 6)",
        "• «açıkla» / «nasıl çalıştırırım» / «proje çalıştır» → yerel rehber (Faz 7)",
        "• Traceback veya «otomatik debug» → otonom düzeltme döngüsü",
        "",
        f"Proje kökü: {root_s or 'ayarlı değil — workspace_root / LOCAL_TOOLS_ROOT'}",
        f"Gemini: {'yapılandırıldı' if gemini else 'anahtar yok (Groq/Ollama devreye girer)'}",
        f"Sahip kilidi: {owner_ver}",
    ]
    rmap = build_repo_map(workspace_root).strip()
    if rmap:
        lines.extend(["", "Kısa harita:", rmap[:900]])

    return {
        "ok": True,
        "version": FAZ2_VERSION,
        "generated_at": time.time(),
        "workspace_root": root_s,
        "text": "\n".join(lines),
        "manifest": _STATIC_MANIFEST,
        "commands": [
            "rüzgar ben ümit",
            "kendini tara",
            "sistem analizi",
            "hataları bul onar",
            "tamam yap",
            "işlem liste",
            "güvenlik tara",
            "onaylıyorum düzelt",
            "otomatik debug",
            "brifing",
            "proje özeti",
            "proje kaydet: …",
            "proje temizle",
            "şablon listele",
            "şablon oluştur: fastapi_api …",
            "proje çalıştır",
            "nasıl çalıştırırım",
        ],
    }


def run_programlama_self_scan(workspace_root: str | Path | None = None) -> dict[str, Any]:
    """Temel self-test + programlama kökü + Windows ortam (Faz 3)."""
    from ilim_assistant.motorlar.programlama_faz3 import (
        attach_failure_catalog,
        run_windows_env_scan,
    )
    from ilim_assistant.ruzgar_selftest import run_self_tests

    data = run_self_tests()
    tests: list[dict[str, Any]] = list(data.get("tests") or [])

    root = repo_root(workspace_root)

    def add(name: str, ok: bool, detail: str = "") -> None:
        tests.append({"name": name, "ok": bool(ok), "detail": detail})

    add("workspace_root", root is not None, str(root) if root else "yok")
    if root is not None:
        add(
            "desktop_server_entry",
            (root / "ilim-assistant" / "desktop_server.py").is_file(),
            "ilim-assistant/desktop_server.py",
        )
        add(
            "ruzgar_desktop_entry",
            (root / "ruzgar-desktop" / "app.js").is_file(),
            "ruzgar-desktop/app.js",
        )
    add("owner_lock_module", True, "ruzgar_owner_lock")
    try:
        from ilim_assistant.ruzgar_owner_lock import is_owner_phrase

        add("owner_phrase_match", is_owner_phrase("rüzgar ben ümit"), "test ifadesi")
    except Exception as exc:
        add("owner_phrase_match", False, str(exc))

    tests.extend(run_windows_env_scan(workspace_root))
    try:
        from ilim_assistant.motorlar.programlama_faz4 import append_faz4_self_scan_tests

        append_faz4_self_scan_tests(tests, workspace_root)
    except Exception:
        pass

    out: dict[str, Any] = {
        "ok": True,
        "tests": tests,
        "failures": [],
        "scanned_at": time.time(),
        "version": "faz3",
    }
    return attach_failure_catalog(out)


def _store_scan_state(data: dict[str, Any]) -> None:
    global _last_scan_state
    _last_scan_state = {
        "data": data,
        "failures": list(data.get("failures") or []),
        "numbered_failures": list(data.get("numbered_failures") or []),
        "tests": list(data.get("tests") or []),
        "at": time.time(),
    }


def get_last_scan_state() -> dict[str, Any] | None:
    return _last_scan_state


def format_self_scan_report(workspace_root: str | Path | None = None) -> str:
    from ilim_assistant.motorlar.programlama_faz3 import format_numbered_scan_report

    data = run_programlama_self_scan(workspace_root)
    _store_scan_state(data)
    return format_numbered_scan_report(data)


def wants_scan_fix_approval(message: str) -> bool:
    low = (message or "").lower()
    if re.search(r"\bonayla\s+(\d|[\w_])", low):
        return True
    return any(
        k in low
        for k in (
            "onaylıyorum düzelt",
            "onayliyorum duzelt",
            "onayla ve düzelt",
            "onayla ve duzelt",
            "hepsini onayla düzelt",
            "hepsini onayla duzelt",
            "onaylı düzeltme",
            "onayli duzeltme",
            "düzeltmeyi onaylıyorum",
            "duzeltmeyi onayliyorum",
        )
    )


def prepare_scan_fix_turn(
    message: str,
    workspace_root: str | Path | None = None,
) -> dict[str, Any] | None:
    """
    Onaylı düzeltme turu hazırlığı (Faz 3 — seçmeli onay).
    Dönüş: instant (anında metin) veya augmented_message + force_debug.
    """
    from ilim_assistant.motorlar.programlama_faz3 import parse_approved_failures

    if not wants_scan_fix_approval(message):
        return None
    state = get_last_scan_state()
    if not state:
        return {
            "instant": (
                "Ümit abi, önce «kendini tara» yaz; raporu göreyim. "
                "Sonra «onayla 1» veya «hepsini onayla düzelt» ile patch+pytest başlatırım."
            )
        }
    if not (state.get("failures") or state.get("numbered_failures")):
        return {
            "instant": (
                "Ümit abi, son tarama temiz — kritik madde yok. "
                "Yine de kod düzeltmesi istersen dosyayı @@ ile aç veya traceback yapıştır."
            )
        }
    approved = parse_approved_failures(message, state)
    if approved is None:
        return None
    if not approved:
        return {
            "instant": (
                "Ümit abi, raporda numaralı madde yok veya onay eşleşmedi. "
                "Önce «kendini tara»; sonra «onayla 1 2» veya madde adı yaz."
            )
        }
    hints: list[str] = []
    for row in state.get("numbered_failures") or []:
        if row.get("name") in approved:
            hints.append(f"- {row['name']}: {row.get('hint', '')}")
    if not hints:
        hints = [f"- {n}" for n in approved]
    fail_lines = "\n".join(hints)
    augmented = (
        (message or "").strip()
        + "\n\n[ONAYLI DÜZELTME — Faz 3 — Ümit abi onayladı]\n"
        "Yalnızca şu maddeler:\n"
        f"{fail_lines}\n\n"
        "Görev: bu maddeler için minimal @@write patch; hassas dosyalara (.env, hafiza) yazma. "
        "pytest_run ile doğrula. Ortam maddeleri (python/pytest) için komut öner, uydurma yol yazma.\n"
    )
    _force_debug_turn.set(True)
    return {
        "augmented_message": augmented,
        "force_debug": True,
        "failures": approved,
    }


def should_force_autonomous_debug(message: str) -> bool:
    from ilim_assistant.motorlar.programlama_motoru import wants_autonomous_code_debug

    if wants_autonomous_code_debug(message):
        return True
    return bool(_force_debug_turn.get())


def clear_force_debug_turn() -> None:
    _force_debug_turn.set(False)
