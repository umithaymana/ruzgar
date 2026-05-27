from __future__ import annotations

import time
from typing import Any


CURRENT_PHASE = 84
CURRENT_PHASE_LABEL = "Faz 68–84"


def _phase(n: int, name: str, status: str = "tamam") -> dict[str, str]:
    return {"phase": f"Faz {n}", "name": name, "status": status}


def build_ui_manifest(*, health: dict[str, Any] | None = None) -> dict[str, Any]:
    """Tek kaynak: masaüstü UI faz/kabiliyet metinlerini backend'den besler."""
    from ilim_assistant.motorlar.video_motoru import list_recent_downloads

    health = health or {}
    super_brain = health.get("super_brain") if isinstance(health, dict) else {}
    gemini_ok = bool((super_brain or {}).get("gemini_configured"))
    recent_downloads = [
        row for row in list_recent_downloads(8) if isinstance(row, dict) and row.get("ok")
    ]

    return {
        "ok": True,
        "version": 2,
        "generated_at": time.time(),
        "current_phase": CURRENT_PHASE,
        "current_phase_label": CURRENT_PHASE_LABEL,
        "dashboard": {
            "badge": "Ana Motor · Hub + Faz 84",
            "promise": (
                "Orkestra: tüm yardımcı motorlar ROK + hub (Hızır dahil). "
                "Video: isimle arama listesi · programlama Dalga H."
            ),
            "welcome_foot": "Faz 68–84 · Ümit & Gökçenur",
            "help_title": "Rüzgar — Konuşarak yap (ROK + Hub)",
        },
        "phases": [
            _phase(68, "Programlama ROK"),
            _phase(71, "Video ROK"),
            _phase(72, "Ses ROK"),
            _phase(73, "Okuma ROK"),
            _phase(74, "Tercüme ROK"),
            _phase(75, "Hafıza ROK"),
            _phase(76, "Ana Motor Hub"),
            _phase(77, "Cila + KPI"),
            _phase(78, "Prog. çekirdek kapsam"),
            _phase(79, "Handoff v3"),
            _phase(80, "Mega refactor"),
            _phase(81, "Araç kurtarma"),
            _phase(82, "Zayıflık raporu"),
            _phase(83, "PR hazırla"),
            _phase(84, "Hızır hub + video ara", "aktif"),
        ],
        "motors": {
            "genel": {"tag": f"Hub Faz 76–84 · Gemini {'✓' if gemini_ok else '?'}"},
            "hafiza": {"tag": "Faz 75 · Konuşarak yap (ROK)"},
            "hizir": {"tag": "Faz 84 · Hub + ticaret (ROK)"},
            "ses": {"tag": "Faz 72 · Konuşarak yap (ROK)"},
            "video": {"tag": "Faz 71/84 · İndir + ara (ROK)"},
            "okuma": {"tag": "Faz 73 · Konuşarak yap (ROK)"},
            "tercume": {"tag": "Faz 74 · Konuşarak yap (ROK)"},
            "programlama": {"tag": "Faz 68–83 · Konuşarak yap"},
        },
        "capabilities": [
            "Ana Motor hub: programlama, video, ses, okuma, tercüme, hafıza, hızır",
            "Video: URL indir · isimle YouTube ara · «2 numarayı indir»",
            "Video API: /api/video/download · /api/video/search",
            "Hızır: pazar tara · fırsat · hub yönlendirme",
            "Programlama Dalga H: çekirdek patch, mega refactor, zayıflık raporu, pr hazırla",
            "ROK tüm yardımcı motorlar · Ümit cevap emri",
            "scripts/rok_smoke.py · programlama_smoke.py",
        ],
        "video": {
            "download_api": "/api/video/download",
            "search_api": "/api/video/search",
            "recent_downloads": recent_downloads,
        },
    }
